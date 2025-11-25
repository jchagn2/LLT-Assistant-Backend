# Code Dependency Parsing Integration

## Overview

This document describes how the backend integrates with frontend LSP (Language Server Protocol) parsers to extract and store code dependencies in Neo4j.

## Workflow

```
Frontend LSP Parser
    ↓ (extracts symbols)
JSON Payload
    ↓ (HTTP POST)
Backend /debug/ingest-symbols
    ↓ (stores in)
Neo4j Graph Database
```

## LSP Parser Output Format

The frontend parser extracts code structure and sends JSON like this:

```json
{
  "file_path": "/path/to/file.py",
  "extraction_time_ms": 2,
  "functions": [
    {
      "name": "calculate_tax",
      "kind": "function",
      "signature": "(price: float, region: str) -> float",
      "line_start": 3,
      "line_end": 7,
      "calls": ["get_tax_rate", "validate_price"],
      "decorates": []
    }
  ],
  "imports": [
    {
      "module": "decimal",
      "imported_names": ["Decimal"],
      "alias": null
    }
  ]
}
```

## Backend Transformation

The backend converts LSP output to Neo4j graph format:

### Input: LSP Format
```json
{
  "functions": [
    {"name": "func_a", "calls": ["func_b", "func_c"]}
  ]
}
```

### Output: Neo4j Format
```json
{
  "symbols": [
    {
      "name": "func_a",
      "qualified_name": "module.func_a",
      "kind": "function",
      "signature": "func_a() -> None",
      "file_path": "/path/to/file.py",
      "line_start": 10,
      "line_end": 20
    }
  ],
  "calls": [
    {
      "caller_qualified_name": "module.func_a",
      "callee_qualified_name": "module.func_b",
      "line": 12
    }
  ],
  "imports": [...]
}
```

## Key Transformations

1. **Qualified Names**: Convert simple names to fully qualified (e.g., `func` → `module.ClassName.func`)
2. **Symbol Nodes**: Each function/class/method becomes a Symbol node
3. **Call Relationships**: Each call in the `calls` array becomes a CALLS relationship
4. **Import Tracking**: Import statements become IMPORTS relationships

## API Contract

### POST /debug/ingest-symbols

**Request Body:**
```json
{
  "project_id": "string",
  "symbols": [SymbolNode],
  "calls": [CallRelationship],
  "imports": [ImportRelationship]
}
```

**Response:**
```json
{
  "nodes_created": 3,
  "relationships_created": 5,
  "processing_time_ms": 150,
  "project_id": "test-project"
}
```

## Integration Example

### 1. Frontend Parses Code
```typescript
// Using LSP or Python AST parser
const symbols = await parseFile("my_module.py");
```

### 2. Frontend Sends to Backend
```typescript
await fetch('http://localhost:8886/debug/ingest-symbols', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_id: 'my-project',
    symbols: transformToSymbols(symbols),
    calls: extractCalls(symbols),
    imports: extractImports(symbols)
  })
});
```

### 3. Backend Stores in Neo4j
```python
# Automatically creates graph structure
# - Symbol nodes
# - CALLS relationships
# - IMPORTS relationships
```

### 4. Query Dependencies
```bash
curl "http://localhost:8886/debug/query-function/calculate_tax?project_id=my-project"
```

## Tools Used

- **Frontend**: LSP (Language Server Protocol) or Python AST parser
- **Backend**: FastAPI + Neo4j Python driver
- **Database**: Neo4j 5.13+ graph database

## Data Flow

```
Source Code (.py files)
    ↓
LSP Parser / AST Analyzer
    ↓
JSON (functions, calls, imports)
    ↓
Backend API Transformation
    ↓
Neo4j Graph (nodes + relationships)
    ↓
Query API
    ↓
Dependency Graph Results
```

## Benefits

1. **Fast Queries**: Graph database optimized for relationship queries
2. **Scalable**: Can handle large codebases
3. **Flexible**: Easy to add new relationship types
4. **Persistent**: Data survives restarts
5. **Visual**: Can visualize in Neo4j Browser

## Next Steps

- Add more relationship types (inheritance, interfaces)
- Support incremental updates (only changed files)
- Add graph visualization API
- Integrate with test impact analysis
