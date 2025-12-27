"""MCP session context management."""

from contextvars import ContextVar
from typing import Optional

_session_repo: ContextVar[Optional[str]] = ContextVar("mcp_repo", default=None)


def set_repository(repo_id: str) -> None:
    """Set the active repository for this session."""
    _session_repo.set(repo_id)


def get_repository() -> Optional[str]:
    """Get the active repository for this session."""
    return _session_repo.get()


def clear_repository() -> None:
    """Clear the repository context."""
    _session_repo.set(None)
