import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger
from neo4j import AsyncDriver, AsyncGraphDatabase
from neo4j.exceptions import ServiceUnavailable

from src.config import get_config
from src.mcp.utils.circuit_breaker import neo4j_query_breaker, with_circuit_breaker
from src.mcp.utils.tracing import get_langfuse


class QueryTimeoutError(Exception):
    """Raised when query exceeds time limit."""

    pass


class Neo4jUnavailableError(Exception):
    """Raised when Neo4j is unreachable."""

    pass


TIMEOUT_ERROR_MSG = """⏱️ Query timeout: The query exceeded the limit.

Suggestions:
- Try a more specific query
- Use deterministic tools like find_dependencies or trace_variable
- Add filters to reduce result set size"""


class Neo4jConnectionManager:
    _instance: Optional["Neo4jConnectionManager"] = None

    def __init__(self) -> None:
        config = get_config()
        self.uri = config.neo4j.uri
        self.auth = (config.neo4j.user, config.neo4j.password)
        self.database = config.neo4j.database
        self.default_timeout = config.neo4j.query_timeout
        self.connection_timeout = config.neo4j.connection_timeout
        self._driver: Optional[AsyncDriver] = None
        self._loop_id: Optional[int] = None

    def _get_driver(self) -> AsyncDriver:
        """Get or create driver for current event loop."""
        try:
            current_loop = asyncio.get_running_loop()
            current_loop_id = id(current_loop)
        except RuntimeError:
            current_loop_id = None

        # Recreate driver if loop changed
        if self._driver is None or self._loop_id != current_loop_id:
            # Don't try to close old driver - its event loop may be closed
            # Just abandon it and let garbage collection handle cleanup
            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=self.auth,
                max_connection_lifetime=300,
                max_connection_pool_size=50,
                connection_acquisition_timeout=self.connection_timeout,
            )
            self._loop_id = current_loop_id

        return self._driver

    @property
    def driver(self) -> AsyncDriver:
        """Property to get driver for current event loop."""
        return self._get_driver()

    @classmethod
    def get_instance(cls) -> "Neo4jConnectionManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def verify_connection(self) -> bool:
        try:
            await self.driver.verify_connectivity()
            return True
        except Exception as e:
            logger.error(f"Neo4j connection failed: {e}")
            return False

    @with_circuit_breaker(neo4j_query_breaker)
    async def execute_with_timeout(
        self, query: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """Execute Cypher query with timeout protection."""
        if timeout is None:
            timeout = self.default_timeout

        langfuse = get_langfuse()
        trace = None
        span = None
        if langfuse:
            trace = langfuse.trace(name="neo4j_query")
            span = trace.span(
                name="neo4j_query",
                input={"query": query, "params": params},
                metadata={"timeout": timeout},
            )

        try:
            async with asyncio.timeout(timeout):
                async with self.driver.session(database=self.database) as session:
                    result = await session.run(query, params or {})
                    data = [record.data() async for record in result]
                    if span:
                        span.update(output={"result_count": len(data)})
                        span.end()
                    return data
        except asyncio.TimeoutError:
            logger.warning(f"Query timed out after {timeout}s: {query[:100]}...")
            if span:
                span.update(level="ERROR", status_message=f"Timeout after {timeout}s")
                span.end()
            raise QueryTimeoutError(f"Query exceeded {timeout}s limit")
        except ServiceUnavailable as e:
            logger.error(f"Neo4j unavailable: {e}")
            if span:
                span.update(level="ERROR", status_message=f"Neo4j unavailable: {str(e)}")
                span.end()
            raise Neo4jUnavailableError(str(e))
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            if span:
                span.update(level="ERROR", status_message=str(e))
                span.end()
            raise

    async def execute_query(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute query using default timeout."""
        return await self.execute_with_timeout(query, params)

    async def execute_write(
        self, query: str, params: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Execute write query using default timeout."""
        return await self.execute_with_timeout(query, params)

    async def close(self) -> None:
        await self.driver.close()


def get_neo4j_connection() -> Neo4jConnectionManager:
    return Neo4jConnectionManager.get_instance()
