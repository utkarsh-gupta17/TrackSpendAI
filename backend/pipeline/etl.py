import pandas as pd
import io
import re
import pypdf
from pypdf.errors import PdfReadError
import pdfplumber

class PasswordRequired(Exception):
    pass

def extract_from_pdf(file_bytes: bytes, password: str = None) -> pd.DataFrame:
    """
    Two-stage extraction strategy optimised for speed on low-resource servers.

    Stage 1 — pypdf (fast, ~0.5s):
    Try pypdf first. It extracts raw text per page.
    Parse text lines looking for rows that match:
    - A date pattern: \d{2}[/-]\d{2}[/-]\d{2,4}
    - An amount pattern: \d{1,3}(?:,\d{3})*(?:\.\d{2})?
    If pypdf finds >5 valid transaction rows, use this result.

    Stage 2 — pdfplumber (slower, ~5-15s, but handles complex tables):
    Fall back to pdfplumber only if pypdf found <5 valid rows.

    File size guard: 5MB
    """
    # Size guard
    if len(file_bytes) > 5_000_000:
        raise ValueError("File too large. Please upload a PDF under 5MB. Most UPI statements are under 1MB.")

    # Stage 1: pypdf (fast path)
    try:
        reader = pypdf.PdfReader(
            io.BytesIO(file_bytes),
            password=password
        )
        all_text = []
        for page in reader.pages:
            all_text.append(page.extract_text() or "")
        full_text = "\n".join(all_text)

        rows = _parse_text_to_rows(full_text)
        if len(rows) >= 5:
            return pd.DataFrame(rows)
        # Less than 5 rows found — fall through to pdfplumber
    except PdfReadError as e:
        if "password" in str(e).lower() or "encrypt" in str(e).lower():
            raise PasswordRequired("PDF is password protected")
    except Exception:
        pass  # Fall through to pdfplumber

    # Stage 2: pdfplumber (slow but thorough)
    try:
        with pdfplumber.open(io.BytesIO(file_bytes), password=password) as pdf:
            all_tables = []
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    all_tables.extend(table)
            if all_tables:
                # Basic normalization for common header-based tables
                return pd.DataFrame(all_tables[1:], columns=all_tables[0])
    except Exception as e:
        if "password" in str(e).lower():
            raise PasswordRequired("PDF is password protected")
        raise ValueError(f"Could not parse PDF: {str(e)}")

    raise ValueError("No transaction data found in this PDF. Try downloading as CSV from your UPI app instead.")


def _parse_text_to_rows(text: str) -> list[dict]:
    """
    Parse raw text extracted by pypdf into transaction rows.
    Look for lines containing a date + amount pattern.
    Returns list of dicts with raw fields for normalisation.
    """
    rows = []
    # Pattern: date (various formats) anywhere in line + amount
    date_pattern = r'\b(\d{2}[/-]\d{2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b'
    amount_pattern = r'₹?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?)'

    for line in text.split('\n'):
        line = line.strip()
        if not line:
            continue
        date_match = re.search(date_pattern, line)
        amount_matches = re.findall(amount_pattern, line)
        if date_match and amount_matches:
            rows.append({
                "raw_date": date_match.group(1),
                "raw_amount": amount_matches[-1],  # Last amount is usually the transaction amount
                "raw_description": line,
            })
    return rows

def run_etl(file_bytes: bytes, filename: str, password: str = None):
    """Entry point for ETL pipeline."""
    if filename.endswith(".pdf"):
        df = extract_from_pdf(file_bytes, password)
    elif filename.endswith(".csv"):
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif filename.endswith(".xlsx"):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file format. Please upload PDF, CSV, or XLSX.")

    # Basic cleaning
    df = df.dropna(how='all')
    
    # Metadata for UI
    metadata = {
        "filename": filename,
        "row_count": len(df),
        "date_range": "N/A" # Will be updated in normalization
    }
    
    # Minimal normalization needed for subsequent stages
    # (Simplified for this prompt, usually more robust)
    if 'raw_date' in df.columns:
        df['date'] = pd.to_datetime(df['raw_date'], errors='coerce', dayfirst=True)
    elif 'Date' in df.columns:
        df['date'] = pd.to_datetime(df['Date'], errors='coerce', dayfirst=True)
    else:
        # Fallback if no date column found
        df['date'] = pd.to_datetime('today')

    if 'raw_amount' in df.columns:
        df['amount'] = df['raw_amount'].str.replace('[,₹ ]', '', regex=True).astype(float)
    elif 'Amount' in df.columns:
        df['amount'] = df['Amount'].astype(float)
    else:
        df['amount'] = 0.0

    if 'raw_description' in df.columns:
        df['description'] = df['raw_description']
    elif 'Description' in df.columns:
        df['description'] = df['Description']
    else:
        df['description'] = "Unknown"

    # Update date range
    valid_dates = df['date'].dropna()
    if not valid_dates.empty:
        metadata["date_range"] = f"{valid_dates.min().strftime('%b %Y')} - {valid_dates.max().strftime('%b %Y')}"

    return df, metadata
