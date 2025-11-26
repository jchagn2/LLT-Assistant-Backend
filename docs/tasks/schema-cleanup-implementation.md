# Task: Schema Cleanup for Async Task API (F1 & F2)

**Created:** 2025-11-26
**Status:** Ready for Implementation
**Priority:** Medium
**Estimated Time:** ~55 minutes

---

## 1. Task Overview

### Objective (目标)

优化异步任务 `/tasks/{task_id}` 的 API 响应，在 `pending` 或 `processing` 状态时，**完全移除** `result` 和 `error` 字段，而不是返回 `null`。

### Current Problem (当前问题)

**现状：** 尽管已有 `@model_serializer` 自定义序列化器，API 仍然返回：

```json
{
  "task_id": "uuid",
  "status": "pending",
  "created_at": "2025-11-26T...",
  "result": null,    ← 不应该出现
  "error": null      ← 不应该出现
}
```

**期望行为：**

```json
{
  "task_id": "uuid",
  "status": "pending",
  "created_at": "2025-11-26T..."
}
```

---

## 2. Why This Task Matters (为何选择此任务)

### Closes F1 Loop (闭环 F1 的发现)
- 这是在 **F1 测试中明确发现**的一个 API 质量问题
- 完成它可以为 F1 的优化画上一个句号

### Supports F2 Development (支持 F2 的开发)
- 前端正在进行 **F2 的集成测试**
- 该测试同样依赖于这个异步任务接口
- 现在进行优化，可以确保 F2 从一开始就使用最规范、最干净的 API

### Lightweight and Independent (轻量且独立)
- 这是一个清晰、独立的 API 优化任务
- 工作量适中（~55分钟）
- 非常适合在完成一个大功能后进行

---

## 3. Technical Context (技术背景)

### Affected Endpoints (影响的端点)

1. **GET /tasks/{task_id}** - 任务状态轮询端点
   - Feature 1 (Test Generation) 和 Feature 2 (Coverage Optimization) 都使用此端点
   - 前端通过轮询此端点获取异步任务结果

### Current Implementation (当前实现)

**File:** `app/api/v1/schemas.py` (lines 202-224)

```python
class TaskStatusResponse(BaseModel):
    """Task status response for polling endpoints."""

    task_id: str
    status: Literal["pending", "processing", "completed", "failed"]
    created_at: Optional[str] = None
    result: Optional[Union[GenerateTestsResult, CoverageOptimizationResult]] = None
    error: Optional[TaskError] = None

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Custom serializer to exclude null result/error fields."""
        data: Dict[str, Any] = {
            "task_id": self.task_id,
            "status": self.status,
        }

        if self.created_at is not None:
            data["created_at"] = self.created_at

        # Only include result/error for completed/failed
        if self.status == "completed" and self.result is not None:
            data["result"] = self.result
        if self.status == "failed" and self.error is not None:
            data["error"] = self.error

        return data
```

**问题：** `@model_serializer` 存在但未生效

---

## 4. Root Cause Analysis (根本原因分析)

### Possible Causes (可能的原因，按可能性排序)

1. **FastAPI Bypassing Custom Serializer** (HIGH likelihood)
   - FastAPI 的 `response_model` 可能使用默认 Pydantic 序列化重新序列化
   - `@model_serializer` 被调用，但 FastAPI 之后又添加了 None 字段
   - **解决方案：** 使用 `response_model_exclude_none=True`

2. **Union Type Re-Serialization** (MEDIUM likelihood)
   - `result: Optional[Union[GenerateTestsResult, CoverageOptimizationResult]]`
   - FastAPI 可能重新序列化 Union 类型，丢失自定义序列化
   - **解决方案：** 在 serializer 中将嵌套模型转换为 dict

3. **Docker Deployment Not Updated** (HIGH likelihood but easy fix)
   - 代码更改可能未反映在运行的容器中
   - **解决方案：** 始终执行 `docker-compose build api && docker-compose up -d`

---

## 5. Implementation Plan (实现计划)

### Phase 1: Primary Fix - Add FastAPI Parameter (5 min)

**File:** `app/api/v1/routes.py` (line 301)

```python
# BEFORE
@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str) -> TaskStatusResponse | StarletteResponse:

# AFTER
@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    response_model_exclude_none=True  # ← 添加这个参数
)
async def get_task_status(task_id: str) -> TaskStatusResponse | StarletteResponse:
```

**理由：**
- 与 `@model_serializer` 形成双重保障
- FastAPI 原生特性，保证有效
- 单行更改，零风险

---

### Phase 2: Enhance Custom Serializer (10 min)

**File:** `app/api/v1/schemas.py` (lines 202-224)

