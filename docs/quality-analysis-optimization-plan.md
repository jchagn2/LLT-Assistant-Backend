# Quality Analysis Performance & Observability Optimization Plan

**Created:** 2025-11-26
**Status:** Approved - Ready for Implementation
**Estimated Duration:** 3 weeks (Phase 1a + Phase 2: 2 weeks, Phase 1b: 1 week)

## Executive Summary

### Problem Statement
- **Current Situation:** Quality Analysis endpoint blocks for 5+ minutes when analyzing 38 files
- **Root Cause:** 91 sequential LLM API calls @ 0.5s each = 45+ seconds total
- **User Impact:** Frontend timeout at 30s causes "Cannot connect to LLT backend" error
- **Backend Status:** No errors logged - system is working correctly but too slow

### Solution Approach: Hybrid Strategy (Two-Phase Implementation)

**Phase 1a (Weeks 1-2):** Parallelize LLM calls for immediate 10x speedup
**Phase 1b (Week 3):** Add async task pattern for unlimited scalability
**Phase 2 (Concurrent with 1a):** Unified logging and observability improvements

### Expected Outcomes
- Response time: 45s → 5s (Phase 1a) → Unlimited batch size (Phase 1b)
- Frontend timeout rate: 100% → 0%
- Complete request lifecycle logging with metrics
- Backwards compatible API migration strategy

---

## Phase 1a: LLM Call Parallelization (Weeks 1-2)

### Goal
Reduce Quality Analysis execution time by 90% through concurrent LLM requests while maintaining synchronous API contract.

### Architecture Changes

**Current (Sequential Execution):**
```
for file in 38_files:
    for func in uncertain_functions:
        await llm_call_1()  # Blocks 0.5s
        await llm_call_2()  # Blocks 0.5s
# Total: 91 calls × 0.5s = 45+ seconds
```

**New (Parallel with Semaphore):**
```
semaphore = asyncio.Semaphore(10)  # Max 10 concurrent
tasks = [llm_call(func) for all uncertain_functions]
await asyncio.gather(*tasks)  # Parallel execution
# Total: 91 calls ÷ 10 concurrent ≈ 5 seconds
```

### Implementation Tasks

#### Task 1.1: Add Semaphore-Based Parallelization to HybridStrategy
**File:** `app/core/analysis/strategies.py`

**Changes:**
1. Add `asyncio.Semaphore(10)` to control concurrent LLM calls
2. Modify `analyze()` method to batch uncertain functions across all files
3. Replace nested sequential loops with `asyncio.gather()`
4. Add throttling wrapper: `_analyze_function_with_llm_throttled()`

**Key Code Pattern:**
```python
class HybridStrategy:
    def __init__(self, ...):
        self.llm_semaphore = asyncio.Semaphore(10)  # Configurable

    async def _analyze_function_with_llm_throttled(self, test_func, parsed_file, llm_analyzer):
        async with self.llm_semaphore:
            return await self._analyze_function_with_llm(test_func, parsed_file, llm_analyzer)

    async def analyze(self, parsed_files, rule_engine, llm_analyzer):
        # Phase 1: Rules (sequential, fast)
        # ...

        # Phase 2: Collect all uncertain functions
        all_uncertain_tasks = []
        for parsed_file in parsed_files:
            uncertain_functions = detector.identify_uncertain_cases(parsed_file)
            for test_func in uncertain_functions:
                task = self._analyze_function_with_llm_throttled(test_func, parsed_file, llm_analyzer)
                all_uncertain_tasks.append(task)

        # Execute in parallel with semaphore throttling
        logger.info("Executing %d LLM calls in parallel (max 10 concurrent)", len(all_uncertain_tasks))
        results = await asyncio.gather(*all_uncertain_tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error("LLM analysis failed: %s", result)
            else:
                all_issues.extend(result)
```

**Testing:**
- Unit: Mock LLM client, verify semaphore limits concurrent calls to 10
- Integration: Test with 50 uncertain cases, verify completion in < 10s
- Error handling: Ensure one failed LLM call doesn't block others

