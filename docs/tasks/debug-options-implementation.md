# Task: Debug Options - Async Task Failure Simulation (F1 & F2)

**Created:** 2025-11-26
**Status:** Ready for Planning & Implementation
**Priority:** High (支持前端测试)
**Estimated Time:** ~60-90 minutes

---

## 1. Task Overview (任务概述)

### Objective (目标)

为后端设置一个**可控的失败任务模拟机制**，允许前端独立、可靠地测试异步任务的失败处理流程（F1 和 F2 的错误提示、UI 状态回滚等），并为未来的自动化端到端测试铺平道路。

### Problem Statement (问题陈述)

**当前状况：**
- 前端无法可靠地测试异步任务失败场景
- 只能通过"手动停止服务"或"临时修改代码"来模拟失败
- 这些方法不可靠且难以自动化

**需求：**
- 提供一个**由后端提供的、可控的失败模拟机制**
- 前端可以通过请求参数触发失败场景
- 支持自定义错误消息，便于测试不同的 UI 显示效果

---

## 2. Why This Task Matters (为何重要)

### Supports Frontend Testing (支持前端测试)
- 前端正在进行 F1 和 F2 的集成测试
- 需要测试异步任务失败时的错误提示和 UI 状态回滚
- 这是一个关键的用户体验测试场景

### Enables E2E Automation (支持端到端自动化)
- 为未来的自动化端到端测试铺平道路
- 测试框架可以可靠地触发失败场景
- 提高测试覆盖率和可靠性

### Development Best Practice (开发最佳实践)
- 提供干净的测试工具，无需修改生产代码
- 遵循"测试即文档"的理念
- 提高开发效率

---

## 3. Technical Approach (技术方案)

### Recommended Implementation (推荐实现方式)

**方案：在现有创建任务的端点中增加一个调试参数**

这是一个**干净且对生产代码零侵入**的方案。

### Affected Endpoints (影响的端点)

1. **POST /workflows/generate-tests** (Feature 1 - Test Generation)
2. **POST /optimization/coverage** (Feature 2 - Coverage Optimization)

---

## 4. Request Body Schema Change (请求体 Schema 变更)

### Step 1: Define DebugOptions Model (定义 DebugOptions 模型)

**File:** `app/api/v1/schemas.py` (add after line 75)

```python
class DebugOptions(BaseModel):
    """Optional debug configuration for development and testing ONLY.

    WARNING: This should NEVER be used in production environments.
    """

    simulate_error: bool = Field(
        default=False,
        description="If true, immediately fail the task without executing business logic"
    )
    error_message: str = Field(
        default="Simulated error for testing purposes",
        description="Custom error message to return when simulating failure"
    )
    error_code: Optional[str] = Field(
        default="SIMULATED_ERROR",
        description="Optional error code for testing error handling"
    )
```

### Step 2: Update GenerateTestsRequest (更新 Feature 1 请求体)

**File:** `app/api/v1/schemas.py` (line 88-105, add new field)

```python
class GenerateTestsRequest(BaseModel):
    """Request payload for Feature 1 workflow: generate tests."""

    source_code: str = Field(description="The Python source code to test")
    user_description: Optional[str] = Field(
        default=None, description="Optional hint or requirement from user"
    )
    existing_test_code: Optional[str] = Field(
        default=None,
        description="Optional existing test code (context for regeneration)",
    )
    context: Optional[GenerateTestsContext] = Field(
        default=None,
        description="Extra context if triggered by Feature 3 (Regeneration)",
    )
    debug_options: Optional[DebugOptions] = Field(
        default=None,
        description="Debug configuration (For Development and Testing ONLY)"
    )
```

### Step 3: Update CoverageOptimizationRequest (更新 Feature 2 请求体)

**File:** `app/api/v1/schemas.py` (line 146-159, add new field)

```python
class CoverageOptimizationRequest(BaseModel):
    """Request payload for Feature 2 workflow: coverage optimization."""

    source_code: str = Field(description="Target source file content")
    existing_test_code: Optional[str] = Field(
        default=None, description="Current test file content"
    )
    uncovered_ranges: List[CoverageUncoveredRange] = Field(
        description="Ranges parsed by Frontend from coverage.xml"
    )
    framework: Literal["pytest", "unittest"] = Field(
        default="pytest", description="Target testing framework"
    )
    debug_options: Optional[DebugOptions] = Field(
        default=None,
        description="Debug configuration (For Development and Testing ONLY)"
    )
```

---

## 5. Backend Logic Changes (后端逻辑变更)

### Step 1: Update submit_generate_tests Handler (更新 Feature 1 端点处理器)

