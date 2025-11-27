# Feature 3: Impact Analysis

**Owner:** Backend Team
**Status:** Production Ready
**Last Updated:** 2025-11-26 (v1.2 - Functional/Non-Functional Classification)

## 1. Objective

Intelligent test impact assessment using Neo4j-powered reverse dependency analysis to determine which tests may be affected by code changes. This feature helps developers understand test execution requirements by identifying potentially impacted tests based on source code modifications.

## 2. Technical Overview

**API Endpoint(s):**
- `POST /analysis/impact` (routes.py:418-500) - Main impact analysis endpoint
- Returns 503 Service Unavailable if Neo4j is not accessible
- Accepts optional git diff for function-level precision extraction

**Core Backend Service(s):**
- `app.core.analyzer.ImpactAnalyzer` (analyzer.py:245) - Main orchestrator for impact calculation
- `app.core.graph.graph_service.GraphService` - Neo4j graph database client for reverse dependency queries
- `app.core.utils.diff_parser.DiffParser` - Parser for extracting modified function names from git unified diff format

**Key Logic Flow:**

1. **Request Received**: The API route handler (`app/api/v1/routes.py:418`) receives an `ImpactAnalysisRequest` containing project context (changed files, related tests) and optional git diff

2. **Service Initialization**: `ImpactAnalyzer` is initialized with async context manager for proper resource management and Neo4j connection handling

3. **Function Extraction from Diff**: If a git diff is provided, `DiffParser` extracts modified function names by parsing lines starting with '+def' to identify new or changed function definitions. This enables function-level granularity instead of file-level analysis.

4. **Change Classification (Enhanced v1.2)**: Modified functions are classified as functional or non-functional using a hybrid approach:
   - **Heuristic Stage**: Fast pattern matching (~5ms) identifies obvious non-functional changes (comments, docstrings, whitespace, imports)
   - **AST Stage**: Semantic analysis (~30-50ms) for ambiguous cases by comparing old vs new AST structures
   - **Classification**: Changes marked as "functional", "non-functional", or "mixed"

5. **Query Graph Database**: For each **functional** change, Neo4j reverse dependency queries are executed to find:
   - **Direct callers**: Functions that directly call the modified function
   - **Transitive callers**: Functions that indirectly depend on the modified function through 2-level call chains
   - **Note**: Non-functional changes skip graph queries for performance

6. **Detect Direct Impacts**: Tests that directly test modified functions are identified and assigned:
   - Impact score: 0.9 (high confidence)
   - Severity: high
   - Reason: "Test directly tests modified function X"

7. **Detect Transitive Dependencies**: Tests that indirectly depend on modified functions through call chains are identified:
   - Impact score: 0.7 (medium confidence)
   - Severity: medium
   - Reason: "Test calls function A, which depends on modified function X"
   - Limited to 2-level traversal to balance accuracy and performance

8. **Handle Non-Functional Changes (Enhanced v1.2)**: Non-functional changes receive special treatment:
   - Impact score: 0.1 (informational)
   - Severity: informational
   - No graph queries performed
   - Reason: "Non-functional change in X: Comment-only changes"

9. **Add Modified Test Files**: Test files directly changed in the commit are included:
   - Impact score: 1.0 (certain)
   - Severity: high
   - Reason: "Test file was directly modified"

10. **Calculate Overall Severity**: Based on the number and severity of impacted tests, determine:
   - Overall severity: none/low/medium/high/informational
   - Suggested action: no-action/run-affected-tests/run-all-tests
   - **Note**: Informational-only changes always result in "no-action"

11. **Response Construction**: An `ImpactAnalysisResponse` is returned containing all impacted tests with scores, reasons, and recommended actions

**Neo4j Dependency:**
- Neo4j is **mandatory** for Feature 3 to function
- If Neo4j is unavailable, the endpoint returns 503 Service Unavailable
- No fallback mechanism currently implemented (unlike Feature 4 which has graceful degradation)
- Requires populated graph with project symbols and call relationships from prior ingestion

## 3. Data Models (Schemas)

