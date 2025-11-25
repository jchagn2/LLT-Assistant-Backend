"""
Unit tests for GraphService batch operations.

Tests batch symbol creation, relationship management, incremental updates,
and project versioning using mocked Neo4j client.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.graph.graph_service import SYMBOL_BATCH_SIZE, GraphService
from app.models.context import SymbolChange, SymbolInfo


@pytest.fixture
def mock_neo4j_client():
    """Create a mocked Neo4j client."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.close = AsyncMock()
    client.execute_query = AsyncMock()
    client.session = MagicMock()
    return client


@pytest.fixture
async def graph_service(mock_neo4j_client):
    """Create GraphService with mocked client."""
    service = GraphService(neo4j_client=mock_neo4j_client)
    await service.connect()
    return service


class TestBatchCreateSymbols:
    """Test batch symbol creation with UNWIND."""

    @pytest.mark.asyncio
    async def test_batch_create_symbols_success(self, graph_service, mock_neo4j_client):
        """Test successful batch symbol creation."""
        symbols_data = [
            {
                "name": "func1",
                "qualified_name": "module.func1",
                "kind": "function",
                "signature": "() -> None",
                "file_path": "test.py",
                "line_start": 1,
                "line_end": 5,
            },
            {
                "name": "func2",
                "qualified_name": "module.func2",
                "kind": "function",
                "signature": "() -> str",
                "file_path": "test.py",
                "line_start": 7,
                "line_end": 10,
            },
        ]

        # Mock session and result
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value={"created": 2})

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        mock_neo4j_client.session.return_value = mock_session

        # Execute
        created = await graph_service.batch_create_symbols(
            project_id="test-project",
            symbols_data=symbols_data,
        )

        assert created == 2
        mock_session.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_create_symbols_empty_list(self, graph_service):
        """Test batch create with empty list returns 0."""
        created = await graph_service.batch_create_symbols(
            project_id="test-project",
            symbols_data=[],
        )

        assert created == 0

    @pytest.mark.asyncio
    async def test_batch_create_symbols_chunked(self, graph_service, mock_neo4j_client):
        """Test chunked batch creation."""
        # Create more symbols than batch size
        num_symbols = SYMBOL_BATCH_SIZE * 2 + 50
        symbols_data = [
            {
                "name": f"func{i}",
                "qualified_name": f"module.func{i}",
                "kind": "function",
                "signature": "() -> None",
                "file_path": "test.py",
                "line_start": i,
                "line_end": i + 1,
            }
            for i in range(num_symbols)
        ]

        # Mock to return batch size for each chunk
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value={"created": SYMBOL_BATCH_SIZE})

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        mock_neo4j_client.session.return_value = mock_session

        # Execute
        created = await graph_service.batch_create_symbols_chunked(
            project_id="test-project",
            all_symbols=symbols_data,
        )

        # Should create all symbols across multiple batches
        assert created == SYMBOL_BATCH_SIZE * 3  # 3 calls made


class TestCreateCallRelationships:
    """Test batch relationship creation."""

    @pytest.mark.asyncio
    async def test_create_call_relationships_success(
        self, graph_service, mock_neo4j_client
    ):
        """Test successful relationship creation."""
        relationships = [
            {
                "caller_qualified_name": "module.func1",
                "callee_qualified_name": "module.func2",
                "line": 3,
            }
        ]

        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value={"created": 1})

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        mock_neo4j_client.session.return_value = mock_session

        created = await graph_service.create_call_relationships(
            project_id="test-project",
            relationships=relationships,
        )

        assert created == 1

    @pytest.mark.asyncio
    async def test_create_call_relationships_partial_success(
        self, graph_service, mock_neo4j_client, caplog
    ):
        """Test relationship creation with missing targets logs warning."""
        relationships = [
            {
                "caller_qualified_name": "module.func1",
                "callee_qualified_name": "module.missing",
                "line": 3,
            },
            {
                "caller_qualified_name": "module.func1",
                "callee_qualified_name": "module.func2",
                "line": 5,
            },
        ]

        # Only 1 created (missing target skipped)
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value={"created": 1})

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        mock_neo4j_client.session.return_value = mock_session

        created = await graph_service.create_call_relationships(
            project_id="test-project",
            relationships=relationships,
        )

        assert created == 1
        assert "Some relationships not created" in caplog.text


