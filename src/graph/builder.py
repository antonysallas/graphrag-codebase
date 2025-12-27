"""Graph builder for constructing Neo4j graph from parsed AST data."""

from collections import defaultdict
from typing import Any, Optional

from loguru import logger
from neo4j import Driver, GraphDatabase

from ..config import Config
from .schema import Node, NodeType, Relationship, RelationshipType, load_schema


class GraphBuilder:
    """Builds and manages the Neo4j graph database."""

    def __init__(
        self, config: Config, schema_profile: str = "ansible", driver: Optional[Driver] = None
    ):
        """Initialize graph builder.

        Args:
            config: Configuration object
            schema_profile: Schema profile name (ansible, python, generic)
            driver: Optional existing Neo4j driver
        """
        self.config = config
        self.schema = load_schema(schema_profile)
        self.driver = driver or self._create_driver()
        self.batch_size = config.pipeline.batch_size

        # Batch collections
        self._node_batch: list[Node] = []
        self._rel_batch: list[Relationship] = []

    def _create_driver(self) -> Driver:
        """Create Neo4j driver from configuration.

        Returns:
            Neo4j driver instance
        """
        return GraphDatabase.driver(
            self.config.neo4j.uri,
            auth=(self.config.neo4j.user, self.config.neo4j.password),
        )

    def close(self) -> None:
        """Close the Neo4j driver."""
        if self.driver:
            self.driver.close()

    def __enter__(self) -> "GraphBuilder":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.flush()  # Flush any remaining batches
        self.close()

    def initialize_schema(self) -> None:
        """Initialize database schema (indexes and constraints)."""
        logger.info("Initializing database schema...")

        with self.driver.session(database=self.config.neo4j.database) as session:
            # Create indexes
            for query in self.schema.get_create_index_queries():
                try:
                    session.run(query)
                    logger.debug(f"Created index: {query}")
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")

            # Create constraints
            for query in self.schema.get_create_constraint_queries():
                try:
                    session.run(query)
                    logger.debug(f"Created constraint: {query}")
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {e}")

        logger.info("Schema initialization complete")

    def clear_graph(self) -> None:
        """Clear all nodes and relationships from the graph.

        Warning: This deletes all data in the database!
        """
        logger.warning("Clearing entire graph database...")

        with self.driver.session(database=self.config.neo4j.database) as session:
            # Delete all nodes and relationships
            session.run("MATCH (n) DETACH DELETE n")

        logger.info("Graph cleared")

    def add_node(self, node: Node) -> None:
        """Add a node to the batch.

        Args:
            node: Node to add
        """
        # Validate node
        is_valid, errors = self.schema.validate_node(node)
        if not is_valid:
            logger.error(f"Node validation failed: {errors}")
            return

        self._node_batch.append(node)

        # Flush if batch is full
        if len(self._node_batch) >= self.batch_size:
            self._flush_nodes()

    def add_relationship(self, rel: Relationship) -> None:
        """Add a relationship to the batch.

        Args:
            rel: Relationship to add
        """
        # Validate relationship
        is_valid, errors = self.schema.validate_relationship(rel)
        if not is_valid:
            logger.error(f"Relationship validation failed: {errors}")
            return

        self._rel_batch.append(rel)

        # Flush if batch is full
        if len(self._rel_batch) >= self.batch_size:
            self._flush_relationships()

    def flush(self) -> None:
        """Flush all pending batches to database."""
        self._flush_nodes()
        self._flush_relationships()

    def _get_merge_keys(self, node_type: NodeType) -> list[str]:
        """Get merge keys for a given node type.

        Args:
            node_type: Type of node

        Returns:
            List of property names to use as composite merge key
        """
        if node_type in [
            NodeType.FILE,
            NodeType.PLAYBOOK,
            NodeType.TEMPLATE,
            NodeType.INVENTORY,
            NodeType.VARS_FILE,
            NodeType.DIRECTORY,
        ]:
            return ["repository", "path"]  # Composite key
        elif node_type == NodeType.ROLE:
            return ["name"]  # Keep global - NO repository
        elif node_type == NodeType.PLAY:
            return ["repository", "playbook_path", "name", "order"]
        elif node_type == NodeType.TASK:
            return ["repository", "file_path", "name", "order"]
        elif node_type == NodeType.HANDLER:
            return ["repository", "file_path", "name"]
        elif node_type == NodeType.VARIABLE:
            return ["repository", "name", "scope", "file_path"]
        elif node_type == NodeType.MODULE:
            return ["repository", "path"]
        elif node_type == NodeType.CLASS:
            return [
                "repository",
                "name",
            ]  # Spec said module_path but existing was name. Sticking to name + repo
        elif node_type == NodeType.FUNCTION:
            return ["repository", "name"]  # Spec said file_path but existing was name.
        elif node_type == NodeType.IMPORT:
            return [
                "repository",
                "module",
                "alias",
            ]  # Spec said file_path, name. Existing schema has module, alias
        elif node_type == NodeType.REFERENCE:
            return ["repository", "name"]
        else:
            return ["name"]

    def _flush_nodes(self) -> None:
        """Flush node batch to database."""
        if not self._node_batch:
            return

        logger.info(f"Flushing {len(self._node_batch)} nodes to database...")

        # Group nodes by type for batch processing
        nodes_by_type: dict[NodeType, list[Node]] = defaultdict(list)
        for node in self._node_batch:
            # Validate merge keys are not None
            merge_keys = self._get_merge_keys(node.node_type)
            props = node.to_cypher_dict()

            # Check for missing keys, allowing for optional repository if not set (e.g. Role)
            missing_keys = []
            for key in merge_keys:
                if props.get(key) is None:
                    # Special case: repository might be missing for global nodes like Role,
                    # but if it's in merge_keys it MUST be present.
                    # Role doesn't have repository in merge_keys, so it's fine.
                    missing_keys.append(key)

            if missing_keys:
                logger.warning(
                    f"Skipping node {node.node_type.value} due to NULL merge keys: {missing_keys}. "
                    f"Properties: {props}"
                )
                continue

            nodes_by_type[node.node_type].append(node)

        with self.driver.session(database=self.config.neo4j.database) as session:
            for node_type, nodes in nodes_by_type.items():
                # Prepare batch data
                batch_data = [node.to_cypher_dict() for node in nodes]

                # Get composite merge keys for this node type
                merge_keys = self._get_merge_keys(node_type)

                # Build MERGE clause with composite keys
                merge_conditions = ", ".join([f"{key}: props.{key}" for key in merge_keys])

                # Use MERGE for all node types to ensure deduplication
                query = f"""
                UNWIND $batch AS props
                MERGE (n:{node_type.value} {{{merge_conditions}}})
                SET n += props
                """

                try:
                    session.run(query, batch=batch_data)
                    logger.debug(f"Created/updated {len(batch_data)} {node_type.value} nodes")
                except Exception as e:
                    logger.error(f"Failed to create nodes of type {node_type.value}: {e}")

        # Clear batch
        self._node_batch.clear()

    def _flush_relationships(self) -> None:
        """Flush relationship batch to database."""
        if not self._rel_batch:
            return

        logger.info(f"Flushing {len(self._rel_batch)} relationships to database...")

        # Group relationships by type
        rels_by_type: dict[RelationshipType, list[Relationship]] = defaultdict(list)
        for rel in self._rel_batch:
            rels_by_type[rel.rel_type].append(rel)

        with self.driver.session(database=self.config.neo4j.database) as session:
            for rel_type, rels in rels_by_type.items():
                for rel in rels:
                    # Build Cypher query for relationship creation
                    # We match nodes by their identifying properties and create relationship
                    from_type = rel.from_node.node_type.value
                    to_type = rel.to_node.node_type.value

                    # Use path as primary identifier for most nodes
                    from_props = rel.from_node.to_cypher_dict()
                    to_props = rel.to_node.to_cypher_dict()
                    rel_props = rel.to_cypher_dict()

                    # Construct match conditions
                    from_id = from_props.get("path") or from_props.get("name")
                    to_id = to_props.get("path") or to_props.get("name")

                    # Get repository from source/target node if available
                    from_repo = from_props.get("repository")
                    to_repo = to_props.get("repository")

                    if not from_id or not to_id:
                        logger.warning("Skipping relationship: missing identifiers")
                        continue

                    # Build match with repository context
                    if from_repo:
                        from_match = (
                            "a.repository = $from_repo AND (a.path = $from_id OR a.name = $from_id)"
                        )
                    else:
                        from_match = "a.path = $from_id OR a.name = $from_id"

                    if to_repo:
                        to_match = (
                            "b.repository = $to_repo AND (b.path = $to_id OR b.name = $to_id)"
                        )
                    else:
                        to_match = "b.path = $to_id OR b.name = $to_id"

                    query = f"""
                    MATCH (a:{from_type})
                    WHERE {from_match}
                    MATCH (b:{to_type})
                    WHERE {to_match}
                    MERGE (a)-[r:{rel_type.value}]->(b)
                    SET r += $rel_props
                    """

                    try:
                        session.run(
                            query,
                            from_id=from_id,
                            to_id=to_id,
                            from_repo=from_repo,
                            to_repo=to_repo,
                            rel_props=rel_props,
                        )
                    except Exception as e:
                        logger.error(f"Failed to create relationship {rel_type.value}: {e}")

        # Clear batch
        self._rel_batch.clear()

    def get_stats(self) -> dict[str, int]:
        """Get statistics about the graph.

        Returns:
            Dictionary with node and relationship counts
        """
        stats = {}

        with self.driver.session(database=self.config.neo4j.database) as session:
            # Count nodes by type
            for node_type in NodeType:
                result = session.run(f"MATCH (n:{node_type.value}) RETURN count(n) as count")
                record = result.single()
                stats[f"nodes_{node_type.value}"] = record["count"] if record else 0

            # Count relationships by type
            for rel_type in RelationshipType:
                result = session.run(f"MATCH ()-[r:{rel_type.value}]->() RETURN count(r) as count")
                record = result.single()
                stats[f"rels_{rel_type.value}"] = record["count"] if record else 0

            # Total counts
            result = session.run("MATCH (n) RETURN count(n) as count")
            record = result.single()
            stats["total_nodes"] = record["count"] if record else 0

            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            record = result.single()
            stats["total_relationships"] = record["count"] if record else 0

        return stats
