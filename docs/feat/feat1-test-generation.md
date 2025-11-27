# Feature 1: Test Generation - Architecture and Implementation

**Document Version:** 1.0
**Last Updated:** 2025-11-25
**Author:** Architecture Documentation

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Request Flow](#request-flow)
4. [Asynchronous Task Management](#asynchronous-task-management)
5. [LLM Integration](#llm-integration)
6. [Message Construction Strategy](#message-construction-strategy)
7. [Response Parsing](#response-parsing)
8. [Error Handling and Retry Logic](#error-handling-and-retry-logic)
9. [Storage Backend](#storage-backend)
10. [API Endpoints](#api-endpoints)
11. [Example Usage](#example-usage)
12. [Performance Characteristics](#performance-characteristics)
13. [Testing Strategy](#testing-strategy)
14. [Summary](#summary)

---

## Overview

Feature 1 (Test Generation) provides AI-powered test code generation using Large Language Models (LLMs). The system generates high-quality pytest tests based on source code, user descriptions, and optional existing test context.

### Key Capabilities

- **AI-Powered Generation**: Uses OpenAI-compatible LLMs (GPT-4, Claude, etc.)
- **Asynchronous Processing**: Non-blocking task execution with polling-based status checks
- **Context-Aware**: Supports existing test code for regeneration scenarios
- **Flexible Input**: Accepts user descriptions and generation context
- **Production-Ready**: Redis-backed task storage with in-memory fallback

### Use Cases

1. **New Test Creation**: Generate tests from scratch for untested code
2. **Test Regeneration**: Improve existing tests based on feedback
3. **CI/CD Integration**: Automated test generation in pipelines
4. **Developer Assistance**: Quick test scaffolding during development

---

## Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                   API Layer                                  │
│  POST /workflows/generate-tests (routes.py:203)             │
│  GET /tasks/{task_id} (routes.py:301)                       │
│  - Request validation                                        │
│  - Task creation and submission                              │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Task Management Layer                           │
│  tasks.py (app/core/tasks/)                                 │
│  - Async task execution with asyncio.create_task            │
│  - Task status tracking (pending → processing → completed)  │
│  - Redis/in-memory storage abstraction                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼             ▼
┌──────────────┬──────────────┬─────────────────────┐
│  LLM Client  │    Storage   │  Message Builder    │
│ (llm_client  │  (Redis/Mem) │  (tasks.py)         │
│    .py)      │              │                     │
│ - OpenAI API │  - Task data │  - Prompt           │
│ - Retries    │    storage   │    engineering      │
│ - Timeouts   │  - TTL 24hrs │  - Context          │
│              │              │    formatting       │
└──────────────┴──────────────┴─────────────────────┘
```

### Layer Responsibilities

#### 1. API Layer (routes.py)
- Receives `GenerateTestsRequest` from frontend
- Creates async task and returns `task_id` immediately (202 Accepted)
- Provides polling endpoint for task status
- Handles HTTP error responses

#### 2. Task Management Layer (tasks.py)
- Executes test generation in background using `asyncio.create_task()`
- Manages task lifecycle: PENDING → PROCESSING → COMPLETED/FAILED
- Persists task state to Redis (or in-memory fallback)
- Implements TTL-based task cleanup (24 hours)

#### 3. LLM Client Layer (llm_client.py)
- Communicates with OpenAI-compatible APIs
- Implements exponential backoff retry logic
- Handles rate limiting (429) and server errors (5xx)
- Tracks token usage and performance metrics

---

## Request Flow

### Step 1: Client Submits Test Generation Request

```http
POST /workflows/generate-tests HTTP/1.1
Content-Type: application/json

{
  "source_code": "def add(a, b):\n    return a + b",
  "user_description": "Test addition with edge cases",
  "existing_test_code": null,
  "context": {
    "mode": "new",
    "target_function": null
  }
}
```

**Request Schema (`GenerateTestsRequest`):**
```python
class GenerateTestsRequest(BaseModel):
    source_code: str                          # Required: code to test
    user_description: Optional[str] = None    # Optional: user hints
    existing_test_code: Optional[str] = None  # Optional: for regeneration
    context: Optional[GenerateTestsContext] = None  # Optional: mode metadata
```

---

### Step 2: API Creates Task and Returns Immediately

```python
# routes.py:203-247
@router.post("/workflows/generate-tests", response_model=AsyncJobResponse)
async def submit_generate_tests(request: GenerateTestsRequest):
    # Convert request to dict
    task_payload = request.model_dump()

    # Create task in storage (returns UUID)
    task_id = await create_task(task_payload)

    # Launch background task (non-blocking)
    asyncio.create_task(execute_generate_tests_task(task_id, task_payload))

    # Return task_id immediately (202 Accepted)
    return AsyncJobResponse(
        task_id=task_id,
        status="pending",
        estimated_time_seconds=30
    )
```

**Response (202 Accepted):**
```json
{
  "task_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "status": "pending",
  "estimated_time_seconds": 30
}
```

**Key Design Choice:**
- Uses **asyncio.create_task()** instead of Celery for simplicity
- No external message broker dependency
- Task executes in the same Python process

---

### Step 3: Background Task Execution

```python
# tasks.py:210-237
async def execute_generate_tests_task(task_id: str, payload: Dict[str, Any]):
    try:
        # Update status to PROCESSING
        await update_task_status(task_id, TaskStatus.PROCESSING)

        # Generate tests using LLM
        generation_result = await _generate_tests_from_llm(payload)

        # Format result per OpenAPI spec
        result = {
            "generated_code": generation_result["generated_code"],
            "explanation": generation_result["explanation"]
        }

        # Update status to COMPLETED with result
        await update_task_status(task_id, TaskStatus.COMPLETED, result=result)

    except Exception as exc:
        # Update status to FAILED with error message
        await update_task_status(task_id, TaskStatus.FAILED, error=str(exc))
```

---

### Step 4: LLM Test Generation

```python
# tasks.py:239-270
async def _generate_tests_from_llm(payload: Dict[str, Any]) -> Dict[str, str]:
    # Extract fields
    source_code = payload.get("source_code", "")
    user_description = payload.get("user_description", "")
    existing_test_code = payload.get("existing_test_code", "")
    context = payload.get("context", {})

    # Build LLM messages
    messages = _build_generation_messages(
        source_code, user_description, existing_test_code, context
    )

    # Call LLM API
    client = create_llm_client()
    try:
        raw_response = await client.chat_completion(
            messages=messages,
            temperature=0.2,  # Low temperature for deterministic code
            max_tokens=2000
        )

        # Parse response
        return _parse_generation_response(raw_response)
    finally:
        await client.close()
```

---

### Step 5: Client Polls for Task Status

```http
GET /tasks/a7b3c4d5-e6f7-8901-2345-6789abcdef01 HTTP/1.1
```

**Response (200 OK - COMPLETED):**
```json
{
  "task_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "status": "completed",
  "created_at": "2025-11-25T10:30:00Z",
  "result": {
    "generated_code": "def test_add():\n    assert add(2, 3) == 5\n    assert add(-1, 1) == 0",
    "explanation": "Generated basic tests covering positive and negative numbers"
  },
  "error": null
}
```

**Response (200 OK - PROCESSING):**
```json
{
  "task_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "status": "processing",
  "created_at": "2025-11-25T10:30:00Z",
  "result": null,
  "error": null
}
```

**Response (200 OK - FAILED):**
```json
{
  "task_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "status": "failed",
  "created_at": "2025-11-25T10:30:00Z",
  "result": null,
  "error": {
    "message": "Rate limit exceeded after all retries",
    "code": null
  }
}
```

---

## Asynchronous Task Management

### Task Lifecycle

```
┌─────────┐   create_task()   ┌─────────┐
│ PENDING ├──────────────────►│PROCESSING│
└─────────┘                    └────┬─────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
              ┌───────────┐                  ┌────────┐
              │ COMPLETED │                  │ FAILED │
              └───────────┘                  └────────┘
```

### Task Status Enum

```python
class TaskStatus(str, Enum):
    PENDING = "pending"        # Task created, not started
    PROCESSING = "processing"  # Task executing
    COMPLETED = "completed"    # Task successful
    FAILED = "failed"          # Task failed with error
```

### Task Data Structure

```python
{
    "id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
    "status": "completed",
    "created_at": "2025-11-25T10:30:00Z",
    "updated_at": "2025-11-25T10:30:45Z",
    "payload": {
        "source_code": "...",
        "user_description": "...",
        ...
    },
    "result": {
        "generated_code": "...",
        "explanation": "..."
    },
    "error": null
}
```

### Why asyncio.create_task() Instead of Celery?

| Aspect | asyncio.create_task() | Celery |
|--------|----------------------|--------|
| **Setup Complexity** | ✅ None (built-in) | ❌ Requires Redis/RabbitMQ + worker processes |
| **Deployment** | ✅ Single process | ❌ Multiple processes (app + workers) |
| **Latency** | ✅ Low (in-process) | ⚠️ Higher (network overhead) |
| **Scalability** | ⚠️ Limited to single machine | ✅ Distributed workers |
| **Persistence** | ⚠️ Lost on restart | ✅ Survives restarts |
| **Best For** | Development, single-server | Production, high-scale |

**Decision:** Use `asyncio.create_task()` for simplicity in current phase. Can migrate to Celery later if needed.

---

## LLM Integration

### LLM Client Architecture

```python
# llm_client.py:45-287
class LLMClient:
    def __init__(self, api_key, base_url, model, timeout, max_retries):
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            headers={"Authorization": f"Bearer {api_key}"}
        )

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000
    ) -> str:
        # Retry loop with exponential backoff
        for attempt in range(self.max_retries + 1):
            try:
                response = await self.client.post(
                    f"{self.base_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    await asyncio.sleep(self._get_retry_after(response))
                    continue

                # Handle server errors (500+)
                if response.status_code >= 500:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue

                # Parse successful response
                return response.json()["choices"][0]["message"]["content"]

            except httpx.TimeoutException:
                if attempt < self.max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
                raise LLMTimeoutError(...)
```

### Configuration

```python
# config.py (environment variables)
LLM_API_KEY=sk-...                          # OpenAI API key
LLM_BASE_URL=https://api.openai.com/v1     # API endpoint
LLM_MODEL=gpt-4                             # Model name
LLM_TIMEOUT=60                              # Request timeout (seconds)
LLM_MAX_RETRIES=3                           # Retry attempts
```

### Supported LLM Providers

Any OpenAI-compatible API:
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude (via OpenAI adapter)
- **Azure OpenAI**: Custom endpoints
- **Local Models**: Ollama, LM Studio, vLLM

---

## Message Construction Strategy

### System Prompt

```python
SYSTEM_PROMPT = (
    "You are an expert Python test engineer. Generate high-quality pytest tests, "
    "covering edge cases, error handling, and clear assertions. Ensure the output "
    "is ready to paste into a test file."
)
```

**Design Philosophy:**
- Clear role definition ("expert Python test engineer")
- Specific framework (pytest)
- Quality expectations (edge cases, assertions)
- Output format (ready-to-paste code)

---

### User Prompt Construction

```python
# tasks.py:297-347
def _build_generation_messages(
    source_code: str,
    user_description: str,
    existing_test_code: str,
    context: Dict[str, Any]
) -> list[Dict[str, str]]:
    user_prompt_parts = []

    # 1. User description (if provided)
    if user_description:
        user_prompt_parts.append(f"User description:\n{user_description}")

    # 2. Source code (always included)
    user_prompt_parts.append(
        f"Source code to test:\n```python\n{source_code}\n```"
    )

    # 3. Existing test code (for regeneration context)
    if existing_test_code:
        user_prompt_parts.append(
            f"Existing test code (for context):\n```python\n{existing_test_code}\n```"
        )

    # 4. Context metadata
    context_text = _format_context(context)
    user_prompt_parts.append(f"Context:\n{context_text}")

    # 5. Requirements
    user_prompt_parts.append("""
Requirements:
- Generate high-quality pytest tests
- Cover edge cases, error handling, and typical scenarios
- Include clear assertions
- Return response with generated code in a Python code block
- Provide brief explanation of what was generated
""")

    user_prompt = "\n\n".join(user_prompt_parts)

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]
```

### Example Prompt

**Input:**
```python
source_code = "def divide(a, b):\n    return a / b"
user_description = "Test division with zero denominator"
```

**Generated Prompt:**
```
[System]
You are an expert Python test engineer. Generate high-quality pytest tests...

[User]
User description:
Test division with zero denominator

Source code to test:
```python
def divide(a, b):
    return a / b
```

Context:
- mode: new

Requirements:
- Generate high-quality pytest tests
- Cover edge cases, error handling, and typical scenarios
- Include clear assertions
...
```

---

## Response Parsing

### Parsing Strategy

```python
# tasks.py:272-294
def _parse_generation_response(raw_response: str) -> Dict[str, str]:
    import re

    # Try to extract Python code block
    code_block_pattern = r"```python\n(.*?)\n```"
    code_blocks = re.findall(code_block_pattern, raw_response, re.DOTALL)

    if code_blocks:
        # Extracted code from markdown
        generated_code = code_blocks[0].strip()

        # Rest is explanation
        explanation = re.sub(
            code_block_pattern, "", raw_response, flags=re.DOTALL
        ).strip()
    else:
        # No code block - treat entire response as code
        generated_code = raw_response.strip()
        explanation = "Generated tests based on provided source code."

    return {
        "generated_code": generated_code,
        "explanation": explanation or "Generated tests based on provided source code."
    }
```

### Example Parsing

**LLM Response:**
```
Here are the tests for the divide function:

```python
def test_divide_positive():
    assert divide(10, 2) == 5

def test_divide_zero_denominator():
    with pytest.raises(ZeroDivisionError):
        divide(10, 0)
```

These tests cover normal division and the zero denominator edge case.
```

**Parsed Result:**
```python
{
    "generated_code": "def test_divide_positive():\n    assert divide(10, 2) == 5\n\ndef test_divide_zero_denominator():\n    with pytest.raises(ZeroDivisionError):\n        divide(10, 0)",
    "explanation": "Here are the tests for the divide function:\n\nThese tests cover normal division and the zero denominator edge case."
}
```

---

## Error Handling and Retry Logic

### LLM Client Error Hierarchy

```python
class LLMClientError(Exception):
    """Base exception"""

class LLMRateLimitError(LLMClientError):
    """Rate limit exceeded (429)"""

class LLMTimeoutError(LLMClientError):
    """Request timeout"""

class LLMAPIError(LLMClientError):
    """General API errors (4xx, 5xx)"""
```

### Retry Logic

```python
# llm_client.py:121-262
for attempt in range(self.max_retries + 1):
    try:
        response = await self.client.post(url, json=payload)

        # Handle 429 Rate Limiting
        if response.status_code == 429:
            if attempt < self.max_retries:
                retry_after = self._get_retry_after(response)  # From header
                await asyncio.sleep(retry_after)
                continue
            else:
                raise LLMRateLimitError("Rate limit exceeded after all retries")

        # Handle 5xx Server Errors
        if response.status_code >= 500:
            if attempt < self.max_retries:
                wait_time = 2 ** attempt  # Exponential: 1s, 2s, 4s
                await asyncio.sleep(wait_time)
                continue
            else:
                raise LLMAPIError(f"Server error after all retries")

        # Success
        return response.json()["choices"][0]["message"]["content"]

    except httpx.TimeoutException:
        if attempt < self.max_retries:
            await asyncio.sleep(2 ** attempt)
            continue
        else:
            raise LLMTimeoutError("Request timed out after all retries")
```

### Retry Examples

| Attempt | Error | Wait Time | Action |
|---------|-------|-----------|--------|
| 1 | 500 Server Error | 1 second | Retry |
| 2 | 500 Server Error | 2 seconds | Retry |
| 3 | 500 Server Error | 4 seconds | Retry |
| 4 | 500 Server Error | - | Fail (exhausted) |

| Attempt | Error | Wait Time | Action |
|---------|-------|-----------|--------|
| 1 | 429 Rate Limit | 60 seconds (from header) | Retry |
| 2 | 200 OK | - | Success |

---

## Storage Backend

### Redis Primary, In-Memory Fallback

```python
# tasks.py:113-128
async def _get_storage():
    global _use_in_memory, _in_memory_store

    if not _use_in_memory:
        redis_client = await _get_redis_client()
        if redis_client is not None:
            return redis_client

        # Redis unavailable - switch to in-memory
        _use_in_memory = True
        _in_memory_store = get_in_memory_task_store()
        await _in_memory_store.start()
        logger.info("Switched to in-memory task storage for development")

    return _in_memory_store
```

### Storage Operations

```python
# Save task
async def _save_task(task_id: str, task_data: Dict[str, Any]):
    storage = await _get_storage()
    key = f"task:{task_id}"
    json_data = json.dumps(task_data)

    if _use_in_memory:
        await storage.setex(key, TASK_TTL_SECONDS, json_data)
    else:  # Redis
        await storage.setex(key, TASK_TTL_SECONDS, json_data)

# Retrieve task
async def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    storage = await _get_storage()
    key = f"task:{task_id}"

    raw = await storage.get(key)
    return json.loads(raw) if raw else None
```

### TTL (Time-To-Live)

- **Default TTL**: 24 hours (86400 seconds)
- **Automatic Cleanup**: Redis/in-memory automatically deletes expired tasks
- **Why 24 hours**: Enough time for debugging, not too long for storage bloat

---

## API Endpoints

### POST /workflows/generate-tests

**Purpose:** Submit test generation request

**Request:**
```json
{
  "source_code": "def add(a, b): return a + b",
  "user_description": "Test edge cases",
  "existing_test_code": null,
  "context": {"mode": "new"}
}
```

**Response (202 Accepted):**
```json
{
  "task_id": "uuid",
  "status": "pending",
  "estimated_time_seconds": 30
}
```

---

### GET /tasks/{task_id}

**Purpose:** Poll task status and retrieve result

**Request:**
```http
GET /tasks/a7b3c4d5-e6f7-8901-2345-6789abcdef01
```

**Response (200 OK - Completed):**
```json
{
  "task_id": "a7b3c4d5-e6f7-8901-2345-6789abcdef01",
  "status": "completed",
  "created_at": "2025-11-25T10:30:00Z",
  "result": {
    "generated_code": "def test_add(): ...",
    "explanation": "Generated tests covering..."
  },
  "error": null
}
```

**Response (404 Not Found):**
- Task not found or expired (TTL elapsed)

---

## Example Usage

### Python Client Example

```python
import httpx
import asyncio
import time

async def generate_tests():
    client = httpx.AsyncClient(base_url="http://localhost:8886")

    # Step 1: Submit test generation request
    response = await client.post("/workflows/generate-tests", json={
        "source_code": "def multiply(a, b):\n    return a * b",
        "user_description": "Test multiplication with zeros and negatives"
    })
    task_id = response.json()["task_id"]
    print(f"Task submitted: {task_id}")

    # Step 2: Poll for task completion
    while True:
        response = await client.get(f"/tasks/{task_id}")
        task = response.json()

        if task["status"] == "completed":
            print("Generated code:")
            print(task["result"]["generated_code"])
            break

        elif task["status"] == "failed":
            print(f"Task failed: {task['error']['message']}")
            break

        else:
            print(f"Status: {task['status']}, waiting...")
            await asyncio.sleep(2)

asyncio.run(generate_tests())
```

### cURL Example

```bash
# Submit request
TASK_ID=$(curl -X POST http://localhost:8886/workflows/generate-tests \
  -H "Content-Type: application/json" \
  -d '{
    "source_code": "def subtract(a, b):\n    return a - b",
    "user_description": "Test subtraction"
  }' | jq -r '.task_id')

echo "Task ID: $TASK_ID"

# Poll for result
while true; do
  STATUS=$(curl -s http://localhost:8886/tasks/$TASK_ID | jq -r '.status')
  echo "Status: $STATUS"

  if [ "$STATUS" = "completed" ]; then
    curl -s http://localhost:8886/tasks/$TASK_ID | jq '.result.generated_code'
    break
  fi

  sleep 2
done
```

---

## Performance Characteristics

### Latency Breakdown

| Phase | Time (Typical) | Notes |
|-------|---------------|-------|
| Task Creation | ~10ms | Redis write |
| LLM API Call | 5-30 seconds | Varies by model/load |
| Response Parsing | ~5ms | Regex extraction |
| Task Status Update | ~10ms | Redis write |
| **Total** | **5-30 seconds** | Dominated by LLM |

### Throughput

- **Serial (no LLM queuing)**: ~2-12 requests/minute (5-30s per request)
- **Parallel (with asyncio)**: Limited by LLM API rate limits
  - OpenAI Tier 1: 500 requests/minute
  - OpenAI Tier 2: 5,000 requests/minute

### Token Usage

| Component | Tokens (Estimate) |
|-----------|-------------------|
| System Prompt | ~50 tokens |
| User Prompt (avg) | ~200-500 tokens |
| Source Code (avg) | ~100-300 tokens |
| Generated Tests | ~200-500 tokens |
| **Total per Request** | **~550-1,350 tokens** |

**Cost Estimate (GPT-4):**
- Input: $0.03 / 1K tokens → ~$0.015-0.025 per request
- Output: $0.06 / 1K tokens → ~$0.012-0.030 per request
- **Total: ~$0.03-0.06 per test generation**

---

## Testing Strategy

### Unit Tests

```python
# Test LLM client retry logic
@pytest.mark.asyncio
async def test_llm_client_retry_on_timeout():
    client = LLMClient(...)
    with pytest.raises(LLMTimeoutError):
        await client.chat_completion(messages=[...])

# Test response parsing
def test_parse_generation_response_with_code_block():
    raw = """Here are tests:\n```python\ndef test_foo(): pass\n```"""
    result = _parse_generation_response(raw)
    assert "def test_foo()" in result["generated_code"]
```

### Integration Tests

```python
# Test end-to-end task flow (with mock LLM)
@pytest.mark.asyncio
async def test_generate_tests_task_success():
    # Create task
    task_id = await create_task({"source_code": "def foo(): pass"})

    # Execute (with mocked LLM)
    with patch("app.core.llm.llm_client.LLMClient.chat_completion") as mock:
        mock.return_value = "```python\ndef test_foo(): pass\n```"
        await execute_generate_tests_task(task_id, payload)

    # Verify result
    task = await get_task(task_id)
    assert task["status"] == "completed"
    assert "test_foo" in task["result"]["generated_code"]
```

### E2E Tests

```python
# Test via HTTP API (with real/mock LLM)
@pytest.mark.e2e
async def test_generate_tests_api_flow(test_client):
    # Submit request
    response = await test_client.post("/workflows/generate-tests", json={
        "source_code": "def add(a, b): return a + b"
    })
    assert response.status_code == 202
    task_id = response.json()["task_id"]

    # Poll until completed
    for _ in range(60):  # Max 2 minutes
        response = await test_client.get(f"/tasks/{task_id}")
        if response.json()["status"] == "completed":
            break
        await asyncio.sleep(2)

    # Verify result
    assert "test_add" in response.json()["result"]["generated_code"]
```

---

## Known Issues & Areas for Improvement

- **Response Schema Optimization**: The current `GET /tasks/{task_id}` response includes `result: null` and `error: null` fields when the task status is `pending` or `processing`. While not functionally breaking, strict RESTful best practices suggest omitting these fields until the task reaches a final state (`completed` or `failed`). This is planned for optimization.

---

## Summary

### Architecture Highlights

1. **Async-First Design**: Uses `asyncio.create_task()` for non-blocking execution
2. **Resilient LLM Integration**: Exponential backoff, rate limiting, timeout handling
3. **Flexible Storage**: Redis primary with in-memory fallback for development
4. **Production-Ready**: TTL-based cleanup, structured logging, error tracking

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| asyncio vs Celery | Simplicity for current scale; can migrate later |
| Redis vs Database | Fast key-value store; auto-expiration with TTL |
| OpenAI-compatible API | Flexibility to swap LLM providers |
| Low temperature (0.2) | Deterministic code generation |
| 24-hour TTL | Balance storage cost vs debugging needs |

### Trade-offs

| Aspect | Pros | Cons |
|--------|------|------|
| **asyncio tasks** | ✅ Simple, no broker | ❌ Not distributed |
| **In-process execution** | ✅ Low latency | ❌ Lost on restart |
| **Polling pattern** | ✅ Simple client | ❌ Higher latency than webhooks |

### Future Enhancements

1. **Webhook Support**: Push task results instead of polling
2. **Celery Migration**: For distributed scaling
3. **Streaming LLM**: Real-time code generation progress
4. **Caching**: Cache similar test generation requests
5. **Quality Scoring**: Rate generated test quality automatically

---

## References

- **Source Files**:
  - `app/api/v1/routes.py`: API endpoint definitions
  - `app/core/tasks/tasks.py`: Task execution logic
  - `app/core/llm/llm_client.py`: LLM client implementation
  - `app/api/v1/schemas.py`: Request/response models

- **External Documentation**:
  - OpenAI API: https://platform.openai.com/docs/api-reference
  - asyncio: https://docs.python.org/3/library/asyncio.html
  - Redis: https://redis.io/docs/

---

**Document Status:** ✅ Complete
**Next Review:** After production deployment
**Maintainer:** Backend Team
