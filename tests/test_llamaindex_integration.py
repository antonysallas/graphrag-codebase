from unittest.mock import MagicMock, patch

import pytest

from src.config import LLMConfig, Neo4jConfig
from src.indexing import GraphRAGIndex


@pytest.fixture
def mock_settings():
    with patch("src.indexing.graph_index.Settings") as mock_settings:
        yield mock_settings


@pytest.fixture
def mock_pg_index():
    with patch("src.indexing.graph_index.PropertyGraphIndex") as mock_idx:
        yield mock_idx


@pytest.fixture
def mock_neo4j_store():
    with patch("src.indexing.graph_index.Neo4jPropertyGraphStore") as mock_store:
        yield mock_store


def test_graph_rag_index_init(mock_settings, mock_pg_index, mock_neo4j_store):
    neo4j_config = Neo4jConfig(uri="bolt://localhost:7687", user="neo4j", password="password")
    llm_config = LLMConfig()

    index = GraphRAGIndex(neo4j_config, llm_config)

    mock_neo4j_store.assert_called_once()
    mock_pg_index.from_existing.assert_called_once()
    assert mock_settings.llm is not None


def test_query(mock_settings, mock_pg_index, mock_neo4j_store):
    neo4j_config = Neo4jConfig(uri="bolt://localhost:7687", user="neo4j", password="password")
    llm_config = LLMConfig()
    index = GraphRAGIndex(neo4j_config, llm_config)

    # Mock query engine
    mock_engine = MagicMock()
    index.index.as_query_engine.return_value = mock_engine

    # Mock response
    mock_response = MagicMock()
    mock_response.__str__.return_value = "Test Answer"
    mock_response.source_nodes = []
    mock_engine.query.return_value = mock_response

    result = index.query("test question")

    assert result["answer"] == "Test Answer"
    assert result["sources"] == []