**增强：** 确保嵌套的 Pydantic 模型序列化为字典

```python
@model_serializer
def serialize_model(self) -> Dict[str, Any]:
    """Custom serializer to exclude null result/error fields."""
    data: Dict[str, Any] = {
        "task_id": self.task_id,
        "status": self.status,
    }

    if self.created_at is not None:
        data["created_at"] = self.created_at

    # Only include result/error for completed/failed
    if self.status == "completed" and self.result is not None:
        # 将嵌套模型序列化为 dict（正确处理 Union 类型）
        data["result"] = (
            self.result.model_dump(mode='json')
            if hasattr(self.result, 'model_dump')
            else self.result
        )
    if self.status == "failed" and self.error is not None:
        # 将 error 序列化为 dict
        data["error"] = (
            self.error.model_dump(mode='json')
            if hasattr(self.error, 'model_dump')
            else self.error
        )

    return data
```

**理由：**
- 确保 Union 类型正确序列化为字典
- 防止 FastAPI 重新序列化嵌套的 Pydantic 模型
- 保持类型安全的同时避免序列化问题

---

### Phase 3: Add Integration Test (10 min)

**File:** `tests/unit/test_feat1_api.py` (add after line 240)

```python
def test_get_task_status_json_response_excludes_null_fields_for_pending():
    """Test JSON response STRUCTURE excludes null fields (not just model)."""
    client = TestClient(app)

    # Create pending task
    task_id = str(uuid.uuid4())
    asyncio.run(create_task({"test": "data"}))

    # Get task status
    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200

    # CRITICAL: 验证 JSON 结构，而不仅仅是 Pydantic 模型
    json_data = response.json()

    assert "task_id" in json_data
    assert "status" in json_data
    assert json_data["status"] == "pending"

    # 字段必须不存在（甚至不是 null）
    assert "result" not in json_data, "result field should not exist for pending tasks"
    assert "error" not in json_data, "error field should not exist for pending tasks"
```

---

### Phase 4: Update Tests for Feature 2 (5 min)

**File:** `tests/unit/test_feat2_api.py` (add after line 206)

```python
def test_get_task_status_json_response_excludes_null_fields_for_processing():
    """Test JSON response excludes null fields for processing status."""
    client = TestClient(app)

    # Create processing task
    task_id = str(uuid.uuid4())
    asyncio.run(create_task({"test": "data"}))
    asyncio.run(update_task_status(task_id, TaskStatus.PROCESSING))

    # Get task status
    response = client.get(f"/tasks/{task_id}")

    assert response.status_code == 200
    json_data = response.json()

    assert json_data["status"] == "processing"
    assert "result" not in json_data
    assert "error" not in json_data
```

---

### Phase 5: Update OpenAPI Specification (10 min)

**File:** `docs/api/openapi.yaml` (lines 587-599)

更新 `TaskStatusResponse` schema 的字段描述：

```yaml
result:
  oneOf:
    - $ref: '#/components/schemas/GenerateTestsResult'
    - $ref: '#/components/schemas/CoverageOptimizationResult'
  description: |
    Task result (only present when status=completed).
    This field is EXCLUDED (not present) for pending/processing status.
    Never returned as null.

error:
  $ref: '#/components/schemas/TaskError'
  description: |
    Error details (only present when status=failed).
    This field is EXCLUDED (not present) for pending/processing/completed status.
    Never returned as null.
```

---

### Phase 6: Deployment and Verification (15 min)

#### Step 6.1: Rebuild Docker Containers
```bash
docker-compose build api
docker-compose up -d
```

#### Step 6.2: Manual Testing

```bash
# Test 1: 提交异步任务（Feature 2）
curl -X POST http://localhost:8886/optimization/coverage \
  -H "Content-Type: application/json" \
  -d '{"source_code":"def add(a,b):\n    return a+b","uncovered_ranges":[{"start_line":1,"end_line":2,"type":"line"}]}'

# 应该返回: {"task_id":"uuid","status":"pending","estimated_time_seconds":30}

# Test 2: 立即获取任务状态（应该是 pending）
TASK_ID="<上面返回的 task_id>"
curl http://localhost:8886/tasks/$TASK_ID | jq

# 期望：没有 "result" 或 "error" 字段

# Test 3: 等待 5 秒后再次检查（可能是 processing）
sleep 5
curl http://localhost:8886/tasks/$TASK_ID | jq

# 期望：如果仍在处理中，仍然没有 "result" 或 "error" 字段

# Test 4: 等待完成
sleep 10
curl http://localhost:8886/tasks/$TASK_ID | jq

# 期望："result" 字段存在，"error" 字段不存在
```

