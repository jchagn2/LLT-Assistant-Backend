"""
Production API endpoints for Context Management (Phase 1).

This module provides RESTful endpoints for managing code dependency graphs:
- Initialize project graph (batch upload)
- Incremental updates with optimistic locking
- Project status queries
"""

import logging
import time
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, status

from app.core.error_handlers import (
    ProjectAlreadyExistsError,
    ProjectNotFoundError,
    VersionConflictError,
)
from app.core.graph.graph_service import GraphService
from app.models.context import (
    FileSymbols,
    IncrementalUpdateRequest,
    IncrementalUpdateResponse,
    InitializeProjectRequest,
    InitializeProjectResponse,
    ProjectStatusResponse,
    SymbolInfo,
)

router = APIRouter(prefix="/context", tags=["Context Management"])
logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_graph_service_context():
    """
    Async context manager for GraphService with proper resource cleanup.

    Yields:
        GraphService instance

    Raises:
        HTTPException: If service initialization fails or raised from endpoint
    """
    service = GraphService()

    try:
        await service.connect()
        await service.create_indexes()  # Ensure indexes exist
        yield service
    except HTTPException:
        # Re-raise HTTPExceptions from endpoints as-is
        raise
    except (
        ProjectNotFoundError,
        ProjectAlreadyExistsError,
        VersionConflictError,
    ):
        # Re-raise our custom exceptions so they reach the exception handlers
        raise
    except Exception as e:
        logger.error("Failed to initialize graph service: %s", e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Graph database service unavailable: {str(e)}",
        ) from e
    finally:
        try:
            await service.close()
        except Exception as e:
            logger.warning("Error closing graph service: %s", e)


def prepare_symbols_for_db(
    file_path: str, symbols: List[SymbolInfo]
) -> List[Dict[str, Any]]:
    """
    Convert SymbolInfo models to database-ready dictionaries.

    Args:
        file_path: File path for the symbols
        symbols: List of SymbolInfo objects

    Returns:
        List of dictionaries with qualified_name added
    """
    return [
        {
            "name": s.name,
            "kind": s.kind,
            "signature": s.signature or "",
            "file_path": file_path,
            "line_start": s.line_start,
            "line_end": s.line_end,
            "qualified_name": f"{file_path}::{s.name}",
            "calls": s.calls,
        }
        for s in symbols
    ]


def prepare_relationships(
    file_path: str, symbols: List[SymbolInfo]
) -> List[Dict[str, Any]]:
    """
    Extract call relationships from symbols.

    Args:
        file_path: File path
        symbols: List of SymbolInfo objects

    Returns:
        List of relationship dictionaries
    """
    relationships = []

    for symbol in symbols:
        caller_qname = f"{file_path}::{symbol.name}"
        for callee in symbol.calls:
            # Note: We don't know the exact file of the callee, so we use a heuristic
            # The actual matching will be done by Neo4j query
            relationships.append(
                {
                    "caller_qualified_name": caller_qname,
                    "callee_qualified_name": callee,  # Will match by name in query
                    "line": symbol.line_start,
                }
            )

    return relationships


@router.post(
    "/projects/initialize",
    response_model=InitializeProjectResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Project initialized successfully"},
        409: {"description": "Project already exists"},
        422: {"description": "Validation error"},
        503: {"description": "Database unavailable"},
    },
)
async def initialize_project(
    request: InitializeProjectRequest,
) -> InitializeProjectResponse:
    """
    Initialize a project's code graph.

    Creates Symbol nodes and CALLS relationships for all files.
    Returns 409 if project already exists.

    Args:
        request: Project initialization request with files and symbols

    Returns:
        InitializeProjectResponse with statistics

    Raises:
        HTTPException: 409 if project exists, 503 if database error
    """
    start_time = time.time()

    logger.info(
        "Initializing project: project_id=%s, files=%d",
        request.project_id,
        len(request.files),
    )

    async with get_graph_service_context() as graph_service:
        # Check if project already exists
        if await graph_service.check_project_exists(request.project_id):
            raise ProjectAlreadyExistsError(request.project_id)

        try:
            # Prepare symbols for database
            all_symbols = []
            all_relationships = []

            for file in request.files:
                symbols_data = prepare_symbols_for_db(file.path, file.symbols)
                all_symbols.extend(symbols_data)

                relationships = prepare_relationships(file.path, file.symbols)
                all_relationships.extend(relationships)

            # Insert into Neo4j using batch operations
            symbols_created = await graph_service.batch_create_symbols_chunked(
                request.project_id,
                all_symbols,
            )

            # Note: Relationship creation may have partial failures if callees don't exist
            # This is acceptable as external library calls won't have targets
            relationships_created = 0
            if all_relationships:
                relationships_created = await graph_service.create_call_relationships(
                    request.project_id,
                    all_relationships,
                )

            # Initialize project version
            await graph_service.increment_project_version(request.project_id)

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Project initialized successfully: project_id=%s, files=%d, symbols=%d, relationships=%d, time_ms=%d",
                request.project_id,
                len(request.files),
                symbols_created,
                relationships_created,
                processing_time_ms,
            )

            return InitializeProjectResponse(
                project_id=request.project_id,
                status="initialized",
                indexed_files=len(request.files),
                indexed_symbols=symbols_created,
                processing_time_ms=processing_time_ms,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Project initialization failed: %s", e, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database operation failed. Please try again.",
            ) from e


