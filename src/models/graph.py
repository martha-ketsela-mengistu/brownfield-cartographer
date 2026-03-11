from typing import List
from pydantic import BaseModel
from .nodes import ModuleNode, DatasetNode, FunctionNode, TransformationNode
from .edges import ImportEdge, ProduceEdge, ConsumeEdge, CallEdge, ConfigureEdge

class KnowledgeGraph(BaseModel):
    modules: List[ModuleNode] = []
    datasets: List[DatasetNode] = []
    functions: List[FunctionNode] = []
    transformations: List[TransformationNode] = []
    
    imports: List[ImportEdge] = []
    produces: List[ProduceEdge] = []
    consumes: List[ConsumeEdge] = []
    calls: List[CallEdge] = []
    configures: List[ConfigureEdge] = []
