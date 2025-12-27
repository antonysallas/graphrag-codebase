# CLI Reference

The GraphRAG Pipeline provides two main command-line interfaces for managing knowledge graphs and exposing them to agents.

## `graphrag-build`

Builds or updates the knowledge graph from a codebase directory.

### Usage

```bash
uv run python scripts/build_graph.py build PATH [OPTIONS]
```

### Arguments

- `<codebase_path>`: (Required) Path to the local filesystem directory containing your source code.

### Options

| Option | Description | Default |
|----|----|----|
| `--repo-id TEXT` | Repository identifier | Auto-detected from directory |
| `--repo-type TEXT` | Repository type (ansible, python, generic, auto) | auto |
| `--clear` | Clear existing nodes for this repo before building | False |
| `--workers INT` | Maximum parallel workers | From config |
| `--log-level TEXT` | Logging level | INFO |
| `--config-dir PATH` | Path to custom config directory | None |

## Other Commands

### list-repos

List all indexed repositories.

```bash
uv run python scripts/build_graph.py list-repos
```

### clear-repo

Clear all nodes for a repository (keeps shared Roles).

```bash
uv run python scripts/build_graph.py clear-repo REPO_ID
```

---

## `graphrag-mcp`

Starts the Model Context Protocol (MCP) server.

### Usage

```bash
uv run graphrag-mcp [OPTIONS]
```

### Modes

- **STDIO**: (Default) Communicates via standard input and output. Use this when connecting to local clients like Claude Desktop.
- **HTTP/SSE**: Starts a long-running web server.

### Options

- `--host <address>`: Host to bind (e.g., `0.0.0.0`). Default is `127.0.0.1`.
- `--port <number>`: Port to listen on. Default is `5003`.

---

## See Also

- [Installation](../getting-started/installation.md)
- [MCP Tools Reference](mcp-tools-reference.md)
- [User Guide: Building Graphs](../user-guide/building-graphs.md)
