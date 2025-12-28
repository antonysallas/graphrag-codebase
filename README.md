# GraphRAG Pipeline

Transform codebases into queryable Neo4j knowledge graphs using Abstract Syntax Tree (AST) parsing. Supports **Ansible** and **Python** codebases with natural language querying via MCP tools and a web UI.

## Architecture

This pipeline follows a **5-layer architecture**:

1. **AST Parsing & Extraction** - Tree-sitter parsers for YAML, Python, Jinja2, Ruby
2. **Graph Construction** - Neo4j graph database with rich schema (10 node types, 13 relationship types)
3. **GraphRAG Query** - LlamaIndex for natural language to Cypher conversion with local LLM (vLLM)
4. **MCP Server** - Model Context Protocol tools for LLM agent integration
5. **Agents & UI** - Gradio web interface and LlamaIndex agents for interactive queries

## Features

- **Multi-language Support**: Tree-sitter parsing for YAML (playbooks), Python (inventory scripts), Jinja2 (templates), Ruby (Vagrantfiles)
- **Comprehensive Relationships**: Tracks file dependencies, role relationships, task hierarchies, and variable flow
- **Git-based Ingestion**: Clone any Ansible repository at runtime for graph building
- **Containerized**: Production-ready Docker image
- **Efficient Parsing**: Parallel processing with configurable workers, ~10-20 files/second
- **Batch Operations**: Optimized Neo4j operations with configurable batch sizes

## Prerequisites

Before running GraphRAG Pipeline, ensure you have:

