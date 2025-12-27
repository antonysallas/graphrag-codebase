# Schema Reference

The GraphRAG Pipeline uses a precisely defined model to represent the hierarchy and logic of an Ansible codebase.

## Node Types (10)

| Node | Description | Properties |
|------|-------------|------------|
| **`File`** | Any source file. | `path`, `absolute_path`, `file_type`, `content_hash`, `size`, `last_modified` |
| **`Playbook`**| Top-level YAML. | `name`, `path`, `description` |
| **`Play`** | Execution block. | `name`, `hosts`, `become`, `gather_facts`, `serial`, `order` |
| **`Task`** | Atomic action. | `name`, `module`, `args`, `when`, `loop`, `register`, `order`, `line_number` |
| **`Handler`** | Notified task. | `name`, `module`, `args`, `line_number` |
| **`Role`** | Reusable unit. | `name`, `source`, `version`, `namespace` |
| **`Variable`** | Data point. | `name`, `value`, `scope`, `line_number` |
| **`Template`** | Jinja2 source. | `path`, `variables_used` |
| **`Inventory`** | Host mapping. | `path`, `type`, `hosts`, `groups` |
| **`VarsFile`** | Variable storage. | `path`, `scope` |

## Relationship Types (13)

| Type | From | To | Description |
|------|------|----|-------------|
| **`INCLUDES`** | `File` | `File` | Captured `include_*` tasks. |
| **`IMPORTS`** | `File` | `File` | Captured `import_*` tasks. |
| **`HAS_PLAY`** | `Playbook` | `Play` | Hierarchy of a playbook. |
| **`HAS_TASK`** | `Play`, `Role` | `Task` | Content of a play or role. |
| **`HAS_HANDLER`**| `Playbook`, `Role` | `Handler` | Event handlers in scope. |
| **`USES_TEMPLATE`**| `Task` | `Template` | Links tasks to templates. |
| **`DEFINES_VAR`** | `Task`, `VarsFile`| `Variable` | Variable origins. |
| **`USES_VAR`** | `Task`, `Template`| `Variable` | Variable consumption points. |
| **`USES_ROLE`** | `Playbook`, `Play` | `Role` | Mapping tasks to roles. |
| **`DEPENDS_ON`** | `Role` | `Role` | Cross-role dependencies. |
| **`NOTIFIES`** | `Task` | `Handler` | Event-driven triggers. |
| **`LOADS_VARS`** | `Playbook`, `Play` | `VarsFile` | Source of variable data. |
| **`IN_FILE`** | Any Entity | `File` | Physical origin of the node. |

## Constraints & Indexes

We enforce data integrity using Neo4j constraints:

- `File.path` (Unique)
- `Role.name` (Unique)

Performance is optimized via indexes on:

- `Playbook.name`
- `Task.module`
- `Variable.name`
- `Handler.name`

---

## See Also

- [Architecture: Graph Schema](../architecture/graph-schema.md)
- [User Guide: Building Graphs](../user-guide/building-graphs.md)
- [Extension Points](../architecture/extension-points.md)
