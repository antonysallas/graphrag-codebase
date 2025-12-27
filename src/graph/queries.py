"""Cypher query templates for common graph operations."""

# Node queries
GET_ALL_PLAYBOOKS = "MATCH (p:Playbook) RETURN p"
GET_ALL_ROLES = "MATCH (r:Role) RETURN r"
GET_ALL_TASKS = "MATCH (t:Task) RETURN t"
GET_ALL_FILES = "MATCH (f:File) RETURN f"
GET_ALL_VARIABLES = "MATCH (v:Variable) RETURN v"

# Relationship queries
GET_ROLE_USAGE = """
MATCH (p:Playbook)-[:USES_ROLE]->(r:Role {name: $role_name})
RETURN p.name as playbook, r.name as role
"""

GET_VARIABLE_DEFINITIONS = """
MATCH (entity)-[:DEFINES_VAR]->(v:Variable {name: $var_name})
RETURN entity, v
"""

GET_VARIABLE_USAGES = """
MATCH (entity)-[:USES_VAR]->(v:Variable {name: $var_name})
RETURN entity, v
"""

# Dependency queries
GET_FILE_DEPENDENCIES = """
MATCH (f:File {path: $file_path})-[:INCLUDES|IMPORTS*1..3]->(dep)
RETURN dep
"""

GET_TASK_HANDLERS = """
MATCH (t:Task)-[:NOTIFIES]->(h:Handler)
WHERE t.name = $task_name
RETURN h
"""

# Schema queries
GET_NODE_COUNTS = """
CALL db.labels() YIELD label
CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {})
YIELD value
RETURN label, value.count as count
"""
