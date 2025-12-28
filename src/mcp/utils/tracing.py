"""Tracing utilities using Langfuse."""

from functools import wraps
from typing import TYPE_CHECKING, Any, Callable, Optional, TypeVar

from loguru import logger

from src.config import get_config

if TYPE_CHECKING:
    from langfuse import Langfuse

F = TypeVar("F", bound=Callable[..., Any])

_langfuse_client: Optional["Langfuse"] = None


def get_langfuse() -> Optional["Langfuse"]:
    """Get or initialize Langfuse client if enabled."""
    global _langfuse_client
    config = get_config()

    if not config.langfuse.enabled:
        return None

    if _langfuse_client is None:
        try:
            # Lazy import to avoid compatibility issues
            from langfuse import Langfuse

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

            # Langfuse v3 API: use start_span() for tracing
            span = None
            try:
                span = langfuse.start_span(
                    name=tool_name,
                    input={"args": str(kwargs)},
                    metadata={"tool": tool_name},
                )
            except Exception as e:
                # If tracing fails, just run without it
                logger.debug(f"Langfuse tracing unavailable: {e}")
                return await func(*args, **kwargs)

            try:
                result = await func(*args, **kwargs)

                # Truncate output if too large
                output_str = str(result)
                if len(output_str) > 1000:
                    output_str = output_str[:1000] + "..."

                if span:
                    # Langfuse v3: update() then end()
                    span.update(output={"result": output_str})
                    span.end()

                return result
            except Exception as e:
                if span:
                    span.update(
                        output={"error": str(e)},
                        level="ERROR",
                        status_message=str(e),
                    )
                    span.end()
                logger.exception(f"Error in traced tool {tool_name}: {e}")
                raise
            finally:
                try:
                    langfuse.flush()
                except Exception:
                    pass

        return wrapper  # type: ignore[return-value]

    return decorator
