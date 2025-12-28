from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agents import GraphRAGAgent


@pytest.fixture
def mock_agent_deps():
    with (
        patch("src.agents.graphrag_agent.OpenAILike") as mock_llm_cls,
        patch("src.agents.graphrag_agent.GraphRAGIndex") as mock_index_cls,
    ):
        mock_llm = AsyncMock()
        mock_llm_cls.return_value = mock_llm

        mock_index = MagicMock()
        mock_index_cls.return_value = mock_index

        yield mock_llm, mock_index


@pytest.mark.asyncio
async def test_agent_initialization(mock_agent_deps):
    agent = GraphRAGAgent()
    assert agent.name == "graphrag"
    assert "query_codebase" in agent.available_tools


@pytest.mark.asyncio
async def test_chat_simple(mock_agent_deps):
    mock_llm, _ = mock_agent_deps

    # Mock LLM response
    mock_response = MagicMock()
    mock_response.message.content = "Hello there"
    mock_llm.achat.return_value = mock_response

    agent = GraphRAGAgent()
    response = await agent.chat("Hi")

    assert response.content == "Hello there"
    assert response.has_tool_calls is False
    assert response.conversation_id is not None


@pytest.mark.asyncio
async def test_chat_with_tool_call(mock_agent_deps):
    mock_llm, mock_index = mock_agent_deps

    # Mock LLM response with tool call
    mock_response = MagicMock()
    mock_response.message.content = """
    I'll check the codebase.
    ```json
    {
        "tool": "query_codebase",
        "args": {
            "question": "list files"
        }
    }
    ```
    """
    mock_llm.achat.return_value = mock_response

    # Mock index response
    mock_index.query.return_value = {"answer": "Some files"}

    agent = GraphRAGAgent()
    response = await agent.chat("List files")

    assert response.has_tool_calls is True
    assert len(response.tool_calls) == 1
    assert response.tool_calls[0].name == "query_codebase"
    assert response.tool_calls[0].result == {"answer": "Some files"}
