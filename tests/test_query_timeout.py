import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.mcp.utils.neo4j_connection import (
    Neo4jConnectionManager,
    QueryTimeoutError,
    get_neo4j_connection,
)


# Mock Neo4j driver and session
@pytest.fixture
def mock_neo4j_driver() -> AsyncMock:
    with patch("src.mcp.utils.neo4j_connection.AsyncGraphDatabase.driver") as mock_driver_cls:
        mock_driver = MagicMock()
        mock_session = AsyncMock()

        mock_session_ctx = MagicMock()
        mock_session_ctx.__aenter__.return_value = mock_session
        mock_session_ctx.__aexit__.return_value = None

        mock_driver.session.return_value = mock_session_ctx

        mock_driver.verify_connectivity = AsyncMock()
        mock_driver.close = AsyncMock()

        mock_driver_cls.return_value = mock_driver
        yield mock_driver


@pytest.mark.asyncio
async def test_query_timeout(mock_neo4j_driver: MagicMock) -> None:
    Neo4jConnectionManager._instance = None
    conn = get_neo4j_connection()

    async def slow_run(*args, **kwargs):
        await asyncio.sleep(1)
        return AsyncMock()

    mock_session = mock_neo4j_driver.session.return_value.__aenter__.return_value
    mock_session.run.side_effect = slow_run

    with pytest.raises(QueryTimeoutError):
        await conn.execute_with_timeout("MATCH (n) RETURN n", timeout=0.1)


@pytest.mark.asyncio
async def test_normal_query(mock_neo4j_driver: MagicMock) -> None:
    Neo4jConnectionManager._instance = None
    conn = get_neo4j_connection()

    mock_result = AsyncMock()

    # Create a mock record with .data() method
    mock_record = MagicMock()
    mock_record.data.return_value = {"val": 1}

    mock_result.__aiter__.return_value = [mock_record]

    mock_session = mock_neo4j_driver.session.return_value.__aenter__.return_value
    mock_session.run.return_value = mock_result

    query = "RETURN 1 as val"
    results = await conn.execute_with_timeout(query, timeout=5.0)
    assert len(results) == 1
    assert results[0]["val"] == 1
