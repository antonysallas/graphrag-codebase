#!/usr/bin/env python3
"""Create GraphRAG agent using LlamaStack Python SDK.

This script creates an agent with MCP tools for querying the codebase.
"""

import asyncio
import os
import sys

from llama_stack_client import LlamaStackClient
from llama_stack_client.lib.agents.agent import Agent
from llama_stack_client.lib.agents.event_logger import EventLogger

LLAMASTACK_URL = os.getenv("LLAMASTACK_URL", "http://localhost:8321")
MODEL_ID = os.getenv("LLAMASTACK_MODEL", "litellm-maas/Mistral-Small-24B-W8A8")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:5003/sse")

GRAPHRAG_INSTRUCTIONS = """You are an expert at analyzing Ansible and Python codebases.
Use the GraphRAG tools to answer questions about:
- Playbooks, roles, tasks, and handlers
- Variables and their definitions/usage
- Dependencies between files and resources
- Code structure and relationships

Always use the appropriate tool for the query type:
- query_codebase: Natural language questions about the codebase
- find_dependencies: Trace file dependencies
- trace_variable: Find variable definitions and usage
- get_role_usage: Find where roles are used
- find_tasks_by_module: Find tasks using specific modules

When answering questions:
1. First determine which tool is most appropriate
2. Call the tool with the correct parameters
3. Interpret the results and provide a clear answer
4. If the query is ambiguous, ask for clarification"""


def get_available_models(client: LlamaStackClient) -> list[str]:
    """Get list of available model IDs."""
    try:
        models = client.models.list()
        return [m.id for m in models.data] if hasattr(models, "data") else [m.id for m in models]
    except Exception as e:
        print(f"Warning: Could not list models: {e}")
        return []


async def create_graphrag_agent() -> None:
    """Create and test the GraphRAG agent."""
    print("=" * 60)
    print("Creating GraphRAG Agent")
    print("=" * 60)

    # Initialize client
    client = LlamaStackClient(base_url=LLAMASTACK_URL)
    print(f"✓ Connected to LlamaStack at {LLAMASTACK_URL}")

    # List available models
    models = get_available_models(client)
    if models:
        print(f"✓ Available models: {', '.join(models)}")
        # Use first available model if configured one doesn't exist
        if MODEL_ID not in models and models:
            model_to_use = models[0]
            print(f"  Using: {model_to_use} (configured model not found)")
        else:
            model_to_use = MODEL_ID
    else:
        model_to_use = MODEL_ID
        print(f"  Using configured model: {model_to_use}")

    # Create agent with MCP tools
    print("\nCreating agent with MCP tools...")
    agent = Agent(
        client,
        model=model_to_use,
        instructions=GRAPHRAG_INSTRUCTIONS,
        tools=[
            {
                "type": "mcp",
                "server_label": "graphrag",
                "server_url": MCP_SERVER_URL,
                "require_approval": "never",
            }
        ],
    )
    print(f"✓ Agent created with model: {model_to_use}")
    print(f"  MCP Server: {MCP_SERVER_URL}")

    # Create a session
    session_id = agent.create_session(session_name="graphrag-session")
    print(f"✓ Session created: {session_id}")

    # Test the agent with a simple query
    print("\n" + "-" * 60)
    print("Testing agent with query: 'What tools do you have available?'")
    print("-" * 60)

    try:
        response = agent.create_turn(
            messages=[
                {"role": "user", "content": "What tools do you have available? List them briefly."}
            ],
            session_id=session_id,
        )

        # Process response - handle both old and new API formats
        for event in EventLogger().log(response):
            if hasattr(event, "print"):
                event.print()
            else:
                print(event)

    except Exception as e:
        print(f"Error during test query: {e}")
        print("The agent was created but the test query failed.")
        print("This may be due to MCP server connectivity issues.")

    print("\n" + "=" * 60)
    print("Agent Setup Complete!")
    print("=" * 60)
    print(f"""
You can now use the agent programmatically:

    from llama_stack_client import LlamaStackClient
    from llama_stack_client.lib.agents.agent import Agent

    client = LlamaStackClient(base_url="{LLAMASTACK_URL}")
    agent = Agent(
        client,
        model="{model_to_use}",
        instructions="Your instructions here",
        tools=[{{"type": "mcp", "server_label": "graphrag", "server_url": "{MCP_SERVER_URL}"}}],
    )
    session_id = agent.create_session(session_name="my-session")
    response = agent.create_turn(
        messages=[{{"role": "user", "content": "Your question here"}}],
        session_id=session_id,
    )
""")


async def interactive_chat() -> None:
    """Run an interactive chat session with the GraphRAG agent."""
    print("=" * 60)
    print("GraphRAG Interactive Chat")
    print("=" * 60)
    print("Type 'quit' or 'exit' to end the session.\n")

    client = LlamaStackClient(base_url=LLAMASTACK_URL)

    # Get available models
    models = get_available_models(client)
    model_to_use = models[0] if models else MODEL_ID

    # Create agent
    agent = Agent(
        client,
        model=model_to_use,
        instructions=GRAPHRAG_INSTRUCTIONS,
        tools=[
            {
                "type": "mcp",
                "server_label": "graphrag",
                "server_url": MCP_SERVER_URL,
                "require_approval": "never",
            }
        ],
    )

    session_id = agent.create_session(session_name="interactive-chat")
    print(f"Session: {session_id}")
    print(f"Model: {model_to_use}")
    print("-" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit"):
                print("Goodbye!")
                break

            print("\nAssistant: ", end="", flush=True)
            response = agent.create_turn(
                messages=[{"role": "user", "content": user_input}],
                session_id=session_id,
            )

            for event in EventLogger().log(response):
                if hasattr(event, "print"):
                    event.print()
                else:
                    print(event)

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")


def list_conversations() -> None:
    """List all stored conversations."""
    print("=" * 60)
    print("Stored Conversations")
    print("=" * 60)

    # Query the SQLite database directly (no list API in v0.4.0)
    import sqlite3
    db_path = os.path.expanduser("~/workarea/projects/personal/llama-stack/sql_store.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, created_at FROM openai_conversations ORDER BY created_at DESC")
        rows = cursor.fetchall()
        print(f"Total conversations: {len(rows)}")
        for row in rows:
            print(f"  - {row[0]} (created: {row[1]})")
        conn.close()
    except Exception as e:
        print(f"Could not read conversations: {e}")


def cleanup_conversations() -> None:
    """Delete all stored conversations."""
    import sqlite3
    db_path = os.path.expanduser("~/workarea/projects/personal/llama-stack/sql_store.db")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get count before
        cursor.execute("SELECT COUNT(*) FROM openai_conversations")
        count = cursor.fetchone()[0]

        # Delete all
        cursor.execute("DELETE FROM conversation_items")
        cursor.execute("DELETE FROM conversation_messages")
        cursor.execute("DELETE FROM openai_conversations")
        conn.commit()
        conn.close()

        print(f"✓ Deleted {count} conversations")
    except Exception as e:
        print(f"Could not cleanup conversations: {e}")


def main() -> int:
    """Main entry point."""
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "chat":
            asyncio.run(interactive_chat())
        elif cmd == "list":
            list_conversations()
        elif cmd == "cleanup":
            cleanup_conversations()
        else:
            print(f"Unknown command: {cmd}")
            print("Usage: create_agent.py [chat|list|cleanup]")
            return 1
    else:
        asyncio.run(create_graphrag_agent())
    return 0


if __name__ == "__main__":
    sys.exit(main())
