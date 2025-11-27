"""Unit tests for async task management utilities.

Tests verify task creation, status updates, and error handling.
"""

import pytest

from app.core.tasks.tasks import (
    TaskStatus,
    create_task,
    get_task,
    update_task_status,
)


@pytest.mark.asyncio
async def test_update_task_status_stores_error_as_dict():
    """Verify errors are stored as dicts matching TaskError schema."""
    # Create a test task
    task_id = await create_task({"test": "data"})

    # Update task status with error string
    await update_task_status(task_id, TaskStatus.FAILED, error="Test error message")

    # Retrieve task and verify error format
    task = await get_task(task_id)

    # Verify error is dict, not string
    assert isinstance(task["error"], dict), "Error should be stored as dict, not string"
    assert (
        task["error"]["message"] == "Test error message"
    ), "Error message should match input"
    assert task["error"]["code"] is None, "Error code should be None by default"
    assert task["error"]["details"] is None, "Error details should be None by default"


@pytest.mark.asyncio
async def test_update_task_status_none_error():
    """Verify None errors are handled correctly."""
    # Create a test task
    task_id = await create_task({"test": "data"})

    # Update task status with successful completion (no error)
    await update_task_status(
        task_id, TaskStatus.COMPLETED, result={"generated_code": "test code"}
    )

    # Retrieve task and verify error is None
    task = await get_task(task_id)
    assert task["error"] is None, "Error should be None for successful tasks"
    assert task["result"] == {
        "generated_code": "test code"
    }, "Result should be stored correctly"


@pytest.mark.asyncio
async def test_update_task_status_with_exception_object():
    """Verify exception objects are converted to string before storage."""
    # Create a test task
    task_id = await create_task({"test": "data"})

    # Simulate what happens in execute_generate_tests_task
    # when an exception is caught: str(exc)
    try:
        raise ValueError("Simulating a backend error")
    except Exception as exc:
        await update_task_status(
            task_id,
            TaskStatus.FAILED,
            error=str(exc),  # Convert to string as done in production code
        )

    # Retrieve task and verify error format
    task = await get_task(task_id)

    # Verify error is dict with correct message
    assert isinstance(task["error"], dict)
    assert task["error"]["message"] == "Simulating a backend error"
    assert task["error"]["code"] is None
    assert task["error"]["details"] is None
