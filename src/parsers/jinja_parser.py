"""Jinja2 template parser using tree-sitter."""

import re
from typing import Any

from tree_sitter import Node as TSNode

from .base_parser import BaseParser, ParseResult


class JinjaParser(BaseParser):
    """Parser for Jinja2 template files using tree-sitter."""

    def __init__(self):
        """Initialize Jinja2 parser with tree-sitter."""
        super().__init__("jinja2")

    def extract_metadata(self, parse_result: ParseResult) -> dict[str, Any]:
        """Extract metadata from Jinja2 template.

        Args:
            parse_result: Parse result

        Returns:
            Dictionary with template metadata
        """
        metadata = {
            "variables_used": [],
            "filters_used": [],
            "blocks": [],
            "includes": [],
            "macros": [],
        }

        if not parse_result.root_node:
            # Fallback to regex-based extraction if tree-sitter fails
            return self._extract_metadata_regex(parse_result.content)

        # Extract using tree-sitter AST
        metadata["variables_used"] = self._extract_variables_from_ast(
            parse_result.root_node, parse_result.content
        )
        metadata["filters_used"] = self._extract_filters_from_ast(
            parse_result.root_node, parse_result.content
        )
        metadata["blocks"] = self._extract_blocks_from_ast(
            parse_result.root_node, parse_result.content
        )
        metadata["includes"] = self._extract_includes_from_ast(
            parse_result.root_node, parse_result.content
        )
        metadata["macros"] = self._extract_macros_from_ast(
            parse_result.root_node, parse_result.content
        )

        return metadata

    def _extract_variables_from_ast(self, root: TSNode, content: str) -> list[str]:
        """Extract variable references from AST.

        Args:
            root: Root AST node
            content: Template content

        Returns:
            List of unique variable names
        """
        variables = set()

        # Find all identifier nodes
        identifiers = self.find_nodes_by_type(root, "identifier")

        for node in identifiers:
            var_name = self.get_node_text(node, content)
            # Filter out Jinja keywords
            if var_name not in {
                "if",
                "for",
                "in",
                "is",
                "not",
                "and",
                "or",
                "true",
                "false",
                "none",
            }:
                # Get root variable name (before any dots)
                root_var = var_name.split(".")[0] if "." in var_name else var_name
                variables.add(root_var)

        return sorted(list(variables))

    def _extract_filters_from_ast(self, root: TSNode, content: str) -> list[str]:
        """Extract Jinja2 filters from AST.

        Args:
            root: Root AST node
            content: Template content

        Returns:
            List of unique filter names
        """
        filters = set()

        # Find filter nodes (depends on tree-sitter-jinja grammar)
        filter_nodes = self.find_nodes_by_type(root, "filter")

        for node in filter_nodes:
            filter_name = self.get_node_text(node, content)
            # Extract filter name (may need to parse based on actual grammar)
            if "|" in filter_name:
                parts = filter_name.split("|")
                for part in parts[1:]:
                    filter_name_clean = part.strip().split("(")[0].split()[0]
                    filters.add(filter_name_clean)

        return sorted(list(filters))

    def _extract_blocks_from_ast(self, root: TSNode, content: str) -> list[str]:
        """Extract block definitions from AST.

        Args:
            root: Root AST node
            content: Template content

        Returns:
            List of block names
        """
        blocks = []

        # Find block statement nodes
        block_nodes = self.find_nodes_by_type(root, "block_statement")

        for node in block_nodes:
            # Get block name from children
            for child in node.children:
                if child.type == "identifier":
                    block_name = self.get_node_text(child, content)
                    blocks.append(block_name)
                    break

        return blocks

    def _extract_includes_from_ast(self, root: TSNode, content: str) -> list[str]:
        """Extract template includes from AST.

        Args:
            root: Root AST node
            content: Template content

        Returns:
            List of included template paths
        """
        includes = []

        # Find include statement nodes
        include_nodes = self.find_nodes_by_type(root, "include_statement")

        for node in include_nodes:
            # Get the string literal containing the template path
            for child in node.children:
                if child.type == "string":
                    include_path = self.get_node_text(child, content).strip("\"'")
                    includes.append(include_path)
                    break

        return includes

    def _extract_macros_from_ast(self, root: TSNode, content: str) -> list[str]:
        """Extract macro definitions from AST.

        Args:
            root: Root AST node
            content: Template content

        Returns:
            List of macro names
        """
        macros = []

        # Find macro statement nodes
        macro_nodes = self.find_nodes_by_type(root, "macro_statement")

        for node in macro_nodes:
            # Get macro name from children
            for child in node.children:
                if child.type == "identifier":
                    macro_name = self.get_node_text(child, content)
                    macros.append(macro_name)
                    break

        return macros

    def _extract_metadata_regex(self, content: str) -> dict[str, Any]:
        """Fallback: Extract metadata using regex (when tree-sitter fails).

        Args:
            content: Template content

        Returns:
            Dictionary with template metadata
        """
        metadata = {
            "variables_used": self._extract_variables_regex(content),
            "filters_used": self._extract_filters_regex(content),
            "blocks": self._extract_blocks_regex(content),
            "includes": self._extract_includes_regex(content),
            "macros": self._extract_macros_regex(content),
        }
        return metadata

    def _extract_variables_regex(self, content: str) -> list[str]:
        """Extract variable references using regex.

        Args:
            content: Template content

        Returns:
            List of unique variable names
        """
        # Match {{ variable_name }} and {% ... variable_name ... %}
        var_pattern = r"\{\{[\s]*([a-zA-Z_][a-zA-Z0-9_.]*)[\s]*(?:\|[^}]+)?\}\}"
        for_pattern = r"\{%\s*for\s+\w+\s+in\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s*%\}"
        if_pattern = r"\{%\s*if\s+([a-zA-Z_][a-zA-Z0-9_.]*)"

        variables = set()

        # Extract from {{ var }}
        for match in re.finditer(var_pattern, content):
            var_name = match.group(1).split(".")[0]  # Get root variable
            variables.add(var_name)

        # Extract from {% for item in var %}
        for match in re.finditer(for_pattern, content):
            var_name = match.group(1).split(".")[0]
            variables.add(var_name)

        # Extract from {% if var %}
        for match in re.finditer(if_pattern, content):
            var_name = match.group(1).split(".")[0]
            variables.add(var_name)

        return sorted(list(variables))

    def _extract_filters_regex(self, content: str) -> list[str]:
        """Extract Jinja2 filters using regex.

        Args:
            content: Template content

        Returns:
            List of unique filter names
        """
        # Match | filter_name
        filter_pattern = r"\|\s*([a-zA-Z_][a-zA-Z0-9_]*)"

        filters = set()
        for match in re.finditer(filter_pattern, content):
            filters.add(match.group(1))

        return sorted(list(filters))

    def _extract_blocks_regex(self, content: str) -> list[str]:
        """Extract block definitions using regex.

        Args:
            content: Template content

        Returns:
            List of block names
        """
        # Match {% block block_name %}
        block_pattern = r"\{%\s*block\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*%\}"

        blocks = []
        for match in re.finditer(block_pattern, content):
            blocks.append(match.group(1))

        return blocks

    def _extract_includes_regex(self, content: str) -> list[str]:
        """Extract template includes using regex.

        Args:
            content: Template content

        Returns:
            List of included template paths
        """
        # Match {% include 'template.j2' %}
        include_pattern = r"\{%\s*include\s+['\"]([^'\"]+)['\"]\s*%\}"

        includes = []
        for match in re.finditer(include_pattern, content):
            includes.append(match.group(1))

        return includes

    def _extract_macros_regex(self, content: str) -> list[str]:
        """Extract macro definitions using regex.

        Args:
            content: Template content

        Returns:
            List of macro names
        """
        # Match {% macro macro_name(...) %}
        macro_pattern = r"\{%\s*macro\s+([a-zA-Z_][a-zA-Z0-9_]*)"

        macros = []
        for match in re.finditer(macro_pattern, content):
            macros.append(match.group(1))

        return macros
