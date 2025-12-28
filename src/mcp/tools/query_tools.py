from typing import Any, Dict, List, Optional

from loguru import logger
from mcp.types import TextContent


def _format_results(results: List[Dict[str, Any]]) -> str:
    """Format query results as readable text."""
    if not results:
        return "No results found."

    # Get column names from first row
    columns = list(results[0].keys())

    # Build formatted output
    lines = [f"Found {len(results)} result(s):\n"]

    for i, row in enumerate(results, 1):
        lines.append(
            f"**{i}.** ",
        )
        parts = []
        for col in columns:
            value = row.get(col)
            # Clean up column name (remove prefix like 'c.' or 'f.')
            clean_col = col.split(".")[-1] if "." in col else col
            if value:
                # Truncate long values
                str_val = str(value)
                if len(str_val) > 100:
                    str_val = str_val[:100] + "..."
                parts.append(f"{clean_col}: {str_val}")
        lines.append(" | ".join(parts))
        lines.append("")

    return "\n".join(lines)


from src.config import LLMConfig, Neo4jConfig
from src.indexing import GraphRAGIndex
from src.mcp.context import get_repository
from src.mcp.utils import (
    TIMEOUT_ERROR_MSG,
    CircuitOpenError,
    CypherValidator,
    GraphRAGClient,
    GraphSchema,
    QueryTimeoutError,
    get_neo4j_connection,
)
from src.mcp.utils.tracing import trace_tool


@trace_tool("query_codebase")
async def query_codebase(question: str, repository_id: Optional[str] = None) -> list[TextContent]:
    """
    Translate natural language question to Cypher and execute it.
    """
    client = GraphRAGClient()
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        # Load schema from Neo4j FIRST - used for both generation and validation
        schema = await GraphSchema.from_neo4j(conn.driver)

        # Pass schema to generate_cypher so LLM only sees actual relationships
        cypher = await client.generate_cypher(
            question,
            repository_id=repo,
            schema=schema,
        )

        logger.info(f"Generated Cypher: {cypher}")

        # Validate using the SAME schema
        validator = CypherValidator(schema)

        validation = validator.validate(cypher)

        if not validation.is_valid:
            error_msg = "\n".join([f"  - {e}" for e in validation.errors])
            return [
                TextContent(
                    type="text",
                    text=f"❌ Invalid query generated:\n{error_msg}\n\nTry rephrasing your question.",
                )
            ]

        for warning in validation.warnings:
            logger.warning(f"Cypher warning: {warning}")

        results = await conn.execute_query(cypher)
        formatted = _format_results(results)
        return [TextContent(type="text", text=formatted)]

    except QueryTimeoutError:
        return [TextContent(type="text", text=TIMEOUT_ERROR_MSG)]
    except CircuitOpenError as e:
        return [TextContent(type="text", text=e.format_message())]
    except Exception as e:
        logger.error(f"Error querying codebase: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@trace_tool("query_with_rag")
async def query_with_rag(
    question: str,
    include_cypher: bool = False,
) -> list[TextContent]:
    """Query the codebase using LlamaIndex RAG.

    This tool uses hybrid retrieval combining graph traversal
    with semantic search for more comprehensive answers.

    Args:
        question: Natural language question about the codebase
        include_cypher: Whether to include the generated Cypher query

    Returns:
        List of TextContent with answer and sources
    """
    try:
        # Load configs
        neo4j_config = Neo4jConfig()
        llm_config = LLMConfig()

        # Note: GraphRAGIndex currently doesn't support repository filtering natively
        # We might need to inject it into the question or update GraphRAGIndex.
        # Spec Phase 5 updates GraphRAG client, but GraphRAGIndex is for LlamaIndex.
        # For now, let's inject context into question if available.
        repo = get_repository()
        if repo:
            question = f"[Repository: {repo}] {question}"

        index = GraphRAGIndex(neo4j_config, llm_config)
        result = index.query(question, include_cypher=include_cypher)

        # Format output
        output = f"Answer: {result.get('answer', 'No answer found.')}\n\n"

        sources = result.get("sources", [])
        if sources:
            output += "Sources:\n"
            for i, source in enumerate(sources, 1):
                node_id = source.get("node_id", "unknown")
                text = source.get("text", "").replace("\n", " ").strip()
                output += f"{i}. Node {node_id}: {text}\n"

        if include_cypher and result.get("cypher"):
            output += f"\nGenerated Cypher:\n{result['cypher']}\n"

        return [TextContent(type="text", text=output)]

    except Exception as e:
        logger.error(f"Error in query_with_rag: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