class TestUpdateFileSymbols:
    """Test incremental file symbol updates."""

    @pytest.mark.asyncio
    async def test_update_file_symbols_add(self, graph_service, mock_neo4j_client):
        """Test adding new symbol."""
        changes = [
            SymbolChange(
                action="added",
                name="new_func",
                new_data=SymbolInfo(
                    name="new_func",
                    kind="function",
                    line_start=10,
                    line_end=20,
                ),
            )
        ]

        mock_tx = MagicMock()
        mock_tx.run = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_tx.rollback = AsyncMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin_transaction = AsyncMock(return_value=mock_tx)

        mock_neo4j_client.session.return_value = mock_session

        stats = await graph_service.update_file_symbols(
            project_id="test-project",
            file_path="test.py",
            changes=changes,
        )

        assert stats["added"] == 1
        assert stats["modified"] == 0
        assert stats["deleted"] == 0
        mock_tx.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_file_symbols_delete(self, graph_service, mock_neo4j_client):
        """Test deleting symbol."""
        changes = [
            SymbolChange(
                action="deleted",
                name="old_func",
            )
        ]

        mock_tx = MagicMock()
        mock_tx.run = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_tx.rollback = AsyncMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin_transaction = AsyncMock(return_value=mock_tx)

        mock_neo4j_client.session.return_value = mock_session

        stats = await graph_service.update_file_symbols(
            project_id="test-project",
            file_path="test.py",
            changes=changes,
        )

        assert stats["deleted"] == 1
        mock_tx.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_file_symbols_modified(self, graph_service, mock_neo4j_client):
        """Test modifying existing symbol."""
        changes = [
            SymbolChange(
                action="modified",
                name="existing_func",
                new_data=SymbolInfo(
                    name="existing_func",
                    kind="function",
                    line_start=10,
                    line_end=25,  # Extended
                    signature="(x: int) -> int",  # Updated signature
                ),
            )
        ]

        mock_tx = MagicMock()
        mock_tx.run = AsyncMock()
        mock_tx.commit = AsyncMock()
        mock_tx.rollback = AsyncMock()

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.begin_transaction = AsyncMock(return_value=mock_tx)

        mock_neo4j_client.session.return_value = mock_session

        stats = await graph_service.update_file_symbols(
            project_id="test-project",
            file_path="test.py",
            changes=changes,
        )

        assert stats["modified"] == 1


class TestDeleteFileSymbols:
    """Test file symbol deletion."""

    @pytest.mark.asyncio
    async def test_delete_file_symbols(self, graph_service, mock_neo4j_client):
        """Test deleting all symbols from a file."""
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value={"total": 5})

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        mock_neo4j_client.session.return_value = mock_session

        deleted = await graph_service.delete_file_symbols(
            project_id="test-project",
            file_path="old_file.py",
        )

        assert deleted == 5


class TestProjectStatistics:
    """Test project statistics queries."""

    @pytest.mark.asyncio
    async def test_get_project_statistics(self, graph_service, mock_neo4j_client):
        """Test retrieving project statistics."""
        mock_neo4j_client.execute_query.return_value = [
            {
                "total_files": 10,
                "total_symbols": 50,
                "total_relationships": 75,
            }
        ]

        stats = await graph_service.get_project_statistics("test-project")

        assert stats["total_files"] == 10
        assert stats["total_symbols"] == 50
        assert stats["total_relationships"] == 75

    @pytest.mark.asyncio
    async def test_get_project_statistics_no_data(
        self, graph_service, mock_neo4j_client
    ):
        """Test statistics for non-existent project."""
        mock_neo4j_client.execute_query.return_value = []

        stats = await graph_service.get_project_statistics("nonexistent")

        assert stats["total_files"] == 0
        assert stats["total_symbols"] == 0
        assert stats["total_relationships"] == 0


class TestProjectExists:
    """Test project existence check."""

    @pytest.mark.asyncio
    async def test_check_project_exists_true(self, graph_service, mock_neo4j_client):
        """Test project exists returns True."""
        mock_neo4j_client.execute_query.return_value = [{"exists": True}]

        exists = await graph_service.check_project_exists("test-project")

        assert exists is True

    @pytest.mark.asyncio
    async def test_check_project_exists_false(self, graph_service, mock_neo4j_client):
        """Test project doesn't exist returns False."""
        mock_neo4j_client.execute_query.return_value = [{"exists": False}]

        exists = await graph_service.check_project_exists("nonexistent")

        assert exists is False


class TestProjectVersioning:
    """Test project versioning for optimistic locking."""

    @pytest.mark.asyncio
    async def test_get_project_version(self, graph_service, mock_neo4j_client):
        """Test getting project version."""
        mock_neo4j_client.execute_query.return_value = [{"version": 5}]

        version = await graph_service.get_project_version("test-project")

        assert version == 5

    @pytest.mark.asyncio
    async def test_get_project_version_not_found(
        self, graph_service, mock_neo4j_client
    ):
        """Test getting version for non-existent project returns 0."""
        mock_neo4j_client.execute_query.return_value = []

        version = await graph_service.get_project_version("nonexistent")

        assert version == 0

    @pytest.mark.asyncio
    async def test_increment_project_version_new(
        self, graph_service, mock_neo4j_client
    ):
        """Test incrementing version for new project."""
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value={"version": 1})

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        mock_neo4j_client.session.return_value = mock_session

        version = await graph_service.increment_project_version("new-project")

        assert version == 1

    @pytest.mark.asyncio
    async def test_increment_project_version_existing(
        self, graph_service, mock_neo4j_client
    ):
        """Test incrementing version for existing project."""
        mock_result = MagicMock()
        mock_result.single = AsyncMock(return_value={"version": 6})

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session.run = AsyncMock(return_value=mock_result)

        mock_neo4j_client.session.return_value = mock_session

        version = await graph_service.increment_project_version("test-project")

        assert version == 6
