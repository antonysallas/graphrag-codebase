# MCP Tools API

The Model Context Protocol (MCP) server exposes the following tools for AI agents.

## query_with_rag

The primary tool for universal codebase understanding. It uses LlamaIndex's `PropertyGraphIndex` for hybrid retrieval.

### Input Schema

```json
{
  "question": "Natural language question",
  "include_cypher": "Boolean (default: false)"
}
```

### Response

Returns a comprehensive answer derived from both graph traversal and semantic similarity, including specific source nodes from the graph.

---

## Existing Tools

For a full list of Ansible-specific tools (e.g., `trace_variable`, `analyze_playbook`), see the [MCP Tools Reference](../reference/mcp-tools-reference.md).

---

## See Also

- [User Guide: MCP Tools](../user-guide/mcp-tools.md)
- [LlamaIndex Integration](../../src/indexing/graph_index.py)
