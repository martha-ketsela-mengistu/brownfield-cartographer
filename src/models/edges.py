from typing import Dict, Any, Optional
from pydantic import BaseModel

class ImportEdge(BaseModel):
    source_module: str
    target_module: str
    weight: int = 1  # import_count

class ProduceEdge(BaseModel):
    transformation: str
    dataset: str

class ConsumeEdge(BaseModel):
    transformation: str
    dataset: str

class CallEdge(BaseModel):
    caller: str
    callee: str

class ConfigureEdge(BaseModel):
    config_file: str
    target: str  # module/pipeline
