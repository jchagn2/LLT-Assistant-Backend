"""Neo4j database client with connection pooling and error handling."""

import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver, AsyncGraphDatabase, AsyncSession
from neo4j.exceptions import (
    AuthError,
    DriverError,
    ServiceUnavailable,
)

from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jClientError(Exception):
    """Base exception for Neo4j client errors."""

    pass


class Neo4jConnectionError(Neo4jClientError):
    """Raised when connection to Neo4j fails."""

    pass


class Neo4jQueryError(Neo4jClientError):
    """Raised when query execution fails."""

    pass


class Neo4jClient:
    """
    Async Neo4j client with connection pooling.

    This class provides a singleton-like interface for managing
    Neo4j connections with proper resource cleanup and error handling.

    Usage:
        client = Neo4jClient()
        await client.connect()

        result = await client.execute_query(
            "MATCH (n:Symbol) RETURN n LIMIT 10"
        )

        await client.close()
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (defaults to settings)
            user: Username (defaults to settings)
            password: Password (defaults to settings)
            database: Database name (defaults to settings)
        """
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database

        self._driver: Optional[AsyncDriver] = None
        self._connected = False

        logger.info(
            "Neo4j client initialized: uri=%s, database=%s",
            self.uri,
            self.database,
        )

    async def connect(self) -> None:
        """
        Establish connection to Neo4j database.

        Raises:
            Neo4jConnectionError: If connection fails
        """
        if self._connected:
            logger.debug("Neo4j client already connected")
            return

        try:
            logger.info("Connecting to Neo4j database...")

            self._driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                max_connection_lifetime=settings.neo4j_max_connection_lifetime,
                max_connection_pool_size=settings.neo4j_max_connection_pool_size,
                connection_acquisition_timeout=settings.neo4j_connection_acquisition_timeout,
            )

            # Verify connectivity
            await self._driver.verify_connectivity()

            self._connected = True
            logger.info("Successfully connected to Neo4j database")

        except AuthError as e:
            logger.error("Neo4j authentication failed: %s", str(e))
            raise Neo4jConnectionError(f"Authentication failed: {e}") from e
        except ServiceUnavailable as e:
            logger.error("Neo4j service unavailable: %s", str(e))
            raise Neo4jConnectionError(f"Service unavailable: {e}") from e
        except Exception as e:
            logger.error("Unexpected Neo4j connection error: %s", str(e))
            raise Neo4jConnectionError(f"Connection failed: {e}") from e

    async def execute_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters
            database: Database name (defaults to configured database)

        Returns:
            List of result records as dictionaries

        Raises:
            Neo4jQueryError: If query execution fails
            Neo4jConnectionError: If not connected
        """
        if not self._connected or self._driver is None:
            raise Neo4jConnectionError("Not connected to Neo4j. Call connect() first.")

        parameters = parameters or {}
        database = database or self.database

        logger.debug(
            "Executing Neo4j query: query_length=%d, params=%s",
            len(query),
            list(parameters.keys()) if parameters else [],
        )

        try:
            async with self._driver.session(database=database) as session:
                result = await session.run(query, parameters)
                records = await result.data()

                logger.debug("Query executed successfully: records=%d", len(records))
                return records

        except DriverError as e:
            logger.error("Neo4j query execution failed: %s", str(e))
            raise Neo4jQueryError(f"Query failed: {e}") from e
        except Exception as e:
            logger.error("Unexpected query error: %s", str(e))
            raise Neo4jQueryError(f"Unexpected error: {e}") from e

    @asynccontextmanager
    async def session(self, database: Optional[str] = None):
        """
        Get a Neo4j session as async context manager.

        Args:
            database: Database name (defaults to configured database)

        Yields:
            AsyncSession instance

        Example:
            async with client.session() as session:
                await session.run("CREATE (n:Test)")
        """
        if not self._connected or self._driver is None:
            raise Neo4jConnectionError("Not connected to Neo4j")

        database = database or self.database

        async with self._driver.session(database=database) as session:
            yield session

    async def execute_write_transaction(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a write query within a transaction.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records
        """
        async with self.session() as session:
            result = await session.run(query, parameters or {})
            return await result.data()

    async def close(self) -> None:
        """Close Neo4j driver and cleanup connections."""
        if self._driver is not None:
            logger.info("Closing Neo4j driver...")
            await self._driver.close()
            self._driver = None
            self._connected = False
            logger.info("Neo4j driver closed")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


def create_neo4j_client() -> Neo4jClient:
    """
    Create a Neo4j client using settings.

    Returns:
        Configured Neo4jClient instance
    """
    return Neo4jClient(
        uri=settings.neo4j_uri,
        user=settings.neo4j_user,
        password=settings.neo4j_password,
        database=settings.neo4j_database,
    )