**Acceptance Criteria:**
- [ ] 38 files complete in < 15s (currently 45s+)
- [ ] Semaphore correctly limits concurrent calls to 10
- [ ] Failed LLM calls logged but don't block other calls
- [ ] No regression in issue detection accuracy

---

#### Task 1.2: Apply Parallelization to LLMOnlyStrategy
**File:** `app/core/analysis/strategies.py`

**Changes:**
1. Apply same semaphore pattern to `LLMOnlyStrategy.analyze()`
2. Batch all test functions and execute with `asyncio.gather()`

**Testing:**
- Same as Task 1.1 but for LLM-only mode
- Verify both hybrid and LLM-only modes benefit from parallelization

**Acceptance Criteria:**
- [ ] LLM-only mode shows similar speedup (5-10x)
- [ ] Code pattern consistent with HybridStrategy

---

#### Task 1.3: Add Configurable Concurrency Limit
**File:** `app/config.py`

**Changes:**
```python
class Settings(BaseSettings):
    # ... existing fields ...

    # LLM Parallelization
    llm_max_concurrent_calls: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum concurrent LLM API calls (balance speed vs rate limits)"
    )
```

**File:** `app/core/constants.py`

**Changes:**
```python
# LLM Concurrency
MAX_CONCURRENT_LLM_CALLS = 10  # Default semaphore limit
```

**Testing:**
- Verify environment variable `LLM_MAX_CONCURRENT_CALLS=5` works
- Test with different limits: 1 (sequential), 5, 10, 20

**Acceptance Criteria:**
- [ ] Concurrency limit configurable via environment variable
- [ ] Default value is 10 (balanced performance)

---

#### Task 1.4: Add Progress Logging for Parallel Execution
**File:** `app/core/analysis/strategies.py`

**Changes:**
```python
async def analyze(self, parsed_files, rule_engine, llm_analyzer):
    # ... Phase 1: Rules ...

    # Phase 2: LLM analysis
    logger.info("Starting parallel LLM analysis: total_tasks=%d, max_concurrent=%d",
                len(all_uncertain_tasks), self.llm_semaphore._value)

    start_time = time.time()
    results = await asyncio.gather(*all_uncertain_tasks, return_exceptions=True)
    elapsed_ms = int((time.time() - start_time) * 1000)

    successful = sum(1 for r in results if not isinstance(r, Exception))
    failed = len(results) - successful

    logger.info("Parallel LLM analysis completed: successful=%d, failed=%d, elapsed_ms=%d",
                successful, failed, elapsed_ms)
```

**Acceptance Criteria:**
- [ ] Logs show total tasks, concurrent limit
- [ ] Logs show success/failure counts and timing
- [ ] Log format matches existing conventions

---

### Phase 1a Rollout Strategy
1. Deploy to staging environment
2. Run performance benchmarks (before/after comparison)
3. Verify no regression in analysis quality (same issues detected)
4. Deploy to production (low risk - no API changes)
5. Monitor logs for:
   - Execution time reduction (target: 70%+)
   - LLM API rate limit errors (429s)
   - Error rates (should be < 1%)

---

## Phase 1b: Async Task Pattern (Week 3)

### Goal
Convert Quality Analysis to async task pattern for unlimited scalability and improved UX.

### Architecture Changes

**Current (Synchronous):**
```
POST /quality/analyze
  ↓ [blocks 5-15s]
  ↓
Response with results
```

**New (Asynchronous):**
```
POST /quality/analyze-async
  ↓ [returns immediately]
  ↓
202 Accepted + task_id
  ↓
Client polls GET /tasks/{task_id}
  ↓
pending → processing → completed (with results)
```

### Implementation Tasks

#### Task 2.1: Create Quality Analysis Task Executor
**File:** `app/core/tasks/tasks.py`

**Changes:**
Follow the exact pattern of `execute_coverage_optimization_task()`:

