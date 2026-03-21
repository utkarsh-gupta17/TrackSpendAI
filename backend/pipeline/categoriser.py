import pandas as pd
import json
import re
from typing import Tuple, Dict, Any, List, Optional
from app.services.groq_client import call_fast

MERCHANT_RULES = {
    'Food & Dining': ['swiggy', 'zomato', 'dominos', 'mcdonalds', 'kfc', 'subway',
                      'dunzo', 'blinkit', 'bigbasket', 'grofers', 'instamart'],
    'Transport': ['uber', 'ola', 'rapido', 'redbus', 'irctc', 'makemytrip',
                  'goibibo', 'metro', 'fastag'],
    'Recharge & Bills': ['airtel', 'jio', 'vodafone', 'bsnl', 'electricity',
                          'bescom', 'mahadiscom', 'tata power', 'paytm postpaid'],
    'Shopping': ['amazon', 'flipkart', 'myntra', 'ajio', 'nykaa', 'meesho',
                 'snapdeal', 'tatacliq'],
    'Entertainment': ['netflix', 'hotstar', 'prime video', 'spotify', 'youtube',
                      'zee5', 'sonyliv', 'bookmyshow', 'pvr', 'inox'],
    'Healthcare': ['pharmeasy', 'netmeds', 'apollo', '1mg', 'practo', 'medplus'],
    'Education': ['udemy', 'coursera', 'byju', 'unacademy', 'vedantu', 'duolingo'],
    'Transfers': ['upi/', 'neft', 'imps', 'rtgs', 'transfer to', 'transfer from'],
    'Investment': ['zerodha', 'groww', 'upstox', 'kuvera', 'coin', 'sip',
                   'mutual fund', 'nps', 'ppf'],
    'Insurance': ['lic', 'hdfc life', 'icici pru', 'bajaj allianz', 'star health'],
}

def rule_based_categorise(description: str) -> Optional[str]:
    desc_lower = str(description).lower()
    for category, keywords in MERCHANT_RULES.items():
        if any(kw in desc_lower for kw in keywords):
            return category
    return None

def batch_llm_categorise(unresolved: List[Dict[str, Any]]) -> Dict[str, str]:
    if not unresolved:
        return {}
    
    prompt = f"""Categorise each UPI transaction description into one of these categories:
    Food & Dining, Transport, Recharge & Bills, Shopping, Entertainment, Healthcare,
    Education, Transfers, Investment, Insurance, Other.
    Descriptions: {json.dumps(unresolved)}
    Respond ONLY with a JSON object mapping id to category.
    Example: {{"tx_1": "Food & Dining", "tx_2": "Transport"}}"""
    
    response = call_fast(prompt)
    try:
        mapping = json.loads(re.search(r'\{.*\}', response, re.DOTALL).group())
        return mapping
    except Exception:
        return {item['id']: 'Other' for item in unresolved}

def run_categorisation(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    if df.empty:
        return df, {"total": 0, "rule_resolved": 0, "llm_resolved": 0, "unresolved": 0}

    df['category'] = df['description'].apply(rule_based_categorise)
    
    unresolved_rows = df[df['category'].isna()]
    unresolved_list = []
    for idx, row in unresolved_rows.iterrows():
        unresolved_list.append({"id": str(idx), "description": row['description']})
    
    llm_resolved_count = 0
    if unresolved_list:
        llm_mapping = batch_llm_categorise(unresolved_list)
        for idx_str, cat in llm_mapping.items():
            df.at[int(idx_str), 'category'] = cat
            llm_resolved_count += 1
            
    df['category'] = df['category'].fillna('Other')
    
    # Add helper columns
    df['amount_inr'] = df['amount'].apply(lambda x: f"₹{x:,.2f}")
    df['month_year'] = df['date'].dt.strftime('%b %Y')
    
    stats = {
        "total": len(df),
        "rule_resolved": len(df) - llm_resolved_count,
        "llm_resolved": llm_resolved_count,
        "unresolved": len(df[df['category'] == 'Other'])
    }
    
    return df, stats

def get_spending_summary(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {}
        
    df['type_lower'] = df['type'].str.lower()
    debits = df[df['type_lower'] == 'debit']
    credits = df[df['type_lower'] == 'credit']
    
    summary = {
        "total_debit": float(debits['amount'].sum()),
        "total_credit": float(credits['amount'].sum()),
        "by_category": {},
        "by_month": {},
        "top_merchants": {str(k): float(v) for k, v in debits.groupby('description')['amount'].sum().sort_values(ascending=False).head(10).to_dict().items()},
        "avg_transaction": float(debits['amount'].mean()) if not debits.empty else 0.0,
        "largest_transaction": debits.loc[debits['amount'].idxmax()].to_dict() if not debits.empty else None
    }
    
    # Handle largest_transaction datetime if present
    if summary['largest_transaction'] and 'date' in summary['largest_transaction']:
        if isinstance(summary['largest_transaction']['date'], pd.Timestamp):
            summary['largest_transaction']['date'] = summary['largest_transaction']['date'].isoformat()
            
    cat_group = debits.groupby('category')['amount'].agg(['sum', 'count'])
    total_spend = summary['total_debit']
    for cat, row in cat_group.iterrows():
        summary['by_category'][str(cat)] = {
            "total": float(row['sum']),
            "count": int(row['count']),
            "percentage_of_spend": float((row['sum'] / total_spend * 100)) if total_spend > 0 else 0.0
        }
        
    month_group = df.groupby('month_year')
    for month, group in month_group:
        summary['by_month'][str(month)] = {
            "debit": float(group[group['type_lower'] == 'debit']['amount'].sum()),
            "credit": float(group[group['type_lower'] == 'credit']['amount'].sum())
        }
        
    return summary
