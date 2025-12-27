"""Graph schema definitions and utilities."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import yaml
from loguru import logger

SCHEMA_DIR = Path(__file__).parent.parent.parent / "config" / "schemas"


class NodeType(str, Enum):
    """Enumeration of all node types in the graph."""

    # Common
    FILE = "File"
    DIRECTORY = "Directory"

    # Ansible
    PLAYBOOK = "Playbook"
    PLAY = "Play"
    TASK = "Task"
    HANDLER = "Handler"
    ROLE = "Role"
    VARIABLE = "Variable"
    TEMPLATE = "Template"
    INVENTORY = "Inventory"
    VARS_FILE = "VarsFile"

    # Python
    MODULE = "Module"
    CLASS = "Class"
    FUNCTION = "Function"
    IMPORT = "Import"

    # Generic
    REFERENCE = "Reference"


class RelationshipType(str, Enum):
    """Enumeration of all relationship types in the graph."""

    # Common
    IN_FILE = "IN_FILE"

    # Ansible
    INCLUDES = "INCLUDES"
    IMPORTS = "IMPORTS"
    HAS_PLAY = "HAS_PLAY"
    HAS_TASK = "HAS_TASK"
    HAS_HANDLER = "HAS_HANDLER"
    USES_TEMPLATE = "USES_TEMPLATE"
    DEFINES_VAR = "DEFINES_VAR"
    USES_VAR = "USES_VAR"
    USES_ROLE = "USES_ROLE"
    DEPENDS_ON = "DEPENDS_ON"
    NOTIFIES = "NOTIFIES"
    LOADS_VARS = "LOADS_VARS"

    # Python
    FROM_IMPORTS = "FROM_IMPORTS"
    DEFINES_CLASS = "DEFINES_CLASS"
    DEFINES_FUNCTION = "DEFINES_FUNCTION"
    HAS_METHOD = "HAS_METHOD"
    INHERITS = "INHERITS"
    CALLS = "CALLS"
    DECORATED_BY = "DECORATED_BY"

    # Generic
    CONTAINS = "CONTAINS"
    REFERENCES = "REFERENCES"
    DEFINES = "DEFINES"
    USES = "USES"


@dataclass
class Node:
    """Represents a node in the graph."""

    node_type: NodeType
    properties: dict[str, Any]
    node_id: Optional[str] = None  # UUID or unique identifier

    def to_cypher_dict(self) -> dict[str, Any]:
        """Convert node properties to Cypher-compatible dictionary.

        Returns:
            Dictionary of properties for Cypher query
        """
        return {k: v for k, v in self.properties.items() if v is not None}


@dataclass
class Relationship:
    """Represents a relationship in the graph."""

    rel_type: RelationshipType
    from_node: Node
    to_node: Node
    properties: dict[str, Any] = field(default_factory=dict)

    def to_cypher_dict(self) -> dict[str, Any]:
        """Convert relationship properties to Cypher-compatible dictionary.

        Returns:
            Dictionary of properties for Cypher query
        """
        return {k: v for k, v in self.properties.items() if v is not None}


class SchemaProfile:
    """Manages graph schema operations and constraints.

    Previously known as GraphSchema.
    """

    def __init__(self, name: str, schema_config: dict[str, Any]):
        """Initialize graph schema from configuration.

        Args:
            name: Profile name
            schema_config: Schema configuration dictionary from YAML
        """
        self.name = name
        self.config = schema_config
        self.description = schema_config.get("description", "")
        self.nodes = schema_config.get("nodes", {})
        self.relationships = schema_config.get("relationships", {})
        self.indexes = schema_config.get("indexes", [])
        self.constraints = schema_config.get("constraints", [])

    @property
    def node_types(self) -> list[str]:
        return list(self.nodes.keys())

    @property
    def relationship_types(self) -> list[str]:
        return list(self.relationships.keys())

    def get_node_properties(self, node_type: str) -> list[dict[str, Any]]:
        props: list[dict[str, Any]] = self.nodes.get(node_type, {}).get("properties", [])
        return props

    def get_create_index_queries(self) -> list[str]:
        """Generate Cypher queries to create indexes.

        Returns:
            List of CREATE INDEX Cypher queries
        """
        queries = []
        for index in self.indexes:
            node_type = index["node"]

            # Support composite indexes
            if "properties" in index:
                props = index["properties"]
                prop_str = ", ".join([f"n.{p}" for p in props])
                index_name = f"idx_{node_type.lower()}_{'_'.join(props)}"
                query = (
                    f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{node_type}) ON ({prop_str})"
                )
            else:
                # Legacy single property
                prop = index["property"]
                index_name = f"idx_{node_type.lower()}_{prop}"
                query = f"CREATE INDEX {index_name} IF NOT EXISTS FOR (n:{node_type}) ON (n.{prop})"

            queries.append(query)
        return queries

    def get_create_constraint_queries(self) -> list[str]:
        """Generate Cypher queries to create constraints.

        Returns:
            List of CREATE CONSTRAINT Cypher queries
        """
        queries = []
        for constraint in self.constraints:
            node_type = constraint["node"]
            constraint_type = constraint["type"]

            if constraint_type == "unique":
                # Support composite constraints
                if "properties" in constraint:
                    props = constraint["properties"]
                    prop_str = ", ".join([f"n.{p}" for p in props])
                    constraint_name = f"unique_{node_type.lower()}_{'_'.join(props)}"
                    query = (
                        f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                        f"FOR (n:{node_type}) REQUIRE ({prop_str}) IS UNIQUE"
                    )
                else:
                    # Legacy single property
                    prop = constraint["property"]
                    constraint_name = f"unique_{node_type.lower()}_{prop}"
                    query = (
                        f"CREATE CONSTRAINT {constraint_name} IF NOT EXISTS "
                        f"FOR (n:{node_type}) REQUIRE n.{prop} IS UNIQUE"
                    )
                queries.append(query)

        return queries

    def validate_node(self, node: Node) -> tuple[bool, list[str]]:
        """Validate a node against schema requirements.

        Args:
            node: Node to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        node_type_str = node.node_type.value

        if node_type_str not in self.nodes:
            # Maybe allow unknown nodes if schema is open?
            # For now strict validation
            errors.append(f"Unknown node type: {node_type_str}")
            return False, errors

        node_schema = self.nodes[node_type_str]
        properties_schema = node_schema.get("properties", [])

        # Check required properties
        for prop_schema in properties_schema:
            prop_name = prop_schema["name"]
            if prop_schema.get("required", False):
                if prop_name not in node.properties or node.properties[prop_name] is None:
                    errors.append(f"Required property '{prop_name}' missing for {node_type_str}")

        return len(errors) == 0, errors

    def validate_relationship(self, rel: Relationship) -> tuple[bool, list[str]]:
        """Validate a relationship against schema requirements.

        Args:
            rel: Relationship to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        rel_type_str = rel.rel_type.value

        if rel_type_str not in self.relationships:
            errors.append(f"Unknown relationship type: {rel_type_str}")
            return False, errors

        rel_schema = self.relationships[rel_type_str]

        # Validate from/to node types
        valid_from = rel_schema.get("from")
        valid_to = rel_schema.get("to")

        # Handle list or string
        if isinstance(valid_from, str):
            valid_from = [valid_from]
        if isinstance(valid_to, str):
            valid_to = [valid_to]

        # Wildcard support
        if valid_from and "*" in valid_from:
            valid_from = None
        if valid_to and "*" in valid_to:
            valid_to = None

        if valid_from and rel.from_node.node_type.value not in valid_from:
            errors.append(
                f"Invalid source node type '{rel.from_node.node_type.value}' for {rel_type_str}"
            )

        if valid_to and rel.to_node.node_type.value not in valid_to:
            errors.append(
                f"Invalid target node type '{rel.to_node.node_type.value}' for {rel_type_str}"
            )

        return len(errors) == 0, errors


# Alias for backward compatibility if needed, though we will update usage
GraphSchema = SchemaProfile


def load_schema(profile: str = "ansible") -> SchemaProfile:
    """Load schema by profile name.

    Args:
        profile: Schema profile name (ansible, python, generic)

    Returns:
        SchemaProfile instance

    Raises:
        FileNotFoundError: If schema file doesn't exist
    """
    schema_path = SCHEMA_DIR / f"{profile}.yaml"

    if not schema_path.exists():
        # Fallback to legacy location
        legacy_path = Path(__file__).parent.parent.parent / "config" / "schema.yaml"
        if legacy_path.exists() and profile == "ansible":
            schema_path = legacy_path
            logger.warning(f"Using legacy schema at {legacy_path}")
        else:
            raise FileNotFoundError(f"Schema not found: {schema_path}")

    with open(schema_path) as f:
        data = yaml.safe_load(f)

    logger.info(f"Loaded schema profile: {profile}")
    return SchemaProfile(profile, data)


def list_schemas() -> list[str]:
    """List available schema profiles."""
    if not SCHEMA_DIR.exists():
        return ["ansible"]  # Legacy fallback
    return [p.stem for p in SCHEMA_DIR.glob("*.yaml")]
