# Coding Standards for LLT-Assistant-Backend

This document outlines the coding standards and conventions for the LLT-Assistant-Backend project. All contributors and AI assistants working on this codebase must follow these guidelines.

---

## 1. Language Requirements

### 1.1 Code Documentation
- **All code comments MUST be in English**
- **All docstrings MUST be in English**
- **All inline comments MUST be in English**
- **All variable, function, class, and module names MUST use English words**

### 1.2 Documentation Files
- README.md, API documentation, and all Markdown files MUST be in English
- OpenAPI/Swagger specifications MUST use English descriptions
- Error messages MUST be in English
- Log messages MUST be in English

### 1.3 Git Commit Messages
- All commit messages MUST be in English
- Follow conventional commits format: `type(scope): description`
- Examples:
  - `feat(api): add new endpoint for test generation`
  - `fix(analyzer): resolve issue with redundant assertion detection`
  - `test(integration): add end-to-end workflow tests`

---

## 2. AI Assistant Guidelines

### 2.1 Tool References
- **NEVER include references to Claude Code or any AI assistant tools in:**
  - Code comments
  - Docstrings
  - Commit messages
  - Documentation files
  - Git commit co-author tags
  - README or changelog entries

### 2.2 Attribution
- Do NOT add "Generated with Claude Code" or similar tags
- Do NOT add "Co-Authored-By: Claude" in commits
- Code should appear as if written by human developers

---

## 3. Python Code Standards

### 3.1 Docstrings
Follow PEP 257 conventions with Google-style or NumPy-style docstrings:

```python
def analyze_test_file(file_path: str, mode: str = "hybrid") -> dict:
    """
    Analyze a pytest test file for quality issues.

    Args:
        file_path: Path to the test file to analyze
        mode: Analysis mode - "rules-only", "llm-only", or "hybrid"

    Returns:
        Dictionary containing analysis results with issues and metrics

    Raises:
        FileNotFoundError: If the specified file does not exist
        ValueError: If mode is not one of the valid options
    """
    pass
```

### 3.2 Comments
- Use clear, descriptive comments in English
- Explain WHY, not WHAT (code should be self-documenting for WHAT)
- Bad example: `# Loop through files` (obvious from code)
- Good example: `# Skip hidden files to avoid processing system metadata`

### 3.3 Type Hints
- Use type hints for all function signatures
- Use `from typing import` for complex types
- Example:
```python
from typing import List, Dict, Optional

def process_issues(
    issues: List[Dict[str, Any]],
    severity_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Process and filter issues based on severity."""
    pass
```

---

## 4. Testing Standards

### 4.1 Test Names
- Test function names MUST be in English
- Use descriptive names following pattern: `test_<what>_<condition>_<expected>`
- Examples:
  - `test_analyze_endpoint_with_empty_files_returns_400`
  - `test_rule_engine_detects_redundant_assertions`
  - `test_llm_client_retries_on_timeout`

### 4.2 Test Documentation
- Test docstrings MUST be in English
- Assert messages MUST be in English
- Example:
```python
def test_analyzer_handles_syntax_errors():
    """
    Verify that the analyzer gracefully handles files with syntax errors.

    The analyzer should return a specific error issue rather than crashing.
    """
    result = analyzer.analyze("invalid python code @#$")
    assert "syntax_error" in result["issues"][0]["type"], \
        "Expected syntax error to be reported"
```

### 4.3 Test Data
- Test fixture files should use English identifiers
- Comments in test data files MUST be in English

---

## 5. API and Error Handling

### 5.1 Error Messages
All error messages returned by the API MUST be in English:

```python
raise ValueError(
    f"Invalid analysis mode '{mode}'. "
    f"Expected one of: rules-only, llm-only, hybrid"
)
```

### 5.2 API Response Messages
```python
{
    "error": "File size exceeds maximum limit of 1MB",
    "detail": "Please reduce file size or split into multiple requests"
}
```

### 5.3 Log Messages
All log entries MUST be in English:

```python
logger.info("Starting analysis of %d files in %s mode", file_count, mode)
logger.warning("LLM API timeout, retrying request (attempt %d/%d)", attempt, max_retries)
logger.error("Failed to parse AST: %s", error_message)
```

---

## 6. Code Style

### 6.1 Formatting
- Follow PEP 8 style guidelines
- Use Black for automatic formatting (line length: 100)
- Use isort for import sorting
- Run pre-commit hooks before committing

