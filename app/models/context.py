"""
Pydantic models for Context Management API (Phase 1).

This module defines request and response models for the production-grade
context management endpoints that handle code graph initialization and updates.
"""

from datetime import UTC, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SymbolInfo(BaseModel):
    """Represents a single code symbol (function, class, method)."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Symbol name",
    )

    kind: str = Field(
        ...,
        pattern="^(function|class|method)$",
        description="Symbol type",
    )

    signature: Optional[str] = Field(
        None,
        max_length=500,
        description="Function signature with type hints",
    )

    line_start: int = Field(..., ge=0, description="Start line (0-based)")
    line_end: int = Field(..., ge=0, description="End line (0-based)")

    calls: List[str] = Field(
        default_factory=list,
        description="Names of functions called by this symbol",
    )

    @field_validator("line_end")
    @classmethod
    def line_end_must_be_after_start(cls, v: int, info) -> int:
        """Validate that line_end is >= line_start."""
        if "line_start" in info.data and v < info.data["line_start"]:
            raise ValueError("line_end must be >= line_start")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "calculate_tax",
                "kind": "function",
                "signature": "(price: float, region: str) -> float",
                "line_start": 10,
                "line_end": 25,
                "calls": ["get_tax_rate", "validate_price"],
            }
        }
    )


class FileSymbols(BaseModel):
    """Symbols extracted from a single file."""

    path: str = Field(
        ...,
        pattern=r"^[\w\-./]+\.py$",
        description="File path relative to workspace",
    )

    symbols: List[SymbolInfo] = Field(
        ...,
        min_length=0,
        max_length=1000,
        description="Symbols in this file",
    )


class InitializeProjectRequest(BaseModel):
    """Request to initialize a project's code graph."""

    project_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique project identifier",
    )

    workspace_path: str = Field(
        ...,
        description="Absolute path to workspace",
    )

    language: str = Field(
        default="python",
        pattern="^python$",
        description="Programming language (only Python supported)",
    )

    files: List[FileSymbols] = Field(
        ...,
        max_length=5000,
        description="Files to index",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "my-python-project",
                "workspace_path": "/Users/dev/my-project",
                "language": "python",
                "files": [
                    {
                        "path": "src/utils.py",
                        "symbols": [
                            {
                                "name": "calculate_tax",
                                "kind": "function",
                                "signature": "(price: float) -> float",
                                "line_start": 10,
                                "line_end": 15,
                                "calls": [],
                            }
                        ],
                    }
                ],
            }
        }
    )


class InitializeProjectResponse(BaseModel):
    """Response from project initialization."""

    project_id: str
    status: str = Field(..., pattern="^(initialized|already_exists)$")
    indexed_files: int = Field(..., ge=0)
    indexed_symbols: int = Field(..., ge=0)
    processing_time_ms: int = Field(..., ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "my-project",
                "status": "initialized",
                "indexed_files": 500,
                "indexed_symbols": 2048,
                "processing_time_ms": 8500,
            }
        }
    )


class SymbolChange(BaseModel):
    """Describes a change to a symbol."""

    action: str = Field(..., pattern="^(added|modified|deleted)$")
    symbol: SymbolInfo = Field(..., description="The symbol being changed")


class FileChange(BaseModel):
    """Describes changes to a file."""

    file_path: str
    action: str = Field(..., pattern="^(modified|deleted)$")
    symbols_changed: Optional[List[SymbolChange]] = None


class IncrementalUpdateRequest(BaseModel):
    """Request to update project incrementally."""

    version: int = Field(..., ge=1, description="Current version (optimistic locking)")
    changes: List[FileChange] = Field(..., min_length=1)


class IncrementalUpdateResponse(BaseModel):
    """Response from incremental update."""

    project_id: str
    version: int
    updated_at: datetime
    changes_applied: int
    processing_time_ms: int


class ProjectStatusResponse(BaseModel):
    """Current project status."""

    project_id: str
    status: str = Field(..., pattern="^(active|indexing|error)$")
    indexed_files: int
    indexed_symbols: int
    last_updated_at: datetime
    backend_version: int = Field(
        ..., description="Version number for optimistic locking"
    )


class ProjectDataResponse(BaseModel):
    """Complete project data for frontend graceful recovery.

    This response contains all files and symbols for a project,
    allowing the frontend to rebuild its local cache when needed.
    """

    project_id: str = Field(..., description="Project identifier")
    version: int = Field(
        ..., description="Current backend version for optimistic locking"
    )
    workspace_path: Optional[str] = Field(
        None, description="Absolute path to workspace directory"
    )
    files: List[FileSymbols] = Field(
        ..., description="All project files with their symbols"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "project_id": "inc-test-1764069594",
                "version": 3,
                "workspace_path": "/Users/user/inc-project",
                "files": [
                    {
                        "path": "src/services.py",
                        "symbols": [
                            {
                                "name": "get_user",
                                "kind": "function",
                                "signature": "(user_id: int) -> dict",
                                "line_start": 5,
                                "line_end": 11,
                                "calls": [],
                            }
                        ],
                    }
                ],
            }
        }
    )


class ErrorResponse(BaseModel):
    """Standardized error response schema for API errors."""

    error: str = Field(..., description="Human-readable error message")
    error_code: str = Field(
        ..., pattern="^[A-Z_]+$", description="Machine-readable error code"
    )
    details: dict = Field(default_factory=dict, description="Additional error context")
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Error timestamp"
    )
    path: str = Field(..., description="Request path where error occurred")
    suggestion: Optional[str] = Field(None, description="Suggested resolution action")
