"""
Unit tests for Context Management Pydantic models.

Tests validation rules, custom validators, and model serialization.
"""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models.context import (
    FileChange,
    FileSymbols,
    IncrementalUpdateRequest,
    IncrementalUpdateResponse,
    InitializeProjectRequest,
    InitializeProjectResponse,
    ProjectStatusResponse,
    SymbolChange,
    SymbolInfo,
)


class TestSymbolInfo:
    """Test SymbolInfo validation."""

    def test_valid_symbol_info(self):
        """Test that valid symbol info passes validation."""
        symbol = SymbolInfo(
            name="calculate_tax",
            kind="function",
            signature="(price: float) -> float",
            line_start=10,
            line_end=20,
            calls=["get_tax_rate"],
        )

        assert symbol.name == "calculate_tax"
        assert symbol.kind == "function"
        assert symbol.line_start == 10
        assert symbol.line_end == 20
        assert symbol.calls == ["get_tax_rate"]

    def test_symbol_info_minimal_fields(self):
        """Test symbol info with only required fields."""
        symbol = SymbolInfo(
            name="foo",
            kind="method",
            line_start=5,
            line_end=10,
        )

        assert symbol.name == "foo"
        assert symbol.signature is None
        assert symbol.calls == []

    def test_invalid_kind_rejected(self):
        """Test that invalid kind value is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SymbolInfo(
                name="test",
                kind="invalid_kind",  # Not function/class/method
                line_start=1,
                line_end=2,
            )

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert "kind" in str(errors[0])

    def test_empty_name_rejected(self):
        """Test that empty name is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SymbolInfo(
                name="",  # Empty name
                kind="function",
                line_start=1,
                line_end=2,
            )

        errors = exc_info.value.errors()
        assert any("name" in str(e) for e in errors)

    def test_name_too_long_rejected(self):
        """Test that name exceeding max length is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SymbolInfo(
                name="x" * 201,  # Exceeds max_length=200
                kind="function",
                line_start=1,
                line_end=2,
            )

        errors = exc_info.value.errors()
        assert any("name" in str(e) for e in errors)

    def test_line_end_before_start_rejected(self):
        """Test that line_end < line_start is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SymbolInfo(
                name="test",
                kind="function",
                line_start=20,
                line_end=10,  # Before line_start
            )

        errors = exc_info.value.errors()
        assert any("line_end must be >= line_start" in str(e) for e in errors)

    def test_line_end_equals_start_allowed(self):
        """Test that line_end == line_start is allowed (single line)."""
        symbol = SymbolInfo(
            name="test",
            kind="function",
            line_start=10,
            line_end=10,
        )

        assert symbol.line_start == 10
        assert symbol.line_end == 10

    def test_negative_line_numbers_rejected(self):
        """Test that negative line numbers are rejected."""
        with pytest.raises(ValidationError):
            SymbolInfo(
                name="test",
                kind="function",
                line_start=-1,
                line_end=10,
            )


class TestFileSymbols:
    """Test FileSymbols validation."""

    def test_valid_file_symbols(self):
        """Test that valid file symbols pass validation."""
        file_symbols = FileSymbols(
            path="src/utils.py",
            symbols=[
                SymbolInfo(
                    name="foo",
                    kind="function",
                    line_start=1,
                    line_end=5,
                )
            ],
        )

        assert file_symbols.path == "src/utils.py"
        assert len(file_symbols.symbols) == 1

    def test_empty_symbols_list_allowed(self):
        """Test that empty symbols list is allowed."""
        file_symbols = FileSymbols(
            path="test.py",
            symbols=[],
        )

        assert file_symbols.symbols == []

    def test_invalid_file_path_rejected(self):
        """Test that non-Python file path is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FileSymbols(
                path="test.txt",  # Not .py file
                symbols=[],
            )

        errors = exc_info.value.errors()
        assert any("path" in str(e) for e in errors)

    def test_too_many_symbols_rejected(self):
        """Test that exceeding max symbols is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            FileSymbols(
                path="test.py",
                symbols=[
                    SymbolInfo(
                        name=f"func_{i}",
                        kind="function",
                        line_start=i,
                        line_end=i + 1,
                    )
                    for i in range(1001)  # Exceeds max_length=1000
                ],
            )

        errors = exc_info.value.errors()
        assert any("symbols" in str(e) for e in errors)


class TestInitializeProjectRequest:
    """Test InitializeProjectRequest validation."""

    def test_valid_request(self):
        """Test that valid request passes validation."""
        request = InitializeProjectRequest(
            project_id="test-project",
            workspace_path="/Users/dev/project",
            language="python",
            files=[
                FileSymbols(
                    path="test.py",
                    symbols=[
                        SymbolInfo(
                            name="foo",
                            kind="function",
                            line_start=1,
                            line_end=5,
                        )
                    ],
                )
            ],
        )

        assert request.project_id == "test-project"
        assert request.language == "python"
        assert len(request.files) == 1

    def test_empty_project_id_rejected(self):
        """Test that empty project_id is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InitializeProjectRequest(
                project_id="",  # Empty
                workspace_path="/test",
                files=[
                    FileSymbols(
                        path="test.py",
                        symbols=[],
                    )
                ],
            )

        errors = exc_info.value.errors()
        assert any("project_id" in str(e) for e in errors)

    def test_empty_files_list_rejected(self):
        """Test that empty files list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InitializeProjectRequest(
                project_id="test",
                workspace_path="/test",
                files=[],  # Empty
            )

        errors = exc_info.value.errors()
        assert any("files" in str(e) or "At least one file" in str(e) for e in errors)

    def test_too_many_files_rejected(self):
        """Test that exceeding max files is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InitializeProjectRequest(
                project_id="test",
                workspace_path="/test",
                files=[
                    FileSymbols(path=f"file_{i}.py", symbols=[])
                    for i in range(5001)  # Exceeds max_length=5000
                ],
            )

        errors = exc_info.value.errors()
        assert any("files" in str(e) for e in errors)

    def test_invalid_language_rejected(self):
        """Test that non-Python language is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InitializeProjectRequest(
                project_id="test",
                workspace_path="/test",
                language="javascript",  # Not python
                files=[
                    FileSymbols(path="test.py", symbols=[]),
                ],
            )

        errors = exc_info.value.errors()
        assert any("language" in str(e) for e in errors)


