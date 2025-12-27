import os
from pathlib import Path

from loguru import logger


class PathSanitizationError(Exception):
    """Raised when path fails sanitization."""

    pass


def sanitize_path(
    user_path: str, allowed_base: str | None = None, allow_absolute: bool = False
) -> str:
    """
    Sanitize a user-provided file path.

    Args:
        user_path: Path provided by user/agent
        allowed_base: Base directory paths must be within (optional)
        allow_absolute: Whether to allow absolute paths

    Returns:
        Sanitized path string

    Raises:
        PathSanitizationError: If path is invalid or attempts traversal
    """
    if not user_path:
        raise PathSanitizationError("Empty path provided")

    # Reject null bytes
    if "\x00" in user_path:
        raise PathSanitizationError("Null byte in path")

    # Reject obvious traversal attempts
    if ".." in user_path:
        raise PathSanitizationError("Path traversal detected: '..' not allowed")

    # Normalize the path
    normalized = os.path.normpath(user_path)

    # Check for absolute paths
    if os.path.isabs(normalized) and not allow_absolute:
        raise PathSanitizationError("Absolute paths not allowed")

    # If base directory specified, ensure path stays within it
    if allowed_base:
        base = Path(allowed_base).resolve()
        if allow_absolute:
            full_path = Path(normalized).resolve()
        else:
            full_path = (base / normalized).resolve()

        try:
            full_path.relative_to(base)
        except ValueError:
            raise PathSanitizationError(f"Path escapes allowed directory: {allowed_base}")

        return str(full_path)

    return normalized


def validate_file_path_param(file_path: str, codebase_root: str | None = None) -> str:
    """
    Validate file_path parameter for MCP tools.

    Args:
        file_path: User-provided file path
        codebase_root: Root directory of indexed codebase

    Returns:
        Validated, normalized path

    Raises:
        PathSanitizationError: If path is invalid
    """
    logger.debug(f"Validating path: {file_path}")

    # Get codebase root from config if not provided
    if codebase_root is None:
        from src.config import Config

        config = Config()
        codebase_root = config.pipeline.codebase_path

    return sanitize_path(file_path, allowed_base=codebase_root, allow_absolute=False)


def is_safe_path(user_path: str, allowed_base: str | None = None) -> bool:
    """
    Check if path is safe without raising exception.

    Args:
        user_path: Path to check
        allowed_base: Optional base directory

    Returns:
        True if path is safe, False otherwise
    """
    try:
        sanitize_path(user_path, allowed_base=allowed_base)
        return True
    except PathSanitizationError:
        return False
