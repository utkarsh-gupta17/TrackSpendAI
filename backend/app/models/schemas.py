from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class Transaction(BaseModel):
    date: datetime
    amount: float
    type: str # 'debit' or 'credit'
    description: str
    counterparty: str = ""
    category: Optional[str] = None
    raw_description: str

class Anomaly(BaseModel):
    type: str
    transaction_id: Optional[str] = None
    amount: float
    date: datetime
    description: str
    severity: str # 'high', 'medium', 'low'
    reason: str

class Recommendation(BaseModel):
    title: str
    detail: str
    priority: str # 'high', 'medium', 'low'
    source: str # 'SEBI', 'RBI', 'Income Tax', 'General'

class FinancialReport(BaseModel):
    health_score: int
    health_label: str
    headline: str
    top_insights: List[str]
    recommendations: List[Recommendation]
    tax_tip: str
    savings_rate: float
    disclaimer: str
    transactions: List[Dict[str, Any]] = []
    anomaly_narrative: str = ""
    metadata: Dict[str, Any] = {}

class AnalysisResponse(BaseModel):
    type: str # 'progress', 'result', 'error'
    step: Optional[int] = None
    total: Optional[int] = None
    message: Optional[str] = None
    status: Optional[str] = None # 'running', 'done'
    report: Optional[FinancialReport] = None
    error_type: Optional[str] = None
