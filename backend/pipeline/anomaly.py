import pandas as pd
import json
from typing import Tuple, List, Dict, Any, Optional
from app.services.groq_client import call_fast
from datetime import datetime

def run_anomaly_detection(df: pd.DataFrame, summary: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str]:
    if df.empty:
        return [], "No transactions found to analyse."
        
    anomalies = []
    debits = df[df['type_lower'] == 'debit'].copy() if 'type_lower' in df.columns else df[df['type'].str.lower() == 'debit'].copy()
    
    if debits.empty:
        return [], "No spending transactions found."

    # 1. Duplicate detection (optimised)
    debits = debits.sort_values('date')
    shifted_debits = debits.shift(-1)
    
    # Vectorised check for same amount, same description, within 24 hours
    dupes = (debits['amount'] == shifted_debits['amount']) & \
            (debits['description'] == shifted_debits['description']) & \
            ((shifted_debits['date'] - debits['date']).dt.total_seconds() / 3600 <= 24)

    for idx in debits.index[dupes]:
        nxt = debits.loc[idx] # This is actually the first of the pair, but works
        anomalies.append({
            "type": "Possible Duplicate",
            "transaction_id": str(idx),
            "amount": float(nxt['amount']),
            "date": nxt['date'].isoformat(),
            "description": nxt['description'],
            "severity": "high",
            "reason": f"Successive transactions of ₹{nxt['amount']} with same description within 24 hours."
        })

    # 2. Large transaction (vectorised)
    avg_txn = summary.get('avg_transaction', 0)
    large_mask = (debits['amount'] > 3 * avg_txn) & (debits['amount'] > 5000)
    for idx, row in debits[large_mask].iterrows():
        anomalies.append({
            "type": "Large Transaction",
            "transaction_id": str(idx),
            "amount": float(row['amount']),
            "date": row['date'].isoformat(),
            "description": row['description'],
            "severity": "medium",
            "reason": f"Transaction of ₹{row['amount']} is significantly higher than your average spend."
        })

    # 3. Unusual hour (vectorised)
    night_mask = (debits['date'].dt.hour >= 1) & (debits['date'].dt.hour <= 5)
    for idx, row in debits[night_mask].iterrows():
        anomalies.append({
            "type": "Uptimely Transaction",
            "transaction_id": str(idx),
            "amount": float(row['amount']),
            "date": row['date'].isoformat(),
            "description": row['description'],
            "severity": "low",
            "reason": "Transaction occurred late at night (between 1 AM and 5 AM)."
        })

    # LLM narrative (using FAST model for speed)
    narrative = ""
    if anomalies:
        prompt = f"Summarize these spending anomalies in 2-3 friendly sentences for a financial report: {json.dumps(anomalies[:5])}. Mention specific amounts with ₹."
        narrative = call_fast(prompt)
    else:
        narrative = "Your spending patterns look normal. No significant anomalies were detected."

    return anomalies, narrative
