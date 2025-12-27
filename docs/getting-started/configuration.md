# Configuration

Configure the GraphRAG pipeline using environment variables or a `.env` file in the project root.

## Core Settings

The following variables control the connection to your Neo4j database.

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Connection string for Neo4j. |
| `NEO4J_USER` | `neo4j` | Database username. |
| `NEO4J_PASSWORD` | - | Database password (Required). |
| `NEO4J_DATABASE` | `neo4j` | Target database name. |
| `NEO4J_QUERY_TIMEOUT` | `10.0` | Max execution time for queries in seconds. |

## Pipeline Execution

Control how the codebase is parsed and indexed.

| Variable | Default | Description |
|----------|---------|-------------|
| `CODEBASE_PATH` | - | Path to the Ansible codebase to analyze. |
| `MAX_WORKERS` | `4` | Number of parallel threads for parsing. |
| `BATCH_SIZE` | `100` | Nodes/relationships per Neo4j transaction. |
| `LOG_LEVEL` | `INFO` | Verbosity (DEBUG, INFO, WARNING, ERROR). |

## LLM Settings

These settings are used by the GraphRAG query layer to translate natural language into Cypher.

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `vllm` | AI provider (`vllm`, `openai`, `ollama`). |
| `API_BASE` | `http://localhost:11434/v1` | Endpoint for the LLM API. |
| `MODEL_NAME` | `Qwen/Qwen2.5-Coder-7B-Instruct` | The specific model ID to use. |
| `TEMPERATURE` | `0.0` | Controls randomness (0.0 is deterministic). |
| `LLM_PROMPT_TEMPLATE` | `default` | Selection of prompt engineering template. |

## Observability (Langfuse)

We use Langfuse for end-to-end tracing of tool calls and LLM generations.

| Variable | Default | Description |
|----------|---------|-------------|
| `LANGFUSE_ENABLED` | `false` | Set to `true` to enable tracing. |
| `LANGFUSE_PUBLIC_KEY` | - | Your Langfuse public key. |
| `LANGFUSE_SECRET_KEY` | - | Your Langfuse secret key. |
| `LANGFUSE_HOST` | `https://cloud.langfuse.com` | Langfuse host URL. |

## MCP Server

Configuration for the Model Context Protocol server.

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVER_HOST` | `127.0.0.1` | Binding address for HTTP mode. |
| `MCP_SERVER_PORT` | `5003` | Binding port for HTTP mode. |
| `MCP_RATE_LIMIT_PER_MINUTE` | `100` | Max requests per client per minute. |

---

## See Also

- [Environment Variables Reference](../reference/environment-variables.md)
- [Production Checklist](../deployment/production-checklist.md)
