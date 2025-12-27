import pytest

from src.graph.schema import list_schemas, load_schema


def test_load_ansible_schema():
    schema = load_schema("ansible")
    assert schema.name == "ansible"
    assert "Playbook" in schema.node_types


def test_load_python_schema():
    schema = load_schema("python")
    assert schema.name == "python"
    assert "Module" in schema.node_types
    assert "Class" in schema.node_types


def test_load_generic_schema():
    schema = load_schema("generic")
    assert schema.name == "generic"
    assert "Directory" in schema.node_types


def test_list_schemas():
    schemas = list_schemas()
    assert "ansible" in schemas
    assert "python" in schemas
    assert "generic" in schemas


def test_invalid_schema():
    with pytest.raises(FileNotFoundError):
        load_schema("non_existent")


from unittest.mock import MagicMock

from src.config import Config, Neo4jConfig
from src.graph.builder import GraphBuilder


def test_graph_builder_init_with_profile():
    config = MagicMock(spec=Config)
    config.neo4j = MagicMock(spec=Neo4jConfig)
    config.neo4j.uri = "bolt://localhost:7687"
    config.neo4j.user = "neo4j"
    config.neo4j.password = "password"
    config.neo4j.database = "neo4j"
    config.pipeline = MagicMock()
    config.pipeline.batch_size = 100

    # Mock driver to avoid connection
    driver = MagicMock()

    gb = GraphBuilder(config, schema_profile="python", driver=driver)
    assert gb.schema.name == "python"
    assert "Class" in gb.schema.node_types