```python
async def execute_quality_analysis_task(task_id: str, payload: Dict[str, Any]) -> None:
    """Execute quality analysis task asynchronously."""
    try:
        logger.debug("Starting quality analysis task: task_id=%s", task_id)
        await update_task_status(task_id, TaskStatus.PROCESSING)

        # Extract request fields
        files = [FileInput(**f) for f in payload.get("files", [])]
        mode = payload.get("mode", "hybrid")

        # Execute analysis with parallelization from Phase 1a
        async with get_quality_service_context() as quality_service:
            result = await quality_service.analyze_batch(files=files, mode=mode)

        # Convert result to dict for task storage
        result_dict = result.model_dump()

        await update_task_status(task_id, TaskStatus.COMPLETED, result=result_dict)
        logger.info("Quality analysis task completed: task_id=%s, issues=%d",
                   task_id, len(result.issues))

    except Exception as exc:
        logger.error("Quality analysis task failed: task_id=%s, error=%s",
                    task_id, exc, exc_info=True)
        await update_task_status(task_id, TaskStatus.FAILED, error=str(exc))
```

**Testing:**
- Unit: Mock QualityAnalysisService, verify task lifecycle transitions
- Integration: Submit task, poll until completion, verify results match synchronous endpoint
- Error handling: Simulate service failure, verify task marked FAILED with error message

**Acceptance Criteria:**
- [ ] Task executor follows existing pattern (coverage optimization)
- [ ] Task status transitions: PENDING → PROCESSING → COMPLETED/FAILED
- [ ] Results stored correctly in task storage
- [ ] Errors logged and stored in task error field

---

#### Task 2.2: Add Async Quality Analysis Endpoint
**File:** `app/api/v1/routes.py`

**Changes:**
```python
@router.post(
    "/quality/analyze-async",
    response_model=AsyncJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit quality analysis task (async)",
    description="Analyze test files asynchronously. Returns task_id immediately, poll /tasks/{task_id} for results.",
)
async def submit_quality_analysis(
    request: QualityAnalysisRequest,
) -> AsyncJobResponse:
    """Submit quality analysis request and return task identifier."""
    try:
        # Validate request
        if not request.files:
            raise HTTPException(status_code=400, detail="No files provided")
        if len(request.files) > MAX_FILES_PER_REQUEST:
            raise HTTPException(status_code=400, detail=f"Too many files (max {MAX_FILES_PER_REQUEST})")

        # Convert to dict for task payload
        task_payload = request.model_dump()

        logger.info("Received quality analysis request: files=%d, mode=%s",
                   len(request.files), request.mode)

        # Create task
        task_id = await create_task(task_payload)

        # Launch background execution
        asyncio.create_task(execute_quality_analysis_task(task_id, task_payload))
        logger.info("Launched quality analysis task: task_id=%s", task_id)

        # Return immediately with task_id
        return AsyncJobResponse(
            task_id=task_id,
            status=TaskStatus.PENDING.value,
            estimated_time_seconds=15,  # Based on Phase 1a improvements
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to submit quality analysis: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit task") from exc
```

**Testing:**
- Unit: Verify task creation and 202 response
- Integration: Full flow - submit, poll, verify results
- Load testing: Submit 10 concurrent tasks, verify all complete

**Acceptance Criteria:**
- [ ] Endpoint returns 202 Accepted in < 100ms
- [ ] Task_id format matches existing tasks (UUID)
- [ ] Background task launches successfully
- [ ] Response schema matches AsyncJobResponse

---

#### Task 2.3: Add Deprecation Strategy for Synchronous Endpoint
**File:** `app/api/v1/routes.py`

**Changes:**
1. Keep existing `POST /quality/analyze` endpoint functional (with Phase 1a improvements)
2. Add deprecation metadata to OpenAPI spec:
```python
@router.post(
    "/quality/analyze",
    response_model=QualityAnalysisResponse,
    deprecated=True,  # OpenAPI deprecation flag
    summary="Analyze test quality (synchronous) - DEPRECATED",
    description="""
    **DEPRECATED:** Use POST /quality/analyze-async for better performance.
    This endpoint may timeout for large batches (>50 files).

    Migration: Use /quality/analyze-async + poll /tasks/{task_id}
    """,
)
async def analyze_quality(request: QualityAnalysisRequest) -> QualityAnalysisResponse:
    # Add deprecation warning to logs
    logger.warning("Synchronous quality analysis endpoint called (deprecated): files=%d",
                  len(request.files))

    # Add response header
    response.headers["X-Deprecated"] = "true"
    response.headers["X-Replacement"] = "POST /quality/analyze-async"

    # ... existing implementation with Phase 1a improvements ...
```

