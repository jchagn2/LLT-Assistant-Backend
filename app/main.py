"""Main FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.context import router as context_router
from app.api.v1.routes import router as api_router
from app.config import settings
from app.core.middleware import RequestIDMiddleware, register_exception_handlers
from app.core.services.logging_config import setup_logging

# Set up structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan events."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")

    # Initialize Neo4j connection and indexes
    from app.core.graph.graph_service import GraphService

    graph_service = None
    try:
        logger.info("Initializing Neo4j connection...")
        graph_service = GraphService()
        await graph_service.connect()
        await graph_service.create_indexes()
        logger.info("Neo4j initialization completed")
    except Exception as e:
        logger.warning(
            "Neo4j initialization failed (continuing without graph features): %s", e
        )

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")

    # Cleanup Neo4j
    if graph_service:
        try:
            await graph_service.close()
            logger.info("Neo4j connection closed")
        except Exception as e:
            logger.warning("Error closing Neo4j connection: %s", e)

    # Cleanup task storage
    try:
        from app.core.tasks.tasks import cleanup_task_storage

        await cleanup_task_storage()
    except Exception as e:
        logger.warning(f"Error during task storage cleanup: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="FastAPI backend for pytest test analysis using hybrid rule engine + LLM approach",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Register exception handlers
register_exception_handlers(app)

# Add RequestID middleware
app.add_middleware(RequestIDMiddleware)

# Add CORS middleware
# NOTE: Configure allowed origins properly for production!
# Current configuration allows all origins for development.
# For production, replace with specific origins:
# allow_origins=["https://yourdomain.com", "https://app.yourdomain.com"]
allowed_origins = settings.cors_origins if hasattr(settings, "cors_origins") else ["*"]

if "*" in allowed_origins:
    logger.warning(
        "CORS is configured to allow all origins. "
        "This is acceptable for development but should be restricted in production."
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint with Neo4j connectivity verification.

    Returns 200 with "healthy" or "degraded" status depending on
    whether Neo4j is accessible.
    """
    import time
    from datetime import UTC, datetime

    from app.core.graph.graph_service import GraphService

    # Initialize response structure
    health_status = {
        "status": "healthy",
        "version": settings.app_version,
        "services": {
            "api": {"status": "up"},
            "neo4j": {"status": "down", "response_time_ms": None},
        },
        "timestamp": datetime.now(UTC).isoformat(),
    }

    # Test Neo4j connectivity
    graph_service = None
    try:
        graph_service = GraphService()
        await graph_service.connect()

        # Measure query response time
        start_time = time.time()
        await graph_service.client.execute_query("RETURN 1 AS test")
        response_time_ms = int((time.time() - start_time) * 1000)

        # Neo4j is healthy
        health_status["services"]["neo4j"] = {
            "status": "up",
            "response_time_ms": response_time_ms,
        }

        logger.debug("Health check: Neo4j up (%dms)", response_time_ms)

    except Exception as e:
        # Neo4j is down, but API is still functional (degraded)
        logger.warning("Health check: Neo4j down - %s", str(e))
        health_status["status"] = "degraded"
        health_status["services"]["neo4j"] = {
            "status": "down",
            "response_time_ms": None,
        }

    finally:
        # Clean up connection
        if graph_service:
            try:
                await graph_service.close()
            except Exception as e:
                logger.warning("Error closing health check connection: %s", str(e))

    return health_status


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "FastAPI backend for pytest test analysis",
    }


# Include API routes
app.include_router(api_router)
app.include_router(context_router)
