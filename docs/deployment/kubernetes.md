# Kubernetes & OpenShift

This guide covers deploying the GraphRAG Pipeline to cloud-native platforms using our official Helm charts.

## Deployment Architecture

In a Kubernetes environment, we separate the concerns into three distinct workloads:

1. **Neo4j StatefulSet**: A persistent database cluster (can be single-node or clustered).
2. **Graph Construction Job**: A standard Kubernetes `Job` that runs the indexing pipeline against a specific Git repository.
3. **MCP Server Deployment**: A scalable deployment that exposes the API to your AI agents.

## Using the Helm Chart

We provide a comprehensive Helm chart in the `helm/` directory.

### 1. Install the Chart

```bash
# Clone the repository
git clone https://github.com/antonysallas/graphrag-codebase.git && cd graphrag-pipeline/helm

# Install with custom values
helm install my-graphrag . \
  --set graphBuilder.git.repoUrl="https://github.com/my-org/ansible-code.git" \
  --set neo4j.auth.password="SuperSecret123"
```

### 2. View Post-Install Notes

```bash
helm status my-graphrag
```

## OpenShift Compatibility

The pipeline is fully compatible with OpenShift's `restricted` Security Context Constraints (SCC).

- **Non-Root User**: The image runs as UID `1001` by default.
- **Group 0**: The application code and workspace are owned by group `0` to support OpenShift's arbitrary UID system.
- **Routes**: A template for an OpenShift `Route` is included to expose the Neo4j web browser securely.

## Resource Limits

Building large graphs is CPU and memory intensive. We recommend the following minimum limits for the **Builder Job**:

```yaml
resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2000m"
    memory: "4Gi"
```

---

## See Also

- [Helm Chart README](https://github.com/antonysallas/graphrag-codebase/tree/main/helm)
- [OpenShift Migration Plan (Archive)](../archive/OPENSHIFT_MIGRATION_PLAN.md.bak)
- [Docker Deployment](docker.md)
