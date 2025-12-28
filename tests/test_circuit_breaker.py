import time

import pytest

from src.mcp.utils import CircuitBreaker, CircuitOpenError, CircuitState, with_circuit_breaker


def test_circuit_opens_after_threshold():
    breaker = CircuitBreaker(name="test", failure_threshold=3)

    # First 2 failures - state remains CLOSED
    breaker.record_failure()
    breaker.record_failure()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request()

    # 3rd failure - state becomes OPEN
    breaker.record_failure()
    assert breaker.state == CircuitState.OPEN
    assert not breaker.allow_request()


def test_circuit_recovers():
    # Use very short timeout for testing
    breaker = CircuitBreaker(name="test_recovery", failure_threshold=3, recovery_timeout=0.1)

    # Open the circuit
    for _ in range(3):
        breaker.record_failure()

    assert breaker.state == CircuitState.OPEN
    assert not breaker.allow_request()

    # Wait for recovery timeout
    time.sleep(0.2)

    # Should transition to HALF_OPEN
    assert breaker.state == CircuitState.HALF_OPEN
    assert breaker.allow_request()

    # Record success - should close
    breaker.record_success()
    assert breaker.state == CircuitState.CLOSED
    assert breaker.allow_request()


@pytest.mark.asyncio
async def test_decorator_opens_circuit():
    breaker = CircuitBreaker(name="test_decorator", failure_threshold=2)

    @with_circuit_breaker(breaker)
    async def failing_func():
        raise ValueError("Fail")

    # 1st fail
    with pytest.raises(ValueError):
        await failing_func()
    assert breaker.state == CircuitState.CLOSED

    # 2nd fail
    with pytest.raises(ValueError):
        await failing_func()
    assert breaker.state == CircuitState.OPEN

    # Next call should raise CircuitOpenError
    with pytest.raises(CircuitOpenError) as excinfo:
        await failing_func()

    assert "Circuit 'test_decorator' is open" in str(excinfo.value)
    assert excinfo.value.circuit_name == "test_decorator"


@pytest.mark.asyncio
async def test_decorator_suggests_tools():
    breaker = CircuitBreaker(name="test_suggestions", failure_threshold=1)
    suggested = ["tool1", "tool2"]

    @with_circuit_breaker(breaker, suggested_tools=suggested)
    async def failing_func():
        raise ValueError("Fail")

    # Open it
    with pytest.raises(ValueError):
        await failing_func()

    # Check error message
    with pytest.raises(CircuitOpenError) as excinfo:
        await failing_func()

    msg = excinfo.value.format_message()
    assert "tool1" in msg
    assert "tool2" in msg
    assert "Service temporarily unavailable" in msg