### 6.2 Naming Conventions
- Classes: `PascalCase` (e.g., `TestAnalyzer`, `RuleEngine`)
- Functions/methods: `snake_case` (e.g., `analyze_file`, `generate_suggestion`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_FILE_SIZE`, `DEFAULT_TIMEOUT`)
- Private methods: prefix with `_` (e.g., `_parse_response`, `_validate_input`)

### 6.3 File Organization
```python
# Standard library imports
import os
import sys
from typing import List, Dict

# Third-party imports
import httpx
from fastapi import FastAPI

# Local application imports
from app.core.analyzer import TestAnalyzer
from app.models.schemas import AnalysisRequest
```

---

## 7. Documentation Requirements

### 7.1 Module Docstrings
Every Python module should have a module-level docstring:

```python
"""
Test analyzer module for detecting quality issues in pytest test files.

This module provides the main TestAnalyzer class which orchestrates
rule-based and LLM-based analysis to identify test code smells.
"""
```

### 7.2 README Updates
When adding new features, update README.md with:
- Feature description in English
- Usage examples in English
- Configuration options in English

---

## 8. Examples

### 8.1 Good Example ✅
```python
class TestAnalyzer:
    """
    Main analyzer for detecting quality issues in pytest test files.

    This class orchestrates both rule-based and LLM-based analysis
    to provide comprehensive test quality feedback.
    """

    def analyze_files(self, files: List[str], mode: str) -> dict:
        """
        Analyze multiple test files for quality issues.

        Args:
            files: List of file paths to analyze
            mode: Analysis mode (rules-only, llm-only, or hybrid)

        Returns:
            Dictionary with analysis results and metrics
        """
        # Validate input parameters
        if not files:
            raise ValueError("File list cannot be empty")

        # Process each file
        results = []
        for file_path in files:
            result = self._analyze_single_file(file_path, mode)
            results.append(result)

        return self._merge_results(results)
```

### 8.2 Bad Example ❌
```python
class TestAnalyzer:
    # 这是测试分析器类

    def analyze_files(self, files, mode):
        # 循环处理文件
        results = []
        for f in files:
            # 分析单个文件
            r = self.analyze(f, mode)
            results.append(r)

        # Generated with Claude Code ❌
        return results
```

---

## 9. Enforcement

### 9.1 Pre-commit Hooks
The project uses pre-commit hooks to enforce:
- Code formatting (Black, isort)
- Type checking (mypy)
- Linting (flake8)

### 9.2 CI/CD Checks
GitHub Actions will verify:
- All tests pass
- Code coverage meets threshold
- No style violations
- Documentation builds successfully

### 9.3 Code Review
During code review, verify:
- All comments and docstrings are in English
- No AI assistant references are present
- Code follows naming conventions
- Error messages are user-friendly and in English

---

## 10. Summary Checklist

Before committing code, verify:

- [ ] All comments and docstrings are in English
- [ ] No references to Claude Code or AI assistants
- [ ] Function and variable names are in English
- [ ] Error messages are in English
- [ ] Log messages are in English
- [ ] Test names are descriptive and in English
- [ ] Type hints are present
- [ ] Code passes pre-commit hooks
- [ ] Documentation is updated if needed
- [ ] Commit message is in English and follows conventional commits

---

**Last Updated:** 2025-11-25
**Version:** 1.1

---

## 11. Neo4j Graph Database Integration (Phase 0)

### 11.1 Overview

The project now includes Neo4j 5.13+ for storing and querying code dependency graphs. This is currently in **Phase 0** (validation/debugging phase) to test Neo4j's suitability for code structure analysis.

### 11.2 Architecture

**Layered Design:**
```
API Layer:       app/api/v1/debug_routes.py (debug endpoints)
                 ↓
Service Layer:   app/core/graph/graph_service.py (business logic)
                 ↓
Client Layer:    app/core/graph/neo4j_client.py (connection pooling)
                 ↓
Database:        Neo4j 5.13+ (Docker container)
```

### 11.3 File Structure

```
app/core/graph/
├── __init__.py              # Module exports
├── neo4j_client.py         # Async Neo4j driver wrapper with connection pooling
└── graph_service.py        # High-level graph operations (ingest, query)

app/api/v1/
├── debug_routes.py         # Debug API endpoints (/debug/*)
└── schemas.py              # Pydantic models for Neo4j API (added at end)

tests/
├── unit/core/graph/
│   └── test_neo4j_client.py   # Unit tests for Neo4j client
├── unit/test_debug_api.py      # Unit tests for debug API
└── integration/
    └── test_neo4j_integration.py  # Integration tests (requires Neo4j)
```

### 11.4 Data Model

**Node: Symbol**
- Properties: `name`, `qualified_name`, `kind`, `signature`, `file_path`, `line_start`, `line_end`, `project_id`
- `qualified_name` has unique constraint (e.g., "module.ClassName.method_name")
- `kind` can be: "function", "class", "method"

**Relationship: CALLS**
- `(caller:Symbol)-[:CALLS {line: N}]->(callee:Symbol)`
- Represents function call dependencies

**Relationship: IMPORTS**
- `(file:Symbol)-[:IMPORTS {names: [...]}]->(module:Symbol)`
- Represents import statements

### 11.5 Debug API Endpoints

**POST /debug/ingest-symbols**
- Accepts code symbols and relationships from frontend
- Uses MERGE to avoid duplicates
- Transaction support for atomicity
- Returns: `nodes_created`, `relationships_created`, `processing_time_ms`

**GET /debug/query-function/{function_name}?project_id=...&depth=1**
- Query function and its dependencies (1-3 levels)
- Returns: function info, dependencies list, `query_time_ms`
- Returns 404 if function not found

**GET /debug/health/neo4j**
- Health check for Neo4j connectivity
- Returns 200 if healthy, 503 if unavailable

### 11.6 Performance Targets

- **Batch Insert**: 100 nodes + 200 relationships < 2 seconds
- **Query Latency**: < 100ms for single function query
- **Memory Usage**: < 500MB for typical workload

### 11.7 Configuration

**Environment Variables:**
```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123
NEO4J_DATABASE=neo4j
```

**Settings in app/config.py:**
- `neo4j_uri`, `neo4j_user`, `neo4j_password`, `neo4j_database`
- `neo4j_max_connection_lifetime`, `neo4j_max_connection_pool_size`
- `neo4j_connection_acquisition_timeout`

### 11.8 Usage Example

**Ingest Symbols:**
```bash
curl -X POST http://localhost:8886/debug/ingest-symbols \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "test-project",
    "symbols": [
      {
        "name": "calculate_tax",
        "qualified_name": "module.calculate_tax",
        "kind": "function",
        "signature": "(price: float) -> float",
        "file_path": "/app/utils.py",
        "line_start": 10,
        "line_end": 20
      }
    ],
    "calls": [],
    "imports": []
  }'