class TestInitializeProjectResponse:
    """Test InitializeProjectResponse serialization."""

    def test_valid_response(self):
        """Test that valid response serializes correctly."""
        response = InitializeProjectResponse(
            project_id="test-project",
            status="initialized",
            indexed_files=100,
            indexed_symbols=500,
            processing_time_ms=1500,
        )

        assert response.project_id == "test-project"
        assert response.status == "initialized"
        assert response.indexed_files == 100
        assert response.processing_time_ms == 1500

    def test_invalid_status_rejected(self):
        """Test that invalid status is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            InitializeProjectResponse(
                project_id="test",
                status="invalid_status",  # Not initialized/already_exists
                indexed_files=0,
                indexed_symbols=0,
                processing_time_ms=0,
            )

        errors = exc_info.value.errors()
        assert any("status" in str(e) for e in errors)

    def test_negative_counts_rejected(self):
        """Test that negative counts are rejected."""
        with pytest.raises(ValidationError):
            InitializeProjectResponse(
                project_id="test",
                status="initialized",
                indexed_files=-1,  # Negative
                indexed_symbols=0,
                processing_time_ms=0,
            )


class TestSymbolChange:
    """Test SymbolChange validation."""

    def test_valid_symbol_change(self):
        """Test that valid symbol change passes validation."""
        change = SymbolChange(
            action="modified",
            name="foo",
            new_data=SymbolInfo(
                name="foo",
                kind="function",
                line_start=1,
                line_end=10,
            ),
        )

        assert change.action == "modified"
        assert change.new_data is not None

    def test_deleted_symbol_without_new_data(self):
        """Test deleted symbol can have no new_data."""
        change = SymbolChange(
            action="deleted",
            name="old_func",
            new_data=None,
        )

        assert change.action == "deleted"
        assert change.new_data is None

    def test_invalid_action_rejected(self):
        """Test that invalid action is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            SymbolChange(
                action="invalid",  # Not added/modified/deleted
                name="foo",
            )

        errors = exc_info.value.errors()
        assert any("action" in str(e) for e in errors)


class TestFileChange:
    """Test FileChange validation."""

    def test_valid_file_change(self):
        """Test that valid file change passes validation."""
        change = FileChange(
            file_path="src/utils.py",
            action="modified",
            symbols_changed=[
                SymbolChange(action="added", name="new_func"),
            ],
        )

        assert change.file_path == "src/utils.py"
        assert change.action == "modified"
        assert len(change.symbols_changed) == 1

    def test_deleted_file_without_symbols(self):
        """Test deleted file can have no symbols_changed."""
        change = FileChange(
            file_path="old_file.py",
            action="deleted",
            symbols_changed=None,
        )

        assert change.action == "deleted"
        assert change.symbols_changed is None


class TestIncrementalUpdateRequest:
    """Test IncrementalUpdateRequest validation."""

    def test_valid_request(self):
        """Test that valid request passes validation."""
        request = IncrementalUpdateRequest(
            version=2,
            changes=[
                FileChange(
                    file_path="test.py",
                    action="modified",
                    symbols_changed=[],
                )
            ],
        )

        assert request.version == 2
        assert len(request.changes) == 1

    def test_version_zero_rejected(self):
        """Test that version 0 is rejected (must be >= 1)."""
        with pytest.raises(ValidationError):
            IncrementalUpdateRequest(
                version=0,  # Invalid
                changes=[
                    FileChange(file_path="test.py", action="modified"),
                ],
            )

    def test_empty_changes_rejected(self):
        """Test that empty changes list is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            IncrementalUpdateRequest(
                version=1,
                changes=[],  # Empty
            )

        errors = exc_info.value.errors()
        assert any("changes" in str(e) for e in errors)


class TestIncrementalUpdateResponse:
    """Test IncrementalUpdateResponse serialization."""

    def test_valid_response(self):
        """Test that valid response serializes correctly."""
        now = datetime.now(UTC)
        response = IncrementalUpdateResponse(
            project_id="test-project",
            version=3,
            updated_at=now,
            changes_applied=5,
            processing_time_ms=200,
        )

        assert response.project_id == "test-project"
        assert response.version == 3
        assert response.updated_at == now


class TestProjectStatusResponse:
    """Test ProjectStatusResponse serialization."""

    def test_valid_response(self):
        """Test that valid response serializes correctly."""
        now = datetime.now(UTC)
        response = ProjectStatusResponse(
            project_id="test-project",
            status="active",
            indexed_files=100,
            indexed_symbols=500,
            last_updated_at=now,
            backend_version=5,
        )

        assert response.project_id == "test-project"
        assert response.status == "active"
        assert response.backend_version == 5

    def test_invalid_status_rejected(self):
        """Test that invalid status is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            ProjectStatusResponse(
                project_id="test",
                status="invalid",  # Not active/indexing/error
                indexed_files=0,
                indexed_symbols=0,
                last_updated_at=datetime.now(UTC),
                backend_version=1,
            )

        errors = exc_info.value.errors()
        assert any("status" in str(e) for e in errors)
