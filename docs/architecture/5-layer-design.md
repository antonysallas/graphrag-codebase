# 5-Layer Design

A deep technical dive into the components and logic within each architectural layer of the GraphRAG Pipeline.

## Layer 1: AST Parsing & Extraction

The goal of this layer is high-fidelity structural understanding of the source code.

- **Parsers**: We use individual Tree-sitter grammar packages for `python`, `yaml`, `ruby`, and `jinja2`. These are error-tolerant and extremely fast.
- **Parallel Processing**: The `AnsibleExtractor` uses a `ThreadPoolExecutor` to parse hundreds of files in parallel, drastically reducing build times for large repositories.
- **Extraction Logic**:
  - `PlaybookExtractor`: Identifies plays, tasks, and handlers.
  - `RoleExtractor`: Maps role dependencies from `meta/main.yml`.
  - `VariableExtractor`: Tracks variable definitions and their scopes.

## Layer 2: Graph Construction (Neo4j)

This layer manages the persistence and indexing of our structural knowledge.

- **Database**: Neo4j 5.x serves as our native graph store.
- **Batch Operations**: We use `UNWIND` Cypher clauses to insert data in configurable batches (default: 100), ensuring efficient network usage.
- **Idempotency**: All insertions use `MERGE` based on unique keys (e.g., `File.path` or `Role.name`), allowing graphs to be rebuilt safely.
- **Schema Validation**: The `GraphSchema` class (defined in `config/schema.yaml`) enforces that only valid node types and properties are written to the database.

## Layer 3: GraphRAG Query Layer

This layer provides the "intelligence" to navigate the graph using natural language.

- **LLM Integration**: We support `vLLM`, `Ollama`, and `OpenAI`.
- **Cypher Generation**: LlamaIndex's graph store integration is used to convert text intent into Cypher.
- **Guardrails**:
  - **Schema Reinforcement**: We inject the graph schema into the LLM prompt to prevent "hallucinated" relationship types.
  - **Query Validation**: Every generated Cypher query is checked against our schema and forbidden patterns (like `DELETE`) before execution.

## Layer 4: MCP Server (Tool Provider)

The interface layer that exposes functionality to the AI ecosystem.

- **Model Context Protocol**: Implements the latest MCP spec for tool discovery.
- **Transport Layers**:
  - **STDIO**: Perfect for local desktop usage (e.g., Claude Desktop).
  - **HTTP/SSE**: Designed for distributed agent stacks and containerized environments.
- **Circuit Breakers**: We monitor the health of LLM and Neo4j connections. If either becomes unresponsive, the circuit opens to prevent cascading failures.

## Layer 5: Agent Integration

The final consumer of the graph data.

- **Llamastack Agents**: We provide pre-configured tool-sets for LlamaStack, allowing agents to perform "multi-hop" reasoning (e.g., "Find the variable definition, then find all tasks using it, then summarize the impact of changing it").
- **Context Injection**: Agent responses are grounded in the structured facts retrieved from the graph, minimizing hallucinations.

---

## See Also

- [Architecture Overview](overview.md)
- [Graph Schema](graph-schema.md)
- [MCP Tools Guide](../user-guide/mcp-tools.md)
