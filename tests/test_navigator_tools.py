import pytest
from unittest.mock import MagicMock, patch
from src.agents.navigator import blast_radius, trace_lineage
from src.graph.knowledge_graph import KnowledgeGraphManager

@patch("src.agents.navigator._kg_manager")
def test_blast_radius_tool(mock_kg):
    # Mock lineage graph with a cycle or transitive deps
    import networkx as nx
    G = nx.DiGraph()
    G.add_edge("A", "B")
    G.add_edge("B", "C")
    mock_kg.lineage_graph = G
    
    # Test tool
    # Tools are StructuredTool objects, call the underlying function
    result = blast_radius.func("A")
    assert "B" in result
    assert "C" in result
    assert "Transitive" in result

@patch("src.agents.navigator._kg_manager")
def test_trace_lineage_tool(mock_kg):
    import networkx as nx
    G = nx.DiGraph()
    G.add_edge("source_db", "dataset_A")
    mock_kg.lineage_graph = G
    
    result = trace_lineage.func("dataset_A")
    assert "source_db" in result
