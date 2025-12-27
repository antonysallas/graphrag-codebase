"""Python codebase extractor."""

import ast
import hashlib
from pathlib import Path
from typing import Any, Generator, Optional

from loguru import logger

from ..base_extractor import BaseExtractor
from ..registry import ExtractorRegistry
from .class_extractor import extract_classes
from .function_extractor import extract_functions
from .module_extractor import extract_modules


@ExtractorRegistry.register("python")
class PythonExtractor(BaseExtractor):
    """Extractor for Python codebases."""

    schema_profile = "python"

    def __init__(self, **kwargs: Any):
        super().__init__()
        self._repository_id: Optional[str] = None

    def supported_extensions(self) -> list[str]:
        return [".py"]

    def extract(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract Python entities (modules, classes, functions)."""
        codebase_path = Path(codebase_path)
        self._repository_id = repository_id

        # Extract modules (files)
        for py_file in codebase_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue

            logger.debug(f"Processing {py_file}")

            # Calculate content hash
            try:
                with open(py_file, "rb") as f:
                    content_hash = hashlib.sha256(f.read()).hexdigest()
            except Exception:
                content_hash = "error"

            # File node
            node: dict[str, Any] = {
                "type": "File",
                "properties": {
                    "path": str(py_file.relative_to(codebase_path)),
                    "absolute_path": str(py_file.absolute()),
                    "name": py_file.name,
                    "file_type": "python",
                    "type": "python",
                    "content_hash": content_hash,
                    "last_modified": int(py_file.stat().st_mtime),
                    "size": py_file.stat().st_size,
                },
            }
            if self._repository_id:
                node["properties"]["repository"] = self._repository_id
            yield node

            # Helper to inject repo
            def inject_repo(
                generator: Generator[dict[str, Any], None, None],
            ) -> Generator[dict[str, Any], None, None]:
                for item in generator:
                    if self._repository_id:
                        item["properties"]["repository"] = self._repository_id
                    yield item

            # Module node
            yield from inject_repo(extract_modules(py_file, codebase_path))

            # Classes
            yield from inject_repo(extract_classes(py_file, codebase_path))

            # Functions
            yield from inject_repo(extract_functions(py_file, codebase_path))

    def extract_relationships(
        self, codebase_path: Path, repository_id: Optional[str] = None
    ) -> Generator[dict[str, Any], None, None]:
        """Extract import relationships, inheritance, calls."""
        codebase_path = Path(codebase_path)
        self._repository_id = repository_id

        for py_file in codebase_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or ".venv" in str(py_file):
                continue

            rel_path = py_file.relative_to(codebase_path)
            module_name = str(rel_path.with_suffix("")).replace("/", ".")

            try:
                with open(py_file) as f:
                    tree = ast.parse(f.read())

                # Walk for imports
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            yield {
                                "type": "IMPORTS",
                                "source": {"type": "Module", "properties": {"name": module_name}},
                                "target": {"type": "Module", "properties": {"name": alias.name}},
                            }
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            target_name = node.module
                            yield {
                                "type": "FROM_IMPORTS",
                                "source": {"type": "Module", "properties": {"name": module_name}},
                                "target": {"type": "Module", "properties": {"name": target_name}},
                            }
            except Exception as e:
                logger.warning(f"Failed to parse {py_file}: {e}")