**File:** `app/api/v1/routes.py` (lines 203-248, modify)

```python
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
    Supports debug_options for simulating failures (development/testing only).
    """
    try:
        # Convert request to dict for task payload
        task_payload = request.model_dump()

        logger.info(
            "Received test generation request: source_code_length=%d",
            len(request.source_code),
        )

        # CHECK FOR DEBUG OPTIONS (NEW LOGIC)
        if request.debug_options and request.debug_options.simulate_error:
            logger.warning(
                "DEBUG MODE: Simulating task failure with message: %s",
                request.debug_options.error_message
            )

            # Create task in PENDING state
            task_id = await create_task(task_payload)

            # Immediately mark as FAILED with custom error
            error_dict = {
                "message": request.debug_options.error_message,
                "code": request.debug_options.error_code,
                "details": {"debug_mode": True, "simulated": True}
            }
            await update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=request.debug_options.error_message  # Will be converted to dict
            )

            # Return task_id immediately (task is already failed)
            return AsyncJobResponse(
                task_id=task_id,
                status=TaskStatus.PENDING.value,  # Return pending to match normal flow
                estimated_time_seconds=0,
            )

        # NORMAL FLOW (unchanged)
        task_id = await create_task(task_payload)
        logger.debug("Created task with ID: %s", task_id)

        # Launch background task using asyncio
        asyncio.create_task(execute_generate_tests_task(task_id, task_payload))
        logger.info(
            "Launched background task for test generation: task_id=%s", task_id
        )

        return AsyncJobResponse(
            task_id=task_id,
            status=TaskStatus.PENDING.value,
            estimated_time_seconds=30,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(
            "Failed to submit test generation task: %s", exc, exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to submit test generation task",
        ) from exc
```

### Step 2: Update submit_coverage_optimization Handler (更新 Feature 2 端点处理器)

**File:** `app/api/v1/routes.py` (lines 250-299, apply same logic)

```python
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
    Supports debug_options for simulating failures (development/testing only).
    """
    try:
        task_payload = request.model_dump()

        logger.info(
            "Received coverage optimization request: source_code_length=%d, uncovered_ranges=%d",
            len(request.source_code),
            len(request.uncovered_ranges),
        )

        # CHECK FOR DEBUG OPTIONS (NEW LOGIC)
        if request.debug_options and request.debug_options.simulate_error:
            logger.warning(
                "DEBUG MODE: Simulating task failure with message: %s",
                request.debug_options.error_message
            )

            # Create and immediately fail the task
            task_id = await create_task(task_payload)
            await update_task_status(
                task_id,
                TaskStatus.FAILED,
                error=request.debug_options.error_message
            )

            return AsyncJobResponse(
                task_id=task_id,
                status=TaskStatus.PENDING.value,
                estimated_time_seconds=0,
            )

        # NORMAL FLOW (unchanged)
        task_id = await create_task(task_payload)
        logger.debug("Created task with ID: %s", task_id)

        asyncio.create_task(execute_coverage_optimization_task(task_id, task_payload))
        logger.info(
            "Launched background task for coverage optimization: task_id=%s", task_id
        )

        return AsyncJobResponse(
            task_id=task_id,
            status=TaskStatus.PENDING.value,
            estimated_time_seconds=30,
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
```

---

## 6. OpenAPI Documentation Update (OpenAPI 文档更新)

### Update Feature 1 Endpoint Documentation

**File:** `docs/api/openapi.yaml` (lines 370-394)

在 `GenerateTestsRequest` schema 中添加 `debug_options` 字段：

```yaml
GenerateTestsRequest:
  type: object
  required:
    - source_code
  properties:
    source_code:
      type: string
      description: The Python source code to test.
    user_description:
      type: string
      description: Optional hint or requirement from user.
    existing_test_code:
      type: string
      description: Optional existing test code (context for regeneration).
    context:
      type: object
      description: Extra context if triggered by Feature 3.
    debug_options:
      type: object
      description: |
        **For Development and Testing ONLY**
        Debug configuration to simulate task failures.
        WARNING: Never use in production environments.
      properties:
        simulate_error:
          type: boolean
          default: false
          description: If true, immediately fail the task without executing business logic
        error_message:
          type: string
          default: "Simulated error for testing purposes"
          description: Custom error message to return when simulating failure
        error_code:
          type: string
          default: "SIMULATED_ERROR"
          description: Optional error code for testing error handling
```

### Update Feature 2 Endpoint Documentation

**File:** `docs/api/openapi.yaml` (lines 399-422)

在 `CoverageOptimizationRequest` schema 中添加相同的 `debug_options` 字段。

