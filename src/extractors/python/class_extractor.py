"""Python class extraction."""

import ast
from pathlib import Path
from typing import Any, Generator


def extract_classes(file_path: Path, codebase_path: Path) -> Generator[dict[str, Any], None, None]:
    """Extract class information from Python file."""
    try:
        with open(file_path) as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            # Resolve base classes (simple names only)
            bases = []
            for base in node.bases:
                if isinstance(base, ast.Name):
                    bases.append(base.id)
                elif isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name):
                    bases.append(f"{base.value.id}.{base.attr}")

            # Decorators
            decorators = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)

            yield {
                "type": "Class",
                "properties": {
                    "name": node.name,
                    "bases": bases,
                    "decorators": decorators,
                    "docstring": (ast.get_docstring(node) or "")[:500],
                    "is_abstract": "ABC" in bases,
                },
            }
