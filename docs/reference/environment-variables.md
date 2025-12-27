# Environment Variables

Reference for all configuration variables used by the GraphRAG Pipeline. These can be set in your OS environment or a local `.env` file.

## Neo4j Configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `NEO4J_URI` | Neo4j Bolt connection URI. | `bolt://localhost:7687` |
| `NEO4J_USER` | Database username. | `neo4j` |
| `NEO4J_PASSWORD` | Database password. | - |
| `NEO4J_DATABASE` | Target database name. | `neo4j` |
| `NEO4J_QUERY_TIMEOUT` | Max execution time (seconds). | `10.0` |

## Pipeline Execution

| Variable | Description | Default |
|----------|-------------|---------|
| `CODEBASE_PATH` | Path to the Ansible code to index. | - |
| `BATCH_SIZE` | Nodes per transaction during indexing. | `100` |
| `MAX_WORKERS` | Parallel parsing concurrency. | `4` |
| `LOG_LEVEL` | Verbosity (DEBUG, INFO, WARNING, ERROR). | `INFO` |

## LLM & AI

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | AI backend (`vllm`, `openai`). | `vllm` |
| `API_BASE` | API endpoint URL. | `http://localhost:11434/v1` |
| `MODEL_NAME` | The LLM model ID. | `Qwen/Qwen2.5-Coder-7B-Instruct` |
| `TEMPERATURE` | Model temperature. | `0.0` |
| `LLM_API_KEY` | Authentication key for provider. | `fake` |
| `LLM_PROMPT_TEMPLATE` | Prompt template ID (`default`, `qwen`). | `default` |

## Langfuse Observability

| Variable | Description | Default |
|----------|-------------|---------|
| `LANGFUSE_ENABLED` | Enable tool and query tracing. | `false` |
| `LANGFUSE_PUBLIC_KEY` | Your project's public key. | - |
| `LANGFUSE_SECRET_KEY` | Your project's secret key. | - |
| `LANGFUSE_HOST` | Host for the Langfuse backend. | `https://cloud.langfuse.com` |

## MCP Server

| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_SERVER_HOST` | Binding address for HTTP mode. | `127.0.0.1` |
| `MCP_SERVER_PORT` | Listening port for HTTP mode. | `5003` |
| `MCP_DEBUG` | Enable debug mode for the MCP protocol. | `false` |

---

## See Also

- [Configuration Guide](../getting-started/configuration.md)
- [Installation](../getting-started/installation.md)
- [Production Checklist](../deployment/production-checklist.md)