```

**Query Function:**
```bash
curl "http://localhost:8886/debug/query-function/calculate_tax?project_id=test-project"
```

### 11.9 Testing

**Unit Tests:**
```bash
pytest tests/unit/core/graph/ tests/unit/test_debug_api.py
```

**Integration Tests (requires running Neo4j):**
```bash
docker-compose up -d neo4j
pytest tests/integration/test_neo4j_integration.py -m integration
```

### 11.10 Key Implementation Details

**Async Transactions:**
```python
# Correct pattern for Neo4j async transactions
async with self.client.session() as session:
    tx = await session.begin_transaction()
    try:
        # Execute queries
        await tx.run(query, params)
        await tx.commit()
    except Exception:
        await tx.rollback()
        raise
```

**Context Manager for Resource Cleanup:**
```python
@asynccontextmanager
async def get_graph_service_context():
    service = GraphService()
    try:
        await service.connect()
        yield service
    finally:
        await service.close()
```

### 11.11 Indexing Strategy

**Automatically created on startup:**
1. Unique constraint on `Symbol.qualified_name` (prevents duplicates)
2. Index on `Symbol.name` (fast function lookup)
3. Index on `Symbol.project_id` (multi-tenant queries)

**Verify indexes in Neo4j Browser:**
```cypher
:schema
```

### 11.12 Common Pitfalls to Avoid

1. **Transaction Management**: Always await `session.begin_transaction()`
2. **Context Managers**: Don't wrap exceptions in async context managers
3. **MERGE vs CREATE**: Use MERGE to avoid duplicate nodes
4. **Qualified Names**: Ensure uniqueness across the codebase
5. **Project Isolation**: Always include `project_id` in queries

### 11.13 Future Enhancements (Post-Phase 0)

- Integrate with Feature 3 (Impact Analysis)
- Add more relationship types (INHERITS, IMPLEMENTS)
- Graph visualization endpoints
- Historical analysis and metrics tracking

---

For detailed Neo4j documentation, see `docs/context/neo4j-integration.md`