3. Document migration timeline:
   - Week 3-4: Both endpoints available
   - Week 4-16: Deprecation warnings in logs
   - Week 16+: Remove synchronous endpoint in v2.0.0

**Acceptance Criteria:**
- [ ] OpenAPI docs show deprecation notice
- [ ] Response includes deprecation headers
- [ ] Logs warn when synchronous endpoint is used
- [ ] Both endpoints work correctly (backwards compatible)

---

#### Task 2.4: Update API Documentation
**File:** `docs/api/openapi.yaml` (if exists) or Swagger UI

**Changes:**
1. Document new `/quality/analyze-async` endpoint
2. Add polling pattern examples
3. Update `/quality/analyze` with deprecation notice

**Example Documentation:**
```markdown
## Async Quality Analysis (Recommended)

**Step 1: Submit Analysis**
POST /quality/analyze-async
→ Returns task_id immediately (< 100ms)

**Step 2: Poll for Results**
GET /tasks/{task_id}
→ Returns status: pending | processing | completed | failed

**Step 3: Retrieve Results**
When status=completed, result field contains QualityAnalysisResponse

**Migration from Synchronous:**
Replace:
  POST /quality/analyze → wait for response
With:
  POST /quality/analyze-async → poll /tasks/{task_id}
```

**Acceptance Criteria:**
- [ ] OpenAPI spec updated with new endpoint
- [ ] Examples show polling pattern
- [ ] Migration guide available in docs

---

### Phase 1b Rollout Strategy
1. Deploy async endpoint alongside synchronous (Week 3)
2. Frontend implements polling mechanism (coordinated release)
3. Gradual rollout: 10% → 50% → 100% of clients
4. Monitor metrics:
   - Async endpoint adoption rate
   - Task completion rate (target: > 99%)
   - Average polling frequency (optimize if excessive)
5. After 3 months: Add removal timeline for sync endpoint (v2.0.0)

---

## Phase 2: Unified Logging & Observability (Concurrent with Phase 1a)

### Goal
Complete request lifecycle visibility with performance metrics and error context.

### Implementation Tasks

#### Task 3.1: Enhance RequestIDMiddleware with Response Logging
**File:** `app/core/middleware.py`

**Changes:**
```python
async def dispatch(self, request: Request, call_next: Callable):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    # Log request start
    start_time = time.time()
    logger.info(
        "Request started",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else None,
        },
    )

    # Process request
    response = await call_next(request)

    # Log response (NEW)
    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        "Request completed",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    response.headers["X-Request-ID"] = request_id
    return response
```

**Acceptance Criteria:**
- [ ] Every request has both "started" and "completed" logs
- [ ] Logs include request_id, method, path, status_code, duration_ms
- [ ] Log format is consistent (JSON or structured)

---

#### Task 3.2: Remove Duplicate RequestLoggingMiddleware (If Exists)
**Files:** `app/core/services/logging_config.py`, `app/main.py`

**Changes:**
1. Search for duplicate `RequestLoggingMiddleware`
2. If found, remove it and consolidate into `RequestIDMiddleware`
3. Ensure field names are consistent ("request_id" not "correlation_id")

**Acceptance Criteria:**
- [ ] Only one request logging middleware exists
- [ ] No duplicate log entries for same request
- [ ] Field names consistent across all logs

---

#### Task 3.3: Add Endpoint-Level Response Summary Logging
**File:** `app/api/v1/routes.py`

