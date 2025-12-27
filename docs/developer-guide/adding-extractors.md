# Adding Extractors

Extractors are the domain-specific "brains" of our pipeline. They take a generic AST (Abstract Syntax Tree) and identify entities like Ansible roles, tasks, and variable definitions.

## Key Responsibilities

1. **Pattern Recognition**: Finding specific structural patterns in the AST (e.g., finding all keys in a YAML dictionary that represent Ansible tasks).
2. **Entity Mapping**: Creating `Node` and `Relationship` objects from the AST data.
3. **Graph Construction**: Submitting these entities to the `GraphBuilder` for batch insertion.

## Implementation Pattern

### 1. Identify the Entry Point

Extractors are typically called by the `AnsibleExtractor` coordinator. They receive a `ParseResult` containing the AST root and the raw file content.

### 2. Manual Traversal

Use the `traverse_tree` utility to find what you need:

```python
def extract_tasks(self, result: ParseResult, builder: GraphBuilder) -> None:
    def on_node(node: TSNode, depth: int) -> None:
        if node.type == "block_mapping_pair":
            key_text = self.get_node_text(node.children[0], result.content)
            if key_text == "tasks":
                # Found a tasks block! Now map it to Task nodes.
                self._map_to_graph(node, builder)

    self.traverse_tree(result.root_node, on_node)
```

### 3. Graph Builder API

Never execute Cypher directly. Use the builder's high-level API to ensure batching and validation:

```python
# Add a Node
builder.add_node(Node(
    node_type=NodeType.TASK,
    properties={"name": "Install Nginx", "module": "apt"}
))

# Add a Relationship
builder.add_relationship(Relationship(
    from_node=task_node,
    to_node=file_node,
    rel_type=RelationshipType.IN_FILE
))
```

## Best Practices

- **Thread Safety**: Extractors are executed in parallel via a thread pool. Ensure they do not use shared mutable state.
- **Batch Efficiency**: Only call `builder.add_node()`. The builder handles the `BATCH_SIZE` and `flush()` logic automatically.
- **Idempotency**: Use properties that uniquely identify an entity (e.g., a combination of `path` and `order`) to prevent duplicate nodes.

---

## See Also

- [Graph Schema Reference](../architecture/graph-schema.md)
- [Adding MCP Tools](adding-mcp-tools.md)
- [Parser Design](../architecture/5-layer-design.md)
