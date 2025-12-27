import asyncio
from typing import Any

from loguru import logger
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp.server import Server
from src.mcp.tools import (
    analyze_playbook,
    find_dependencies,
    find_tasks_by_module,
    find_template_usage,
    get_role_usage,
    get_task_hierarchy,
    query_codebase,
    query_with_rag,
    trace_variable,
)

# Initialize MCP Server
app = Server("graphrag")


@app.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="set_repository_context",
            description="Set the active repository for all subsequent queries. Required before querying multi-repo graphs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "repository_id": {
                        "type": "string",
                        "description": "Repository identifier (e.g., 'my-ansible', 'infra-prod')",
                    }
                },
                "required": ["repository_id"],
            },
        ),
        Tool(
            name="query_codebase",
            description="Translate natural language question to Cypher and execute it against the Neo4j graph.",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "Natural language question"},
                    "repository_id": {
                        "type": "string",
                        "description": "Optional repository filter",
                    },
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="query_with_rag",
            description="Query the codebase using LlamaIndex RAG for hybrid retrieval (graph + semantic).",
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "Natural language question",
                    },
                    "include_cypher": {
                        "type": "boolean",
                        "description": "Include generated Cypher in response",
                        "default": False,
                    },
                },
                "required": ["question"],
            },
        ),
        Tool(
            name="find_dependencies",
            description="Find dependencies for a given file (includes, imports, variable loads).",
            inputSchema={
                "type": "object",
                "properties": {"file_path": {"type": "string", "description": "Path to the file"}},
                "required": ["file_path"],
            },
        ),
        Tool(
            name="trace_variable",
            description="Trace definition and usage of a specific variable.",
            inputSchema={
                "type": "object",
                "properties": {
                    "variable_name": {"type": "string", "description": "Name of the variable"}
                },
                "required": ["variable_name"],
            },
        ),
        Tool(
            name="get_role_usage",
            description="Find where a specific Ansible role is used.",
            inputSchema={
                "type": "object",
                "properties": {"role_name": {"type": "string", "description": "Name of the role"}},
                "required": ["role_name"],
            },
        ),
        Tool(
            name="analyze_playbook",
            description="Analyze the structure of a playbook (plays, tasks).",
            inputSchema={
                "type": "object",
                "properties": {
                    "playbook_path": {"type": "string", "description": "Path to the playbook"}
                },
                "required": ["playbook_path"],
            },
        ),
        Tool(
            name="find_tasks_by_module",
            description="Find tasks that use a specific Ansible module.",
            inputSchema={
                "type": "object",
                "properties": {
                    "module_name": {
                        "type": "string",
                        "description": "Name of the module (e.g., debug, copy)",
                    }
                },
                "required": ["module_name"],
            },
        ),
        Tool(
            name="get_task_hierarchy",
            description="Get the execution hierarchy of tasks within a playbook.",
            inputSchema={
                "type": "object",
                "properties": {
                    "playbook_path": {"type": "string", "description": "Path to the playbook"}
                },
                "required": ["playbook_path"],
            },
        ),
        Tool(
            name="find_template_usage",
            description="Find where a Jinja2 template is used and what variables it requires.",
            inputSchema={
                "type": "object",
                "properties": {
                    "template_path": {"type": "string", "description": "Path to the template file"}
                },
                "required": ["template_path"],
            },
        ),
    ]


@app.call_tool()  # type: ignore[untyped-decorator]
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    logger.info(f"Tool called: {name} with arguments: {arguments}")

    if name == "set_repository_context":
        from src.mcp.context import set_repository

        set_repository(arguments["repository_id"])
        return [
            TextContent(
                type="text", text=f"Repository context set to: {arguments['repository_id']}"
            )
        ]
    elif name == "query_codebase":
        return await query_codebase(arguments["question"], arguments.get("repository_id"))
    elif name == "query_with_rag":
        return await query_with_rag(arguments["question"], arguments.get("include_cypher", False))
    elif name == "find_dependencies":
        return await find_dependencies(arguments["file_path"])
    elif name == "trace_variable":
        return await trace_variable(arguments["variable_name"])
    elif name == "get_role_usage":
        return await get_role_usage(arguments["role_name"])
    elif name == "analyze_playbook":
        return await analyze_playbook(arguments["playbook_path"])
    elif name == "find_tasks_by_module":
        return await find_tasks_by_module(arguments["module_name"])
    elif name == "get_task_hierarchy":
        return await get_task_hierarchy(arguments["playbook_path"])
    elif name == "find_template_usage":
        return await find_template_usage(arguments["template_path"])
    else:
        logger.error(f"Unknown tool: {name}")
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main() -> None:
    logger.info("Starting GraphRAG MCP Server (STDIO)")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
