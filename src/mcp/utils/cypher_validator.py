import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set

from neo4j import AsyncDriver


@dataclass
class GraphSchema:
    """Known graph schema elements."""

    node_labels: Set[str]
    relationship_types: Set[str]

    @classmethod
    async def from_neo4j(cls, driver: AsyncDriver) -> "GraphSchema":
        """Load schema from Neo4j database."""
        async with driver.session() as session:
            # Get node labels
            labels_result = await session.run("CALL db.labels()")
            labels = {record["label"] async for record in labels_result}

            # Get relationship types
            rels_result = await session.run("CALL db.relationshipTypes()")
            rels = {record["relationshipType"] async for record in rels_result}

            return cls(node_labels=labels, relationship_types=rels)

    @classmethod
    def from_config(cls, schema_config: Dict[str, Any]) -> "GraphSchema":
        """Load schema from configuration (schema.yaml)."""
        labels = set(schema_config.get("nodes", {}).keys())
        rels = set(schema_config.get("relationships", {}).keys())
        return cls(node_labels=labels, relationship_types=rels)


@dataclass
class ValidationResult:
    """Result of Cypher validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.is_valid


class CypherValidator:
    """Validate Cypher queries against known schema."""

    # Dangerous patterns to reject
    FORBIDDEN_PATTERNS = [
        (r"\bDETACH\s+DELETE\b", "DETACH DELETE operations"),
        (r"\bDROP\b", "DROP operations"),
        (r"\bCREATE\s+INDEX\b", "CREATE INDEX operations"),
        (r"\bCREATE\s+CONSTRAINT\b", "CREATE CONSTRAINT operations"),
        (r"\bCALL\s+db\.", "db.* procedure calls"),
        (r"\bCALL\s+apoc\.", "APOC procedure calls"),
        (r"\bDELETE\b", "DELETE operations"),
        (r"\bREMOVE\b", "REMOVE operations"),
        (r"\bSET\b", "SET operations"),
        (r"\bCREATE\b", "CREATE operations"),
        (r"\bMERGE\b", "MERGE operations"),
    ]

    # Warning patterns for expensive operations
    WARNING_PATTERNS = [
        (r"\[\*\]", "Unbounded variable-length path"),
        (r"\[\*\d+\.\.\]", "Open-ended variable-length path"),
        (r"(?<!LIMIT\s)\bRETURN\s+\*", "RETURN * without LIMIT"),
    ]

    def __init__(self, schema: GraphSchema):
        self.schema = schema

    def validate(self, query: str) -> ValidationResult:
        """Validate a Cypher query."""
        errors = []
        warnings = []

        # Check for forbidden patterns
        for pattern, description in self.FORBIDDEN_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                errors.append(f"Forbidden: {description}")

        # Extract and validate node labels
        label_pattern = r"\([\w]*:([\w]+)\)"
        labels_used = set(re.findall(label_pattern, query))
        unknown_labels = labels_used - self.schema.node_labels
        if unknown_labels:
            errors.append(f"Unknown node labels: {unknown_labels}")

        # Extract and validate relationship types
        rel_pattern = r"\[[\w]*:([\w]+)\]"
        rels_used = set(re.findall(rel_pattern, query))
        unknown_rels = rels_used - self.schema.relationship_types
        if unknown_rels:
            errors.append(f"Unknown relationship types: {unknown_rels}")

        # Check for warning patterns
        for pattern, description in self.WARNING_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                warnings.append(description)

        # Warn if no LIMIT clause
        if not re.search(r"\bLIMIT\s+\d+", query, re.IGNORECASE):
            warnings.append("No LIMIT clause (will be added automatically)")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)


class CypherValidationError(Exception):
    """Raised when Cypher validation fails."""

    def __init__(self, message: str, errors: List[str]):
        super().__init__(message)
        self.errors = errors
