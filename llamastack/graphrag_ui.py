"""GraphRAG Search UI using Gradio.

Simple UI that queries the Neo4j graph directly using MCP tools.
"""

import asyncio
import os
import sys
from typing import List

import gradio as gr
from loguru import logger

# Add src to path if running from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mcp.context import clear_repository, set_repository
from src.mcp.tools import query_codebase
from src.mcp.utils.neo4j_connection import get_neo4j_connection

EXAMPLES = [
    # Python codebase queries (graphrag-pipeline)
    "List all classes",
    "Show all async functions",
    "What modules exist?",
    "Find classes that inherit from BaseSettings",
    "List functions with docstrings",
    # Ansible codebase queries (ansible-for-devops)
    "What playbooks exist?",
    "Find tasks using the copy module",
    "What roles are defined?",
    # Cross-repo queries
    "Which repositories use the geerlingguy.docker role?",
]


def get_available_repos() -> List[str]:
    """Fetch indexed repositories from Neo4j."""

    async def _fetch() -> List[str]:
        try:
            manager = get_neo4j_connection()
            result = await manager.execute_query(
                "MATCH (n) WHERE n.repository IS NOT NULL "
                "RETURN DISTINCT n.repository as repo ORDER BY repo"
            )
            return ["All Repositories"] + [r["repo"] for r in result]
        except Exception as e:
            logger.error(f"Failed to fetch repositories: {e}")
            return ["All Repositories"]

    try:
        return asyncio.run(_fetch())
    except Exception:
        return ["All Repositories"]


async def respond(
    message: str, chat_history: List[dict], selected_repo: str
) -> tuple[str, List[dict]]:
    """Handle chat message using MCP tools directly."""

    if not message.strip():
        return "", chat_history

    # Set repository context
    if selected_repo and selected_repo != "All Repositories":
        set_repository(selected_repo)
    else:
        clear_repository()

    # Add user message to history
    chat_history.append({"role": "user", "content": message})

    try:
        # Use query_codebase tool directly
        result = await query_codebase(message)

        # Extract text from result
        if isinstance(result, list):
            bot_message = "\n".join(
                item.text if hasattr(item, "text") else str(item) for item in result
            )
        else:
            bot_message = str(result)

        # Append assistant response
        chat_history.append({"role": "assistant", "content": bot_message})

        return "", chat_history

    except Exception as e:
        logger.exception(f"Error in chat: {e}")
        chat_history.append({"role": "assistant", "content": f"Error: {str(e)}"})
        return "", chat_history


with gr.Blocks(title="GraphRAG Search") as demo:
    gr.Markdown(
        """
# GraphRAG Search
Query your codebase using natural language. Powered by Neo4j.
"""
    )

    with gr.Row():
        repo_dropdown = gr.Dropdown(
            choices=get_available_repos(),
            value="All Repositories",
            label="Repository",
            interactive=True,
        )

    chatbot = gr.Chatbot(label="Chat History", height=400)

    with gr.Row():
        msg = gr.Textbox(
            label="Query",
            placeholder="Ask about your code...",
            scale=4,
            show_label=False,
        )
        submit_btn = gr.Button("Send", variant="primary", scale=1)

    with gr.Accordion("Example Queries", open=True):
        gr.Examples(examples=EXAMPLES, inputs=msg)

    clear = gr.ClearButton([msg, chatbot], value="Clear Chat")

    # Wire up events
    msg.submit(respond, [msg, chatbot, repo_dropdown], [msg, chatbot])
    submit_btn.click(respond, [msg, chatbot, repo_dropdown], [msg, chatbot])


if __name__ == "__main__":
    print("Starting GraphRAG Search UI on http://localhost:11436")
    demo.queue().launch(server_name="0.0.0.0", server_port=11436)
