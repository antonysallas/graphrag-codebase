from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict


@dataclass
class RateLimiter:
    """Token bucket rate limiter."""

    requests_per_minute: int = 100
    burst_size: int = 10

    _buckets: Dict[str, float] = field(
        default_factory=lambda: defaultdict(float), init=False, repr=False
    )
    _last_update: Dict[str, datetime] = field(default_factory=dict, init=False, repr=False)

    def _refill(self, client_id: str) -> float:
        """Refill tokens based on elapsed time."""
        now = datetime.now()

        if client_id not in self._last_update:
            self._buckets[client_id] = float(self.burst_size)
            self._last_update[client_id] = now
            return float(self.burst_size)

        last = self._last_update[client_id]
        elapsed = (now - last).total_seconds()

        # Add tokens based on elapsed time
        refill_rate = self.requests_per_minute / 60.0
        tokens = self._buckets[client_id] + (elapsed * refill_rate)
        tokens = min(tokens, self.burst_size)  # Cap at burst size

        self._buckets[client_id] = tokens
        self._last_update[client_id] = now

        return tokens

    def allow(self, client_id: str = "default") -> bool:
        """Check if request is allowed and consume a token."""
        tokens = self._refill(client_id)
        if tokens >= 1:
            self._buckets[client_id] = tokens - 1
            return True
        return False

    def get_retry_after(self, client_id: str = "default") -> float:
        """Get seconds until next token available."""
        tokens = self._buckets.get(client_id, 0)
        if tokens >= 1:
            return 0
        refill_rate = self.requests_per_minute / 60.0
        return (1 - tokens) / refill_rate

    def get_remaining(self, client_id: str = "default") -> int:
        """Get remaining tokens for client."""
        self._refill(client_id)
        return int(self._buckets.get(client_id, self.burst_size))


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: float):
        super().__init__(f"Rate limit exceeded. Retry after {retry_after:.1f}s")
        self.retry_after = retry_after


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=100, burst_size=10)
