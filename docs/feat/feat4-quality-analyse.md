# Feature 4: Quality Analysis

**Owner:** Backend Team
**Status:** Production Ready

## 1. Objective

Feature 4 provides comprehensive quality analysis for pytest test files, detecting common test code smells and providing actionable fix suggestions to improve test quality and maintainability.

## 2. Technical Overview

**API Endpoint(s):**
- `POST /quality/analyze` - Batch analysis of multiple test files with embedded fix suggestions

**Core Backend Service(s):**
- `app.core.services.quality_service.QualityAnalysisService` - Main service orchestrating quality analysis workflow
- `app.analyzers.rule_engine.RuleEngine` - Executes 6 detection rules for common test issues
- `app.core.analyzer.TestAnalyzer` - Parses test files into AST and coordinates analysis strategies
- `app.core.graph.graph_service.GraphService` - Optional Neo4j integration for enhanced mock detection

**Key Logic Flow:**

1. **Request Received**: The API route handler (`app/api/v1/routes.py:350`) receives a `QualityAnalysisRequest` containing test files and analysis mode (fast/deep/hybrid)

2. **Service Initialization**: `QualityAnalysisService.analyze_batch()` is called with resource management via async context manager to ensure proper cleanup

3. **Graph-Based Enhancement (Optional)**: If Neo4j is configured, the service queries the graph database to fetch dependency data for each test function, enabling more accurate mock detection

4. **Rule Engine Analysis**: The service invokes `TestAnalyzer.analyze_files()` which:
   - Parses each file into an Abstract Syntax Tree (AST)
   - Executes 6 quality detection rules:
     * **Redundant Assertion Rule**: Detects duplicate assertions in the same test
     * **Missing Assertion Rule**: Identifies tests without any verification logic
     * **Trivial Assertion Rule**: Finds assertions that always pass (e.g., `assert True`)
     * **Unused Fixture Rule**: Detects fixture definitions that are never used
     * **Unused Variable Rule**: Identifies variables assigned but never referenced
     * **Missing Mock Rule**: Detects tests calling external dependencies without proper mocking (enhanced by Neo4j graph data)

5. **Issue Conversion**: Raw issues from TestAnalyzer are converted to `QualityIssue` format with:
   - File path and line number
   - Severity level (error/warning/info)
   - Issue code (e.g., "redundant-assertion")
   - Human-readable message
   - Fix suggestion with actionable code changes (type: replace/delete/insert)
   - Detection source (rule-based or LLM-based)

6. **Response Construction**: A `QualityAnalysisResponse` is built containing:
   - Unique analysis ID for tracking
   - Summary statistics (total files, total issues, critical issues)
   - Complete list of detected issues with embedded fix suggestions

**Analysis Modes:**
- **Fast (rules-only)**: Runs only the 6 deterministic rules, fastest execution (~100-200ms)
- **Deep (LLM-only)**: Uses Large Language Model for semantic analysis, slower but more comprehensive (~2-5 seconds)
- **Hybrid (recommended)**: Combines both rule-based and LLM analysis for balanced accuracy and performance (~500ms-1s)

**Neo4j Integration:**
- Feature 4 uses Neo4j **optionally** for enhanced mock detection
- If Neo4j is unavailable, gracefully falls back to AST-based analysis
- Graph-based analysis provides ~2x better accuracy for detecting missing mocks by following call chains across files
- Unlike Feature 3 (Impact Analysis) where Neo4j is mandatory, Feature 4 maintains full functionality without it

## 3. Data Models (Schemas)

**Request:** `QualityAnalysisRequest`
```python
{
  "files": [              # Array of files to analyze (1-10 files)
    {
      "path": str,        # File path relative to workspace
      "content": str      # Complete file content
    }
  ],
  "mode": str            # "fast" | "deep" | "hybrid" (default: "hybrid")
}
```

**Response:** `QualityAnalysisResponse`
```python
{
  "analysis_id": str,    # Unique identifier for this analysis
  "summary": {
    "total_files": int,
    "total_issues": int,
    "critical_issues": int  # Count of "error" severity issues
  },
  "issues": [            # Array of detected quality issues
    {
      "file_path": str,
      "line": int,       # 1-based line number
      "column": int,     # Optional column number
      "severity": "error" | "warning" | "info",
      "code": str,       # Machine-readable issue code
      "message": str,    # Human-readable description
      "detected_by": "rule" | "llm",
      "suggestion": {    # Optional fix suggestion
        "type": "replace" | "delete" | "insert",
        "new_text": str,
        "description": str  # Explanation of the fix
      }
    }
  ]
}
```

For complete schema definitions, see `docs/api/openapi.yaml` sections for Quality Analysis (lines 455-479 and components 1034-1127).

## 4. Known Issues & Areas for Improvement

**Current Limitations:**

1. **No `severity_breakdown` in API Response**: The service internally tracks issue counts by severity (error/warning/info) for logging purposes, but this breakdown is not currently exposed in the API response. This is planned for a future version but requires API versioning strategy first.

2. **Limited Transitive Dependency Analysis**: The Neo4j-enhanced mock detection currently analyzes only direct dependencies (1-level deep). Future versions could implement 2-3 level transitive analysis to catch indirect external dependencies, though this increases query complexity and latency.

3. **Python-Only Support**: Currently only supports Python/pytest test files. Multi-language support (JavaScript/Jest, Java/JUnit) would require significant extensions to the AST parsing and rule engine architecture.

4. **No Custom Rule API**: Organizations cannot currently define project-specific quality rules. A plugin system for custom rules would improve flexibility but requires careful design to maintain performance and security.

5. **Manual Fix Application**: Fix suggestions are provided but must be manually applied by developers (or integrated into IDE plugins). Automatic fix application with safety checks could improve developer experience.

**Future Enhancements:**

- **Severity Breakdown Endpoint**: Add optional query parameter to include detailed severity statistics in response
- **Custom Rule System**: Plugin architecture allowing teams to define organization-specific quality rules
- **IDE Integration**: VS Code extension to show quality issues inline with automatic fix application
- **Coverage Correlation**: Link quality issues to code coverage data to prioritize fixing issues in uncovered code
- **Batch Project Analysis**: Analyze entire project structure in single request for holistic quality assessment
- **Historical Trending**: Track quality metrics over time to identify regression patterns
- **Performance Optimization**: Implement caching layer for repeated analyses of unchanged files

**Performance Considerations:**

- Fast mode handles 10 files in <300ms (pure AST parsing)
- Hybrid mode with Neo4j adds ~200ms overhead for graph queries
- Large files (>1000 lines) may cause AST parsing to exceed 500ms
- Consider implementing parallel file processing for batch requests

**Related Documentation:**

- Full architectural details: `docs/feat/feat4-quality-analyse-detailed.md` (comprehensive 797-line analysis)
- Neo4j integration guide: `docs/context/neo4j-integration.md`
- Testing guide: `tests/unit/test_feat4_api.py` and `tests/integration/test_quality_with_graph.py`
