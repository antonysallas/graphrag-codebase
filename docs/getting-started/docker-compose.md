# Docker Compose

Deploy the entire GraphRAG stack locally using Docker Compose. This is the fastest way to get a production-mirrored environment for development and testing.

## Service Overview

The `compose.yml` file defines the following services:

### 1. **Neo4j** (`neo4j`)

The core graph database engine.

- **Ports**: 7474 (HTTP Browser), 7687 (Bolt API).
- **Plugins**: Pre-configured with the **APOC** library for advanced graph algorithms.
- **Persistence**: Uses Docker volumes for data, logs, and plugins.

### 2. **Graph Builder** (`graphrag-builder`)

A one-off job container that runs the indexing pipeline. It is designed to clone a Git repository and populate the Neo4j instance.

### 3. **MCP Server** (`graphrag-mcp`)

The Model Context Protocol API. This long-running service connects your graph to AI agents.

## Running the Stack

We provide simple commands to manage the lifecycle of your services:

```bash
# Start Neo4j and the MCP Server
docker compose up -d

# View the status of your containers
docker compose ps

# Inspect logs for the MCP server
docker compose logs -f mcp-server
```

## Persistent Data

We use named volumes to ensure your knowledge graph survives container restarts:

- `graphrag_neo4j_data`: Database records.
- `graphrag_neo4j_logs`: Database execution logs.
- `graphrag_neo4j_plugins`: APOC and other extension files.

To **completely wipe** the database and start fresh:

```bash
docker compose down -v
```

---

## See Also

- [Installation Guide](installation.md)
- [User Guide: Building Graphs](../user-guide/building-graphs.md)
- [Production Deployment](../deployment/docker.md)
