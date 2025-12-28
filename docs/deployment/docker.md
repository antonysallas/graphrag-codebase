# Docker Deployment

The GraphRAG Pipeline is designed to be fully containerized, making it easy to deploy alongside other infrastructure-as-code tools.

## Container Images

We provide a multi-stage `Containerfile` optimized for minimal image size and maximum security.

### Building the Image

```bash
docker build -t graphrag-pipeline:latest .
```

The image is based on `python:3.13-slim` and includes all required system dependencies (like `git`).

## Docker Compose (Local Stack)

For local development or single-node deployments, use the provided `compose.yml`.

### Key Services

- **`neo4j`**: Native graph store with APOC pre-installed.
- **`graphrag-mcp`**: The API server exposing tools to agents.
- **`graphrag-builder`**: A worker container for building/updating the graph.

## Production Configuration

When deploying to production, we recommend the following overrides in your `docker-compose.prod.yml`:

```yaml
services:
  neo4j:
    deploy:
      resources:
        limits:
          memory: 4G
    volumes:
      - /mnt/ssd/neo4j:/data

  mcp-server:
    read_only: true
    tmpfs:
      - /tmp
    environment:
      - LOG_LEVEL=WARNING
```

## Security Hardening

1. **Non-Root User**: The official image runs as UID `1001` (`graphbuilder`). Ensure your volume mounts have the correct permissions.
2. **No Privilege Escalation**: Our `Containerfile` is compatible with `allowPrivilegeEscalation: false`.
3. **Network Isolation**: Use a dedicated Docker bridge network so the Neo4j Bolt port is not exposed to the public internet.

---

## See Also

- [Kubernetes & OpenShift](kubernetes.md)
- [Production Checklist](production-checklist.md)
- [Docker Compose Guide](../getting-started/docker-compose.md)