**Request:** `ImpactAnalysisRequest`
```python
{
  "project_context": {      # Required: Project and change context
    "files_changed": [      # List of modified file paths
      "src/checkout.py",
      "src/payment.py"
    ],
    "related_tests": [      # Optional: Known related tests from static analysis
      "tests/test_checkout.py"
    ]
  },
  "git_diff": str,          # Optional: Unified diff format for function-level extraction
  "project_id": str         # Optional: Project identifier (default: "default")
}
```

**Response:** `ImpactAnalysisResponse`
```python
{
  "impacted_tests": [       # List of potentially impacted test files
    {
      "test_path": str,     # Path to test file (e.g., "tests/test_checkout.py")
      "impact_score": float, # Confidence score 0.0-1.0 (0.7=medium, 0.9=high, 1.0=certain)
      "severity": "high" | "medium" | "low" | "informational" | "none",
      "reasons": [           # List of explanations for why this test is impacted
        "Test directly tests modified function process_payment",
        "Test calls calculate_tax, which depends on modified function get_tax_rate"
      ]
    }
  ],
  "severity": "none" | "low" | "medium" | "high" | "informational",  # Overall impact severity
  "suggested_action": str   # "no-action" | "run-affected-tests" | "run-all-tests"
}
```

**Nested Schema:** `ProjectImpactContext`
- `files_changed: List[str]` - Required, list of modified file paths relative to project root
- `related_tests: List[str]` - Optional, statically known related tests

**Nested Schema:** `ImpactItem`
- `test_path: str` - Required, path to potentially impacted test file
- `impact_score: float` - Required, confidence score between 0.0 and 1.0
- `severity: "low" | "medium" | "high" | "informational" | "none"` - Required, impact severity classification
- `reasons: List[str]` - Required, list of human-readable explanations (empty array if no specific reasons, never null)

For complete schema definitions with validation rules, see `docs/api/openapi.yaml` lines 1186+

**Impact Scoring Algorithm (Enhanced v1.2):**
- **1.0**: Test file was directly modified in the changeset
- **0.9**: Test directly tests a modified function (direct dependency detected in graph)
- **0.7**: Test indirectly depends on modified function through 1 intermediate function
- **0.5**: Test indirectly depends on modified function through 2 intermediate functions
- **0.3**: Test file is in related_tests but no graph connection found (heuristic match)
- **0.1**: Non-functional change only (comments, docstrings, whitespace) - informational severity

## 4. Known Issues & Areas for Improvement

**Fixed in v1.2 (2025-11-26):**
- ✅ **Functional vs Non-Functional Distinction**: Now implemented using hybrid classification (heuristics + AST semantic analysis)
- ✅ **False Positives from Formatting Changes**: Resolved by detecting non-functional changes and marking them as "informational"
- ✅ **Comment/Docstring Changes Treated as High Impact**: Fixed - now correctly identified as non-functional with impact_score=0.1

**Current Limitations:**

1. **Mandatory Neo4j Dependency**: Neo4j is required for Feature 3 to function. If the graph database is unavailable, the endpoint returns 503 Service Unavailable with no fallback mechanism. This makes the feature non-functional in environments where Neo4j cannot be deployed or is temporarily down.

2. **Transitive Depth Limited to 2 Levels**: The current implementation only follows call chains up to 2 levels deep (test → intermediate_function → modified_function). This misses deeper transitive dependencies like test → A → B → C → modified_function, potentially causing false negatives where relevant tests are not identified.

3. **AST Analysis Limitations** (NEW in v1.2): While AST analysis significantly improves classification accuracy, it has some limitations:
   - Cannot detect semantic equivalence (e.g., `x + 1` vs `1 + x` are treated as different)
   - Macros and code generation are not analyzed
   - Type-only changes (annotations) may be misclassified as functional
   - Performance: AST mode adds ~30-50ms per ambiguous file (mitigated by heuristic first-pass)

4. **Heuristic Pattern Limitations** (NEW in v1.2): The heuristic classifier may have edge cases:
   - May miss complex non-functional changes (e.g., reordered imports with side effects)
   - False negatives possible for unusual formatting patterns
   - Import changes treated as non-functional (may not always be accurate for imports with side effects)

