from typing import Optional

from loguru import logger
from mcp.types import TextContent

from src.mcp.context import get_repository
from src.mcp.utils import get_neo4j_connection
from src.mcp.utils.tracing import trace_tool


@trace_tool("trace_variable")
async def trace_variable(
    variable_name: str, repository_id: Optional[str] = None
) -> list[TextContent]:
    """
    Trace definition and usage of a specific variable.
    """
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        # Find Definitions
        if repo:
            def_query = """
            MATCH (v:Variable {name: $name, repository: $repo})
            OPTIONAL MATCH (source)-[:DEFINES_VAR]->(v)
            RETURN source.path as path, source.name as source_name, labels(source)[0] as type
            """
            params = {"name": variable_name, "repo": repo}
        else:
            def_query = """
            MATCH (v:Variable {name: $name})
            OPTIONAL MATCH (source)-[:DEFINES_VAR]->(v)
            RETURN source.path as path, source.name as source_name, labels(source)[0] as type
            """
            params = {"name": variable_name}

        definitions = await conn.execute_query(def_query, params)

        # Find Usages
        if repo:
            usage_query = """
            MATCH (v:Variable {name: $name, repository: $repo})
            OPTIONAL MATCH (source)-[:USES_VAR]->(v)
            RETURN source.path as path, source.name as source_name, labels(source)[0] as type
            """
        else:
            usage_query = """
            MATCH (v:Variable {name: $name})
            OPTIONAL MATCH (source)-[:USES_VAR]->(v)
            RETURN source.path as path, source.name as source_name, labels(source)[0] as type
            """

        usages = await conn.execute_query(usage_query, params)

        if not definitions and not usages:
            return [
                TextContent(type="text", text=f"Variable '{variable_name}' not found in the graph.")
            ]

        output = [f"Trace for variable '{variable_name}':\n"]

        if definitions:
            output.append("Definitions:")
            for d in definitions:
                source = d["source_name"] or d["path"]
                output.append(f"  - Defined in {d['type']}: {source}")
        else:
            output.append("Definitions: None found")

        if usages:
            output.append("\nUsages:")
            for u in usages:
                source = u["source_name"] or u["path"]
                output.append(f"  - Used in {u['type']}: {source}")
        else:
            output.append("\nUsages: None found")

        return [TextContent(type="text", text="\n".join(output))]

    except Exception as e:
        logger.error(f"Error tracing variable: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
