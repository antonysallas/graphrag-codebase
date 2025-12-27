# Changelog

All notable changes to the GraphRAG Pipeline will be documented in this file.

## [0.1.0] - 2025-01-23

This is the initial production-ready release of the GraphRAG Pipeline.

### Added

- **Core Architecture**: Structured 5-layer design (Parsing, Construction, Query, MCP, Agents).
- **Multi-language Parsing**: High-fidelity Tree-sitter parsers for YAML, Python, Ruby, and Jinja2.
- **Graph Model**: Native Neo4j schema with 10 node types and 13 relationships.
- **GraphRAG Layer**: Natural language to Cypher translation via LlamaIndex and vLLM.
- **MCP Server**: 8 specialized tools for deep codebase analysis.
- **Observability**: Integrated Langfuse tracing for tools and queries.
- **Resilience**: Circuit breakers, rate limiting, and query guardrails.
- **Cloud Native**: Helm charts for K8s/OpenShift and multi-stage Containerfiles.
- **Documentation**: Comprehensive Material MkDocs suite.

### Changed

- Optimized parser footprint by switching to individual grammar packages (93% reduction in size).

---

## Roadmap

### v0.2.0 (Planned)

- [ ] **Incremental Updates**: Detect file changes and update only affected graph segments.
- [ ] **Graph Diff**: Compare structure between two git commits.
- [ ] **Web UI**: Interactive dashboard for graph exploration and statistics.

### v0.3.0 (Planned)

- [ ] **Vector Search**: Hybrid search combining graph traversal with semantic embeddings.
- [ ] **Multi-repo**: Support for indexing multiple repositories in a single graph.
- [ ] **Real-time**: Filesystem watchers for instantaneous indexing.

---

## See Also

- [Glossary](glossary.md)
- [Architecture Overview](../architecture/overview.md)
