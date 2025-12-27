from typing import Optional

from loguru import logger
from mcp.types import TextContent

from src.mcp.context import get_repository
from src.mcp.utils import get_neo4j_connection, validate_file_path_param
from src.mcp.utils.tracing import trace_tool


@trace_tool("find_dependencies")
async def find_dependencies(
    file_path: str, repository_id: Optional[str] = None
) -> list[TextContent]:
    """
    Find dependencies for a given file (includes, imports, variable loads).
    """
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        # Sanitize file path (prevent directory traversal)
        safe_path = validate_file_path_param(file_path)

        if repo:
            query = """
            MATCH (f:File {path: $path, repository: $repo})
            OPTIONAL MATCH (f)-[:INCLUDES|IMPORTS|LOADS_VARS]->(dep)
            WHERE dep.repository = $repo OR dep:Role
            RETURN dep.path as dependency, dep.repository as repository, labels(dep)[0] as type
            """
            params = {"path": safe_path, "repo": repo}
        else:
            # Backward compatible
            query = """
            MATCH (f:File {path: $path})
            OPTIONAL MATCH (f)-[:INCLUDES|IMPORTS|LOADS_VARS]->(dep)
            RETURN dep.path as dependency, dep.repository as repository, labels(dep)[0] as type
            """
            params = {"path": safe_path}

        results = await conn.execute_query(query, params)

        if not results:
            return [TextContent(type="text", text=f"No dependencies found for {safe_path}")]

        formatted_results = [
            f"- {r['type']}: {r['dependency']} (Repo: {r.get('repository', 'global')})"
            for r in results
            if r["dependency"]
        ]

        if not formatted_results:
            return [
                TextContent(type="text", text=f"File found but no dependencies for {safe_path}")
            ]

        return [
            TextContent(
                type="text",
                text=f"Dependencies for {safe_path}:\n" + "\n".join(formatted_results),
            )
        ]

    except ValueError as e:
        return [TextContent(type="text", text=str(e))]
    except Exception as e:
        logger.error(f"Error finding dependencies: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