**Changes for Quality Analysis Endpoints:**
```python
async def analyze_quality(request: QualityAnalysisRequest) -> QualityAnalysisResponse:
    start_time = time.time()

    logger.info("Quality analysis request: files=%d, mode=%s", len(request.files), request.mode)

    async with get_quality_service_context() as quality_service:
        result = await quality_service.analyze_batch(files=request.files, mode=request.mode)

    # Log response summary (NEW)
    duration_ms = int((time.time() - start_time) * 1000)
    logger.info(
        "Quality analysis completed: issues=%d, critical=%d, files=%d, mode=%s, duration_ms=%d",
        len(result.issues),
        result.summary.critical_issues,
        result.summary.total_files,
        request.mode,
        duration_ms,
    )

    return result
```

**Apply to:**
- `analyze_quality()` - synchronous endpoint
- `submit_quality_analysis()` - async endpoint (log submission only)
- `analyze_impact()` - impact analysis endpoint

**Acceptance Criteria:**
- [ ] Response summary logged with issue counts and timing
- [ ] Log format consistent across all analysis endpoints
- [ ] No sensitive data (file contents) logged

---

#### Task 3.4: Add LLM Request/Response Logging with Token Tracking
**File:** `app/core/llm/llm_client.py`

**Changes:**
```python
async def chat_completion(
    self,
    messages: List[Dict[str, str]],
    temperature: float = 0.2,
    max_tokens: int = 1000,
) -> str:
    start_time = time.time()
    request_id = str(uuid.uuid4())

    logger.debug(
        "LLM request: request_id=%s, model=%s, messages=%d, temperature=%.2f, max_tokens=%d",
        request_id,
        self.model,
        len(messages),
        temperature,
        max_tokens,
    )

    # Make API call
    response = await self.client.chat.completions.create(...)

    # Log response with token usage (NEW)
    latency_ms = int((time.time() - start_time) * 1000)
    usage = response.usage

    logger.info(
        "LLM response: request_id=%s, model=%s, prompt_tokens=%d, completion_tokens=%d, total_tokens=%d, latency_ms=%d",
        request_id,
        self.model,
        usage.prompt_tokens,
        usage.completion_tokens,
        usage.total_tokens,
        latency_ms,
    )

    return response.choices[0].message.content
```

**Acceptance Criteria:**
- [ ] All LLM calls logged with request_id
- [ ] Token usage tracked (prompt, completion, total)
- [ ] Latency metrics recorded
- [ ] Request/response correlation via request_id

---

#### Task 3.5: Add Service-Level Progress Logging
**File:** `app/core/services/quality_service.py`

**Changes:**
```python
async def analyze_batch(self, files, mode):
    start_time = time.time()
    analysis_id = str(uuid.uuid4())

    logger.info(
        "Quality analysis started: analysis_id=%s, files=%d, mode=%s",
        analysis_id, len(files), mode
    )

    # Phase 1: Dependency data
    if self.graph_service:
        logger.debug("Fetching dependency data: analysis_id=%s", analysis_id)
        dependency_data = await self._fetch_dependency_data(files)
        logger.info("Dependency data fetched: analysis_id=%s, functions=%d",
                   analysis_id, len(dependency_data))

    # Phase 2: Analysis
    logger.debug("Starting TestAnalyzer: analysis_id=%s", analysis_id)
    analysis_result = await self.test_analyzer.analyze_files(files, mode)
    logger.info("TestAnalyzer completed: analysis_id=%s, raw_issues=%d",
               analysis_id, len(analysis_result.issues))

    # Phase 3: Conversion
    quality_issues = self._convert_issues(analysis_result.issues)

    elapsed_ms = int((time.time() - start_time) * 1000)
    logger.info(
        "Quality analysis completed: analysis_id=%s, issues=%d, elapsed_ms=%d",
        analysis_id, len(quality_issues), elapsed_ms
    )

    return QualityAnalysisResponse(...)
```

**Acceptance Criteria:**
- [ ] Each analysis phase logged with analysis_id
- [ ] Progress indicators at major milestones
- [ ] Timing metrics for each phase
- [ ] analysis_id traceable across all logs

---

