# GraphRAG Search UI

A web-based interface for querying your codebase using natural language.

## Starting the UI

```bash
uv run python llamastack/graphrag_ui.py
```

The UI will be available at [http://localhost:11436](http://localhost:11436).

## Prerequisites

* **Neo4j database** running with indexed repositories.
* **LLM Provider** configured in `.env` (e.g., vLLM, Ollama, or OpenAI-compatible API).
* **Python 3.13+** environment.

## Features

### Natural Language Queries

Ask questions about your codebase in plain English:

* *"What playbooks are in this codebase?"*
* *"Find all tasks that use the copy module"*
* *"What classes are defined in the extractor module?"*

### Repository Selection

Select which repository to query from the dropdown:

* **All Repositories**: Query across all indexed repos (useful for role usage).
* **Specific repo**: Filter results to one repository.

### Available Tools

The UI uses the GraphRAG Agent which has access to these tools:

| Tool | Description |
|----|----|
| `query_codebase` | Natural language to Cypher queries |
| `find_dependencies` | Find file dependencies |
| `get_role_usage` | Find where roles are used (cross-repo) |
| `find_tasks_by_module` | Find tasks using specific modules |
| `analyze_playbook` | Analyze playbook structure |
| `trace_variable` | Trace variable definitions and usage |
| `query_with_rag` | Hybrid retrieval using LlamaIndex |

### Example Queries

Click on example queries to auto-fill the input:

**Ansible:**

* What playbooks are in this codebase?
* Find all tasks that use the copy module
* What roles are available?

**Python:**

* What classes are defined in the extractor module?
* Find all functions that call Neo4j
* What modules import asyncio?

**Cross-repo:**

* Which repositories use the geerlingguy.apache role?

## Configuration

The UI uses the project's global configuration (`src/config.py`).

### LLM Provider

Configure your LLM in `.env`:

```bash
LLM_PROVIDER=vllm
API_BASE=http://localhost:11434/v1
LLM_API_KEY=fake
MODEL_NAME=Qwen/Qwen2.5-Coder-7B-Instruct
```

### Neo4j Connection

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
```

### Langfuse Tracing (Optional)

Enable tracing in `.env`:

```bash
LANGFUSE_ENABLED=true
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-xxx
LANGFUSE_SECRET_KEY=sk-xxx
```

## Troubleshooting

### "Error: Neo4j connection failed"

Ensure your Neo4j container is running:

```bash
docker ps | grep neo4j
```

### "No results found"

1. Check if repositories are indexed:

    ```bash
    uv run python scripts/build_graph.py list-repos
    ```

2. Verify your repository selection matches the indexed data.

### "Error: LLM API connection failed"

Ensure your LLM provider (vLLM/Ollama) is running and reachable at the configured `API_BASE`.

---

## See Also

* [Querying Graphs](querying-graphs.md)

* [Configuration Guide](../getting-started/configuration.md)
* [Agent API](../api/agents.md)
