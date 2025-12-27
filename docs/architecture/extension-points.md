# Extension Points

The GraphRAG Pipeline is built with a modular architecture that makes it easy to add support for new languages, capture custom Ansible concepts, or expose new AI-powered analysis tools.

## Adding a New Parser

Our parsing layer is based on [tree-sitter](https://tree-sitter.github.io/tree-sitter/). To support a new language (e.g., shell scripts in `ansible.builtin.shell` tasks):

### 1. Register Grammar

Add the corresponding tree-sitter package to `pyproject.toml`:

```toml
dependencies = [
    "tree-sitter-bash==0.21.0",
]
```

### 2. Implement the Parser

Create a new class in `src/parsers/` that inherits from `BaseParser`:

```python
from tree_sitter import Language
import tree_sitter_bash
from src.parsers.base_parser import BaseParser, ParseResult

class BashParser(BaseParser):
    def __init__(self):
        super().__init__("bash")

    def extract_metadata(self, result: ParseResult) -> dict:
        # custom logic to find shebangs or exported functions
        return {"type": "bash_script"}
```

### 3. Integrate with Extractor

Add your new parser to the `AnsibleExtractor` mapping in `src/extractors/ansible_extractor.py`.

## Adding a New Extractor

Extractors bridge the gap between a generic AST and domain-specific knowledge graph entities.

### 1. Identify the Pattern

Use the `BaseParser.traverse_tree()` method or tree-sitter queries to find specific code patterns (e.g., finding all `include_role` keys in a YAML file).

### 2. Define the Mapping

In your extractor logic, use the `GraphBuilder` instance to register what you found:

```python
# Example: Adding a custom relationship
builder.add_relationship(Relationship(
    from_node=current_task,
    to_node=referenced_file,
    rel_type=RelationshipType.INCLUDES,
    properties={"line": node.start_point[0]}
))
```

## Adding a New MCP Tool

Tools are the "hands" of your AI agents. To add a new capability:

### 1. Write the Cypher Logic

Create a specialized function in `src/mcp/tools/` that executes a targeted Neo4j query.

### 2. Add Observability

Always decorate your new tool with `@trace_tool` from `src/mcp/utils/tracing.py`.

### 3. Register in Server

Expose the tool in `src/mcp/server.py` by adding it to the `list_tools()` response and the `call_tool()` switch logic.

---

## See Also

- [Adding Parsers Guide](../developer-guide/adding-parsers.md)
- [Adding Extractors Guide](../developer-guide/adding-extractors.md)
- [Adding MCP Tools Guide](../developer-guide/adding-mcp-tools.md)
