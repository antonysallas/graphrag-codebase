# MCP Tools

The GraphRAG Pipeline exposes its capabilities through the Model Context Protocol (MCP), enabling AI agents to interact with your codebase as a structured knowledge graph.

## Why use MCP?

Standard RAG (Retrieval-Augmented Generation) often struggles with source code because it treats files as flat text chunks. By using MCP tools, agents can:

- **Traverse Relationships**: Follow `NOTIFIES` or `USES_ROLE` links that cross file boundaries.
- **Understand Structure**: See the hierarchy of playbooks, plays, and tasks without reading every line of code.
- **Trace Data Flow**: Follow variable definitions across different scopes and inclusion levels.

## Available Tools

We provide 8 specialized tools designed for Ansible codebase analysis:

1. **`query_codebase`**: The most flexible tool. Ask any question in natural language.
2. **`find_dependencies`**: Identifies all files included or imported by a specific file.
3. **`trace_variable`**: Locates where a variable is defined and all places where it is used.
4. **`get_role_usage`**: Shows which playbooks and plays utilize a specific Ansible role.
5. **`analyze_playbook`**: Summarizes the plays, hosts, and task counts within a playbook.
6. **`find_tasks_by_module`**: Searches for all tasks using a specific module (e.g., `ansible.builtin.copy`).
7. **`get_task_hierarchy`**: Provides the execution order of tasks within a playbook.
8. **`find_template_usage`**: Finds Jinja2 templates and lists the variables they require.

## Client Integration

### Claude Desktop

To use these tools with Claude, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "graphrag-pipeline": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/graphrag-pipeline",
        "run", "graphrag-mcp"
      ]
    }
  }
}
```

### Direct Execution

For local testing or CLI-based agents, you can run the server in STDIO mode:

```bash
uv run graphrag-mcp
```

The server will wait for JSON-RPC requests on standard input.

---

## See Also

- [MCP Tools Reference](../reference/mcp-tools-reference.md)
- [Querying Graphs](querying-graphs.md)
- [Architecture: Layer 4](../architecture/5-layer-design.md)