@router.patch(
    "/projects/{project_id}/incremental",
    response_model=IncrementalUpdateResponse,
    responses={
        200: {"description": "Update applied successfully"},
        404: {"description": "Project not found"},
        409: {"description": "Version conflict"},
        422: {"description": "Validation error"},
    },
)
async def update_incremental(
    project_id: str,
    request: IncrementalUpdateRequest,
) -> IncrementalUpdateResponse:
    """
    Apply incremental changes to project graph.

    Uses optimistic locking via version number to prevent conflicts.

    Args:
        project_id: Project identifier
        request: Incremental update request with version and changes

    Returns:
        IncrementalUpdateResponse with new version

    Raises:
        HTTPException: 404 if project not found, 409 if version conflict
    """
    start_time = time.time()

    logger.info(
        "Applying incremental update: project_id=%s, version=%d, changes=%d",
        project_id,
        request.version,
        len(request.changes),
    )

    async with get_graph_service_context() as graph_service:
        # Check project exists
        if not await graph_service.check_project_exists(project_id):
            raise ProjectNotFoundError(project_id)

        # Check version (optimistic locking)
        current_version = await graph_service.get_project_version(project_id)
        if request.version != current_version:
            raise VersionConflictError(
                expected=current_version,
                received=request.version,
                project_id=project_id,
            )

        try:
            total_changes = 0

            for file_change in request.changes:
                if file_change.action == "deleted":
                    # Delete all symbols from this file
                    deleted = await graph_service.delete_file_symbols(
                        project_id, file_change.file_path
                    )
                    total_changes += deleted

                elif file_change.action == "modified" and file_change.symbols_changed:
                    # Apply symbol changes
                    stats = await graph_service.update_file_symbols(
                        project_id,
                        file_change.file_path,
                        file_change.symbols_changed,
                    )
                    total_changes += sum(stats.values())

            # Increment version
            new_version = await graph_service.increment_project_version(project_id)

            processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Incremental update completed: project_id=%s, changes=%d, new_version=%d, time_ms=%d",
                project_id,
                total_changes,
                new_version,
                processing_time_ms,
            )

            return IncrementalUpdateResponse(
                project_id=project_id,
                version=new_version,
                updated_at=datetime.now(UTC),
                changes_applied=total_changes,
                processing_time_ms=processing_time_ms,
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error("Incremental update failed: %s", e, exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Update operation failed",
            ) from e


@router.get(
    "/projects/{project_id}/status",
    response_model=ProjectStatusResponse,
    responses={
        200: {"description": "Status retrieved"},
        404: {"description": "Project not found"},
    },
)
async def get_project_status(
    project_id: str,
) -> ProjectStatusResponse:
    """
    Get current status and statistics of a project.

    Args:
        project_id: Project identifier

    Returns:
        ProjectStatusResponse with statistics and version

    Raises:
        HTTPException: 404 if project not found
    """
    logger.info("Retrieving project status: project_id=%s", project_id)

    async with get_graph_service_context() as graph_service:
        if not await graph_service.check_project_exists(project_id):
            raise ProjectNotFoundError(project_id)

        stats = await graph_service.get_project_statistics(project_id)
        version = await graph_service.get_project_version(project_id)

        logger.info(
            "Project status retrieved: project_id=%s, files=%d, symbols=%d, version=%d",
            project_id,
            stats["total_files"],
            stats["total_symbols"],
            version,
        )

        return ProjectStatusResponse(
            project_id=project_id,
            status="active",
            indexed_files=stats["total_files"],
            indexed_symbols=stats["total_symbols"],
            last_updated_at=datetime.now(UTC),
            backend_version=version,
        )