---

## 7. Testing Strategy (测试策略)

### Unit Tests (单元测试)

**File:** `tests/unit/test_feat1_api.py` (add new test)

```python
def test_submit_generate_tests_with_simulate_error():
    """Test that debug_options.simulate_error creates a failed task immediately."""
    client = TestClient(app)

    request_payload = {
        "source_code": "def example():\n    pass",
        "debug_options": {
            "simulate_error": True,
            "error_message": "Test error simulation",
            "error_code": "TEST_ERROR"
        }
    }

    # Submit task with simulate_error=True
    response = client.post("/workflows/generate-tests", json=request_payload)

    assert response.status_code == 202
    data = response.json()

    task_id = data["task_id"]
    assert task_id is not None

    # Poll task status - should be FAILED immediately (or very quickly)
    time.sleep(0.5)  # Small delay to allow task update

    status_response = client.get(f"/tasks/{task_id}")
    assert status_response.status_code == 200

    status_data = status_response.json()
    assert status_data["status"] == "failed"
    assert status_data["error"]["message"] == "Test error simulation"
    assert status_data["error"]["code"] == "TEST_ERROR"
    assert "result" not in status_data  # No result for failed tasks
```

**File:** `tests/unit/test_feat2_api.py` (add similar test for Feature 2)

```python
def test_submit_coverage_optimization_with_simulate_error():
    """Test that debug_options.simulate_error creates a failed task for F2."""
    client = TestClient(app)

    request_payload = {
        "source_code": "def add(a, b):\n    return a + b",
        "uncovered_ranges": [
            {"start_line": 1, "end_line": 2, "type": "line"}
        ],
        "debug_options": {
            "simulate_error": True,
            "error_message": "Coverage optimization test failure"
        }
    }

    response = client.post("/optimization/coverage", json=request_payload)

    assert response.status_code == 202
    task_id = response.json()["task_id"]

    # Verify task is failed
    time.sleep(0.5)
    status_response = client.get(f"/tasks/{task_id}")
    status_data = status_response.json()

    assert status_data["status"] == "failed"
    assert status_data["error"]["message"] == "Coverage optimization test failure"
```

### Manual Testing (手动测试)

```bash
# Test Feature 1 with simulated error
curl -X POST http://localhost:8886/workflows/generate-tests \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "def example():\n    pass",
    "debug_options": {
      "simulate_error": true,
      "error_message": "Simulated database connection failed"
    }
  }'

# Expected response:
# {"task_id":"<uuid>","status":"pending","estimated_time_seconds":0}

# Then poll status:
curl http://localhost:8886/tasks/<task_id> | jq

# Expected response:
# {
#   "task_id": "<uuid>",
#   "status": "failed",
#   "error": {
#     "message": "Simulated database connection failed",
#     "code": "SIMULATED_ERROR",
#     "details": {"debug_mode": true, "simulated": true}
#   }
# }
```

---

## 8. Implementation Checklist (实现检查清单)

### Code Changes (代码更改)
- [ ] 定义 `DebugOptions` schema 在 `app/api/v1/schemas.py`
- [ ] 更新 `GenerateTestsRequest` 添加 `debug_options` 字段
- [ ] 更新 `CoverageOptimizationRequest` 添加 `debug_options` 字段
- [ ] 修改 `submit_generate_tests()` 处理 debug_options
- [ ] 修改 `submit_coverage_optimization()` 处理 debug_options

### Documentation (文档)
- [ ] 更新 OpenAPI spec - Feature 1 endpoint
- [ ] 更新 OpenAPI spec - Feature 2 endpoint
- [ ] 添加明确的警告："For Development and Testing ONLY"

### Testing (测试)
- [ ] 添加 Feature 1 单元测试（simulate_error）
- [ ] 添加 Feature 2 单元测试（simulate_error）
- [ ] 运行所有测试确保无回归
- [ ] 手动测试两个端点的 debug_options

### Deployment (部署)
- [ ] 重新构建 Docker：`docker-compose build api`
- [ ] 重启容器：`docker-compose up -d`
- [ ] 验证日志中的 DEBUG MODE 警告
- [ ] 通知前端团队新功能可用

---

## 9. Success Criteria (成功标准)

### Functional Requirements (功能需求)
✅ 当 `debug_options.simulate_error=true` 时，任务立即失败
✅ 不调用 LLM 或执行正常业务逻辑
✅ 使用 `debug_options.error_message` 填充 error 对象
✅ 返回的 task_id 可用于轮询状态
✅ 轮询结果显示 status="failed" 和自定义错误消息

