"""Role extractor for Ansible Galaxy roles."""

from typing import Any

from loguru import logger

from ...graph import Node, NodeType, Relationship, RelationshipType
from ...parsers import ParseResult, YAMLParser


class RoleExtractor:
    """Extractor for Ansible roles."""

    def __init__(self, graph_builder: Any):
        """Initialize role extractor.

        Args:
            graph_builder: GraphBuilder or NodeCollector instance
        """
        self.graph_builder = graph_builder
        self.yaml_parser = YAMLParser()

    def extract_requirements(self, parse_result: ParseResult, file_node: Node) -> None:
        """Extract role requirements from requirements.yml.

        Args:
            parse_result: Parsed YAML result
            file_node: File node
        """
        logger.debug(f"Extracting role requirements: {parse_result.file_path}")

        requirements = self.yaml_parser.extract_requirements(parse_result)

        for req in requirements:
            role_name = req.get("name")
            if not role_name:
                continue

            # Create Role node
            role_node = Node(
                node_type=NodeType.ROLE,
                properties={
                    "name": role_name,
                    "source": req.get("src", ""),
                    "version": req.get("version", ""),
                    "namespace": self._extract_namespace(role_name),
                },
            )
            self.graph_builder.add_node(role_node)

            # Link role to requirements file
            file_rel = Relationship(
                rel_type=RelationshipType.IN_FILE,
                from_node=role_node,
                to_node=file_node,
            )
            self.graph_builder.add_relationship(file_rel)

    def _extract_namespace(self, role_name: str) -> str:
        """Extract namespace from role name.

        Args:
            role_name: Role name (e.g., 'geerlingguy.apache')

        Returns:
            Namespace part or empty string
        """
        if "." in role_name:
            return role_name.split(".")[0]
        return ""
