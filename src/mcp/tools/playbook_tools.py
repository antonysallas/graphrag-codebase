from typing import Optional

from loguru import logger
from mcp.types import TextContent

from src.mcp.context import get_repository
from src.mcp.utils import get_neo4j_connection, validate_file_path_param
from src.mcp.utils.tracing import trace_tool


@trace_tool("analyze_playbook")
async def analyze_playbook(
    playbook_path: str, repository_id: Optional[str] = None
) -> list[TextContent]:
    """
    Analyze the structure of a playbook (plays, tasks).
    """
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        safe_path = validate_file_path_param(playbook_path)

        if repo:
            query = """
            MATCH (p:Playbook {path: $path, repository: $repo})
            OPTIONAL MATCH (p)-[:HAS_PLAY]->(play)
            OPTIONAL MATCH (play)-[:HAS_TASK]->(task)
            RETURN
                p.name as name,
                count(DISTINCT play) as play_count,
                count(DISTINCT task) as task_count,
                collect(DISTINCT play.name) as plays
            """
            params = {"path": safe_path, "repo": repo}
        else:
            query = """
            MATCH (p:Playbook {path: $path})
            OPTIONAL MATCH (p)-[:HAS_PLAY]->(play)
            OPTIONAL MATCH (play)-[:HAS_TASK]->(task)
            RETURN
                p.name as name,
                count(DISTINCT play) as play_count,
                count(DISTINCT task) as task_count,
                collect(DISTINCT play.name) as plays
            """
            params = {"path": safe_path}

        results = await conn.execute_query(query, params)

        if not results:
            return [TextContent(type="text", text=f"Playbook not found: {safe_path}")]

        data = results[0]
        output = f"Analysis of {safe_path}:\n"
        output += f"- Plays: {data['play_count']}\n"
        output += f"- Total Tasks: {data['task_count']}\n"
        output += "- Play Names:\n"
        for play in data["plays"]:
            output += f"  - {play}\n"

        return [TextContent(type="text", text=output)]

    except ValueError as e:
        return [TextContent(type="text", text=str(e))]
    except Exception as e:
        logger.error(f"Error analyzing playbook: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@trace_tool("find_tasks_by_module")
async def find_tasks_by_module(
    module_name: str, repository_id: Optional[str] = None
) -> list[TextContent]:
    """
    Find tasks that use a specific Ansible module.
    """
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        if repo:
            query = """
            MATCH (t:Task {module: $module, repository: $repo})
            RETURN t.name as task, t.file_path as path, t.line_number as line
            LIMIT 50
            """
            params = {"module": module_name, "repo": repo}
        else:
            query = """
            MATCH (t:Task {module: $module})
            RETURN t.name as task, t.file_path as path, t.line_number as line
            LIMIT 50
            """
            params = {"module": module_name}

        results = await conn.execute_query(query, params)

        if not results:
            return [TextContent(type="text", text=f"No tasks found using module '{module_name}'")]

        output = [f"Tasks using module '{module_name}':"]
        for r in results:
            output.append(f"- {r['task']} ({r['path']}:{r['line']})")

        return [TextContent(type="text", text="\n".join(output))]

    except Exception as e:
        logger.error(f"Error finding tasks: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@trace_tool("get_task_hierarchy")
async def get_task_hierarchy(
    playbook_path: str, repository_id: Optional[str] = None
) -> list[TextContent]:
    """
    Get the execution hierarchy of tasks within a playbook.
    """
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        safe_path = validate_file_path_param(playbook_path)

        if repo:
            query = """
            MATCH (p:Playbook {path: $path, repository: $repo})-[:HAS_PLAY]->(play)
            OPTIONAL MATCH (play)-[:HAS_TASK]->(task)
            RETURN play.name as play, play.order as play_order,
                   task.name as task, task.order as task_order
            ORDER BY play_order, task_order
            """
            params = {"path": safe_path, "repo": repo}
        else:
            query = """
            MATCH (p:Playbook {path: $path})-[:HAS_PLAY]->(play)
            OPTIONAL MATCH (play)-[:HAS_TASK]->(task)
            RETURN play.name as play, play.order as play_order,
                   task.name as task, task.order as task_order
            ORDER BY play_order, task_order
            """
            params = {"path": safe_path}

        results = await conn.execute_query(query, params)

        if not results:
            return [TextContent(type="text", text=f"No hierarchy found for {safe_path}")]

        output = [f"Task Hierarchy for {safe_path}:"]
        current_play = None

        for r in results:
            if r["play"] != current_play:
                output.append(f"\nPlay: {r['play']}")
                current_play = r["play"]
            if r["task"]:
                output.append(f"  - {r['task']}")

        return [TextContent(type="text", text="\n".join(output))]

    except ValueError as e:
        return [TextContent(type="text", text=str(e))]
    except Exception as e:
        logger.error(f"Error getting hierarchy: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


@trace_tool("find_template_usage")
async def find_template_usage(
    template_path: str, repository_id: Optional[str] = None
) -> list[TextContent]:
    """
    Find where a Jinja2 template is used and what variables it requires.
    """
    conn = get_neo4j_connection()
    repo = repository_id or get_repository()

    try:
        safe_path = validate_file_path_param(template_path)

        if repo:
            query = """
            MATCH (t:Template {path: $path, repository: $repo})
            OPTIONAL MATCH (task:Task)-[:USES_TEMPLATE]->(t)
            OPTIONAL MATCH (t)-[:USES_VAR]->(v:Variable)
            RETURN
                collect(DISTINCT task.name) as used_by_tasks,
                collect(DISTINCT v.name) as variables_required
            """
            params = {"path": safe_path, "repo": repo}
        else:
            query = """
            MATCH (t:Template {path: $path})
            OPTIONAL MATCH (task:Task)-[:USES_TEMPLATE]->(t)
            OPTIONAL MATCH (t)-[:USES_VAR]->(v:Variable)
            RETURN
                collect(DISTINCT task.name) as used_by_tasks,
                collect(DISTINCT v.name) as variables_required
            """
            params = {"path": safe_path}

        results = await conn.execute_query(query, params)

        if not results:
            return [TextContent(type="text", text=f"Template not found: {safe_path}")]

        data = results[0]
        output = [f"Template Usage: {safe_path}"]

        output.append("\nUsed by Tasks:")
        if data["used_by_tasks"]:
            for task in data["used_by_tasks"]:
                output.append(f"- {task}")
        else:
            output.append("- None found")

        output.append("\nVariables Required:")
        if data["variables_required"]:
            for var in data["variables_required"]:
                output.append(f"- {var}")
        else:
            output.append("- None explicitly detected")

        return [TextContent(type="text", text="\n".join(output))]

    except ValueError as e:
        return [TextContent(type="text", text=str(e))]
    except Exception as e:
        logger.error(f"Error finding template usage: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]
