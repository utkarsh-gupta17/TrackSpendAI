import json
import pandas as pd
from typing import List, Dict, Any
import re
from app.services.groq_client import call_quality

def run_synthesis(summary: Dict[str, Any], anomalies: List[Dict[str, Any]], rag_context: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
    system_prompt = """You are TrackSpendAI, an AI financial analyst specialising in Indian personal finance.
    You analyse UPI spending data and provide grounded, actionable advice.
    Always cite specific numbers from the user's data.
    Reference Indian financial guidelines (SEBI, RBI, Income Tax) when giving advice.
    Use ₹ symbol. Be warm and encouraging, not preachy.
    Never give stock or crypto investment advice.
    End with a disclaimer: For educational purposes only. Consult a SEBI-registered advisor for personalised advice."""

    # Calculate savings rate
    debit = summary.get('total_debit', 0)
    credit = summary.get('total_credit', 0)
    savings_rate = (credit - debit) / credit * 100 if credit > 0 else 0

    user_prompt = f'''Analyse this user's UPI spending data and generate a financial health report.

    SPENDING SUMMARY:
    {json.dumps(summary, indent=2)}

    ANOMALIES DETECTED:
    {json.dumps(anomalies, indent=2)}

    RELEVANT FINANCIAL GUIDELINES (retrieved from official sources):
    {chr(10).join([f"[{c['source_file']}] {c['text']}" for c in rag_context])}

    Generate a JSON response with exactly these keys:
    {{
      "health_score": <integer 0-100>,
      "health_label": <"Excellent"|"Good"|"Fair"|"Needs Attention">,
      "headline": <one sentence summary of their financial health>,
      "top_insights": [<3-4 specific insights referencing their actual numbers>],
      "recommendations": [
        {{
          "title": <short title>,
          "action": <1-2 sentences with specific action + Indian context>,
          "reason": <explain WHY by pointing out specific instances from their spending anomalies or totals>,
          "priority": <"high"|"medium"|"low">,
          "source": <"SEBI"|"RBI"|"Income Tax"|"General">
        }}
      ],
      "savings_rate": {savings_rate:.1f}
    }}

    Respond ONLY with valid JSON. No markdown, no preamble.'''

    response = call_quality(user_prompt, system=system_prompt)
    
    try:
        # Better JSON extraction
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            report = json.loads(match.group())
        else:
            raise ValueError("No JSON found in response")
        return report
    except Exception as e:
        print(f"Failed to parse synthesis JSON: {e}")
        # Fallback report
        return {
            "health_score": 50,
            "health_label": "Fair",
            "headline": "We've analysed your data and prepared some insights.",
            "top_insights": ["Your total spending was ₹" + str(debit)],
            "recommendations": [],
            "savings_rate": round(savings_rate, 1),
            "disclaimer": "For educational purposes only."
        }
