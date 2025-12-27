# Adding MCP Tools

MCP tools provide AI agents with a standardized way to interact with your knowledge graph. Each tool should represent a discrete, atomic capability (e.g., "Find all tasks by module" or "Trace this variable").

## Implementation Workflow

### 1. Write the Neo4j Logic

Create a new async function in `src/mcp/tools/` (e.g., `audit_tools.py`).

```python
from mcp.types import TextContent
from src.mcp.utils.neo4j_connection import get_neo4j_connection
from src.mcp.utils.tracing import trace_tool

@trace_tool("audit_permissions")
async def audit_file_permissions(file_path: str) -> list[TextContent]:
    """Search for 'mode' usage in tasks for a specific file."""
    conn = get_neo4j_connection()
    query = """
    MATCH (f:File {path: $path})<-[:IN_FILE]-(t:Task)
    WHERE t.args CONTAINS 'mode:'
    RETURN t.name as task, t.args as args
    """
    results = await conn.execute_query(query, {"path": file_path})
    return [TextContent(type="text", text=str(results))]
```

### 2. Register Tool in the Server

Open `src/mcp/server.py` and add your tool to the `list_tools()` definition and the `call_tool()` router.

```python
# Registration in list_tools()
Tool(
    name="audit_permissions",
    description="Finds file permission definitions in tasks.",
    inputSchema={
        "type": "object",
        "properties": {
            "file_path": {"type": "string"}
        },
        "required": ["file_path"]
    }
)

# Routing in call_tool()
if name == "audit_permissions":
    return await audit_file_permissions(arguments["file_path"])
```

## Best Practices

- **Description is Prompt Engineering**: The `description` field in `Tool` is what the LLM uses to decide when to call your tool. Be very specific.
- **Structured Output**: Use the `TextContent` type for consistent formatting.
- **Error Handling**: Wrap your logic in `try/except` blocks. Return user-friendly error messages that help the agent rephrase its request.
- **Always Trace**: The `@trace_tool` decorator is mandatory for production observability.

---

## See Also

- [MCP Tools Reference](../reference/mcp-tools-reference.md)
- [Observability with Langfuse](../getting-started/configuration.md)
- [Querying Graphs](../user-guide/querying-graphs.md)
