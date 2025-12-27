from src.mcp.utils.cypher_validator import CypherValidator, GraphSchema


def test_rejects_unknown_label() -> None:
    schema = GraphSchema(
        node_labels={"Task", "Role", "Playbook"}, relationship_types={"USES_ROLE", "HAS_TASK"}
    )
    validator = CypherValidator(schema)

    result = validator.validate("MATCH (n:FakeNode) RETURN n")
    assert not result.is_valid
    assert "Unknown node labels" in result.errors[0]


def test_rejects_unknown_relationship() -> None:
    schema = GraphSchema(node_labels={"Task"}, relationship_types={"HAS_TASK"})
    validator = CypherValidator(schema)

    result = validator.validate("MATCH (n)-[:FAKE_REL]->(m) RETURN n")
    assert not result.is_valid
    assert "Unknown relationship types" in result.errors[0]


def test_blocks_delete() -> None:
    validator = CypherValidator(GraphSchema(set(), set()))
    result = validator.validate("MATCH (n) DELETE n")
    assert not result.is_valid
    assert "Forbidden: DELETE operations" in result.errors[0]


def test_warns_no_limit() -> None:
    schema = GraphSchema(node_labels={"Task"}, relationship_types=set())
    validator = CypherValidator(schema)

    result = validator.validate("MATCH (n:Task) RETURN n")
    assert result.is_valid
    assert any("No LIMIT clause" in w for w in result.warnings)


def test_valid_query() -> None:
    schema = GraphSchema(node_labels={"Task"}, relationship_types=set())
    validator = CypherValidator(schema)

    result = validator.validate("MATCH (n:Task) RETURN n LIMIT 10")
    assert result.is_valid
    assert not result.errors
    assert not result.warnings
