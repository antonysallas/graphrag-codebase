"""Python parser for dynamic inventory scripts."""

from typing import Any

from tree_sitter import Node as TSNode

from .base_parser import BaseParser, ParseResult


class PythonParser(BaseParser):
    """Parser for Python files (mainly dynamic inventory scripts)."""

    def __init__(self):
        """Initialize Python parser."""
        super().__init__("python")

    def extract_metadata(self, parse_result: ParseResult) -> dict[str, Any]:
        """Extract metadata from Python file.

        Args:
            parse_result: Parse result

        Returns:
            Dictionary with Python file metadata
        """
        metadata = {
            "is_inventory_script": False,
            "functions": [],
            "classes": [],
            "imports": [],
        }

        if not parse_result.root_node:
            return metadata

        # Extract functions
        function_nodes = self.find_nodes_by_type(parse_result.root_node, "function_definition")
        metadata["functions"] = [
            self._extract_function_info(node, parse_result.content) for node in function_nodes
        ]

        # Extract classes
        class_nodes = self.find_nodes_by_type(parse_result.root_node, "class_definition")
        metadata["classes"] = [
            self._extract_class_info(node, parse_result.content) for node in class_nodes
        ]

        # Extract imports
        import_nodes = self.find_nodes_by_type(parse_result.root_node, "import_statement")
        import_from_nodes = self.find_nodes_by_type(parse_result.root_node, "import_from_statement")
        metadata["imports"] = [
            self.get_node_text(node, parse_result.content) for node in import_nodes
        ] + [self.get_node_text(node, parse_result.content) for node in import_from_nodes]

        # Check if it's likely a dynamic inventory script
        metadata["is_inventory_script"] = self._is_inventory_script(metadata)

        return metadata

    def _extract_function_info(self, node: TSNode, content: str) -> dict[str, Any]:
        """Extract function information.

        Args:
            node: Function definition node
            content: Source code

        Returns:
            Dictionary with function info
        """
        func_info = {"name": "", "line_number": node.start_point[0] + 1, "args": []}

        # Get function name
        name_node = node.child_by_field_name("name")
        if name_node:
            func_info["name"] = self.get_node_text(name_node, content)

        # Get parameters
        params_node = node.child_by_field_name("parameters")
        if params_node:
            func_info["args"] = self.get_node_text(params_node, content)

        return func_info

    def _extract_class_info(self, node: TSNode, content: str) -> dict[str, Any]:
        """Extract class information.

        Args:
            node: Class definition node
            content: Source code

        Returns:
            Dictionary with class info
        """
        class_info = {
            "name": "",
            "line_number": node.start_point[0] + 1,
            "bases": [],
            "methods": [],
        }

        # Get class name
        name_node = node.child_by_field_name("name")
        if name_node:
            class_info["name"] = self.get_node_text(name_node, content)

        # Get base classes
        superclasses_node = node.child_by_field_name("superclasses")
        if superclasses_node:
            class_info["bases"] = self.get_node_text(superclasses_node, content)

        # Get methods
        body_node = node.child_by_field_name("body")
        if body_node:
            method_nodes = self.find_nodes_by_type(body_node, "function_definition")
            class_info["methods"] = [
                self._extract_function_info(method, content) for method in method_nodes
            ]

        return class_info

    def _is_inventory_script(self, metadata: dict[str, Any]) -> bool:
        """Heuristic to determine if this is an Ansible dynamic inventory script.

        Args:
            metadata: Extracted metadata

        Returns:
            True if likely an inventory script
        """
        # Check for common inventory functions
        func_names = [f["name"] for f in metadata.get("functions", [])]

        inventory_indicators = [
            "get_inventory",
            "parse_cli_args",
            "list_inventory",
            "host_inventory",
        ]

        return any(indicator in func_names for indicator in inventory_indicators)