5. **Diff Parsing Limitations**: The DiffParser detects function definition changes but has gaps:
   - Modifications to existing function bodies without signature changes require careful analysis
   - Refactorings that rename functions are not tracked across commits
   - Class method changes require both function detection and class context parsing
   - Non-function changes (global variables, class attributes) receive file-level classification

6. **No Caching**: Function extraction and classification from git diffs is performed on every request without caching. For repeated analyses of the same changeset (e.g., during CI/CD retries), this results in redundant parsing work.

7. **Linear Scaling Performance**: Query time scales linearly with the number of modified functions. A changeset touching 50 functions could take 5-10 seconds to analyze, which may be too slow for interactive use cases.

8. **Path Normalization Issues**: The system assumes file paths in the graph database exactly match paths in the request. Path format inconsistencies (absolute vs relative, leading slashes, symlinks) can cause false negatives.

9. **No Historical Analysis**: The feature only analyzes current state without considering historical test failure patterns. Tests that frequently fail together with certain changes could receive higher impact scores based on machine learning from past data.

**Future Enhancements:**

- **Graceful Fallback Mode**: Implement heuristic-based fallback when Neo4j is unavailable, using file path matching and simple string searching for function calls
- **Configurable Transitive Depth**: Allow clients to specify traversal depth (1-5 levels) with pagination for large result sets
- **Classification Improvements** (v1.2+):
  - Machine learning models trained on historical changes to improve classification accuracy
  - Configurable heuristic patterns for project-specific non-functional patterns
  - Visual diff UI showing why changes were classified a certain way
  - Cross-language support (JavaScript, TypeScript, etc.)
- **Intelligent Caching**: Cache function extraction and classification results keyed by git diff hash to improve performance for repeated analyses
- **Batch Query Optimization**: Use Neo4j batch queries and parallel execution for analyzing large changesets (50+ functions)
- **ML-Based Impact Scoring**: Train models on historical test failures to improve impact score accuracy based on past correlations
- **Path Normalization Layer**: Automatically normalize all file paths to a canonical format before graph queries
- **Incremental Graph Updates**: Support real-time graph updates as code changes occur, reducing staleness
- **Change Pattern Recognition**: Identify common change patterns (e.g., "adding parameter to widely-used utility function") and suggest broader test suites

**Performance Considerations:**

- **Typical Performance (v1.2)**: 160-320ms for changesets with 3 modified functions and 2 transitive dependencies
  - Baseline (v1.1): 150-300ms
  - Classification overhead: +10-20ms (heuristic mode handles 80% of cases quickly)
- **Large Changesets**: 100+ modified functions can take 5-10 seconds, consider async processing
- **Graph Query Latency**: Each reverse dependency query takes 30-80ms depending on graph density
- **Classification Performance** (v1.2):
  - Heuristic-only: <5ms per file (80% of cases)
  - AST analysis: 30-50ms per ambiguous file (20% of cases)
  - Overall overhead: <10% increase in average latency
- **Memory Usage**: Impact analysis for typical changesets uses <50MB memory
- **Recommendation**: For changesets with >20 modified functions, consider moving to async task processing

**Performance Impact by Change Type (v1.2):**

| Change Type | Baseline (v1.1) | With Classification (v1.2) | Overhead |
|------------|----------------|---------------------------|----------|
| Small (1-3 files) | 150-200ms | 160-220ms | +10-20ms |
| Medium (5-10 files) | 250-300ms | 280-350ms | +30-50ms |
| Large (20+ files) | 500-800ms | 550-900ms | +50-100ms |

*Note: Performance overhead is minimal due to two-stage classification (heuristics first, AST only when needed)*

**Related Documentation:**

- Comprehensive architectural analysis: `docs/feat/feat3-impact-analysis-detailed.md` (1,205-line deep dive)
- Neo4j integration guide: `docs/context/neo4j-integration.md`
- DiffParser implementation: `app/core/utils/diff_parser.py`
- ChangeClassifier implementation (v1.2): `app/core/utils/change_classifier.py`
- Testing guide: `tests/unit/test_feat3_api.py` and `tests/integration/test_graph_based_impact.py`
- ChangeClassifier tests (v1.2): `tests/unit/core/utils/test_change_classifier.py`
- API specification: `docs/api/openapi.yaml` sections 1186-1295
