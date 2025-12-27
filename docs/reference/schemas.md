# Schema Profiles Reference

The GraphRAG Pipeline uses dynamic schema profiles to ensure the knowledge graph correctly models the specific semantics of different languages.

## 1. Ansible Schema

Optimized for infrastructure-as-code analysis.

**Node Types (10):**

* `File`, `Playbook`, `Play`, `Task`, `Handler`, `Role`, `Variable`, `Template`, `Inventory`, `VarsFile`

**Key Relationships:**

* `HAS_TASK`: Connects Plays/Roles to their Tasks.
* `NOTIFIES`: Connects Tasks to Handlers.
* `DEFINES_VAR`: Tracks variable origins.

## 2. Python Schema

Designed for object-oriented software analysis.

**Node Types (6):**

* `File`: Physical file.
* `Module`: Python module (logical).
* `Class`: Class definition.
* `Function`: Function or method.
* `Import`: External dependency.
* `Variable`: Local or global variable.

**Key Relationships:**

* `DEFINES_CLASS`: Module → Class.
* `HAS_METHOD`: Class → Function.
* `IMPORTS`: Module → Module.

## 3. Generic Schema

A minimal fallback for any repository.

**Node Types (3):**

* `File`: Any source file.
* `Directory`: Folder structure.
* `Reference`: A generic symbol or name reference.

**Key Relationships:**

* `CONTAINS`: Directory → File/Directory.
* `REFERENCES`: File → File.

---

## See Also
* [Architecture: Schema Profiles](../architecture/overview.md#layer-2-graph-construction)
* [Legacy Schema Reference](schema-reference.md)
