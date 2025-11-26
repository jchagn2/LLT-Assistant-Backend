# Fix F1 Async Task "Crash-on-Error" Bug

**Priority:** 🔴 CRITICAL - Blocking Frontend Testing
**Estimated Time:** 1.5 hours
**Status:** Ready for Implementation

---

## Problem Summary

When async tasks fail, the backend stores errors as **strings** in Redis, but the API expects **structured TaskError objects**. This mismatch causes Pydantic ValidationError, crashing the FastAPI service when clients poll for failed task status.

**Current Flow (Broken):**
```
Exception → str(exc) → Redis → API tries to read → ValidationError → Service Crash
```

**Expected Flow (Fixed):**
```
Exception → TaskError dict → Redis → API reads → 200 OK with error object
```

---

## Delivery Plan

### Change 1: Fix Error Storage (Primary)
**File:** `app/core/tasks/tasks.py` (lines 166-191)
**Function:** `update_task_status`

**Action:** Transform error strings into TaskError-compatible dictionaries before storing.

```python
# Current (lines 180-181)
task["result"] = result
task["error"] = error  # ❌ Stores raw string

# Fixed (after line 180)
task["result"] = result

# Transform error string into TaskError-compatible dict
if error is not None:
    task["error"] = {
        "message": str(error),
        "code": None,
        "details": None
    }
else:
    task["error"] = None
```

---

### Change 2: Update Route Handler (Secondary)
**File:** `app/api/v1/routes.py` (lines 326-331)
**Function:** `get_task_status`

**Action:** Add backward compatibility to handle both dict and legacy string formats with defensive programming.

```python
# Current (lines 326-331)
error = None
if task_data.get("error"):
    error = TaskError(
        message=task_data["error"],  # ❌ Assumes string
        code=None,
    )

# Fixed (with backward compatibility and defensive programming)
error = None
if task_data.get("error"):
    error_data = task_data["error"]
    # Handle both dict (new) and string (legacy) formats
    if isinstance(error_data, dict):
        # Extract fields explicitly to avoid issues with polluted data
        error = TaskError(
            message=error_data.get("message", "Unknown error"),
            code=error_data.get("code"),
            details=error_data.get("details")
        )
    else:
        # Legacy string format fallback
        error = TaskError(
            message=str(error_data),
            code=None,
            details=None
        )
```

---

## Implementation Steps

1. ✅ **Read current implementation** (tasks.py, routes.py, schemas.py)
2. **Modify `update_task_status`** - Add error dict transformation
3. **Update route handler** - Add backward compatibility
4. **Add unit tests** - Verify error storage format
5. **Add integration test** - E2E error flow verification
6. **Manual testing** - Inject ValueError and verify no crash
7. **Commit changes** - Message: `fix(tasks): store async task errors as structured dicts matching TaskError schema`

---

## Testing Strategy

### Unit Test (New)
**File:** `tests/unit/test_tasks.py`

```python
async def test_update_task_status_stores_error_as_dict():
    """Verify errors are stored as dicts matching TaskError schema."""
    task_id = await create_task({"test": "data"})

    await update_task_status(
        task_id,
        TaskStatus.FAILED,
        error="Test error message"
    )

    task = await get_task(task_id)

    # Verify error is dict, not string
    assert isinstance(task["error"], dict)
    assert task["error"]["message"] == "Test error message"
    assert task["error"]["code"] is None
    assert task["error"]["details"] is None
```

### Integration Test (New)
**File:** `tests/unit/test_feat1_api.py`

```python
async def test_generate_tests_task_failure_returns_structured_error():
    """
    E2E test: Verify failed tasks return structured error in API response.

    This test ensures that when async tasks fail, the error is properly
    stored as a structured dict and returned correctly via the API.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    import time

    client = TestClient(app)

    # Create task with invalid payload to trigger error
    response = client.post("/workflows/generate-tests", json={
        "source_code": "",  # Empty source code should trigger error
        "test_framework": "pytest"
    })

    assert response.status_code in [200, 202]  # Task created
    task_id = response.json()["task_id"]

    # Poll until task fails (max 10 seconds)
    for _ in range(10):
        time.sleep(1)
        status_response = client.get(f"/tasks/{task_id}")

        # Service must NOT crash - always return 200
        assert status_response.status_code == 200

        data = status_response.json()
        if data["status"] == "failed":
            # Verify error is structured object
            assert "error" in data
            assert isinstance(data["error"], dict)
            assert "message" in data["error"]
            assert isinstance(data["error"]["message"], str)
            assert data["error"]["code"] is None or isinstance(data["error"]["code"], str)
            return

    pytest.fail("Task did not fail within timeout")
```

### Manual Verification
1. Inject error: Add `raise ValueError("Simulating a backend error")` after line 213 in `execute_generate_tests_task`
2. Trigger task: `POST /workflows/generate-tests`
3. Poll status: `GET /tasks/{task_id}` every 2 seconds
4. **Expected:** All polling returns 200 OK with structured error field
5. **Expected:** No service crash or timeouts

---

## Success Criteria

✅ Service does NOT crash when tasks fail
✅ Error responses match TaskError schema: `{"message": str, "code": str|None, "details": dict|None}`
✅ Polling returns 200 OK with structured error field
✅ Redis stores errors as structured dicts
✅ Existing tests continue passing
✅ Manual reproduction scenario works correctly

---

## Risk Assessment

**Overall Risk:** Low

- ✅ Isolated change in error handling logic
- ✅ Backward compatibility ensures no breaking changes
- ✅ Comprehensive testing strategy (unit + integration)
- ✅ Defensive programming prevents polluted data issues
- ✅ No database schema changes
- ✅ No API contract changes (just fixes incorrect behavior)

## Code Review Improvements Applied

✅ **Added explicit `details=None` in legacy fallback** - Maintains consistency
✅ **Defensive dict unpacking** - Uses `.get()` to avoid exceptions from polluted Redis data
✅ **Integration test added** - E2E verification of error flow
✅ **Line numbers verified** - Confirmed against current codebase (tasks.py:166-191, routes.py:326-331)

---

## Files to Modify

| File | Lines | Changes | Risk |
|------|-------|---------|------|
| `app/core/tasks/tasks.py` | 166-191 | Add error dict transformation | Low |
| `app/api/v1/routes.py` | 326-331 | Add backward compatibility | Low |
| `tests/unit/test_tasks.py` | New | Add unit tests | None |

**No changes needed:**
- ✅ `app/api/v1/schemas.py` - TaskError schema already correct
- ✅ `execute_generate_tests_task` (line 236) - Already calls `update_task_status`
- ✅ `execute_coverage_optimization_task` (line 377) - Already calls `update_task_status`

---

## Next Steps

1. Exit plan mode
2. Implement changes in `tasks.py`
3. Update route handler in `routes.py`
4. Add unit tests
5. Run integration tests
6. Perform manual verification
7. Commit and notify frontend team

---

**Ready for Implementation** ✅
