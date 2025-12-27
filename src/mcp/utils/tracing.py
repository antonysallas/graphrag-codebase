"""Tracing utilities using Langfuse."""

from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from langfuse import Langfuse
from loguru import logger

from src.config import get_config

F = TypeVar("F", bound=Callable[..., Any])

_langfuse_client: Optional[Langfuse] = None


def get_langfuse() -> Optional[Langfuse]:
    """Get or initialize Langfuse client if enabled."""
    global _langfuse_client
    config = get_config()

    if not config.langfuse.enabled:
        return None

    if _langfuse_client is None:
        try:
            _langfuse_client = Langfuse(
                secret_key=config.langfuse.secret_key,
                public_key=config.langfuse.public_key,
                host=config.langfuse.host,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse: {e}")
            return None

    return _langfuse_client


def trace_tool(tool_name: str) -> Callable[[F], F]:
    """Decorator to trace MCP tool invocations.

    Args:
        tool_name: Name of the tool being traced

    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            langfuse = get_langfuse()
            if langfuse is None:
                return await func(*args, **kwargs)

            trace = langfuse.trace(name=tool_name)
            span = trace.span(name=tool_name, metadata={"tool": tool_name, "args": str(kwargs)})
            try:
                result = await func(*args, **kwargs)
                # Truncate output if too large
                output_str = str(result)
                if len(output_str) > 1000:
                    output_str = output_str[:1000] + "..."
                span.update(output=output_str)
                return result
            except Exception as e:
                span.update(level="ERROR", status_message=str(e))
                logger.exception(f"Error in traced tool {tool_name}: {e}")
                raise
            finally:
                span.end()
                langfuse.flush()

        return wrapper  # type: ignore[return-value]

    return decorator