1. **Python 3.13+** with [uv](https://docs.astral.sh/uv/) package manager
2. **Neo4j Database** - Graph database for storing the knowledge graph
3. **vLLM or compatible LLM server** - For natural language to Cypher conversion
4. **LlamaStack** (optional) - For the full agent UI experience

### LlamaStack Setup

LlamaStack provides the agent runtime and web UI for interactive queries.

```bash
# Clone LlamaStack
git clone https://github.com/meta-llama/llama-stack.git
cd llama-stack

# Create virtual environment and install
python -m venv .venv
source .venv/bin/activate
pip install -e .

# Note the path for LLAMA_STACK_DIR in your .env
```

Configure in `.env`:

```bash
LLAMA_STACK_DIR=/path/to/llama-stack
VLLM_URL=http://localhost:11434/v1
VLLM_API_TOKEN=your-token
VLLM_MODEL=Qwen/Qwen2.5-Coder-7B-Instruct
```

## Installation

```bash
# Install dependencies using uv (recommended)
uv sync

# Or with pip
pip install -e .
```

**Note:** This project uses individual tree-sitter grammar packages (`tree-sitter-python`, `tree-sitter-yaml`, `tree-sitter-ruby`, `tree-sitter-jinja`) instead of the monolithic `tree-sitter-languages` package for faster installation and smaller footprint.

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

1. Update Neo4j connection details in `.env`:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_QUERY_TIMEOUT=10.0
```

1. Configure LLM for natural language queries:

```bash
LLM_PROVIDER=vllm
API_BASE=http://localhost:11434/v1
MODEL_NAME=Qwen/Qwen2.5-Coder-7B-Instruct
```

1. (Optional) Configure MCP server:

```bash
MCP_SERVER_HOST=127.0.0.1
MCP_SERVER_PORT=5003
MCP_RATE_LIMIT_PER_MINUTE=100
```

1. (Optional) Customize graph schema in `config/schema.yaml`

## Usage

### Local Development

Parse a codebase locally and build the Neo4j graph:

```bash
# Start Neo4j
podman-compose up -d neo4j

# Build graph from local filesystem
uv run python scripts/build_graph.py /path/to/codebase

# Build with options
uv run python scripts/build_graph.py /path/to/codebase \
  --clear \
  --workers 8 \
  --log-level DEBUG

# Or clone from Git and build
uv run python scripts/clone_and_build.py \
  --git-url https://github.com/your-org/ansible-repo.git \
  --git-branch main
```

## Graph Schema

### Node Types

- **File**: Source files (playbooks, vars, templates, etc.)
- **Playbook**: Ansible playbook definitions
- **Play**: Individual plays within playbooks
- **Task**: Ansible tasks
- **Handler**: Event handlers
- **Role**: Ansible roles
- **Variable**: Variable definitions
- **Template**: Jinja2 templates
- **Inventory**: Host and group definitions

### Relationship Types

- `INCLUDES`: File includes another file
- `IMPORTS`: File imports tasks/playbooks
- `HAS_PLAY`: Playbook contains play
- `HAS_TASK`: Play contains task
- `USES_TEMPLATE`: Task uses template
- `DEFINES_VAR`: Task/file defines variable
- `USES_VAR`: Task uses variable
- `USES_ROLE`: Playbook uses role
- `DEPENDS_ON`: Role depends on another role
- `NOTIFIES`: Task notifies handler

## Querying the Graph

Once the graph is built, you can query it using:

### Cypher Queries (Neo4j Browser)

```cypher
// Find all playbooks
MATCH (p:Playbook) RETURN p.name, p.path LIMIT 10

// Find role dependencies
MATCH (r1:Role)-[:DEPENDS_ON]->(r2:Role)
RETURN r1.name, r2.name

// Trace variable usage
MATCH (v:Variable {name: 'ansible_user'})<-[:USES_VAR]-(t:Task)
RETURN v, t

// Get task hierarchy for a playbook
MATCH (pb:Playbook {name: 'site.yml'})-[:HAS_PLAY]->(p:Play)-[:HAS_TASK]->(t:Task)
RETURN pb, p, t
```

## MCP Server

The MCP (Model Context Protocol) server exposes graph query tools for LLM agents.

### Available Tools

| Tool | Description |
| ------ | ------------- |
| `query_codebase` | Natural language to Cypher query execution |
| `query_with_rag` | Hybrid RAG query (graph + semantic) |
| `find_dependencies` | Find file dependencies (includes, imports) |
| `trace_variable` | Track variable definitions and usage |
| `get_role_usage` | Find where Ansible roles are used |
| `analyze_playbook` | Analyze playbook structure |
| `find_tasks_by_module` | Find tasks using specific modules |
| `get_task_hierarchy` | Get task execution hierarchy |
| `find_template_usage` | Find template usage and variables |
| `set_repository_context` | Set active repository for multi-repo queries |

### STDIO Mode (Claude Desktop / CLI)

For Claude Desktop or other MCP clients that use STDIO transport:

```bash
# Run the MCP server in STDIO mode
uv run python -m src.mcp.server
```

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "graphrag": {
      "command": "uv",
      "args": ["run", "python", "-m", "src.mcp.server"],
      "cwd": "/path/to/graphrag-pipeline"
    }
  }
}
```

### HTTP Mode (SSE Transport)

For web-based integrations using Server-Sent Events:

```bash
# Start HTTP server with SSE transport
uv run python -m src.mcp.http_server
```

Server runs on `http://127.0.0.1:5003` by default (configurable via `MCP_SERVER_HOST` and `MCP_SERVER_PORT`).

**Endpoints:**

- `GET /sse` - SSE connection for MCP protocol
- `POST /messages` - Send messages to MCP server
- `GET /health` - Health check

### Rate Limiting

HTTP mode includes rate limiting (configurable):

```bash
MCP_RATE_LIMIT_PER_MINUTE=100
MCP_RATE_LIMIT_BURST=10
```

## Web UI (LlamaStack)

LlamaStack provides a web interface for interactive graph queries with agent capabilities.

### Running with LlamaStack

```bash
# Start all services (Neo4j, MCP server, LlamaStack)
make run
```

This starts:

- Neo4j database (port 7687)
- MCP HTTP server (port 5003)
- LlamaStack with UI (port 8321)

Access the LlamaStack UI at: **<http://localhost:8321>**

### Alternative: Standalone Gradio UI

For a simpler UI without LlamaStack:

```bash
make ui
```

Access at: **<http://localhost:11436>**

### UI Features

- **Repository Selector**: Query specific repositories or all
- **Natural Language Queries**: Ask questions in plain English
- **Example Queries**: Pre-built examples for Python and Ansible codebases
- **Chat History**: Maintains conversation context

### Example Queries

**Python codebases:**

- "List all classes"
- "Show all async functions"
- "Find classes that inherit from BaseSettings"

**Ansible codebases:**

- "What playbooks exist?"
- "Find tasks using the copy module"
- "What roles are defined?"

## GraphRAG Agent

The GraphRAG agent provides conversational access to the knowledge graph using LlamaIndex.

### Using the Agent

```python
from src.agents.graphrag_agent import GraphRAGAgent
from src.config import LLMConfig, Neo4jConfig

# Initialize agent
agent = GraphRAGAgent(
    llm_config=LLMConfig(),
    neo4j_config=Neo4jConfig(),
)

# Chat with the agent
response = await agent.chat("What modules import asyncio?")
print(response.content)

# Tool calls are automatically executed
for tool_call in response.tool_calls:
    print(f"Tool: {tool_call.name}, Result: {tool_call.result}")
```

### Agent Tools

The agent can call these tools during conversations:

- `query_codebase(question)` - Natural language graph search
- `query_with_rag(question)` - Hybrid RAG query
- `find_dependencies(file_path)` - File dependency analysis
- `trace_variable(variable_name)` - Variable flow tracking

## Development

```bash
# Run tests
uv run pytest

# Format and lint
uv run ruff check src/ --fix
uv run ruff format src/

# Type checking
uv run mypy src/ --strict
```

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-org/graphrag-pipeline.git
cd graphrag-pipeline
uv sync

# 2. Configure environment
cp .env.example .env
# Edit .env with:
#   - Neo4j credentials
#   - LLM/vLLM settings
#   - LLAMA_STACK_DIR (path to llama-stack clone)

# 3. Start Neo4j
make neo4j

# 4. Build graph from your codebase
make graph CODEBASE_PATH=/path/to/your/codebase

# 5. Start with LlamaStack UI (recommended)
make run
# Open http://localhost:8321

# Or standalone Gradio UI
make ui
# Open http://localhost:11436

# Or use MCP tools with Claude Desktop
make mcp
```

## Make Targets

| Target | Description |
| ------ | ----------- |
| `make run` | Start all services + LlamaStack UI (port 8321) |
| `make services` | Start Neo4j + Langfuse (background) |
| `make stop` | Stop all services |
| `make ui` | Start standalone Gradio UI (port 11436) |
| `make mcp` | Start MCP server (STDIO mode) |
| `make mcp-http` | Start MCP server (HTTP/SSE mode, port 5003) |
| `make neo4j` | Start Neo4j database |
| `make langfuse` | Start Langfuse observability (port 11437) |
| `make graph CODEBASE_PATH=...` | Build graph from codebase |
| `make test` | Run tests |
| `make lint` | Run linter |
| `make format` | Format code |
| `make docs-serve` | Serve documentation locally |

## License

MIT
