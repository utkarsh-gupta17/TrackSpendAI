import pandas as pd
import numpy as np
import pdfplumber
import re
import json
import io
from datetime import datetime
from typing import Tuple, Dict, Any, Optional
from app.services.groq_client import call_fast

class PasswordRequired(Exception):
    pass

def detect_format(filename: str, raw_bytes: bytes) -> str:
    """Returns 'pdf', 'csv', or 'xlsx' based on extension + magic bytes."""
    if filename.lower().endswith('.pdf') or raw_bytes[:4] == b'%PDF':
        return 'pdf'
    elif filename.lower().endswith('.xlsx') or raw_bytes[:4] == b'PK\x03\x04':
        return 'xlsx'
    else:
        return 'csv'

def extract_from_pdf(file_bytes: bytes, password: Optional[str] = None) -> pd.DataFrame:
    """
    Use pdfplumber to extract tables from PDF.
    If password provided, pass to pdfplumber.open(password=password).
    Try all pages, concatenate all tables found.
    If pdfplumber finds no tables, fall back to text extraction
    and parse lines that match date + amount patterns using regex.
    Regex pattern for fallback: r'(\d{2}[/-]\d{2}[/-]\d{2,4}).*?([+-]?\d+[,\d]*\.\d{2})'
    """
    try:
        with pdfplumber.open(io.BytesIO(file_bytes), password=password) as pdf:
            all_data = []
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    all_data.extend(table)
            
            if all_data:
                df = pd.DataFrame(all_data[1:], columns=all_data[0])
                return df
            
            # Fallback to text extraction
            text = ""
            for page in pdf.pages:
                text += page.extract_text() or ""
            
            pattern = re.compile(r'(\d{2}[/-]\d{2}[/-]\d{2,4}).*?([+-]?\d+[,\d]*\.\d{2})')
            matches = pattern.findall(text)
            if matches:
                return pd.DataFrame(matches, columns=['date', 'amount'])
                
            return pd.DataFrame()
    except Exception as e:
        if "password" in str(e).lower() or "encrypted" in str(e).lower():
            raise PasswordRequired("PDF is password-protected")
        raise e

def normalise_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect which columns map to: date, amount, type (credit/debit), description, counterparty.
    """
    if df.empty:
        return df

    cols = [str(c).lower().strip() for c in df.columns]
    mapping = {}
    
    # Rule-based matching
    date_hints = ['date', 'transaction date', 'txn date', 'value date', 'time']
    amount_hints = ['amount', 'txn amount', 'transaction amount', 'debit', 'credit', 'inr']
    desc_hints = ['description', 'narration', 'remarks', 'particulars', 'merchant']
    type_hints = ['type', 'cr/dr', 'dr/cr', 'transaction type']
    
    for i, col in enumerate(cols):
        if any(h in col for h in date_hints) and 'date' not in mapping:
            mapping['date'] = df.columns[i]
        elif any(h in col for h in amount_hints) and 'amount' not in mapping:
            mapping['amount'] = df.columns[i]
        elif any(h in col for h in desc_hints) and 'description' not in mapping:
            mapping['description'] = df.columns[i]
        elif any(h in col for h in type_hints) and 'type' not in mapping:
            mapping['type'] = df.columns[i]

    # If essential fields missing, use LLM
    if len(mapping) < 3:
        prompt = f"""Given these column names: {list(df.columns)}, map them to:
        date, amount, type, description, counterparty.
        Respond only with valid JSON like:
        {{"date": "col_name", "amount": "col_name", "type": "col_name", "description": "col_name", "counterparty": "col_name"}}
        If a field has no match, use null."""
        
        response = call_fast(prompt)
        try:
            llm_mapping = json.loads(re.search(r'\{.*\}', response, re.DOTALL).group())
            for k, v in llm_mapping.items():
                if v and v in df.columns:
                    mapping[k] = v
        except Exception:
            pass

    # Apply mapping
    new_df = pd.DataFrame()
    for canonical, original in mapping.items():
        if original in df.columns:
            new_df[canonical] = df[original]

    # Fill missing essential columns
    if 'date' not in new_df: new_df['date'] = pd.NA
    if 'amount' not in new_df: new_df['amount'] = 0.0
    if 'description' not in new_df: new_df['description'] = ""
    
    # Normalise amount and type
    def clean_amount(val):
        if pd.isna(val) or val == "": return 0.0
        val = str(val).replace('₹', '').replace('Rs.', '').replace(',', '').strip()
        try:
            return float(val)
        except:
            return 0.0

    new_df['amount'] = new_df['amount'].apply(clean_amount)
    
    if 'type' not in new_df:
        new_df['type'] = new_df['amount'].apply(lambda x: 'debit' if x < 0 else 'credit')
        new_df['amount'] = new_df['amount'].abs()
    else:
        new_df['type'] = new_df['type'].astype(str).str.lower().apply(lambda x: 'debit' if 'deb' in x or 'dr' in x else 'credit')

    # Normalise date
    new_df['date'] = pd.to_datetime(new_df['date'], errors='coerce')
    
    # Counterparty extraction
    def extract_counterparty(desc):
        if pd.isna(desc): return ""
        match = re.search(r'(?:UPI[-/](?:CR|DR)[-/]\d+[-/])([^/-]+)', str(desc))
        return match.group(1) if match else ""

    new_df['counterparty'] = new_df['description'].apply(extract_counterparty)
    new_df['raw_description'] = new_df['description']
    
    return new_df

def run_etl(file_bytes: bytes, filename: str, password: str = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    fmt = detect_format(filename, file_bytes)
    
    if fmt == 'pdf':
        df = extract_from_pdf(file_bytes, password)
    elif fmt == 'xlsx':
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        df = pd.read_csv(io.BytesIO(file_bytes))
        
    normalised_df = normalise_schema(df)
    
    # Metadata
    metadata = {
        "row_count": len(normalised_df),
        "format_detected": fmt,
        "date_range": f"{normalised_df['date'].min()} to {normalised_df['date'].max()}" if not normalised_df.empty else "N/A",
        "total_debit": normalised_df[normalised_df['type'] == 'debit']['amount'].sum(),
        "total_credit": normalised_df[normalised_df['type'] == 'credit']['amount'].sum(),
    }
    
    return normalised_df, metadata
