# MCP Tools Reference

Detailed reference for the specialized tools provided by the GraphRAG MCP server.

## 1. `query_codebase`

Translates natural language questions into Cypher queries and executes them against the Neo4j graph.

- **Parameters**:
  - `question` (string): Natural language query.
- **Returns**: JSON array of matching node/relationship data.
- **Example**: `"How many playbooks use the apache role?"`
- **Use Case**: Discovery and general analysis.

## 2. `find_dependencies`

Finds file-level dependencies including tasks, imports, and variable loads.

- **Parameters**:
  - `file_path` (string): Path to the source file.
- **Returns**: List of dependency paths and their relationship type.
- **Example**: `file_path="site.yml"`
- **Use Case**: Impact analysis.

## 3. `trace_variable`

Follows a variable from its definition to every point of consumption in the codebase.

- **Parameters**:
  - `variable_name` (string): The exact name of the variable.
- **Returns**: List of definitions (with scope) and usages.
- **Example**: `variable_name="nginx_port"`
- **Use Case**: Debugging configuration values.

## 4. `get_role_usage`

Locates all occurrences where an Ansible role is utilized.

- **Parameters**:
  - `role_name` (string): The name of the role.
- **Returns**: List of playbooks and plays utilizing the role.
- **Example**: `role_name="geerlingguy.mysql"`
- **Use Case**: Auditing role dependencies.

## 5. `analyze_playbook`

Provides a structural summary of a playbook's hierarchy.

- **Parameters**:
  - `playbook_path` (string): Path to the playbook.
- **Returns**: Summary of plays, hosts, and task counts.
- **Example**: `playbook_path="deploy.yml"`
- **Use Case**: High-level structural understanding.

## 6. `find_tasks_by_module`

Finds all tasks using a specific module.

- **Parameters**:
  - `module_name` (string): Module name (e.g., `template`).
- **Returns**: List of task names and their parent playbooks.
- **Example**: `module_name="ansible.builtin.copy"`
- **Use Case**: Refactoring modules.

## 7. `get_task_hierarchy`

Lists the exact execution order of tasks within a playbook.

- **Parameters**:
  - `playbook_path` (string): Path to the playbook.
- **Returns**: Ordered list of plays and nested tasks.
- **Example**: `playbook_path="provision.yml"`
- **Use Case**: Flow analysis.

## 8. `find_template_usage`

Locates Jinja2 templates and identifies the variables they consume.

- **Parameters**:
  - `template_path` (string): Path to the `.j2` file.
- **Returns**: List of variable names found in the template AST.
- **Example**: `template_path="templates/config.j2"`
- **Use Case**: Template auditing.

---

## See Also

- [User Guide: MCP Tools](../user-guide/mcp-tools.md)
- [Architecture: Layer 4](../architecture/5-layer-design.md)
- [CLI Reference](cli-reference.md)
