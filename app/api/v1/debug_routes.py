"""
Debug API routes for Neo4j graph database operations.

These endpoints are for development and testing purposes to validate
Neo4j integration and performance.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import APIRouter, HTTPException, Query, status

from app.api.v1.schemas import (
    IngestSymbolsRequest,
    IngestSymbolsResponse,
    QueryCallersResponse,
    QueryFunctionResponse,
    SymbolInfo,
)
from app.core.graph.graph_service import GraphService

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_graph_service_context():
    """
    Async context manager for GraphService with proper resource cleanup.

    Yields:
        GraphService instance

    Raises:
        HTTPException: If service initialization fails
    """
    service = GraphService()

    try:
        await service.connect()
        yield service
    except Exception as e:
        logger.error("Failed to initialize graph service: %s", e)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to initialize graph service: {str(e)}",
        ) from e
    finally:
        try:
            await service.close()
        except Exception as e:
            logger.warning("Error closing graph service: %s", e)


@router.post(
    "/ingest-symbols",
    response_model=IngestSymbolsResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_symbols(
    request: IngestSymbolsRequest,
) -> IngestSymbolsResponse:
    """
    Ingest symbol information into Neo4j graph database.

    This endpoint accepts symbol nodes and relationships from the frontend
    and stores them in Neo4j. Uses MERGE to avoid duplicates and transactions
    for atomicity.

    Args:
        request: Symbol ingestion request with nodes and relationships

    Returns:
        Ingestion statistics including processing time

    Raises:
        HTTPException: If ingestion fails
    """
    try:
        logger.info(
            "Received symbol ingestion request: project=%s, symbols=%d, calls=%d, imports=%d",
            request.project_id,
            len(request.symbols),
            len(request.calls),
            len(request.imports),
        )

        async with get_graph_service_context() as graph_service:
            # Ensure indexes exist
            await graph_service.create_indexes()

            # Convert Pydantic models to dictionaries
            symbols = [symbol.model_dump() for symbol in request.symbols]
            calls = [call.model_dump() for call in request.calls]
            imports = [imp.model_dump() for imp in request.imports]

            # Ingest symbols and relationships
            stats = await graph_service.ingest_symbols(
                symbols=symbols,
                calls=calls,
                imports=imports,
                project_id=request.project_id,
            )

        logger.info(
            "Symbol ingestion completed: nodes=%d, relationships=%d, time_ms=%d",
            stats["nodes_created"],
            stats["relationships_created"],
            stats["processing_time_ms"],
        )

        return IngestSymbolsResponse(
            nodes_created=stats["nodes_created"],
            relationships_created=stats["relationships_created"],
            processing_time_ms=stats["processing_time_ms"],
            project_id=request.project_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Symbol ingestion failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Symbol ingestion failed due to internal error",
        )


@router.get(
    "/query-function/{function_name}",
    response_model=QueryFunctionResponse,
)
async def query_function_dependencies(
    function_name: str,
    project_id: str = Query(default="test-project", description="Project identifier"),
    depth: int = Query(default=1, ge=1, le=3, description="Dependency depth (1-3)"),
) -> QueryFunctionResponse:
    """
    Query function and its dependencies from Neo4j graph.

    This endpoint retrieves a function's information and its direct/transitive
    dependencies up to the specified depth.

    Performance target: < 100ms query latency

    Args:
        function_name: Name of the function to query
        project_id: Project identifier (defaults to 'test-project')
        depth: Traversal depth for dependencies (1-3)

    Returns:
        Function information with dependencies and query metrics

    Raises:
        HTTPException: If query fails or function not found
    """
    try:
        logger.info(
            "Querying function: name=%s, project=%s, depth=%d",
            function_name,
            project_id,
            depth,
        )

        async with get_graph_service_context() as graph_service:
            result = await graph_service.query_function_dependencies(
                function_name=function_name,
                project_id=project_id,
                depth=depth,
            )

        # Check if function was found
        if result["function"] is None:
            logger.warning(
                "Function not found: name=%s, project=%s",
                function_name,
                project_id,
            )
            raise HTTPException(
                status_code=404,
                detail=f"Function '{function_name}' not found in project '{project_id}'",
            )

        # Convert result to response format
        function_info = SymbolInfo(**result["function"])

        dependencies = [SymbolInfo(**dep) for dep in result["dependencies"]]

        logger.info(
            "Function query completed: dependencies=%d, time_ms=%d",
            len(dependencies),
            result["query_time_ms"],
        )

        return QueryFunctionResponse(
            function=function_info,
            dependencies=dependencies,
            query_time_ms=result["query_time_ms"],
            project_id=project_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Function query failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Function query failed due to internal error",
        )


@router.get(
    "/query-callers/{function_name}",
    response_model=QueryCallersResponse,
)
async def query_function_callers(
    function_name: str,
    project_id: str = Query(default="test-project", description="Project identifier"),
) -> QueryCallersResponse:
    """
    Query functions that call the specified function (reverse dependencies).

    This endpoint retrieves a function's information and the list of functions
    that call it (reverse lookup). Useful for impact analysis.

    Performance target: < 100ms query latency

    Args:
        function_name: Name of the function to query callers for
        project_id: Project identifier (defaults to 'test-project')

    Returns:
        Function information with list of callers and query metrics

    Raises:
        HTTPException: If query fails or function not found
    """
    try:
        logger.info(
            "Querying function callers: name=%s, project=%s",
            function_name,
            project_id,
        )

        async with get_graph_service_context() as graph_service:
            result = await graph_service.query_reverse_dependencies(
                function_name=function_name,
                project_id=project_id,
            )

        # Check if function was found
        if result["function"] is None:
            logger.warning(
                "Function not found: name=%s, project=%s",
                function_name,
                project_id,
            )
            raise HTTPException(
                status_code=404,
                detail=f"Function '{function_name}' not found in project '{project_id}'",
            )

        # Convert result to response format
        function_info = SymbolInfo(**result["function"])

        callers = [SymbolInfo(**caller) for caller in result["callers"]]

        logger.info(
            "Function callers query completed: callers=%d, time_ms=%d",
            len(callers),
            result["query_time_ms"],
        )

        return QueryCallersResponse(
            function=function_info,
            callers=callers,
            query_time_ms=result["query_time_ms"],
            project_id=project_id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Function callers query failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Function callers query failed due to internal error",
        )


@router.get("/health/neo4j")
async def neo4j_health_check() -> dict:
    """
    Health check endpoint for Neo4j connection.

    Returns:
        Status dictionary indicating Neo4j connectivity
    """
    try:
        async with get_graph_service_context() as graph_service:
            # Simple query to verify connectivity
            await graph_service.client.execute_query("RETURN 1")

        return {
            "status": "healthy",
            "service": "neo4j",
        }
    except Exception as e:
        logger.error("Neo4j health check failed: %s", e)
        raise HTTPException(
            status_code=503,
            detail=f"Neo4j is unhealthy: {str(e)}",
        )
