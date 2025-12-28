.PHONY: help docs docs-serve docs-build clean test lint format typecheck mcp mcp-http graph neo4j langfuse services run stop llamastack chat agent

# Load .env file if it exists
ifneq (,$(wildcard ./.env))
    include .env
    export
endif

# Ports (registered via portreg)
DOCS_PORT := 6002
MCP_PORT := 5003
LANGFUSE_PORT := 11437
LLAMASTACK_PORT := 8321

help:
	@echo "GraphRAG Pipeline - Available targets:"
	@echo ""
	@echo "  Run Services:"
	@echo "  run           - Start all services + LlamaStack UI (port $(LLAMASTACK_PORT))"
	@echo "  services      - Start Neo4j + Langfuse (background)"
	@echo "  stop          - Stop all services"
	@echo "  chat          - Interactive chat with GraphRAG agent (requires services)"
	@echo "  agent         - Create and test GraphRAG agent"
	@echo "  mcp           - Start MCP server (STDIO mode)"
	@echo "  mcp-http      - Start MCP server (HTTP/SSE mode, port $(MCP_PORT))"
	@echo "  neo4j         - Start Neo4j database"
	@echo "  langfuse      - Start Langfuse observability (port $(LANGFUSE_PORT))"
	@echo "  graph         - Build graph from CODEBASE_PATH"
	@echo ""
	@echo "  Documentation:"
	@echo "  docs          - Build documentation"
	@echo "  docs-serve    - Serve documentation locally (port $(DOCS_PORT))"
	@echo "  docs-build    - Build documentation for production"
	@echo ""
	@echo "  Development:"
	@echo "  test          - Run tests with pytest"
	@echo "  lint          - Run ruff linter"
	@echo "  format        - Format code with ruff"
	@echo "  typecheck     - Run mypy type checker"
	@echo "  clean         - Remove build artifacts"

# Documentation
docs: docs-build

docs-serve:
	uv run mkdocs serve -a 0.0.0.0:$(DOCS_PORT) --livereload --watch docs --watch mkdocs.yml

docs-build:
	uv run mkdocs build --strict

# Testing
test:
	uv run pytest

# Code quality
lint:
	uv run ruff check src/ tests/

format:
	uv run ruff format src/ tests/
	uv run ruff check src/ tests/ --fix

typecheck:
	uv run mypy src/ --strict

# Run services
run: services
	@echo "Waiting for services to be ready..."
	@sleep 3
	@echo "Starting MCP server in background on http://localhost:$(MCP_PORT)..."
	@uv run python -m src.mcp.http_server &
	@sleep 2
	@echo "Registering GraphRAG agent in background..."
	@(sleep 10 && uv run python scripts/register_agent.py) &
	@echo "Starting LlamaStack with UI on http://localhost:$(LLAMASTACK_PORT)"
	@echo "Langfuse UI available at http://localhost:$(LANGFUSE_PORT)"
	@echo "UI: http://localhost:8322"
	cd $(LLAMA_STACK_DIR) && . .venv/bin/activate && llama stack run $(CURDIR)/llamastack/config/run.yaml --enable-ui --port $(LLAMASTACK_PORT)

services: neo4j langfuse
	@echo "All background services started."

stop:
	@echo "Stopping all services..."
	@# Kill any running MCP/LlamaStack processes
	@lsof -ti :$(MCP_PORT) | xargs kill -9 2>/dev/null || true
	@lsof -ti :$(LLAMASTACK_PORT) | xargs kill -9 2>/dev/null || true
	@# Stop containers (15s timeout before SIGKILL)
	podman-compose down -t 15
	@echo "Services stopped."

mcp:
	@echo "Starting MCP server (STDIO mode)..."
	uv run python -m src.mcp.server

mcp-http:
	@echo "Starting MCP server (HTTP/SSE mode) on http://localhost:$(MCP_PORT)"
	uv run python -m src.mcp.http_server

llamastack: run

neo4j:
	@echo "Starting Neo4j database..."
	podman-compose up -d neo4j

langfuse:
	@echo "Starting Langfuse (postgres + server)..."
	podman-compose up -d langfuse-postgres langfuse

graph:
ifndef CODEBASE_PATH
	$(error CODEBASE_PATH is not set. Usage: make graph CODEBASE_PATH=/path/to/codebase)
endif
	@echo "Building graph from $(CODEBASE_PATH)..."
	uv run python scripts/build_graph.py build $(CODEBASE_PATH)

# Agent interaction
chat:
	@echo "Starting interactive chat with GraphRAG agent..."
	@echo "Make sure LlamaStack and MCP server are running (make run in another terminal)"
	uv run python scripts/create_agent.py chat

agent:
	@echo "Creating and testing GraphRAG agent..."
	uv run python scripts/create_agent.py

# Cleanup
clean:
	rm -rf site/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
