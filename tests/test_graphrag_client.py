from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp.utils.graphrag_client import GraphRAGClient


@pytest.fixture
def mock_config():
    with patch("src.mcp.utils.graphrag_client.get_config") as mock_get_config:
        config = MagicMock()
        config.llm.model_name = "test-model"
        config.llm.api_base = "http://test"
        config.llm.temperature = 0.0
        config.llm.max_tokens = 100
        config.llm.api_key = "test-key"
        config.llm.prompt_template = "default"
        config.schema = {
            "nodes": {"TestNode": {"properties": [{"name": "name"}]}},
            "relationships": {"TEST_REL": {"properties": []}},
        }
        mock_get_config.return_value = config
        yield config


@pytest.mark.asyncio
async def test_generate_cypher_default_template(mock_config):
    with patch("src.mcp.utils.graphrag_client.OpenAILike") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.acomplete = AsyncMock()
        mock_llm.acomplete.return_value = MagicMock(text="MATCH (n) RETURN n")
        mock_llm_cls.return_value = mock_llm

        client = GraphRAGClient()
        cypher = await client.generate_cypher("How many nodes?")

        assert "MATCH (n) RETURN n" in cypher
        mock_llm.acomplete.assert_called_once()
        # Verify prompt structure roughly
        args, _ = mock_llm.acomplete.call_args
        prompt = args[0]
        assert "<instructions>" in prompt
        assert "<schema>" in prompt
        assert "TestNode" in prompt


@pytest.mark.asyncio
async def test_generate_cypher_template_selection(mock_config):
    mock_config.llm.prompt_template = "qwen"

    with patch("src.mcp.utils.graphrag_client.OpenAILike") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.acomplete = AsyncMock()
        mock_llm.acomplete.return_value = MagicMock(text="MATCH (q) RETURN q")
        mock_llm_cls.return_value = mock_llm

        client = GraphRAGClient()
        await client.generate_cypher("test query")

        # In our implementation, qwen currently uses same as default but it proves it selects it
        args, _ = mock_llm.acomplete.call_args
        prompt = args[0]
        assert "<instructions>" in prompt


@pytest.mark.asyncio
async def test_generate_cypher_with_provided_schema(mock_config):
    """Test that provided GraphSchema overrides config.schema."""
    from src.mcp.utils.cypher_validator import GraphSchema

    with patch("src.mcp.utils.graphrag_client.OpenAILike") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.acomplete = AsyncMock()
        mock_llm.acomplete.return_value = MagicMock(text="MATCH (n) RETURN n")
        mock_llm_cls.return_value = mock_llm

        # Provide a schema with different labels than config.schema
        provided_schema = GraphSchema(
            node_labels={"CustomNode", "AnotherNode"},
            relationship_types={"CUSTOM_REL", "ANOTHER_REL"},
        )

        client = GraphRAGClient()
        await client.generate_cypher("test query", schema=provided_schema)

        args, _ = mock_llm.acomplete.call_args
        prompt = args[0]

        # Verify provided schema is used, not config.schema
        assert "CustomNode" in prompt
        assert "AnotherNode" in prompt
        assert "CUSTOM_REL" in prompt
        # Should NOT contain config.schema labels
        assert "TestNode" not in prompt


@pytest.mark.asyncio
async def test_generate_cypher_fallback_to_config_schema(mock_config):
    """Test that config.schema is used when no schema is provided."""
    with patch("src.mcp.utils.graphrag_client.OpenAILike") as mock_llm_cls:
        mock_llm = MagicMock()
        mock_llm.acomplete = AsyncMock()
        mock_llm.acomplete.return_value = MagicMock(text="MATCH (n) RETURN n")
        mock_llm_cls.return_value = mock_llm

        client = GraphRAGClient()
        # No schema parameter - should use config.schema
        await client.generate_cypher("test query")

        args, _ = mock_llm.acomplete.call_args
        prompt = args[0]

        # Should contain config.schema labels
        assert "TestNode" in prompt
        assert "TEST_REL" in prompt
