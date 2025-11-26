# Fix: Unhashable Type Error in Quality Analysis

## Problem Description

**Error Message:**
```
Failed to initialize quality service: unhashable type: 'TestFunctionInfo'
```

**Error Source:**
When the VSCode extension calls the `/quality/analyze` endpoint, the backend fails to initialize the quality analysis service.

## Root Cause

In `app/core/analysis/uncertain_case_detector.py` at lines 97-102, the code attempts to add `TestFunctionInfo` objects to a Python set for deduplication:

```python
# ❌ Incorrect implementation
seen = set()
for func in uncertain_functions:
    if func not in seen:
        seen.add(func)  # TestFunctionInfo is not a hashable type
        result.append(func)
```

`TestFunctionInfo` is a dataclass that contains mutable fields (such as `List[AssertionInfo]`), therefore **it is not a hashable type** and cannot be added to a set or used as a dictionary key.

## Fix Solution

### 1. Fix Core Code

**File:** `app/core/analysis/uncertain_case_detector.py` (lines 96-107)

**Before:**
```python
# Remove duplicates while preserving order
seen = set()
result = []
for func in uncertain_functions:
    if func not in seen:
        seen.add(func)
        result.append(func)
```

**After:**
```python
# Remove duplicates while preserving order
# Use (name, line_number, class_name) as unique identifier instead of the object itself
seen = set()
result = []
for func in uncertain_functions:
    func_id = (func.name, func.line_number, func.class_name)
    if func_id not in seen:
        seen.add(func_id)
        result.append(func)
```

**Improvement Explanation:**
- Use the tuple `(name, line_number, class_name)` as the unique identifier for a function
- Tuples are hashable and can be safely added to a set
- This combination is sufficient to uniquely identify a test function (there won't be two functions with the same name at the same line in the same file)

### 2. Update Unit Tests

**File:** `tests/test_uncertain_case_detector.py`

**Main Changes:**

1. **Update mock function creator** (lines 15-28):
   - Add `line_number` and `class_name` parameters
   - Remove unused `unique_id` field
   - Remove `uuid` module import

2. **Update test method names and implementations:**
   - `test_are_similar_functions` → `test_calculate_name_similarity`
   - `test_has_unusual_patterns` → `test_has_test_smells` + `test_has_unusual_decorator_patterns`

3. **Adjust test parameters:**
   - Add `line_number` parameter to all mock functions to ensure uniqueness
   - Add `class_name` parameter to functions requiring similarity detection
   - Adjust assertion counts to match new threshold (min_assertions=5)
   - Adjust decorator counts to match new threshold (min_decorators=4)

## Rebuild and Deployment Steps

### Step 1: Rebuild Docker Image

```bash
cd /Users/efan404/Codes/courses/CityU_CS5351/LLT-Assistant-Backend

# Rebuild image
docker-compose build api

# Or use no-cache build (ensures latest code is used)
docker-compose build --no-cache api
```

### Step 2: Restart Services

```bash
# Stop and restart services
docker-compose down
docker-compose up -d

# Or restart only API service
docker-compose restart api
```

### Step 3: Verify Fix

```bash
# 1. Check health status
curl http://localhost:8886/health

# 2. Test quality analysis endpoint
curl -X POST http://localhost:8886/quality/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "files": [
      {
        "path": "test_sample.py",
        "content": "def test_example():\n    assert True\n"
      }
    ],
    "mode": "hybrid"
  }'

# Expected response:
# {
#   "analysis_id": "...",
#   "summary": {"total_files": 1, "total_issues": 0, "critical_issues": 0},
#   "issues": []
# }
```

### Step 4: Test in VSCode Extension

1. Reload VSCode window
2. Open test project
3. Click "Analyze" button in LLT Quality sidebar
4. Confirm analysis completes successfully without 503 errors

## Verification Checklist

- [ ] Code changes applied to `uncertain_case_detector.py`
- [ ] Unit tests updated
- [ ] Docker image rebuilt
- [ ] Services restarted
- [ ] Health check returns "healthy"
- [ ] Quality analysis API test successful
- [ ] VSCode extension functions normally

## Technical Details

### Why is TestFunctionInfo Not Hashable?

In Python, for an object to be hashable it must satisfy:
1. Implement `__hash__()` method
2. Implement `__eq__()` method
3. The object's hash value must remain constant during its lifetime

The `TestFunctionInfo` dataclass contains mutable fields (List, Dict, etc.), whose modifications would change the hash value, so Python does not automatically generate a `__hash__` method for it.

### Why Use (name, line_number, class_name) as ID?

This combination has the following properties:
- **Uniqueness**: Within the same file, there won't be two functions with the same name at the same line
- **Immutability**: All are primitive types (str, int) and are hashable
- **Semantic Correctness**: Accurately identifies the function's position in the code

## Related Files

- Fix file: `app/core/analysis/uncertain_case_detector.py`
- Test file: `tests/test_uncertain_case_detector.py`
- API routes: `app/api/v1/routes.py`
- Service layer: `app/core/services/quality_service.py`
