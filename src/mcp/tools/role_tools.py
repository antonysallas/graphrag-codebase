from typing import Optional

from loguru import logger
from mcp.types import TextContent

from src.mcp.context import get_repository
from src.mcp.utils import get_neo4j_connection
from src.mcp.utils.tracing import trace_tool


@trace_tool("get_role_usage")
async def get_role_usage(role_name: str, repository_id: Optional[str] = None) -> list[TextContent]:
    """
    Find where a specific Ansible role is used.
    """
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        # Note: repository_id is optional filter, but we always show which repo uses the role
        # We query for the role (global) and then find usages, optionally filtering usages by repo

        where_clause = "WHERE $repo IS NULL OR usage.repository = $repo"

        query = f"""
        MATCH (r:Role {{name: $name}})
        OPTIONAL MATCH (usage)-[:USES_ROLE]->(r)
        {where_clause}
        RETURN
            r.name as role,
            collect(DISTINCT {{
                repository: usage.repository,
                type: labels(usage)[0],
                name: usage.name,
                path: usage.path
            }}) as usages
        """

        results = await conn.execute_query(query, {"name": role_name, "repo": repo})

        if not results or not results[0]["usages"]:
            return [TextContent(type="text", text=f"Role '{role_name}' is not used or not found.")]

        output = [f"Usage of role '{role_name}':"]

        for usage in results[0]["usages"]:
            # Handle case where optional match returns null inside collect (if no usages)
            if not usage["type"]:
                continue

            repo_info = f" [Repo: {usage['repository']}]" if usage.get("repository") else ""
            source = usage["name"] or usage["path"]
            output.append(f"- Used by {usage['type']}: {source}{repo_info}")

        if len(output) == 1:  # Only header
            return [
                TextContent(type="text", text=f"Role '{role_name}' found but no usages detected.")
            ]

        return [TextContent(type="text", text="\n".join(output))]

    except Exception as e:
        logger.error(f"Error getting role usage: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
