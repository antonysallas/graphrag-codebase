"""LlamaIndex PropertyGraphIndex integration."""

from typing import Any, Optional, cast

from llama_index.core import Settings
from llama_index.core.indices.property_graph import PropertyGraphIndex
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.llms.openai_like import OpenAILike
from loguru import logger

from ..config import LLMConfig, Neo4jConfig


class GraphRAGIndex:
    """LlamaIndex-based GraphRAG query interface.

    Provides hybrid retrieval combining:
    - Graph traversal (Cypher queries)
    - Semantic search (embedding similarity)
    """

    def __init__(
        self,
        neo4j_config: Neo4jConfig,
        llm_config: LLMConfig,
    ):
        """Initialize GraphRAG index.

        Args:
            neo4j_config: Neo4j connection settings
            llm_config: LLM provider settings
        """
        self.neo4j_config = neo4j_config
        self.llm_config = llm_config

        # Initialize LLM
        self._setup_llm()

        # Initialize graph store
        self.graph_store = Neo4jPropertyGraphStore(
            url=neo4j_config.uri,
            username=neo4j_config.user,
            password=neo4j_config.password,
            database=neo4j_config.database,
        )

        # Create index from existing graph
        self.index = PropertyGraphIndex.from_existing(
            property_graph_store=self.graph_store,
        )

        logger.info("GraphRAG index initialized")

    def _setup_llm(self) -> None:
        """Configure LlamaIndex to use our LLM provider."""
        llm = OpenAILike(
            api_base=self.llm_config.api_base,
            api_key=self.llm_config.api_key,
            model=self.llm_config.model_name,
            temperature=self.llm_config.temperature,
            max_tokens=self.llm_config.max_tokens,
            is_chat_model=True,
        )
        Settings.llm = llm
        logger.debug(f"LLM configured: {self.llm_config.model_name}")

    def query(
        self,
        question: str,
        include_cypher: bool = False,
    ) -> dict[str, Any]:
        """Query the graph using natural language.

        Args:
            question: Natural language question
            include_cypher: Whether to include generated Cypher in response

        Returns:
            Dict with 'answer', 'sources', and optionally 'cypher'
        """
        try:
            query_engine = self.index.as_query_engine(
                include_text=True,
                response_mode="tree_summarize",
            )

            response = query_engine.query(question)

            result: dict[str, Any] = {
                "answer": str(response),
                "sources": [
                    {
                        "node_id": node.node_id,
                        "text": node.get_content()[:200],
                    }
                    for node in response.source_nodes
                ],
            }

            if include_cypher and hasattr(response, "metadata") and response.metadata:
                result["cypher"] = response.metadata.get("cypher_query", "")

            return result

        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {
                "answer": f"Query failed: {str(e)}",
                "sources": [],
                "error": str(e),
            }

    def cypher_query(self, cypher: str) -> list[dict[str, Any]]:
        """Execute raw Cypher query.

        Args:
            cypher: Cypher query string

        Returns:
            List of result records as dicts
        """
        res = self.graph_store.structured_query(cypher)
        return cast(list[dict[str, Any]], res)

    def get_node_by_id(self, node_id: str) -> Optional[dict[str, Any]]:
        """Retrieve a specific node by ID.

        Args:
            node_id: Node identifier

        Returns:
            Node properties or None
        """
        cypher = "MATCH (n) WHERE elementId(n) = $node_id RETURN n"
        results = self.graph_store.structured_query(cypher, param_map={"node_id": node_id})
        return results[0] if results else None

    def get_neighbors(
        self,
        node_id: str,
        relationship_types: Optional[list[str]] = None,
        direction: str = "both",
    ) -> list[dict[str, Any]]:
        """Get neighboring nodes.

        Args:
            node_id: Starting node ID
            relationship_types: Filter by relationship types
            direction: 'in', 'out', or 'both'

        Returns:
            List of neighboring nodes with relationship info
        """
        rel_filter = ""
        if relationship_types:
            rel_filter = ":" + "|".join(relationship_types)

        if direction == "in":
            pattern = f"<-[r{rel_filter}]-"
        elif direction == "out":
            pattern = f"-[r{rel_filter}]->"
        else:
            pattern = f"-[r{rel_filter}]-"

        cypher = f"""
        MATCH (start){pattern}(neighbor)
        WHERE elementId(start) = $node_id
        RETURN neighbor, type(r) as relationship
        LIMIT 50
        """

        res = self.graph_store.structured_query(cypher, param_map={"node_id": node_id})
        return cast(list[dict[str, Any]], res)
