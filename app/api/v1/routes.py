"""API routes for version 1.

This module defines the REST API endpoints using FastAPI with proper
dependency injection and resource management.
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Response, status
from starlette.responses import Response as StarletteResponse

from app.analyzers.rule_engine import RuleEngine
from app.api.v1 import debug_routes
from app.api.v1.schemas import (
    AsyncJobResponse,
    CoverageOptimizationRequest,
    GenerateTestsRequest,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
    QualityAnalysisRequest,
    QualityAnalysisResponse,
    TaskError,
    TaskStatusResponse,
)
from app.core.analysis.llm_analyzer import LLMAnalyzer
from app.core.analyzer import ImpactAnalyzer, TestAnalyzer
from app.core.constants import MAX_FILES_PER_REQUEST
from app.core.graph.graph_service import GraphService
from app.core.llm.llm_client import create_llm_client
from app.core.services.quality_service import QualityAnalysisService
from app.core.tasks.tasks import (
    TaskStatus,
    create_task,
    execute_coverage_optimization_task,
    execute_generate_tests_task,
    get_task,
    update_task_status,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_analyzer_context():
    """
    Async context manager for TestAnalyzer with proper resource cleanup.

    This ensures LLM clients are properly closed after use, preventing
    resource leaks.

    Yields:
        TestAnalyzer instance

    Raises:
        HTTPException: If analyzer initialization fails
    """
    try:
        rule_engine = RuleEngine()
        llm_client = create_llm_client()
        llm_analyzer = LLMAnalyzer(llm_client)
        analyzer = TestAnalyzer(rule_engine, llm_analyzer)

        try:
            yield analyzer
        finally:
            await analyzer.close()

    except Exception as e:
        logger.error(f"Failed to initialize analyzer: {e}")
        raise HTTPException(
            status_code=503, detail=f"Failed to initialize analyzer: {str(e)}"
        )


@asynccontextmanager
async def get_quality_service_context():
    """
    Async context manager for QualityAnalysisService with proper resource cleanup.

    This ensures LLM clients are properly closed after use.

    Yields:
        QualityAnalysisService instance

    Raises:
        HTTPException: If service initialization fails
    """
    try:
        service = QualityAnalysisService()

        try:
            yield service
        finally:
            await service.close()

    except Exception as e:
        logger.error(f"Failed to initialize quality service: {e}")
        raise HTTPException(
            status_code=503, detail=f"Failed to initialize quality service: {str(e)}"
        )


@asynccontextmanager
async def get_impact_analyzer_context(
    project_id: str = "default",
    use_graph: bool = True,
):
    """
    Async context manager for ImpactAnalyzer with GraphService integration.

    This context manager initializes the ImpactAnalyzer with a GraphService
    for graph-based dependency analysis. If Neo4j is unavailable, the analyzer
    will raise an appropriate error.

    Args:
        project_id: Project identifier for graph queries
        use_graph: Whether to use graph-based analysis (default True)

    Yields:
        ImpactAnalyzer instance with GraphService

    Raises:
        HTTPException: If analyzer or graph service initialization fails
    """
    graph_service = None

    try:
        rule_engine = RuleEngine()
        llm_client = create_llm_client()
        llm_analyzer = LLMAnalyzer(llm_client)

        if use_graph:
            graph_service = GraphService()
            try:
                await graph_service.connect()
                logger.debug("GraphService connected for impact analysis")
            except Exception as e:
                logger.error("Failed to connect to Neo4j: %s", e)
                raise HTTPException(
                    status_code=503,
                    detail="Graph database unavailable for impact analysis",
                )

        analyzer = ImpactAnalyzer(
            rule_engine,
            llm_analyzer,
            graph_service=graph_service,
            project_id=project_id,
        )

        try:
            yield analyzer
        finally:
            # Close LLM analyzer
            if hasattr(analyzer, "llm_analyzer") and hasattr(
                analyzer.llm_analyzer, "close"
            ):
                await analyzer.llm_analyzer.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to initialize impact analyzer: %s", e)
        raise HTTPException(
            status_code=503, detail=f"Failed to initialize impact analyzer: {str(e)}"
        )
    finally:
        # Always close graph service if it was created
        if graph_service is not None:
            try:
                await graph_service.close()
                logger.debug("GraphService closed")
            except Exception as e:
                logger.warning("Error closing graph service: %s", e)


# Backward compatibility functions for dependency injection (used by tests)
def get_quality_service() -> QualityAnalysisService:
    """
    Deprecated: Use get_quality_service_context() instead.

    Kept for backward compatibility with existing tests.
    """
    return QualityAnalysisService()


def get_impact_analyzer() -> ImpactAnalyzer:
    """
    Deprecated: Use get_impact_analyzer_context() instead.

    Kept for backward compatibility with existing tests.
    Note: Returns analyzer without GraphService (heuristic-only mode).
    """
    rule_engine = RuleEngine()
    llm_client = create_llm_client()
    llm_analyzer = LLMAnalyzer(llm_client)
    return ImpactAnalyzer(rule_engine, llm_analyzer, graph_service=None)


@router.post(
    "/workflows/generate-tests",
    response_model=AsyncJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_generate_tests(
    request: GenerateTestsRequest,
) -> AsyncJobResponse:
    """
    Submit a test generation request and return an async task identifier.
    Uses asyncio.create_task to run the generation in the background.
    Supports debug_options for simulating failures (development/testing only).
    """
    try:
        # Convert request to dict for task payload
        task_payload = request.model_dump()

        logger.info(
            "Received test generation request: source_code_length=%d, has_description=%s, has_existing_tests=%s",
            len(request.source_code),
            request.user_description is not None,
            request.existing_test_code is not None,
        )
        logger.debug("Request payload: %s", task_payload)

        # Check for debug options to simulate task failure
        if request.debug_options and request.debug_options.simulate_error:
            logger.warning(
                "DEBUG MODE: Simulating task failure with message: %s",
                request.debug_options.error_message,
            )

            # Create task in PENDING state
            task_id = await create_task(task_payload)

            # Immediately mark as FAILED with custom error
            await update_task_status(
                task_id, TaskStatus.FAILED, error=request.debug_options.error_message
            )

            # Return task_id immediately (task is already failed)
            return AsyncJobResponse(
                task_id=task_id,
                status=TaskStatus.PENDING.value,  # Return pending to match normal flow
                estimated_time_seconds=0,
            )

        # Normal flow: create task and launch background execution
        task_id = await create_task(task_payload)
        logger.debug("Created task with ID: %s", task_id)

        # Launch background task using asyncio instead of Celery
        asyncio.create_task(execute_generate_tests_task(task_id, task_payload))
        logger.info("Launched background task for test generation: task_id=%s", task_id)

        # Return AsyncJobResponse per OpenAPI spec
        return AsyncJobResponse(
            task_id=task_id,
            status=TaskStatus.PENDING.value,
            estimated_time_seconds=30,  # Default estimate
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to submit test generation task: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to submit test generation task",
        ) from exc


@router.post(
    "/optimization/coverage",
    response_model=AsyncJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_coverage_optimization(
    request: CoverageOptimizationRequest,
) -> AsyncJobResponse:
    """
    Submit a coverage optimization request and return an async task identifier.
    Uses asyncio.create_task to run the optimization in the background.
    Supports debug_options for simulating failures (development/testing only).
    """
    try:
        # Convert request to dict for task payload
        task_payload = request.model_dump()

        logger.info(
            "Received coverage optimization request: source_code_length=%d, uncovered_ranges=%d, framework=%s",
            len(request.source_code),
            len(request.uncovered_ranges),
            request.framework,
        )
        logger.debug("Request payload: %s", task_payload)

        # Check for debug options to simulate task failure
        if request.debug_options and request.debug_options.simulate_error:
            logger.warning(
                "DEBUG MODE: Simulating task failure with message: %s",
                request.debug_options.error_message,
            )

            # Create and immediately fail the task
            task_id = await create_task(task_payload)
            await update_task_status(
                task_id, TaskStatus.FAILED, error=request.debug_options.error_message
            )

            return AsyncJobResponse(
                task_id=task_id,
                status=TaskStatus.PENDING.value,
                estimated_time_seconds=0,
            )

        # Normal flow: create task and launch background execution
        task_id = await create_task(task_payload)
        logger.debug("Created task with ID: %s", task_id)

        # Launch background task using asyncio
        asyncio.create_task(execute_coverage_optimization_task(task_id, task_payload))
        logger.info(
            "Launched background task for coverage optimization: task_id=%s", task_id
        )

        # Return AsyncJobResponse per OpenAPI spec
        return AsyncJobResponse(
            task_id=task_id,
            status=TaskStatus.PENDING.value,
            estimated_time_seconds=30,  # Default estimate
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to submit coverage optimization task: %s", exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to submit coverage optimization task",
        ) from exc


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    response_model_exclude_none=True,
)
async def get_task_status(task_id: str) -> TaskStatusResponse | StarletteResponse:
    """
    Get task status and results.

    Poll for async task status and results.
    Used for long-running operations like test generation.

    Args:
        task_id: Task identifier (UUID)

    Returns:
        Task status information

    Raises:
        HTTPException: 404 if task not found
    """
    logger.debug("Polling task status: task_id=%s", task_id)

    task_data = await get_task(task_id)
    if task_data is None:
        logger.debug("Task not found: task_id=%s", task_id)
        return StarletteResponse(status_code=404)

    # Convert task data to TaskStatusResponse
    error = None
    if task_data.get("error"):
        error_data = task_data["error"]
        # Handle both dict (new format) and string (legacy format)
        if isinstance(error_data, dict):
            # Extract fields explicitly to avoid issues with polluted data
            error = TaskError(
                message=error_data.get("message", "Unknown error"),
                code=error_data.get("code"),
                details=error_data.get("details"),
            )
        else:
            # Legacy string format fallback
            error = TaskError(message=str(error_data), code=None, details=None)

    logger.info(
        "Returning task status: task_id=%s, status=%s, has_result=%s, has_error=%s",
        task_id,
        task_data["status"],
        task_data.get("result") is not None,
        error is not None,
    )

    return TaskStatusResponse(
        task_id=task_data["id"],
        status=task_data["status"],
        result=task_data.get("result"),
        error=error,
        created_at=task_data.get("created_at"),
    )


@router.post("/quality/analyze", response_model=QualityAnalysisResponse)
async def analyze_quality(
    request: QualityAnalysisRequest,
) -> QualityAnalysisResponse:
    """
    Analyze multiple test files for quality issues with fix suggestions.

    This endpoint provides batch quality analysis with suggestions for fixes.
    Uses fast (rules-only), deep (LLM-only), or hybrid analysis modes.

    Args:
        request: Quality analysis request containing files and mode

    Returns:
        Quality analysis response with issues and summary statistics

    Raises:
        HTTPException: If analysis fails or request is invalid
    """
    start_time = time.time()

    try:
        # Validate request
        if not request.files:
            raise HTTPException(
                status_code=400, detail="No files provided for analysis"
            )

        if len(request.files) > MAX_FILES_PER_REQUEST:
            raise HTTPException(
                status_code=400,
                detail=f"Too many files (max {MAX_FILES_PER_REQUEST})",
            )

        logger.info(
            "Starting quality analysis: %d files, mode=%s",
            len(request.files),
            request.mode,
        )
        logger.debug(
            "Quality analysis request received for files: %s",
            [f.path for f in request.files],
        )

        # Use context manager for proper resource management
        async with get_quality_service_context() as quality_service:
            result = await quality_service.analyze_batch(
                files=request.files, mode=request.mode
            )

        # Calculate endpoint duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log endpoint-level response summary with metrics
        logger.info(
            "Quality analysis completed: issues=%d, critical=%d, files=%d, mode=%s, duration_ms=%d",
            len(result.issues) if result.issues else 0,
            result.summary.critical_issues,
            result.summary.total_files,
            request.mode,
            duration_ms,
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Quality analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Quality analysis failed due to internal error"
        )


@router.post("/analysis/impact", response_model=ImpactAnalysisResponse)
async def analyze_impact(
    request: ImpactAnalysisRequest,
) -> ImpactAnalysisResponse:
    """
    Analyze the impact of file changes on test files using graph-based analysis.

    This endpoint uses the Neo4j graph database to find reverse dependencies
    (functions that call the modified functions) for accurate impact assessment.
    When git_diff is provided, the analysis extracts modified function names
    and queries the dependency graph.

    Args:
        request: Impact analysis request containing project context

    Returns:
        Impact analysis response with impacted tests and suggested actions

    Raises:
        HTTPException: 400 if request is invalid
        HTTPException: 503 if graph database is unavailable
        HTTPException: 500 if analysis fails due to internal error
    """
    try:
        # Validate request
        if not request.project_context.files_changed:
            raise HTTPException(status_code=400, detail="files_changed cannot be empty")

        logger.info(
            "Starting impact analysis (graph-based): %d changed files, %d related tests, project=%s",
            len(request.project_context.files_changed),
            len(request.project_context.related_tests),
            request.project_id,
        )
        logger.debug(
            "Changed files: %s",
            [entry.path for entry in request.project_context.files_changed],
        )

        # Extract data from request
        files_changed = [
            {"path": entry.path, "change_type": entry.change_type}
            for entry in request.project_context.files_changed
        ]
        related_tests = request.project_context.related_tests

        # Use context manager for proper resource management with GraphService
        async with get_impact_analyzer_context(
            project_id=request.project_id,
            use_graph=True,
        ) as impact_analyzer:
            result = await impact_analyzer.analyze_impact_async(
                files_changed,
                related_tests,
                git_diff=request.git_diff,
            )

        logger.info(
            "Impact analysis completed: %d impacted tests found",
            len(result.impacted_tests) if result.impacted_tests else 0,
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except ValueError as e:
        logger.error("Validation error: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        # Handle graph service errors
        logger.error("Runtime error in impact analysis: %s", e)
        raise HTTPException(
            status_code=503,
            detail=str(e),
        )
    except Exception as e:
        logger.error("Impact analysis failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500, detail="Impact analysis failed due to internal error"
        )


# Include debug routes for Neo4j testing
router.include_router(debug_routes.router)
