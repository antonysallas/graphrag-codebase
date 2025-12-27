# Adding Extractors

The GraphRAG Pipeline's extensible architecture makes it easy to add support for new languages or frameworks by creating a new Extractor plugin.

## Implementation Steps

### 1. Define the Schema Profile

Create a new YAML file in `config/schemas/` (e.g., `go.yaml`) defining the nodes and relationships for your language.

```yaml
name: go
nodes:
  Package:
    properties:
      - name: string
  Function:
    properties:
      - name: string
relationships:
  - CALLS: [Function, Function]
```

### 2. Create the Extractor Class

Create a new directory in `src/extractors/` and implement a class that inherits from `BaseExtractor`.

```python
from src.extractors.base_extractor import BaseExtractor
from src.extractors.registry import ExtractorRegistry

@ExtractorRegistry.register("go")
class GoExtractor(BaseExtractor):
    schema_profile = "go" # Matches the filename in config/schemas/

    def extract(self, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
        # Implementation to yield nodes
        yield {
            "type": "Package",
            "properties": {"name": "main"}
        }

    def extract_relationships(self, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
        # Implementation to yield relationships
        pass
```

### 3. Implement Parsing Logic

Use the appropriate `Parser` (either an existing one or a new one created in `src/parsers/`) within your extractor to walk the AST and identify entities.

### 4. Register for Auto-Detection (Optional)

Update `src/extractors/registry.py`'s `detect_repo_type` function to recognize your repository type based on file patterns (e.g., `go.mod` files).

## Testing Your Extractor

Add a new test file in `tests/` (e.g., `test_go_extractor.py`):

```python
def test_go_extraction(tmp_path):
    (tmp_path / "main.go").touch()
    extractor = GoExtractor()
    nodes = list(extractor.extract(tmp_path))
    assert any(n["type"] == "Package" for n in nodes)
```

---

## See Also

- [Extractor Architecture](../architecture/extractors.md)
- [Adding Parsers](adding-parsers.md)
- [Contributing Guide](contributing.md)
