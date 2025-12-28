import time

from src.mcp.utils import RateLimiter


def test_allows_under_limit():
    limiter = RateLimiter(requests_per_minute=10, burst_size=5)

    for _ in range(5):
        assert limiter.allow("test")


def test_blocks_over_limit():
    limiter = RateLimiter(requests_per_minute=10, burst_size=5)

    for _ in range(5):
        limiter.allow("test")

    assert not limiter.allow("test")


def test_refills_over_time():
    limiter = RateLimiter(requests_per_minute=600, burst_size=5)  # 10/sec

    for _ in range(5):
        limiter.allow("test")

    time.sleep(0.2)  # Wait for 2 tokens to refill

    assert limiter.allow("test")
