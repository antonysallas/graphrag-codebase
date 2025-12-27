# Quickstart Guide

Get the GraphRAG pipeline up and running in under 5 minutes.

## Prerequisites

Before starting, ensure you have the following installed:

- **Python 3.13+** (recommended for Langfuse compatibility)
- **Docker & Docker Compose**
- **uv** (high-performance Python package manager)

## 1. Installation

Clone the repository and install dependencies using `uv`:

```bash
git clone https://github.com/antonysallas/graphrag-codebase.git
cd graphrag-pipeline
uv sync
```

## 2. Start Infrastructure

Launch the Neo4j database and MCP server stack:

```bash
# Start Neo4j and the MCP API
docker compose up -d
```

Verify Neo4j is available at [http://localhost:7474](http://localhost:7474) (Default login: `neo4j` / `password`).

## 3. Build Your First Graph

Point the pipeline to a codebase to begin indexing. The tool will auto-detect the repository type (Ansible or Python) and use the appropriate schema.

### Auto-Detection (Recommended)

```bash
# Auto-detect repository type
uv run graphrag-build /path/to/any/repo --clear
```

### Explicit Repo Types

You can override auto-detection if needed:

```bash
# Explicitly specify Python
uv run graphrag-build /path/to/python/project --repo-type python --clear

# Use generic for any unknown codebase
uv run graphrag-build /path/to/unknown/repo --repo-type generic --clear
```

## 4. Execute a Query

You can now query your codebase using natural language (requires a running LLM provider) or Cypher:

```bash
# Test the MCP server locally
uv run graphrag-mcp
```

Or run a direct Cypher query in the Neo4j Browser:

```cypher
MATCH (n:File) RETURN n.path LIMIT 5
```

---

## See Also

- [Installation Deep-Dive](installation.md)
- [Configuration Reference](configuration.md)
- [User Guide: Building Graphs](../user-guide/building-graphs.md)
