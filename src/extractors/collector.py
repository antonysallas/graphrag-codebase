from typing import Optional

from ..graph import Node, NodeType, Relationship


class NodeCollector:
    """Collects nodes and relationships during extraction."""

    def __init__(self, repository_id: Optional[str] = None) -> None:
        self.nodes: list[Node] = []
        self.rels: list[Relationship] = []
        self.repository_id = repository_id

    def add_node(self, node: Node) -> None:
        """Add a node to the collection."""
        # Inject repository into non-Role nodes
        if self.repository_id and node.node_type != NodeType.ROLE:
            node.properties["repository"] = self.repository_id
        self.nodes.append(node)

    def add_relationship(self, rel: Relationship) -> None:
        """Add a relationship to the collection."""
        self.rels.append(rel)

    def flush(self) -> None:
        """Mock flush method."""
        pass
