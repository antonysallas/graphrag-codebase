# Extractor Plugin Architecture

The GraphRAG Pipeline uses a plugin-based architecture for codebase extraction, allowing it to dynamically adapt to different repository types.

## Extractor Registry

At the heart of the system is the `ExtractorRegistry`. This component manages the registration and selection of specialized extractors based on the detected repository type.

```
ExtractorRegistry
    ├── @register("ansible") → AnsibleExtractor
    │       ├── PlaybookExtractor
    │       ├── RoleExtractor
    │       └── VariableExtractor
    ├── @register("python") → PythonExtractor
    │       ├── ModuleExtractor
    │       ├── ClassExtractor
    │       └── FunctionExtractor
    └── @register("generic") → GenericExtractor
            └── FileExtractor
```

## How It Works

1. **Detection**: The `detect_repo_type()` function scans the codebase for indicators (e.g., `ansible.cfg` for Ansible, `pyproject.toml` for Python).
2. **Selection**: The `ExtractorRegistry` selects the most appropriate `BaseExtractor` implementation.
3. **Extraction**: The selected extractor performs two passes:
    * **Node Extraction**: Identifies all semantic entities (Files, Classes, Tasks).
    * **Relationship Extraction**: Identifies how those entities are connected (Inherits, Calls, Notifies).

## BaseExtractor Interface

All extractors must implement the `BaseExtractor` abstract class:

```python
class BaseExtractor(ABC):
    schema_profile: str = "generic"

    @abstractmethod
    def extract(self, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
        """Yields node data dictionaries."""
        pass

    @abstractmethod
    def extract_relationships(self, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
        """Yields relationship data dictionaries."""
        pass
```

---

## See Also
* [Adding New Extractors](../developer-guide/adding-extractors.md)
* [Architecture Overview](overview.md)
* [Supported Languages](../index.md#supported-languages)
