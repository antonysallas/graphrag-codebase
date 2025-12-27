"""Variable extractor for tracking variables across Ansible codebase."""

import json
from typing import Any

from loguru import logger

from ...graph import Node, NodeType, Relationship, RelationshipType
from ...parsers import ParseResult, YAMLParser


class VariableExtractor:
    """Extractor for Ansible variables."""

    def __init__(self, graph_builder: Any):
        """Initialize variable extractor.

        Args:
            graph_builder: GraphBuilder or NodeCollector instance
        """
        self.graph_builder = graph_builder
        self.yaml_parser = YAMLParser()

    def extract_vars_file(self, parse_result: ParseResult, file_node: Node) -> None:
        """Extract variables from vars file.

        Args:
            parse_result: Parsed YAML result
            file_node: File node
        """
        logger.debug(f"Extracting variables from: {parse_result.file_path}")

        variables = self.yaml_parser.extract_variables(parse_result)

        # Determine scope based on file path
        scope = self._determine_scope(parse_result.file_path)

        # Create VarsFile node
        vars_file_node = Node(
            node_type=NodeType.VARS_FILE,
            properties={"path": parse_result.file_path, "scope": scope},
        )
        self.graph_builder.add_node(vars_file_node)

        # Link to file
        file_rel = Relationship(
            rel_type=RelationshipType.IN_FILE,
            from_node=vars_file_node,
            to_node=file_node,
        )
        self.graph_builder.add_relationship(file_rel)

        # Create Variable nodes
        for var_name, var_value in variables.items():
            self._create_variable(var_name, var_value, scope, vars_file_node)

    def _create_variable(
        self, var_name: str, var_value: Any, scope: str, definer_node: Node
    ) -> None:
        """Create a variable node.

        Args:
            var_name: Variable name
            var_value: Variable value
            scope: Variable scope
            definer_node: Node that defines this variable
        """
        # Serialize value as JSON
        try:
            value_str = json.dumps(var_value)
        except (TypeError, ValueError):
            value_str = str(var_value)

        # Create Variable node
        var_node = Node(
            node_type=NodeType.VARIABLE,
            properties={
                "name": var_name,
                "value": value_str if len(value_str) < 1000 else value_str[:1000],
                "scope": scope,
                "file_path": definer_node.properties.get("path", "unknown"),
            },
        )
        self.graph_builder.add_node(var_node)

        # Link definer to variable
        var_rel = Relationship(
            rel_type=RelationshipType.DEFINES_VAR,
            from_node=definer_node,
            to_node=var_node,
        )
        self.graph_builder.add_relationship(var_rel)

    def _determine_scope(self, file_path: str) -> str:
        """Determine variable scope based on file path.

        Args:
            file_path: Path to vars file

        Returns:
            Scope string
        """
        if "group_vars" in file_path:
            return "group_vars"
        elif "host_vars" in file_path:
            return "host_vars"
        elif "defaults" in file_path:
            return "defaults"
        elif "vars" in file_path:
            return "vars"
        else:
            return "unknown"