### Phase 2 Acceptance Criteria (Overall)
- [ ] 100% of requests have lifecycle logs (start → complete)
- [ ] LLM token usage visible in all logs
- [ ] No duplicate middleware or conflicting field names
- [ ] Log format consistent and structured (JSON recommended)
- [ ] Performance impact of logging < 5ms per request

---

## Testing Strategy

### Unit Tests
**Location:** `tests/unit/core/analysis/`

**Coverage:**
1. Semaphore limits concurrent LLM calls correctly
2. `asyncio.gather()` handles exceptions properly (one failure doesn't block others)
3. Task executor transitions through states correctly
4. Logging methods called with expected parameters

**Tools:** pytest-asyncio, unittest.mock

---

### Integration Tests
**Location:** `tests/integration/`

**Scenarios:**
1. Quality analysis with 50 files completes in < 15s (Phase 1a)
2. Async endpoint returns task_id, polling returns results (Phase 1b)
3. Synchronous and async endpoints return identical results (quality parity)
4. Failed LLM calls don't prevent analysis completion
5. Concurrent task submissions (10 tasks simultaneously)

**Tools:** pytest, httpx.AsyncClient

---

### Performance Benchmarks
**Metrics:**
- Execution time (before/after parallelization)
- LLM API rate limit errors (429 status codes)
- Memory usage during parallel execution
- Task completion rate (target: > 99%)

**Baselines:**
- Current: 38 files = 45+ seconds (sequential)
- Target Phase 1a: 38 files < 15 seconds (parallel)
- Target Phase 1b: < 100ms response time (async submission)

---

### Load Testing
**Scenarios:**
1. Submit 100 quality analysis requests concurrently
2. Monitor task queue depth and completion rate
3. Verify no memory leaks or resource exhaustion
4. Check LLM API rate limit handling

**Tools:** locust or k6

---

## Deployment Plan

### Week 1-2: Phase 1a + Phase 2 (Parallel Development)
**Monday-Wednesday:**
- Implement Task 1.1: Semaphore parallelization in HybridStrategy
- Implement Task 3.1-3.2: Unified middleware and response logging

**Thursday-Friday:**
- Implement Task 1.2: Parallelization in LLMOnlyStrategy
- Implement Task 3.3: Endpoint-level summary logging
- Unit tests for parallelization and logging

**Week 2:**
- Implement Task 1.3-1.4: Configuration and progress logging
- Implement Task 3.4-3.5: LLM logging and service-level progress
- Integration tests and performance benchmarks
- Deploy to staging, validate metrics
- Deploy to production (low risk - no API changes)

### Week 3: Phase 1b (Async Task Pattern)
**Monday-Tuesday:**
- Implement Task 2.1: Task executor
- Implement Task 2.2: Async endpoint
- Unit tests for task lifecycle

**Wednesday-Thursday:**
- Implement Task 2.3: Deprecation strategy
- Implement Task 2.4: Documentation updates
- Integration tests for async pattern
- Frontend coordination for polling implementation

**Friday:**
- Deploy to staging
- E2E testing with frontend
- Deploy to production with feature flag
- Monitor adoption metrics

### Post-Deployment (Week 4+)
- Monitor performance improvements (execution time, timeout rate)
- Track async endpoint adoption rate
- Collect user feedback
- Plan synchronous endpoint removal (3 months)

---

## Rollback Plan

### Phase 1a Rollback
If parallelization causes issues:
1. Set `LLM_MAX_CONCURRENT_CALLS=1` (revert to sequential)
2. Or: Revert commits for Task 1.1-1.4
3. No data loss - strategies are stateless

### Phase 1b Rollback
If async tasks fail:
1. Disable async endpoint via feature flag
2. Keep synchronous endpoint (unchanged)
3. No client impact - synchronous endpoint still works

### Phase 2 Rollback
If logging causes issues:
1. Reduce log level (INFO → WARNING)
2. Or: Revert logging commits
3. No functional impact - logging is observability only

---

## Success Metrics & Monitoring

### Key Performance Indicators (KPIs)

**Performance:**
- Quality Analysis execution time: < 15s for 50 files (currently 45s+)
- Async endpoint response time: < 100ms (task creation only)
- LLM call parallelization: 10 concurrent (configurable)

**Reliability:**
- Frontend timeout rate: 0% (currently 100% for large batches)
- Task completion rate: > 99%
- LLM API error rate: < 1%

**Observability:**
- Request lifecycle logging: 100% coverage
- LLM token usage tracking: 100% coverage
- Log volume increase: < 20% (structured logging)

### Monitoring Dashboards

**Create Grafana/CloudWatch Dashboards for:**
1. Quality Analysis execution time (P50, P95, P99)
2. LLM API latency and token usage
3. Task status distribution (pending/processing/completed/failed)
4. Async endpoint adoption rate
5. Error rates by endpoint and error type

**Alerts:**
- Quality Analysis execution time > 30s (Phase 1a regression)
- Task completion rate < 95%
- LLM API error rate > 5%
- Log volume increase > 50%

---

## Risk Mitigation

### Technical Risks

**Risk:** LLM API rate limiting (429 errors)
**Mitigation:** Semaphore limit of 10, exponential backoff, retry logic
**Contingency:** Reduce concurrency to 5 via environment variable

**Risk:** Memory exhaustion with many concurrent tasks
**Mitigation:** Semaphore limits resource usage, task TTL (24h)
**Contingency:** Add max task queue size, reject if queue full

**Risk:** Task storage (Redis) unavailable
**Mitigation:** In-memory fallback already implemented
**Contingency:** Tasks lost on restart (acceptable for dev/staging)

### Operational Risks

**Risk:** Frontend not ready for async pattern
**Mitigation:** Keep synchronous endpoint functional, gradual rollout
**Contingency:** Extend timeline, delay async endpoint release

**Risk:** Log volume increase impacts performance
**Mitigation:** Use structured logging, appropriate log levels (DEBUG for verbose)
**Contingency:** Reduce log verbosity, use sampling for high-traffic endpoints

---

## Dependencies & Prerequisites

### External Dependencies
- LLM API (DeepSeek): Stable, supports concurrent requests
- Redis (optional): For task storage in production
- Frontend: Will need polling mechanism for async pattern (coordinate release)

### Code Dependencies
- `asyncio`: Core Python library, no version constraints
- `httpx`: Already used for LLM client
- `pytest-asyncio`: Already in dev dependencies

### Infrastructure
- Staging environment: Required for testing
- Production deployment pipeline: Existing (Docker-based)
- Monitoring tools: Grafana/CloudWatch (preferred) or logs-based monitoring

---

## Documentation Updates

### Developer Documentation
**File:** `docs/development/quality-analysis-architecture.md` (create)

**Content:**
- Architecture diagrams (sequential vs parallel)
- Semaphore pattern explanation
- Task executor pattern
- Testing guidelines

### API Documentation
**File:** `docs/api/quality-analysis.md` (update)

**Content:**
- New async endpoint documentation
- Polling pattern examples
- Migration guide from sync to async
- Error handling examples

### Runbooks
**File:** `docs/operations/quality-analysis-runbook.md` (create)

**Content:**
- Troubleshooting slow analysis (check concurrency config)
- Handling task failures (inspect task error field)
- Monitoring dashboards and alert responses

---

## Conclusion

This plan provides a comprehensive, phased approach to solving the Quality Analysis timeout issue while improving system observability. The hybrid strategy ensures:

1. **Quick Wins (Week 1-2):** Immediate 10x speedup via parallelization + better logging
2. **Long-Term Solution (Week 3):** Async task pattern for unlimited scalability
3. **Backwards Compatibility:** Gradual migration, no breaking changes
4. **Low Risk:** Incremental rollout, feature flags, rollback plans

**Next Steps:**
1. Review and approve this plan
2. Create implementation branch: `feat/quality-analysis-optimization`
3. Begin Week 1 development (Phase 1a + Phase 2)
4. Schedule frontend coordination meeting for async pattern (Week 3)

**Estimated Delivery:** 3 weeks from start date
**Risk Level:** Low (phased approach with rollback options)
**Impact:** High (eliminates frontend timeouts, improves UX, better observability)
