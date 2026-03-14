import pytest
from unittest.mock import MagicMock, patch
from src.agents.semanticist import SemanticistAgent, IntelligentLLMWrapper
from src.models.nodes import ModuleNode

def test_token_counting():
    wrapper = IntelligentLLMWrapper()
    text = "Hello world"
    # Overly simplified check
    assert wrapper.count_tokens(text) > 0

@patch("ollama.chat")
@patch("ollama.embeddings")
@patch("chromadb.PersistentClient")
def test_semanticist_purpose(mock_chroma, mock_embed, mock_chat):
    # Mock Ollama chat
    mock_chat.return_value = {
        'message': {'content': "Purpose: This module handles data ingestion.\nDrift: No\nDriftReason: None"}
    }
    # Mock Ollama embeddings
    mock_embed.return_value = {'embedding': [0.1, 0.2, 0.3]}
    
    # Mock ChromaDB
    mock_client = MagicMock()
    mock_chroma.return_value = mock_client
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    agent = SemanticistAgent(repo_path="test_repo")
    node = ModuleNode(id="test.py", path="test.py", language=".py", loc=10, comment_ratio=0.1, change_frequency=1)
    
    result = agent.generate_purpose_statement(node, "def ingest(): pass")
    
    assert "ingestion" in result.purpose_statement
    assert result.is_doc_drift is False
    mock_collection.add.assert_called_once()

@patch("src.agents.semanticist.IntelligentLLMWrapper.chat")
@patch("chromadb.PersistentClient")
def test_clustering(mock_chroma, mock_chat):
    # Mock ChromaDB retrieval
    mock_client = MagicMock()
    mock_chroma.return_value = mock_client
    mock_collection = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection
    
    mock_collection.get.return_value = {
        'ids': ['module1', 'module2', 'module3', 'module4', 'module5', 'module6'],
        'embeddings': [
            [1.0, 0.0], [1.1, 0.1], # Cluster 1
            [0.0, 1.0], [0.1, 1.1], # Cluster 2
            [0.5, 0.5], [0.55, 0.55] # Cluster 3
        ],
        'documents': ['doc1', 'doc2', 'doc3', 'doc4', 'doc5', 'doc6']
    }
    
    mock_chat.return_value = "Ingestion" # Domain name label

    agent = SemanticistAgent(repo_path="test_repo")
    domain_map = agent.cluster_into_domains(n_clusters=3)
    
    assert len(domain_map) == 6
    assert domain_map['module1'] == "Ingestion"
