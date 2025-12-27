# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-27

### Added

* Initial public release of GraphRAG Codebase
* **AST Parsing Layer**
  * Tree-sitter based parsing for YAML, Python, Jinja2, Ruby
  * Error-tolerant parsing for incomplete or malformed files
  * Parallel processing with configurable workers
* **Multi-Language Support**
  * Ansible extractor (playbooks, roles, tasks, handlers, variables)
  * Python extractor (classes, functions, modules, imports)
  * Generic extractor (fallback for any codebase)
  * Schema profiles for language-specific graph models
* **Graph Construction**
  * Neo4j graph database with rich schema (10+ node types, 13+ relationships)
  * Batch operations for high-performance ingestion
  * Schema validation and constraint management
* **GraphRAG Query**
  * LlamaIndex integration for natural language to Cypher conversion
  * Hybrid retrieval combining graph traversal with semantic search
  * Support for local LLMs (vLLM, Ollama) and MaaS providers
* **MCP Server**
  * 9 specialized query tools for codebase analysis
  * JSON-RPC interface over stdio and HTTP/SSE transports
  * Rate limiting and authentication support
* **Agent API**
  * Programmatic GraphRAGAgent for custom applications
  * Conversation memory for multi-turn interactions
* **Multi-Repository Support**
  * Repository ID tagging on all nodes
  * Cross-repository query capabilities
  * Migration script for existing graphs
* **Web UI**
  * Gradio-based interactive query interface
  * Example queries for quick exploration
* **CLI Tools**
  * `graphrag-build` - Build knowledge graph from codebase
  * `graphrag-mcp` - Start MCP server (stdio)
  * `graphrag-mcp-http` - Start MCP server (HTTP/SSE)
* **Observability**
  * Langfuse integration for LLM tracing
  * OpenTelemetry support

### Security

* Cypher schema validation to prevent injection attacks
* Path sanitization for file access
* Query timeout enforcement
* Rate limiting on MCP endpoints

[Unreleased]: https://github.com/antonysallas/graphrag-codebase/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/antonysallas/graphrag-codebase/releases/tag/v0.1.0
