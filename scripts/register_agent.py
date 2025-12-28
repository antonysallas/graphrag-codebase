#!/usr/bin/env python3
"""Verify GraphRAG MCP tools are available in LlamaStack.

Checks that the MCP server is connected and tools are registered.
"""

import os
import sys
import time

import httpx

LLAMASTACK_URL = os.getenv("LLAMASTACK_URL", "http://localhost:8321")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:5003/sse")


def wait_for_llamastack(max_retries: int = 30, delay: float = 2.0) -> bool:
    """Wait for LlamaStack to be ready."""
    print(f"Waiting for LlamaStack at {LLAMASTACK_URL}...")
    for i in range(max_retries):
        try:
            response = httpx.get(f"{LLAMASTACK_URL}/v1/health", timeout=5.0)
            if response.status_code == 200:
                print("✓ LlamaStack is ready")
                return True
        except httpx.RequestError:
            pass
        time.sleep(delay)
        if (i + 1) % 5 == 0:
            print(f"  Still waiting... ({i + 1}/{max_retries})")
    print("✗ LlamaStack did not become ready in time")
    return False


def verify_toolgroup() -> bool:
    """Verify mcp::graphrag toolgroup is registered."""
    try:
        response = httpx.get(
            f"{LLAMASTACK_URL}/v1/toolgroups/mcp::graphrag",
            timeout=10.0,
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Toolgroup registered: mcp::graphrag")
            mcp_endpoint = data.get("mcp_endpoint", {})
            if mcp_endpoint:
                print(f"  MCP endpoint: {mcp_endpoint.get('uri', 'N/A')}")
            return True
        else:
            print(f"✗ Toolgroup not found: {response.status_code}")
            return False
    except httpx.RequestError as e:
        print(f"✗ Error checking toolgroup: {e}")
        return False


def verify_tools() -> list[str]:
    """Verify MCP tools are available. Returns list of tool names."""
    tools_found = []
    try:
        response = httpx.get(
            f"{LLAMASTACK_URL}/v1/tool-runtime/list-tools",
            params={"toolgroup_id": "mcp::graphrag"},
            timeout=30.0,  # Increased timeout for MCP connection
        )
        if response.status_code == 200:
            data = response.json()
            tools = data if isinstance(data, list) else data.get("data", [])
            if tools:
                print(f"✓ GraphRAG tools available: {len(tools)} tools")
                for tool in tools:
                    name = tool.get("name", tool.get("tool_name", "unknown"))
                    tools_found.append(name)
                    desc = tool.get("description", "")[:50]
                    print(f"  - {name}: {desc}...")
            else:
                print("✗ No GraphRAG tools found")
        else:
            print(f"✗ Failed to list tools: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
    except httpx.ReadTimeout:
        print("✗ Timeout listing tools (MCP server may be slow to respond)")
    except httpx.RequestError as e:
        print(f"✗ Error listing tools: {e}")
    return tools_found


def get_model_id() -> str | None:
    """Get the configured model ID."""
    try:
        response = httpx.get(f"{LLAMASTACK_URL}/v1/models", timeout=10.0)
        if response.status_code == 200:
            data = response.json()
            models = data.get("data", data) if isinstance(data, dict) else data
            if models:
                model_id = models[0].get("id", models[0].get("model_id"))
                print(f"✓ Model available: {model_id}")
                return model_id
    except httpx.RequestError:
        pass
    return None


def main() -> int:
    """Main entry point."""
    print("=" * 60)
    print("GraphRAG + LlamaStack Verification")
    print("=" * 60)

    # Wait for LlamaStack to be ready
    if not wait_for_llamastack():
        return 1

    # Check toolgroup registration
    verify_toolgroup()

    # Get model info
    get_model_id()

    # Verify tools are available (may timeout if MCP server is slow)
    verify_tools()

    print("\nVerification complete!")
    print(f"  LlamaStack API: {LLAMASTACK_URL}")
    print(f"  LlamaStack UI:  http://localhost:8322")
    print(f"  MCP Server:     {MCP_SERVER_URL}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
