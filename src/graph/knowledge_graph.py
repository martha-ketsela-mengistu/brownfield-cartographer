import networkx as nx
import json
import os
from typing import List, Dict, Any
from ..models.nodes import ModuleNode
from ..models.graph import KnowledgeGraph

class KnowledgeGraphManager:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.data_store = KnowledgeGraph()
        self.lineage_graph = nx.DiGraph()

    def add_module(self, node: ModuleNode):
        # Remove existing module with same ID if it exists (for incremental updates)
        self.data_store.modules = [m for m in self.data_store.modules if m.id != node.id]
        self.data_store.modules.append(node)
        
        # Update graph node
        if node.id in self.graph:
            self.graph.remove_node(node.id)
        self.graph.add_node(node.id, **node.model_dump(mode='json'))
        
        # Add edges for imports
        for imp in node.imports:
            # Simple heuristic for now: if import looks like a local module path
            if "/" in imp or "." in imp:
                target = imp.split(" ")[-1]
                self.graph.add_edge(node.id, target, type="IMPORTS")

    def add_lineage(self, source: str, target: str, transformation_type: str, file_path: str):
        self.lineage_graph.add_edge(source, target, 
                                   type=transformation_type, 
                                   file_path=file_path)

    def blast_radius(self, node_id: str) -> List[str]:
        """Find all downstream dependents."""
        if node_id not in self.lineage_graph:
            return []
        return list(nx.descendants(self.lineage_graph, node_id))

    def find_sources(self) -> List[str]:
        return [n for n, d in self.lineage_graph.in_degree() if d == 0]

    def find_sinks(self) -> List[str]:
        return [n for n, d in self.lineage_graph.out_degree() if d == 0]

    def get_upstream(self, node_id: str) -> List[str]:
        if node_id not in self.lineage_graph:
            return []
        return list(nx.ancestors(self.lineage_graph, node_id))

    def compute_pagerank(self) -> Dict[str, float]:
        if len(self.graph) == 0:
            return {}
        return nx.pagerank(self.graph)

    def serialize_lineage(self, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = nx.node_link_data(self.lineage_graph)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def serialize(self, output_path: str):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        data = nx.node_link_data(self.graph)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def save_knowledge_graph(self, output_path: str):
        with open(output_path, "w") as f:
            f.write(self.data_store.model_dump_json(indent=2))

    def deserialize(self, input_path: str):
        with open(input_path, "r") as f:
            data = json.load(f)
        self.graph = nx.node_link_graph(data)
        
        # Reconstruct data_store.modules from graph nodes
        self.data_store.modules = []
        for node_id, data in self.graph.nodes(data=True):
            # Convert graph data back to ModuleNode
            # Filter out NetworkX specific internal keys if any
            node_data = {k: v for k, v in data.items() if not k.startswith("_")}
            try:
                self.data_store.modules.append(ModuleNode(**node_data))
            except Exception as e:
                import logging
                logging.error(f"Failed to deserialize module {node_id}: {e}")

    def deserialize_lineage(self, input_path: str):
        with open(input_path, "r") as f:
            data = json.load(f)
        self.lineage_graph = nx.node_link_graph(data)
