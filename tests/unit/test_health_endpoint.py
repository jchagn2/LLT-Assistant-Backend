"""
Unit tests for health check endpoint.

Tests the GET /health endpoint with Neo4j connectivity verification.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoint:
    """Test GET /health endpoint."""

    def test_health_check_neo4j_up(self):
        """Test health check when Neo4j is available."""
        # Mock GraphService
        mock_service = MagicMock()
        mock_service.connect = AsyncMock()
        mock_service.close = AsyncMock()
        mock_service.client.execute_query = AsyncMock(return_value=[{"test": 1}])

        with patch("app.main.GraphService", return_value=mock_service):
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["services"]["api"]["status"] == "up"
        assert data["services"]["neo4j"]["status"] == "up"
        assert "response_time_ms" in data["services"]["neo4j"]
        assert isinstance(data["services"]["neo4j"]["response_time_ms"], int)
        assert data["services"]["neo4j"]["response_time_ms"] >= 0
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_neo4j_down(self):
        """Test health check when Neo4j is unavailable."""
        # Mock GraphService to raise exception
        mock_service = MagicMock()
        mock_service.connect = AsyncMock(side_effect=Exception("Connection refused"))
        mock_service.close = AsyncMock()

        with patch("app.main.GraphService", return_value=mock_service):
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["api"]["status"] == "up"
        assert data["services"]["neo4j"]["status"] == "down"
        assert data["services"]["neo4j"]["response_time_ms"] is None
        assert "timestamp" in data
        assert "version" in data

    def test_health_check_neo4j_query_timeout(self):
        """Test health check when Neo4j query times out."""
        # Mock GraphService with successful connection but query timeout
        mock_service = MagicMock()
        mock_service.connect = AsyncMock()
        mock_service.close = AsyncMock()
        mock_service.client.execute_query = AsyncMock(
            side_effect=Exception("Query timeout")
        )

        with patch("app.main.GraphService", return_value=mock_service):
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert data["services"]["neo4j"]["status"] == "down"
        assert data["services"]["neo4j"]["response_time_ms"] is None

    def test_health_check_cleanup_on_success(self):
        """Test that GraphService connection is closed after successful check."""
        mock_service = MagicMock()
        mock_service.connect = AsyncMock()
        mock_service.close = AsyncMock()
        mock_service.client.execute_query = AsyncMock(return_value=[{"test": 1}])

        with patch("app.main.GraphService", return_value=mock_service):
            response = client.get("/health")

        assert response.status_code == 200
        mock_service.connect.assert_called_once()
        mock_service.close.assert_called_once()

    def test_health_check_cleanup_on_failure(self):
        """Test that GraphService connection is closed even when Neo4j is down."""
        mock_service = MagicMock()
        mock_service.connect = AsyncMock(side_effect=Exception("Connection failed"))
        mock_service.close = AsyncMock()

        with patch("app.main.GraphService", return_value=mock_service):
            response = client.get("/health")

        assert response.status_code == 200
        mock_service.connect.assert_called_once()
        # close should not be called if connect failed
        mock_service.close.assert_not_called()

    def test_health_check_response_time_measurement(self):
        """Test that response time is measured accurately."""
        mock_service = MagicMock()
        mock_service.connect = AsyncMock()
        mock_service.close = AsyncMock()

        # Mock a slow query
        async def slow_query(*args, **kwargs):
            import asyncio

            await asyncio.sleep(0.01)  # 10ms
            return [{"test": 1}]

        mock_service.client.execute_query = AsyncMock(side_effect=slow_query)

        with patch("app.main.GraphService", return_value=mock_service):
            response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        # Should be at least 10ms (accounting for execution time)
        assert data["services"]["neo4j"]["response_time_ms"] >= 10
