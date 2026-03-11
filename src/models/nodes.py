from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

class ModuleNode(BaseModel):
    id: str
    path: str
    language: str
    imports: List[str] = []
    functions: List[str] = []
    classes: List[str] = []
    loc: int
    comment_ratio: float
    change_frequency: int
    purpose_statement: Optional[str] = None
    domain_cluster: Optional[str] = None
    complexity_score: float = 0.0 # Cyclomatic complexity
    is_dead_code_candidate: bool = False
    last_modified: datetime = Field(default_factory=datetime.now)

class DatasetNode(BaseModel):
    id: str
    name: str
    storage_type: str  # [table|file|stream|api]
    schema_snapshot: Optional[Dict[str, Any]] = None
    freshness_sla: Optional[str] = None
    owner: Optional[str] = None
    is_source_of_truth: bool = False

class FunctionNode(BaseModel):
    qualified_name: str
    parent_module: str
    signature: str
    purpose_statement: Optional[str] = None
    call_count_within_repo: int = 0
    is_public_api: bool = True

class TransformationNode(BaseModel):
    source_datasets: List[str]
    target_datasets: List[str]
    transformation_type: str # [batch|streaming|api]
    source_file: str
    line_range: tuple[int, int]
    sql_query_if_applicable: Optional[str] = None
