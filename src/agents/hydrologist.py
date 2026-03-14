import os
from typing import List, Dict, Any
from ..analyzers.sql_lineage import SQLLineageAnalyzer
from ..analyzers.python_data_flow import PythonDataFlowAnalyzer
from ..analyzers.dag_config_parser import DAGConfigAnalyzer
from ..graph.knowledge_graph import KnowledgeGraphManager
from ..utils.trace_logger import default_trace

class HydrologistAgent:
    def __init__(self, repo_path: str, kg_manager: KnowledgeGraphManager):
        self.repo_path = repo_path
        self.kg_manager = kg_manager
        self.sql_analyzer = SQLLineageAnalyzer()
        self.python_analyzer = PythonDataFlowAnalyzer()
        self.config_analyzer = DAGConfigAnalyzer()

    def analyze_lineage(self):
        """
        Walks through the repo and extracts lineage using all available analyzers.
        """
        for root, dirs, files in os.walk(self.repo_path):
            # Exclude directories
            dirs[:] = [d for d in dirs if d not in [".git", "__pycache__", ".venv", ".cartography", ".antigravity", ".specify"]]
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_path)
                
                if file.endswith(".sql"):
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    lineage = self.sql_analyzer.extract_dependencies(content)
                    
                    # For dbt models, if no target is found, use the file name
                    if not lineage.get("targets"):
                        model_name = os.path.splitext(file)[0]
                        lineage["targets"] = [model_name]
                        
                    self._add_to_graph(lineage, "sql", rel_path)
                
                elif file.endswith(".py"):
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    lineage = self.python_analyzer.analyze_content(content)
                    self._add_to_graph(lineage, "python", rel_path)
                
                elif file.endswith(".yml") or file.endswith(".yaml"):
                    if "schema" in file or "sources" in file:
                        lineage = self.config_analyzer.parse_dbt_schema(file_path)
                        self._add_to_graph(lineage, "dbt_config", rel_path)

    def _add_to_graph(self, lineage: Dict[str, List[str]], trans_type: str, file_path: str):
        sources = lineage.get("sources", [])
        targets = lineage.get("targets", [])
        
        for tgt in targets:
            for src in sources:
                self.kg_manager.add_lineage(src, tgt, trans_type, file_path)
                
        # Log to trace
        default_trace.log_action(
            agent="Hydrologist",
            action="extract_lineage",
            evidence=f"{trans_type} analyzer on {file_path}",
            confidence=0.85,
            metadata={"sources": sources, "targets": targets, "path": file_path}
        )
