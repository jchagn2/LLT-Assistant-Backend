"""
Custom exception classes for LLT Assistant Backend.

Provides domain-specific exceptions with error codes and structured details.
"""


class LLTException(Exception):
    """
    Base exception for LLT backend.

    All custom exceptions inherit from this class and include:
    - Human-readable message
    - Machine-readable error code
    - Optional details dictionary for debugging
    """

    def __init__(self, message: str, error_code: str, details: dict = None):
        """
        Initialize LLT exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code (e.g., "PROJECT_EXISTS")
            details: Optional dictionary with additional error context
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ProjectAlreadyExistsError(LLTException):
    """Raised when attempting to create a project that already exists."""

    def __init__(self, project_id: str):
        """
        Initialize project exists error.

        Args:
            project_id: The project identifier that already exists
        """
        super().__init__(
            message=f"Project '{project_id}' already exists",
            error_code="PROJECT_EXISTS",
            details={"project_id": project_id},
        )


class ProjectNotFoundError(LLTException):
    """Raised when a requested project doesn't exist."""

    def __init__(self, project_id: str):
        """
        Initialize project not found error.

        Args:
            project_id: The project identifier that was not found
        """
        super().__init__(
            message=f"Project '{project_id}' not found",
            error_code="PROJECT_NOT_FOUND",
            details={"project_id": project_id},
        )


class VersionConflictError(LLTException):
    """Raised when version mismatch detected during optimistic locking."""

    def __init__(self, expected: int, received: int, project_id: str = None):
        """
        Initialize version conflict error.

        Args:
            expected: Expected version number
            received: Received version number from client
            project_id: Optional project identifier
        """
        details = {"expected": expected, "received": received}
        if project_id:
            details["project_id"] = project_id

        super().__init__(
            message=f"Version conflict: expected {expected}, got {received}",
            error_code="VERSION_CONFLICT",
            details=details,
        )


class Neo4jConnectionError(LLTException):
    """Raised when Neo4j connection fails."""

    def __init__(self, details: str):
        """
        Initialize Neo4j connection error.

        Args:
            details: Detailed error message from Neo4j driver
        """
        super().__init__(
            message="Database connection failed",
            error_code="DB_CONNECTION_ERROR",
            details={"reason": details},
        )


class Neo4jQueryError(LLTException):
    """Raised when Neo4j query execution fails."""

    def __init__(self, query: str, error: str):
        """
        Initialize Neo4j query error.

        Args:
            query: The Cypher query that failed (truncated for safety)
            error: Error message from Neo4j
        """
        # Truncate query to prevent leaking sensitive data in logs
        truncated_query = query[:100] + "..." if len(query) > 100 else query

        super().__init__(
            message="Database query failed",
            error_code="DB_QUERY_ERROR",
            details={"query": truncated_query, "error": error},
        )


class ValidationError(LLTException):
    """Raised when input validation fails."""

    def __init__(self, field: str, reason: str):
        """
        Initialize validation error.

        Args:
            field: The field that failed validation
            reason: Reason for validation failure
        """
        super().__init__(
            message=f"Validation failed for field '{field}': {reason}",
            error_code="VALIDATION_ERROR",
            details={"field": field, "reason": reason},
        )


class BatchOperationError(LLTException):
    """Raised when batch operation partially fails."""

    def __init__(self, total: int, succeeded: int, failed: int):
        """
        Initialize batch operation error.

        Args:
            total: Total number of operations attempted
            succeeded: Number of successful operations
            failed: Number of failed operations
        """
        super().__init__(
            message=f"Batch operation partially failed: {succeeded}/{total} succeeded, {failed} failed",
            error_code="BATCH_OPERATION_ERROR",
            details={"total": total, "succeeded": succeeded, "failed": failed},
        )


class EmptyFilesError(LLTException):
    """Raised when files array is empty during project initialization."""

    def __init__(self) -> None:
        """Initialize empty files error."""
        super().__init__(
            message="Files array cannot be empty. At least one file with symbols is required.",
            error_code="EMPTY_FILES",
            details={"files_count": 0},
        )


class NoSymbolsError(LLTException):
    """Raised when all files contain zero symbols."""

    def __init__(self, total_files: int) -> None:
        """
        Initialize no symbols error.

        Args:
            total_files: Number of files that had no symbols
        """
        super().__init__(
            message="All files contain no symbols. Cannot initialize empty project.",
            error_code="NO_SYMBOLS",
            details={"total_files": total_files, "files_with_symbols": 0},
        )