### Non-Functional Requirements (非功能需求)
✅ 对生产代码零侵入（仅在 debug_options 存在时触发）
✅ 明确标记为"仅用于开发和测试"
✅ 不影响正常请求的性能
✅ 日志中记录 DEBUG MODE 警告

---

## 10. Security Considerations (安全考虑)

### Development/Testing Only (仅限开发/测试)

⚠️ **重要安全提示：**

1. **不应在生产环境中使用**
   - 这是一个测试工具，不应暴露给最终用户
   - 考虑添加环境变量控制（如 `ENABLE_DEBUG_OPTIONS`）

2. **可选的环境保护**（未来增强）：
   ```python
   # In routes.py
   if request.debug_options and not settings.enable_debug_options:
       raise HTTPException(
           status_code=403,
           detail="Debug options are disabled in this environment"
       )
   ```

3. **日志审计**：
   - 所有 debug_options 使用都会记录警告日志
   - 便于审计和监控潜在滥用

---

## 11. Future Enhancements (未来增强)

### Phase 2 功能（可选）

1. **更多模拟场景**：
   ```python
   class DebugOptions(BaseModel):
       simulate_error: bool = False
       simulate_timeout: bool = False  # 模拟超时
       simulate_delay_seconds: int = 0  # 模拟延迟
       error_message: str = "Simulated error"
   ```

2. **环境变量控制**：
   ```python
   # app/config.py
   enable_debug_options: bool = Field(
       default=True,
       description="Enable debug options (should be False in production)"
   )
   ```

3. **随机失败率**：
   ```python
   class DebugOptions(BaseModel):
       failure_rate: float = Field(
           default=0.0,
           ge=0.0,
           le=1.0,
           description="Random failure probability (0.0-1.0)"
       )
   ```

---

## 12. Critical Files Summary (关键文件摘要)

| File | Action | Lines | Priority |
|------|--------|-------|----------|
| `app/api/v1/schemas.py` | ADD DebugOptions model | After 75 | **HIGH** |
| `app/api/v1/schemas.py` | UPDATE GenerateTestsRequest | 88-105 | **HIGH** |
| `app/api/v1/schemas.py` | UPDATE CoverageOptimizationRequest | 146-159 | **HIGH** |
| `app/api/v1/routes.py` | MODIFY submit_generate_tests | 203-248 | **HIGH** |
| `app/api/v1/routes.py` | MODIFY submit_coverage_optimization | 250-299 | **HIGH** |
| `tests/unit/test_feat1_api.py` | ADD test | New | MEDIUM |
| `tests/unit/test_feat2_api.py` | ADD test | New | MEDIUM |
| `docs/api/openapi.yaml` | UPDATE GenerateTestsRequest | 874-898 | MEDIUM |
| `docs/api/openapi.yaml` | UPDATE CoverageOptimizationRequest | 911-940 | MEDIUM |

---

## 13. Example Request/Response (请求/响应示例)

### Request with Debug Options (带 debug_options 的请求)

```json
POST /workflows/generate-tests

{
  "source_code": "def calculate(x, y):\n    return x + y",
  "user_description": "Test the calculate function",
  "debug_options": {
    "simulate_error": true,
    "error_message": "Simulated database connection failed",
    "error_code": "DB_CONNECTION_ERROR"
  }
}
```

### Immediate Response (立即响应)

```json
HTTP 202 Accepted

{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "estimated_time_seconds": 0
}
```

### Poll Status Response (轮询状态响应)

```json
GET /tasks/550e8400-e29b-41d4-a716-446655440000

HTTP 200 OK

{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "created_at": "2025-11-26T10:30:00Z",
  "error": {
    "message": "Simulated database connection failed",
    "code": "DB_CONNECTION_ERROR",
    "details": {
      "debug_mode": true,
      "simulated": true
    }
  }
}
```

---

## 14. Timeline (时间线)

| Phase | Task | Time |
|-------|------|------|
| 1 | 定义 DebugOptions schema | 10 min |
| 2 | 更新两个请求体 schema | 10 min |
| 3 | 修改 Feature 1 端点处理器 | 15 min |
| 4 | 修改 Feature 2 端点处理器 | 15 min |
| 5 | 添加单元测试 | 20 min |
| 6 | 更新 OpenAPI 文档 | 15 min |
| 7 | 部署和手动测试 | 15 min |

**总计时间：** ~90 minutes

---

## 15. Next Steps (下一步)

1. 在新的会话中继续实施此任务
2. 参考本文档进行实现
3. 完成后通知前端团队
4. 提供使用示例和文档

---

**Last Updated:** 2025-11-26
**Version:** 1.0
**Status:** Ready for Implementation
