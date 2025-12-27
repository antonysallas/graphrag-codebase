"""Python function extraction."""

import ast
from pathlib import Path
from typing import Any, Generator


def extract_functions(
    file_path: Path, codebase_path: Path
) -> Generator[dict[str, Any], None, None]:
    """Extract function information from Python file."""
    try:
        with open(file_path) as f:
            source = f.read()
        tree = ast.parse(source)
    except (SyntaxError, UnicodeDecodeError):
        return

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Params
            params = [arg.arg for arg in node.args.args]

            # Decorators
            decorators = []
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name):
                    decorators.append(dec.id)
                elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                    decorators.append(dec.func.id)

            yield {
                "type": "Function",
                "properties": {
                    "name": node.name,
                    "params": params,
                    "return_type": "",  # Complex to extract from AST annotation without resolution
                    "decorators": decorators,
                    "docstring": (ast.get_docstring(node) or "")[:500],
                    "is_async": isinstance(node, ast.AsyncFunctionDef),
                    "is_method": False,  # Hard to tell without context (if inside class)
                },
            }