---

## 6. Implementation Checklist (实现检查清单)

### Code Changes (代码更改)
- [ ] 添加 `response_model_exclude_none=True` 到 `app/api/v1/routes.py:301`
- [ ] 增强 `@model_serializer` 在 `app/api/v1/schemas.py:202-224`
- [ ] 添加 JSON 响应集成测试到 `test_feat1_api.py`
- [ ] 添加 JSON 响应集成测试到 `test_feat2_api.py`

### Documentation (文档)
- [ ] 更新 OpenAPI spec 在 `docs/api/openapi.yaml:587-599`
- [ ] 明确记录字段排除行为

### Testing (测试)
- [ ] 运行单元测试：`pytest tests/unit/test_feat1_api.py tests/unit/test_feat2_api.py -v`
- [ ] 验证现有测试仍然通过（4 个关于 null 字段排除的测试）
- [ ] 运行新的集成测试
- [ ] 对所有任务状态进行手动 curl 测试

### Deployment (部署)
- [ ] 重新构建 Docker：`docker-compose build api`
- [ ] 重启容器：`docker-compose up -d`
- [ ] 验证日志：`docker logs llt-assistant-backend-api-1 --tail 50`
- [ ] 使用 curl 测试实时端点

---

## 7. Critical Files Summary (关键文件摘要)

| File | Action | Lines | Priority |
|------|--------|-------|----------|
| `app/api/v1/routes.py` | ADD parameter | 301 | **HIGH** |
| `app/api/v1/schemas.py` | ENHANCE serializer | 202-224 | **HIGH** |
| `tests/unit/test_feat1_api.py` | ADD test | After 240 | MEDIUM |
| `tests/unit/test_feat2_api.py` | ADD test | After 206 | MEDIUM |
| `docs/api/openapi.yaml` | UPDATE docs | 587-599 | MEDIUM |

---

## 8. Success Criteria (成功标准)

### Functional Requirements (功能需求)
✅ Pending 状态：`result` 和 `error` 字段**不存在**于 JSON 响应中
✅ Processing 状态：`result` 和 `error` 字段**不存在**于 JSON 响应中
✅ Completed 状态：`result` 字段存在，`error` 字段不存在
✅ Failed 状态：`error` 字段存在，`result` 字段不存在

### Technical Requirements (技术需求)
✅ 所有现有测试继续通过
✅ 新的集成测试验证 JSON 响应结构
✅ OpenAPI spec 准确记录字段排除行为
✅ API 行为无破坏性更改

### Non-Functional Requirements (非功能需求)
✅ 零性能影响
✅ 向后兼容（客户端已经处理缺失字段）
✅ 为前端开发人员提供清晰的文档

---

## 9. Risk Assessment (风险评估)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Docker 未重新构建 | HIGH | HIGH | 明确记录重建步骤 |
| FastAPI 序列化边缘情况 | MEDIUM | MEDIUM | 使用 `response_model_exclude_none=True` |
| Union 类型序列化问题 | LOW | MEDIUM | 将嵌套模型序列化为字典 |
| 破坏性更改 | VERY LOW | HIGH | 字段移除是向后兼容的 |

**总体风险等级：** LOW

---

## 10. Rollback Plan (回滚计划)

如果部署后出现问题：

1. **代码回滚（如果需要）：**
   ```bash
   git revert <commit-hash>
   docker-compose build api
   docker-compose up -d
   ```

2. **无破坏性更改：** 移除 null 字段是向后兼容的 - 前端代码已经处理可选字段

3. **快速恢复：** 更改很小且隔离在 2 个文件中

---

## 11. Timeline (时间线)

| Phase | Task | Time |
|-------|------|------|
| 1 | 添加 FastAPI 参数 | 5 min |
| 2 | 增强序列化器 | 10 min |
| 3 | 添加集成测试 | 10 min |
| 4 | 更新 F2 测试 | 5 min |
| 5 | 更新 OpenAPI spec | 10 min |
| 6 | 部署和验证 | 15 min |

**总计时间：** ~55 minutes

---

## 12. References (参考资料)

- **Detailed Plan File:** `/Users/efan404/.claude/plans/tranquil-conjuring-wreath.md`
- **Related Issue:** Discovered during F1 testing
- **Frontend Dependency:** F2 integration testing relies on this fix

---

## 13. Next Steps (下一步)

1. 在新的会话中继续实施此任务
2. 参考本文档和详细计划文件
3. 按照 Phase 1-6 的顺序执行
4. 完成后更新此文档的状态为 "Completed"

---

**Last Updated:** 2025-11-26
**Version:** 1.0
**Status:** Ready for Implementation
