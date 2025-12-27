"""Generic file-based extractor for unknown repo types."""

import hashlib
from pathlib import Path
from typing import Any, Generator, Optional

from ..base_extractor import BaseExtractor
from ..registry import ExtractorRegistry

IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
}

IGNORED_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".so",
    ".dylib",
    ".dll",
    ".exe",
    ".bin",
    ".o",
    ".a",
}


@ExtractorRegistry.register("generic")
class GenericExtractor(BaseExtractor):
    """File-based extractor for any repository type."""

    schema_profile = "generic"

    def __init__(self, **kwargs: Any):
        super().__init__()
        self._repository_id: Optional[str] = None

    def extract(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract file and directory structure."""
        codebase_path = Path(codebase_path)
        self._repository_id = repository_id

        for item in codebase_path.rglob("*"):
            # Skip ignored directories
            if any(ignored in item.parts for ignored in IGNORED_DIRS):
                continue

            rel_path = item.relative_to(codebase_path)

            if item.is_dir():
                node: dict[str, Any] = {
                    "type": "Directory",
                    "properties": {
                        "path": str(rel_path),
                        "name": item.name,
                    },
                }
                if self._repository_id:
                    node["properties"]["repository"] = self._repository_id
                yield node
            elif item.is_file():
                # Skip binary/compiled files
                if item.suffix in IGNORED_EXTENSIONS:
                    continue

                # Calculate hash
                try:
                    with open(item, "rb") as f:
                        content_hash = hashlib.sha256(f.read()).hexdigest()
                except Exception:
                    content_hash = "error"

                node = {
                    "type": "File",
                    "properties": {
                        "path": str(rel_path),
                        "absolute_path": str(item.absolute()),
                        "name": item.name,
                        "file_type": item.suffix[1:] if item.suffix else "none",  # Generic type
                        "type": self._detect_file_type(item),  # For spec 'type' property
                        "extension": item.suffix,
                        "size": item.stat().st_size,
                        "content_hash": content_hash,
                        "last_modified": int(item.stat().st_mtime),
                    },
                }
                if self._repository_id:
                    node["properties"]["repository"] = self._repository_id
                yield node

    def _detect_file_type(self, path: Path) -> str:
        """Detect file type from extension."""
        ext_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".md": "markdown",
            ".rst": "rst",
            ".go": "go",
            ".rs": "rust",
            ".rb": "ruby",
            ".sh": "shell",
        }
        return ext_map.get(path.suffix.lower(), "unknown")

    def extract_relationships(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract directory containment relationships."""
        codebase_path = Path(codebase_path)
        self._repository_id = repository_id

        for item in codebase_path.rglob("*"):
            if any(ignored in item.parts for ignored in IGNORED_DIRS):
                continue

            # Skip binary/compiled files (same check as extract nodes)
            if item.is_file() and item.suffix in IGNORED_EXTENSIONS:
                continue

            if item.parent != codebase_path:
                # Check if parent is ignored?
                if any(ignored in item.parent.parts for ignored in IGNORED_DIRS):
                    continue

                source_path = str(item.parent.relative_to(codebase_path))
                target_path = str(item.relative_to(codebase_path))

                # Identify source/target by path
                yield {
                    "type": "CONTAINS",
                    "source": {"type": "Directory", "properties": {"path": source_path}},
                    "target": {
                        "type": "File" if item.is_file() else "Directory",
                        "properties": {"path": target_path},
                    },
                }
