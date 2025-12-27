"""Python module extraction."""

import ast
from pathlib import Path
from typing import Any, Generator


def extract_modules(file_path: Path, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
    """Extract module information from Python file."""
    try:
        with open(file_path) as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return  # Skip files with syntax errors or encoding issues

    # Calculate module name from path
    rel_path = file_path.relative_to(codebase_path)
    module_name = str(rel_path.with_suffix("")).replace("/", ".")

    # Get docstring
    docstring = ast.get_docstring(tree) or ""

    yield {
        "type": "Module",
        "properties": {
            "name": module_name,
            "path": str(rel_path),
            "docstring": docstring[:500],  # Truncate long docstrings
            "is_package": file_path.name == "__init__.py",
        },
    }
