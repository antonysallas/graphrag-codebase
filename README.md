# GraphRAG Codebase

Transform codebases into queryable Neo4j knowledge graphs using Abstract Syntax Tree (AST) parsing. Supports **Ansible**, **Python**, and generic file analysis.

## Features

- **Multi-language Parsing**: Tree-sitter parsers for YAML, Python, Jinja2, Ruby
- **Rich Graph Schema**: 10+ node types, 13+ relationship types
- **MCP Server**: Model Context Protocol tools for LLM agent integration
- **Extensible**: Add custom extractors for new languages/frameworks
- **Efficient**: Parallel processing (~10-20 files/second), batch Neo4j operations

## Installation

```bash
# Clone the repository
git clone https://github.com/antonysallas/graphrag-codebase.git
cd graphrag-codebase

# Install with uv
uv sync
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Update Neo4j connection details in `.env`:

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

3. (Optional) Customize graph schema in `config/schema.yaml`

## Usage

### Build a Graph

```bash
# Build graph from local filesystem
uv run python scripts/build_graph.py /path/to/codebase

# Clone from Git and build
uv run python scripts/clone_and_build.py \
  --git-url https://github.com/your-org/repo.git \
  --git-branch main
```

### Query the Graph

Use Neo4j Browser or Cypher queries:

```cypher
-- Find all Python classes
MATCH (c:Class) RETURN c.name, c.path LIMIT 10

-- Find function dependencies
MATCH (f:Function)-[:CALLS]->(g:Function)
RETURN f.name, g.name

-- Trace Ansible role usage
MATCH (p:Playbook)-[:USES_ROLE]->(r:Role)
RETURN p.name, r.name
```

## Graph Schema

### Node Types

| Type | Description |
|------|-------------|
| File | Source files |
| Module | Python modules |
| Class | Python classes |
| Function | Python functions |
| Playbook | Ansible playbooks |
| Play | Ansible plays |
| Task | Ansible tasks |
| Role | Ansible roles |
| Variable | Variable definitions |
| Template | Jinja2 templates |

### Relationship Types

| Type | Description |
|------|-------------|
| CONTAINS | Parent contains child |
| IMPORTS | Module imports |
| CALLS | Function calls |
| INHERITS | Class inheritance |
| USES_ROLE | Playbook uses role |
| DEFINES_VAR | Defines variable |
| USES_VAR | Uses variable |

## Project Structure

```
src/
├── extractors/     # Code extractors (Ansible, Python, Generic)
├── parsers/        # Tree-sitter language parsers
├── graph/          # Neo4j graph builder
├── mcp/            # MCP server and tools
└── config.py       # Configuration management

scripts/
├── build_graph.py      # Main CLI
└── clone_and_build.py  # Git clone + build

config/
└── schemas/        # Language-specific graph schemas
```

## Development

```bash
# Run tests
uv run pytest

# Lint and format
ruff check src/ --fix
ruff format src/

# Type checking
uv run mypy src/
```

## License

GPLv3 - See [LICENSE](LICENSE) for details.
