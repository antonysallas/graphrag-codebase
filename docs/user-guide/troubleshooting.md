# Troubleshooting

Solutions to common issues encountered while deploying and using the GraphRAG Pipeline.

## Connection Issues

### Neo4j: "ServiceUnavailable"

This usually means the database container is not running or the URI is incorrect.

- **Check Status**: Run `docker compose ps` to verify the `neo4j` service is up.
- **Verify URI**: Ensure `NEO4J_URI` in your `.env` is set to `bolt://localhost:7687`.
- **Authentication**: If you get a "Unauthorized" error, double-check `NEO4J_PASSWORD`.

### MCP Server: "Broken Pipe" or "Connection Refused"

- **STDIO Mode**: If using with Claude Desktop, ensure the `args` path in `claude_desktop_config.json` is absolute and the `uv` executable is in your PATH.
- **HTTP Mode**: Check if `MCP_SERVER_PORT` (default 5003) is exposed and not blocked by a firewall.

## Parsing Failures

### "Parse Error" in Logs

The pipeline is designed to be error-tolerant, but some files might still fail.

- **YAML Syntax**: Ansible playbooks must be valid YAML. Run `ansible-lint` on your codebase to catch basic syntax errors.
- **Unsupported Features**: Some very new Ansible features might not be captured by the current extractors. Set `LOG_LEVEL=DEBUG` to see which nodes are being skipped.

## RAG Quality

### "Generated Cypher is Invalid"

If the LLM generates queries that don't match the schema:

- **Model Choice**: Ensure you are using a coding-specific model like `Qwen2.5-Coder-7B-Instruct`. General-purpose models are more prone to schema hallucinations.
- **Prompt Tuning**: You can adjust the prompt templates in `src/mcp/utils/prompt_templates.py` to better instruct the model.

## Performance

### Slow Graph Building

- **Workers**: If you have a multi-core machine, increase `MAX_WORKERS` in `.env` (e.g., set to 8 or 12).
- **Disk I/O**: Ensure the Neo4j data volume is on an SSD. Graph databases perform millions of small random reads/writes.

---

## See Also

- [Installation Guide](../getting-started/quickstart.md)
- [CLI Reference](../reference/cli-reference.md)
- [Production Checklist](../deployment/production-checklist.md)
