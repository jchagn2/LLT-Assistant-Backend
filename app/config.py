"""Configuration management for LLT Assistant Backend."""

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    app_name: str = Field(
        default="LLT Assistant Backend", description="Application name"
    )
    app_version: str = Field(default="0.1.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")

    # Server Configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8886, description="Server port")

    # LLM Configuration
    llm_api_key: str = Field(
        default="test-key-for-development",
        validation_alias="LLM_API_KEY",
        description="LLM API key (from LLM_API_KEY env var)",
    )
    llm_base_url: str = Field(
        default="https://api.deepseek.com",
        validation_alias="LLM_BASE_URL",
        description="LLM API base URL (from LLM_BASE_URL env var)",
    )
    llm_model: str = Field(default="deepseek-chat", description="LLM model name")
    llm_timeout: float = Field(
        default=120.0,
        validation_alias="LLM_TIMEOUT",
        description="LLM API timeout in seconds",
    )
    llm_max_retries: int = Field(default=3, description="Maximum LLM API retries")
    llm_max_concurrent_calls: int = Field(
        default=10,
        ge=1,
        le=50,
        validation_alias="LLM_MAX_CONCURRENT_CALLS",
        description="Maximum concurrent LLM API calls for parallelization",
    )

    # Analysis Configuration
    max_file_size: int = Field(
        default=1024 * 1024, description="Maximum file size in bytes"
    )
    max_files_per_request: int = Field(
        default=50, description="Maximum files per analysis request"
    )

    # Logging Configuration
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json or text)")
    log_sensitive_data: bool = Field(
        default=False,
        validation_alias="LOG_SENSITIVE_DATA",
        description="Whether to log sensitive data like full LLM requests/responses",
    )

    # CORS Configuration
    cors_origins: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins (use specific domains in production)",
    )

    # Task / Redis Configuration
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for task management",
    )

    # Neo4j Configuration
    neo4j_uri: str = Field(
        default="bolt://localhost:7687",
        validation_alias="NEO4J_URI",
        description="Neo4j connection URI",
    )
    neo4j_user: str = Field(
        default="neo4j",
        validation_alias="NEO4J_USER",
        description="Neo4j username",
    )
    neo4j_password: str = Field(
        default="neo4j123",
        validation_alias="NEO4J_PASSWORD",
        description="Neo4j password",
    )
    neo4j_database: str = Field(
        default="neo4j",
        validation_alias="NEO4J_DATABASE",
        description="Neo4j database name",
    )
    neo4j_max_connection_lifetime: int = Field(
        default=3600,
        description="Max connection lifetime in seconds",
    )
    neo4j_max_connection_pool_size: int = Field(
        default=50,
        description="Max connection pool size",
    )
    neo4j_connection_acquisition_timeout: int = Field(
        default=60,
        description="Connection acquisition timeout in seconds",
    )

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
        "populate_by_name": True,
    }


# Global settings instance
# NOTE: This is a singleton for configuration only, which is acceptable
# as configuration should be immutable after initialization.
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance.

    This factory function provides a testable way to access settings,
    allowing for dependency injection and mocking in tests.

    Returns:
        Settings: The global settings instance
    """
    return settings
