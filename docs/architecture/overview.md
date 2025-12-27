# Architecture Overview

The GraphRAG Pipeline is designed using a structured 5-layer architecture that separates concern from raw source code parsing to high-level agent orchestration.

## 5-Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Layer 5: Agent Integration              │
│    Llamastack Agents │ Claude Desktop │ Custom Clients  │
├─────────────────────────────────────────────────────────┤
│                  Layer 4: MCP Server                     │
│    9 Tools: query_codebase, query_with_rag, etc.        │
├─────────────────────────────────────────────────────────┤
│                  Layer 3: GraphRAG Query                 │
│    LlamaIndex PropertyGraphIndex │ Hybrid Retrieval     │
├─────────────────────────────────────────────────────────┤
│                  Layer 2: Graph Construction             │
│    Neo4j │ Schema Profiles │ Batch Operations           │
├─────────────────────────────────────────────────────────┤
│                  Layer 1: AST Parsing                    │
│    Tree-sitter │ YAML/Python/Jinja2/Ruby Parsers        │
└─────────────────────────────────────────────────────────┘
```

### Layer 1: AST Parsing

The foundation of the pipeline. We use **Tree-sitter** to parse source code into high-fidelity Abstract Syntax Trees (ASTs). This allows us to understand the structural meaning of the code (e.g., distinguishing between a variable definition and a variable usage) rather than just treating it as raw text.

### Layer 2: Graph Construction

In this layer, parsed AST data is transformed into a Labeled Property Graph. We use **Schema Profiles** to ensure the graph structure matches the language being analyzed (Ansible vs. Python). Operations are batched for high performance.

### Layer 3: GraphRAG Query

This layer provides the intelligence for retrieval. We integrate with **LlamaIndex's PropertyGraphIndex** to enable hybrid queries that combine exact graph traversals (Cypher) with semantic vector search.

### Layer 4: MCP Server

We expose the graph's capabilities via the **Model Context Protocol (MCP)**. This provides a standardized set of tools that any LLM agent can use to "inspect" the codebase without needing to read every file into its context window.

### Layer 5: Agent Integration

The top layer where AI agents (like those built with **Llamastack**) use the MCP tools to perform complex reasoning, such as impact analysis, refactoring, or security auditing.

---

## See Also

- [Extractor Plugin Architecture](extractors.md)
- [Graph Schema Reference](../reference/schemas.md)
- [Developer Guide](../developer-guide/contributing.md)
