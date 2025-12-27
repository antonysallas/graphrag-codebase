# Testing

The GraphRAG Pipeline maintains high reliability through a combination of unit, security, and performance tests.

## Testing Strategy

### 1. Parser Tests (`tests/test_parsers.py`)

These verify that Tree-sitter is correctly identifying syntax nodes across different Ansible versions.

- **Fixtures**: We use raw string snippets representing real-world playbooks.
- **Expectations**: Assert that node types (e.g., `Task`) and counts match reality.

### 2. Security Tests (`tests/test_path_sanitization.py`)

Since our tools accept file paths, we must prevent directory traversal attacks.

- Tests verify that paths containing `..` or null bytes are rejected.
- Verifies that paths are resolved correctly relative to the codebase root.

### 3. System Resilience (`tests/test_circuit_breaker.py`)

Tests our custom circuit breaker implementation.

- Mocks failures in LLM or Neo4j.
- Verifies that the circuit opens after the threshold and recovers after the timeout.

## Running Tests

We use `pytest` with the `asyncio` plugin.

```bash
# Run all tests with detailed output
uv run pytest -v

# Run with code coverage report
uv run pytest --cov=src --cov-report=term-missing

# Run a specific test file
uv run pytest tests/test_query_guardrails.py
```

## Mocking the Database

Never connect to a production Neo4j instance during tests. We provide a `mock_neo4j_driver` fixture in most test files to simulate database responses:

```python
from unittest.mock import MagicMock, AsyncMock

async def test_my_tool(mock_neo4j_driver):
    # Setup mock data
    mock_session = mock_neo4j_driver.session.return_value.__aenter__.return_value
    mock_session.run.return_value = AsyncMock()
    
    # Run tool...
```

---

## See Also

- [Contributing Guide](contributing.md)
- [Adding Parsers](adding-parsers.md)
- [Production Readiness Guide](../deployment/production-checklist.md)
