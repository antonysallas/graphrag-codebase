# Production Checklist

Before moving your GraphRAG Pipeline from development to production, ensure you have addressed the following items to ensure security, reliability, and performance.

## 1. Operational Hardening

- [ ] **Timeouts**: `NEO4J_QUERY_TIMEOUT` is set to 10s or less.
- [ ] **Guardrails**: All queries use the `enforce_limit` utility to prevent unbounded result sets.
- [ ] **Circuit Breakers**: `cypher_generation_breaker` and `neo4j_query_breaker` are active and configured with sensible thresholds.
- [ ] **Rate Limiting**: `MCP_RATE_LIMIT_PER_MINUTE` is enabled to prevent accidental DoS from AI agents.

## 2. Security & Compliance

- [ ] **Non-Root**: Containers are running as UID 1001.
- [ ] **Secrets**: Database passwords and LLM API keys are **not** in `.env` files tracked by git. Use K8s Secrets or HashiCorp Vault.
- [ ] **Path Sanitization**: All user inputs for file paths are validated through `src/mcp/utils/path_sanitizer.py`.
- [ ] **Network Isolation**: Neo4j is only accessible via the internal cluster network.

## 3. Data Integrity

- [ ] **Schema Validation**: The `CypherValidator` is active for all natural language tools.
- [ ] **Canonicalization**: Ansible modules are mapped to FQCN (Fully Qualified Collection Names) to ensure query consistency.
- [ ] **Index Maintenance**: All constraints and indexes defined in `config/schema.yaml` have been initialized.

## 4. Monitoring & Tracing

- [ ] **Langfuse**: Tracing is enabled (`LANGFUSE_ENABLED=true`) and data is flowing to your project dashboard.
- [ ] **Structured Logging**: `LOG_LEVEL` is set to `INFO` or `WARNING`.
- [ ] **Error Tagging**: Exceptions are correctly tagged in Langfuse traces for alerting.

## 5. Performance Tuning

- [ ] **Heap Size**: Neo4j memory settings are tuned for your codebase size (at least 2GB for medium repos).
- [ ] **Parsing Concurrency**: `MAX_WORKERS` is set based on available CPU cores.
- [ ] **SSD**: The persistent volume for Neo4j data is backed by an SSD.

---

## See Also

- [Architecture: 5-Layer Design](../architecture/5-layer-design.md)
- [User Guide: Troubleshooting](../user-guide/troubleshooting.md)
- [Kubernetes & OpenShift](kubernetes.md)
