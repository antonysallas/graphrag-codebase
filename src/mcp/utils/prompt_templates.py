"""Prompt templates for LLM interactions."""

from typing import Dict

DEFAULT_TEMPLATE = """<instructions>
Convert the user's question into a Cypher query for a Neo4j graph database.
Return ONLY the Cypher query. No explanations, no markdown.
</instructions>

<schema>
{schema_str}
</schema>

<constraints>
- Use ONLY the node labels and relationship types in schema
- Always include LIMIT clause (default 100)
- Do not use procedures (CALL) unless necessary
</constraints>

<examples>
Question: How many playbooks are there?
MATCH (p:Playbook) RETURN count(p) as count

Question: Find tasks using copy module
MATCH (t:Task) WHERE t.module = 'copy' RETURN t.name, t.path LIMIT 100

Question: What roles are used?
MATCH (r:Role)<-[:USES_ROLE]-(usage) RETURN r.name, count(usage) LIMIT 100

Question: List all classes
MATCH (c:Class) RETURN c.name, c.docstring LIMIT 100

Question: Show async functions
MATCH (f:Function) WHERE f.is_async = true RETURN f.name, f.params LIMIT 100

Question: What modules exist?
MATCH (m:Module) RETURN m.name, m.path LIMIT 100

Question: Find classes inheriting from BaseSettings
MATCH (c:Class) WHERE 'BaseSettings' IN c.bases RETURN c.name LIMIT 100
</examples>

<question>
{question}
</question>
"""

MULTI_REPO_TEMPLATE = """<instructions>
Convert the user's question into a Cypher query for a Neo4j graph database.
Return ONLY the Cypher query. No explanations, no markdown.
</instructions>

<schema>
{schema_str}
</schema>

<repository_context>
Active repository: {repository_id}
All nodes except Role have a 'repository' property.
ALWAYS filter by repository unless querying global entities like Role.
</repository_context>

<constraints>
- Use ONLY the node labels and relationship types in schema
- Always include WHERE n.repository = '{repository_id}' for non-Role nodes
- Role nodes are global - no repository filter
- Always include LIMIT clause (default 100)
</constraints>

<examples>
Question: How many playbooks are there?
MATCH (p:Playbook) WHERE p.repository = '{repository_id}' RETURN count(p) as count

Question: Find tasks using copy module
MATCH (t:Task) WHERE t.repository = '{repository_id}' AND t.module = 'copy' RETURN t.name, t.path LIMIT 100

Question: What roles are used?
MATCH (r:Role)<-[:USES_ROLE]-(usage) WHERE usage.repository = '{repository_id}' RETURN r.name, count(usage) LIMIT 100

Question: Which repos use the nginx role?
MATCH (r:Role {{name: 'nginx'}})<-[:USES_ROLE]-(usage) RETURN r.name, collect(DISTINCT usage.repository) as repos

Question: List all classes
MATCH (c:Class) WHERE c.repository = '{repository_id}' RETURN c.name, c.docstring LIMIT 100

Question: Show async functions
MATCH (f:Function) WHERE f.repository = '{repository_id}' AND f.is_async = true RETURN f.name, f.params LIMIT 100

Question: What modules exist?
MATCH (m:Module) WHERE m.repository = '{repository_id}' RETURN m.name, m.path LIMIT 100

Question: Find classes inheriting from BaseSettings
MATCH (c:Class) WHERE c.repository = '{repository_id}' AND 'BaseSettings' IN c.bases RETURN c.name LIMIT 100
</examples>

<question>
{question}
</question>
"""

TEMPLATES: Dict[str, str] = {
    "default": DEFAULT_TEMPLATE,
    "multi_repo": MULTI_REPO_TEMPLATE,
}


def get_prompt_template(name: str = "default") -> str:
    """Get prompt template by name."""
    return TEMPLATES.get(name, DEFAULT_TEMPLATE)
