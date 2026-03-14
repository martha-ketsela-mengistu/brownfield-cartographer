from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ContextWindowBudget(BaseModel):
    """
    Tracks LLM token/character usage and budget limits.
    """
    total_tokens_used: int = 0
    total_estimated_cost: float = 0.0
    budget_limit: float = 10.0  # Default $10 budget for testing
    model_name: str = "llama3.2:3b"

class SemanticAnalysisResult(BaseModel):
    """
    Storage for the output of a single module's semantic analysis.
    """
    module_id: str
    purpose_statement: str
    is_doc_drift: bool = False
    doc_drift_explanation: Optional[str] = None
    domain_cluster: Optional[str] = None
    embedding: List[float] = []
    analyzed_at: datetime = Field(default_factory=datetime.now)
