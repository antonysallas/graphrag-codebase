from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Callable, List, Optional, TypeVar

from loguru import logger

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if recovered


@dataclass
class CircuitBreaker:
    """Circuit breaker for external service calls."""

    name: str = "default"
    failure_threshold: int = 3
    recovery_timeout: float = 30.0  # seconds

    _failure_count: int = field(default=0, init=False, repr=False)
    _last_failure_time: Optional[datetime] = field(default=None, init=False, repr=False)
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False, repr=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._last_failure_time:
                elapsed = (datetime.now() - self._last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    logger.info(f"Circuit '{self.name}' transitioning to HALF_OPEN")
                    self._state = CircuitState.HALF_OPEN
        return self._state

    def record_success(self) -> None:
        """Record a successful call."""
        if self._state != CircuitState.CLOSED:
            logger.info(f"Circuit '{self.name}' closing after success")
        self._failure_count = 0
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = datetime.now()

        if self._failure_count >= self.failure_threshold:
            if self._state != CircuitState.OPEN:
                logger.warning(f"Circuit '{self.name}' OPEN after {self._failure_count} failures")
            self._state = CircuitState.OPEN

    def allow_request(self) -> bool:
        """Check if request should be allowed."""
        state = self.state
        if state == CircuitState.CLOSED:
            return True
        if state == CircuitState.HALF_OPEN:
            return True  # Allow one test request
        return False

    def get_status(self) -> dict[str, Any]:
        """Get circuit status for health checks."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "threshold": self.failure_threshold,
        }


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""

    def __init__(self, message: str, circuit_name: str, suggested_tools: List[str] | None = None):
        super().__init__(message)
        self.circuit_name = circuit_name
        self.suggested_tools = suggested_tools or []

    def format_message(self) -> str:
        """Format user-friendly error message."""
        lines = [
            f"⚡ Service temporarily unavailable: {self.circuit_name}",
            "",
            "The service is experiencing issues. Please try again in 30 seconds.",
        ]

        if self.suggested_tools:
            lines.append("")
            lines.append("In the meantime, try these deterministic tools:")
            for tool in self.suggested_tools:
                lines.append(f"  • {tool}")

        return "\n".join(lines)


F = TypeVar("F", bound=Callable[..., Any])


def with_circuit_breaker(
    breaker: CircuitBreaker, suggested_tools: List[str] | None = None
) -> Callable[[F], F]:
    """Decorator to apply circuit breaker to async functions."""

    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if not breaker.allow_request():
                raise CircuitOpenError(
                    f"Circuit '{breaker.name}' is open",
                    circuit_name=breaker.name,
                    suggested_tools=suggested_tools,
                )
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception:
                breaker.record_failure()
                raise

        return wrapper  # type: ignore[return-value]

    return decorator


# Global circuit breakers
cypher_generation_breaker = CircuitBreaker(
    name="cypher_generation", failure_threshold=3, recovery_timeout=30
)

neo4j_query_breaker = CircuitBreaker(name="neo4j_query", failure_threshold=5, recovery_timeout=60)
