"""
Unit tests for Neo4j client.

Tests connection management, query execution, error handling, and resource cleanup.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.graph.neo4j_client import (
    Neo4jClient,
    Neo4jClientError,
    Neo4jConnectionError,
    Neo4jQueryError,
)


@pytest.fixture
def mock_driver():
    """Create mock Neo4j driver."""
    driver = AsyncMock()
    driver.verify_connectivity = AsyncMock()
    driver.close = AsyncMock()
    return driver


@pytest.mark.asyncio
async def test_neo4j_client_connect_success(mock_driver):
    """Verify that client successfully connects to Neo4j."""
    with patch("app.core.graph.neo4j_client.AsyncGraphDatabase.driver") as mock_create:
        mock_create.return_value = mock_driver

        client = Neo4jClient(
            uri="bolt://localhost:7687",
            user="neo4j",
            password="test",
        )

        await client.connect()

        assert client._connected is True
        mock_driver.verify_connectivity.assert_called_once()


@pytest.mark.asyncio
async def test_neo4j_client_execute_query_success(mock_driver):
    """Verify that client executes queries successfully."""
    mock_session = AsyncMock()
    mock_result = AsyncMock()
    mock_result.data = AsyncMock(return_value=[{"n": {"name": "test"}}])
    mock_session.run = AsyncMock(return_value=mock_result)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    mock_driver.session = MagicMock(return_value=mock_session)

    with patch("app.core.graph.neo4j_client.AsyncGraphDatabase.driver") as mock_create:
        mock_create.return_value = mock_driver

        client = Neo4jClient()
        await client.connect()

        result = await client.execute_query("MATCH (n) RETURN n LIMIT 1")

        assert len(result) == 1
        assert result[0]["n"]["name"] == "test"


@pytest.mark.asyncio
async def test_neo4j_client_not_connected_error():
    """Verify that executing query without connection raises error."""
    client = Neo4jClient()

    with pytest.raises(Neo4jConnectionError, match="Not connected"):
        await client.execute_query("RETURN 1")


@pytest.mark.asyncio
async def test_neo4j_client_close(mock_driver):
    """Verify that client properly closes connection."""
    with patch("app.core.graph.neo4j_client.AsyncGraphDatabase.driver") as mock_create:
        mock_create.return_value = mock_driver

        client = Neo4jClient()
        await client.connect()
        await client.close()

        assert client._connected is False
        mock_driver.close.assert_called_once()


@pytest.mark.asyncio
async def test_neo4j_client_context_manager(mock_driver):
    """Verify that client works as async context manager."""
    with patch("app.core.graph.neo4j_client.AsyncGraphDatabase.driver") as mock_create:
        mock_create.return_value = mock_driver

        async with Neo4jClient() as client:
            assert client._connected is True

        mock_driver.close.assert_called_once()
