# Querying Graphs

The GraphRAG Pipeline provides powerful interfaces for exploring your codebase, ranging from plain English questions to direct database queries.

## Natural Language Queries

Using the `query_codebase` tool, you can ask complex questions without knowing the underlying graph schema. This is powered by our GraphRAG layer which translates your intent into Cypher.

### Example Questions

- *"Which playbooks use the geerlingguy.apache role?"*
- *"Find all tasks that use the template module and notify a handler."*
- *"Show me where the variable 'db_password' is defined and where it's used."*
- *"What is the execution order of tasks in my webserver.yml playbook?"*

### Using the CLI

```bash
uv run scripts/query_graph.py "Which roles install nginx?"
```

## Repository Context

When querying a multi-repo database:

### MCP Session Context

Set repository context before querying:

```python
from src.mcp.context import set_repository, get_repository

# Set context for session
set_repository("ansible-for-devops")

# All queries now filter by this repo
result = await query_codebase("What playbooks exist?")
```

### Cross-Repository Queries

Role usage queries always show cross-repo results:

```python
# Shows ALL repos that use this role
result = await get_role_usage("geerlingguy.apache")
```

### Direct Cypher Queries

For developers and power users, you can query Neo4j directly using [Cypher](https://neo4j.com/docs/cypher-manual/current/). This is useful for building custom dashboards or performing deep structural audits.

```cypher
-- Query specific repository
MATCH (f:File {repository: 'graphrag-pipeline'})
WHERE f.path ENDS WITH '.py'
RETURN f.path

-- Query across all repositories
MATCH (r:Role)<-[:USES_ROLE]-(p)
RETURN r.name, p.repository, count(p) as usage_count
```

## Direct Cypher Queries (General)

### Neo4j Browser

Open [http://localhost:7474](http://localhost:7474) and login to see a visual representation of your data.

### Common Patterns

**Find all roles and their dependencies:**

```cypher
MATCH (r1:Role)-[:DEPENDS_ON]->(r2:Role)
RETURN r1.name, r2.name
```

**Trace file inclusion depth:**

```cypher
MATCH path = (f:File)-[:INCLUDES*1..3]->(dep:File)
RETURN path
LIMIT 10
```

## Templated Queries

We maintain a collection of optimized Cypher templates in `src/graph/queries.py`. These are used by our internal tools to ensure consistent and fast results.

| Template Name | Purpose |
|---------------|---------|
| `GET_ROLE_USAGE` | Identifies all playbooks using a specific role. |
| `GET_VARIABLE_FLOW` | Traces a variable from definition to all usage points. |
| `GET_FILE_DEPENDENCIES` | Builds a complete inclusion/import tree for a file. |

## Guardrails & Limits

To protect system performance, we enforce several limits on generated queries:

- **Result Limit**: All queries are automatically appended with `LIMIT 100` unless otherwise specified.
- **Timeout**: Queries exceeding 10 seconds (configurable via `NEO4J_QUERY_TIMEOUT`) are terminated.
- **Safety**: Destructive operations like `DELETE` or `DROP` are blocked in the GraphRAG layer.

---

## See Also

- [MCP Tools Reference](../reference/mcp-tools-reference.md)
- [Schema Reference](../reference/schema-reference.md)
- [Troubleshooting](troubleshooting.md)
