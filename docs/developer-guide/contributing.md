# Contributing Guide

We welcome contributions to the GraphRAG Pipeline! This guide will help you set up your development environment and follow our engineering standards.

## Development Setup

### Prerequisites

- **Python 3.13+**
- **Docker** (for Neo4j)
- **uv** (Package manager)

### Installation

```bash
# 1. Clone the repo
git clone https://github.com/antonysallas/graphrag-codebase.git
cd graphrag-pipeline

# 2. Setup virtualenv and dependencies
uv sync --extra dev --extra docs

# 3. Start Neo4j for testing
docker compose up -d neo4j
```

## Adding New Language Support

To add a new language, follow these steps:

1. **Parser**: Add a Tree-sitter parser in `src/parsers/`.
2. **Schema**: Define a new schema profile in `config/schemas/`.
3. **Extractor**: Implement a new `BaseExtractor` in `src/extractors/`.
4. **Detection**: Update `detect_repo_type` in `src/extractors/registry.py`.

## Engineering Standards

### 1. Strict Typing

All new code **must** include type hints. We use `mypy` in strict mode.

### 2. Testing

Every new extractor or parser must have 100% test coverage for its core logic. Use `pytest` and mock external dependencies.

### 3. Documentation

Update the [Schema Reference](../reference/schemas.md) if you add new node or relationship types.

## Validation Workflow

Before submitting a pull request, ensure all checks pass:

```bash
# 1. Format and Lint
uv run ruff check src/ --fix
uv run ruff format src/

# 2. Type Check
uv run mypy src/ --strict

# 3. Run Tests
uv run pytest -v
```

---

## See Also

- [Adding Parsers](adding-parsers.md)
- [Architecture Overview](../architecture/overview.md)
- [API Reference](../api/agents.md)
