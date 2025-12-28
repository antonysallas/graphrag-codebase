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
- For name searches, use CONTAINS or toLower() for flexible matching
- Consider common aliases: httpd=apache, webserver=nginx/apache, db=mysql/postgres
- Role names often have prefixes like "geerlingguy." - search partial names with CONTAINS
- IMPORTANT: Always connect nodes via relationships in MATCH - never use separate MATCH clauses that create cartesian products
- ALWAYS use DISTINCT when returning node properties to avoid duplicates from path traversals
- Prefer returning individual columns over collect() to avoid confusing results
</constraints>

<examples>
Question: How many playbooks are there?
MATCH (p:Playbook) RETURN count(p) as count

Question: Find tasks using copy module
MATCH (t:Task) WHERE t.module = 'copy' RETURN t.name, t.path LIMIT 100

Question: What roles are used?
MATCH (r:Role)<-[:USES_ROLE]-(usage) RETURN r.name, count(usage) LIMIT 100

Question: Find roles for httpd or apache
MATCH (r:Role) WHERE toLower(r.name) CONTAINS 'apache' OR toLower(r.name) CONTAINS 'httpd' RETURN r.name LIMIT 100

Question: Find playbooks using httpd/apache roles
MATCH (p:Playbook)-[:HAS_PLAY]->(play)-[:USES_ROLE]->(r:Role) WHERE toLower(r.name) CONTAINS 'apache' RETURN DISTINCT p.name as playbook, r.name as role LIMIT 100

Question: Find playbooks that use roles
MATCH (p:Playbook)-[:HAS_PLAY]->(play)-[:USES_ROLE]->(r:Role) RETURN DISTINCT p.name as playbook, r.name as role LIMIT 100

Question: What tasks are in a playbook?
MATCH (p:Playbook)-[:HAS_PLAY]->(play)-[:HAS_TASK]->(t:Task) RETURN p.name, t.name, t.module LIMIT 100

Question: Find handlers in roles
MATCH (r:Role)-[:HAS_HANDLER]->(h:Handler) RETURN r.name, h.name LIMIT 100

Question: What variables are defined?
MATCH (v:Variable)<-[:DEFINES_VAR]-(source) RETURN v.name, labels(source)[0] as defined_by LIMIT 100

Question: Find tasks that notify handlers
MATCH (t:Task)-[:NOTIFIES]->(h:Handler) RETURN t.name, h.name LIMIT 100

Question: List all classes
MATCH (c:Class) RETURN c.name, c.docstring LIMIT 100

Question: Show async functions
MATCH (f:Function) WHERE f.is_async = true RETURN f.name, f.params LIMIT 100
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
- For name searches, use CONTAINS or toLower() for flexible matching
- Consider common aliases: httpd=apache, webserver=nginx/apache, db=mysql/postgres
- Role names often have prefixes like "geerlingguy." - search partial names with CONTAINS
- IMPORTANT: Always connect nodes via relationships in MATCH - never use separate MATCH clauses that create cartesian products
- ALWAYS use DISTINCT when returning node properties to avoid duplicates from path traversals
- Prefer returning individual columns over collect() to avoid confusing results
</constraints>

<examples>
Question: How many playbooks are there?
MATCH (p:Playbook) WHERE p.repository = '{repository_id}' RETURN count(p) as count

Question: Find tasks using copy module
MATCH (t:Task) WHERE t.repository = '{repository_id}' AND t.module = 'copy' RETURN t.name, t.path LIMIT 100

Question: What roles are used?
MATCH (r:Role)<-[:USES_ROLE]-(usage) WHERE usage.repository = '{repository_id}' RETURN r.name, count(usage) LIMIT 100

Question: Find roles for httpd or apache
MATCH (r:Role) WHERE toLower(r.name) CONTAINS 'apache' OR toLower(r.name) CONTAINS 'httpd' RETURN r.name LIMIT 100

Question: Find playbooks using httpd/apache roles
MATCH (p:Playbook)-[:HAS_PLAY]->(play)-[:USES_ROLE]->(r:Role) WHERE p.repository = '{repository_id}' AND toLower(r.name) CONTAINS 'apache' RETURN DISTINCT p.name as playbook, r.name as role LIMIT 100

Question: Find playbooks that use roles
MATCH (p:Playbook)-[:HAS_PLAY]->(play)-[:USES_ROLE]->(r:Role) WHERE p.repository = '{repository_id}' RETURN DISTINCT p.name as playbook, r.name as role LIMIT 100

Question: What tasks are in a playbook?
MATCH (p:Playbook)-[:HAS_PLAY]->(play)-[:HAS_TASK]->(t:Task) WHERE p.repository = '{repository_id}' RETURN p.name, t.name, t.module LIMIT 100

Question: Find handlers in roles
MATCH (r:Role)-[:HAS_HANDLER]->(h:Handler) WHERE h.repository = '{repository_id}' RETURN r.name, h.name LIMIT 100

Question: What variables are defined?
MATCH (v:Variable)<-[:DEFINES_VAR]-(source) WHERE v.repository = '{repository_id}' RETURN v.name, labels(source)[0] as defined_by LIMIT 100

Question: Find tasks that notify handlers
MATCH (t:Task)-[:NOTIFIES]->(h:Handler) WHERE t.repository = '{repository_id}' RETURN t.name, h.name LIMIT 100

Question: Which repos use the nginx role?
MATCH (r:Role {{name: 'nginx'}})<-[:USES_ROLE]-(usage) RETURN r.name, collect(DISTINCT usage.repository) as repos

Question: List all classes
MATCH (c:Class) WHERE c.repository = '{repository_id}' RETURN c.name, c.docstring LIMIT 100

Question: Show async functions
MATCH (f:Function) WHERE f.repository = '{repository_id}' AND f.is_async = true RETURN f.name, f.params LIMIT 100
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
