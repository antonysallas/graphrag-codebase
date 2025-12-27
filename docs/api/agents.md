# Agent API

The GraphRAG Agent API provides a programmatic interface for interacting with the knowledge graph using Large Language Models and autonomous tool calling.

## GraphRAGAgent

The primary class for AI interaction. It combines LlamaIndex retrieval with a persistent conversation memory.

### Basic Usage

```python
from src.agents import GraphRAGAgent

# Initialize agent (uses default LLM and Neo4j configs)
agent = GraphRAGAgent()

# Single query
response = await agent.chat("What playbooks exist in this codebase?")
print(f"Agent: {response.content}")

# Multi-turn conversation
conv_id = response.conversation_id
response2 = await agent.chat("Which of those use the 'apache' role?", conversation_id=conv_id)
print(f"Follow-up: {response2.content}")
```

### Response Object

The `AgentResponse` dataclass contains:

* `content`: The textual response from the LLM.
* `tool_calls`: A list of `ToolCall` objects representing the tools invoked by the agent.
* `conversation_id`: The ID required to continue the conversation.

### Tool Call Inspection

```python
if response.has_tool_calls:
    for tc in response.tool_calls:
        print(f"Tool: {tc.name}")
        print(f"Args: {tc.arguments}")
        print(f"Result: {tc.result}")
```

---

## See Also
* [Example: Agent Usage](../../examples/agent_usage.py)
* [Architecture: Agents](../architecture/overview.md#layer-5-agent-integration)
* [MCP Tools Reference](../reference/mcp-tools-reference.md)
