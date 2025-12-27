# Extractor API

The Extractor API provides the framework for turning source code into structured knowledge graph data.

## BaseExtractor

Abstract base class for all language-specific extractors.

```python
class BaseExtractor(ABC):
    schema_profile: str = "generic"

    @abstractmethod
    def extract(self, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
        """Yields node data."""
        pass

    @abstractmethod
    def extract_relationships(self, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
        """Yields relationship data."""
        pass
```

## ExtractorRegistry

Used to register and retrieve extractors for specific repository types.

### Registration

```python
@ExtractorRegistry.register("python")
class PythonExtractor(BaseExtractor):
    ...
```

### Retrieval

```python
extractor_cls = ExtractorRegistry.get_extractor("ansible")
extractor = extractor_cls()
```

## Auto-Detection

### `detect_repo_type(path: Path) -> DetectionResult`

Scans a directory for patterns indicating its repository type.

**Returns:**

* `repo_type`: "ansible", "python", or "generic"
* `confidence`: Score from 0.0 to 1.0
* `indicators`: List of files that triggered the match

---

## See Also
* [Extractor Architecture](../architecture/extractors.md)
* [Adding Extractors](../developer-guide/adding-parsers.md)
* [Schema Reference](../reference/schemas.md)
