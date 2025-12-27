# Installation

Detailed installation instructions and dependency management for the GraphRAG Pipeline.

## System Requirements

- **Operating System**: Linux (tested on Ubuntu/Fedora) or macOS.
- **Python**: 3.13 or higher (required for Langfuse SDK compatibility).
- **Memory**: 4GB+ RAM (8GB+ recommended for large graph builds).
- **Storage**: 10GB+ free space for Neo4j data.

## Python Dependencies

We use `uv` for lightning-fast, reproducible dependency management.

### Installing with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/antonysallas/graphrag-codebase.git
cd graphrag-codebase

# Sync all dependencies including dev tools
uv sync --extra dev --extra docs
```

### Key Dependencies

- **Tree-sitter**: Used for high-fidelity AST parsing across multiple languages.
- **LlamaIndex**: Provides the `PropertyGraphIndex` for hybrid graph+semantic retrieval.
- **Neo4j Python Driver**: High-performance connection to the graph database.
- **Loguru**: Structured logging for all pipeline operations.

## Infrastructure Requirements

### Neo4j Graph Database

The pipeline requires **Neo4j 5.x**. You can run it via Docker:

```bash
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5-community
```

### LLM Provider

For natural language querying (GraphRAG), you need an OpenAI-compatible API endpoint. We support:

- **vLLM** (Recommended for local production)
- **Ollama** (Recommended for local development)
- **MaaS** (Model-as-a-Service providers like OpenAI, Groq, Together, or Fireworks)

See [Configuration](configuration.md#maas-provider-examples) for MaaS setup examples.

## Tree-sitter Grammars

This project uses **individual tree-sitter grammar packages** to handle different file types within a repository.

| Language | Package | Usage |
|----------|---------|-------|
| **YAML** | `tree-sitter-yaml` | Ansible Playbooks, Roles, Vars |
| **Python** | `tree-sitter-python` | Python modules, classes, functions |
| **Jinja2** | `tree-sitter-jinja` | Ansible Templates |
| **Ruby** | `tree-sitter-ruby` | Vagrantfiles |

---

## See Also

- [Quickstart Guide](quickstart.md)
- [Configuration](configuration.md)
- [User Guide: Building Graphs](../user-guide/building-graphs.md)
