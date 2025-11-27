# Neo4j Graph Database Integration

## Overview

This project integrates **Neo4j 5.13+** graph database to store and query code dependency relationships. This enables tracking function calls, imports, and code structure for analysis.

## What It Does

- **Store Code Symbols**: Functions, classes, methods from parsed code
- **Track Dependencies**: Which functions call which other functions
- **Query Relationships**: Fast lookups of code dependencies and call graphs
- **Multi-Project Support**: Isolate data by project using `project_id`

## Technology Stack

### New Dependencies

```toml
neo4j>=5.13.0  # Official Python driver for Neo4j
```

### Architecture

```
Frontend (LSP Parser)
    ↓ (sends symbols + relationships)
POST /debug/ingest-symbols
    ↓
GraphService (app/core/graph/graph_service.py)
    ↓
Neo4jClient (app/core/graph/neo4j_client.py)
    ↓
Neo4j Database (Docker container)
```

## Data Model

### Nodes
- **Symbol**: Represents code elements (functions, classes, methods)
  - Properties: `name`, `qualified_name`, `kind`, `signature`, `file_path`, `line_start`, `line_end`, `project_id`

### Relationships
- **CALLS**: `(FunctionA)-[:CALLS]->(FunctionB)` - Function call dependencies
- **IMPORTS**: `(File)-[:IMPORTS]->(Module)` - Import statements

## API Endpoints

### 1. Ingest Code Symbols
```
POST /debug/ingest-symbols
```
**Purpose**: Store parsed code symbols and their relationships

**Input**: JSON with symbols, calls, imports from LSP/parser

**Output**: Statistics (nodes_created, relationships_created, processing_time_ms)

### 2. Query Function Dependencies
```
GET /debug/query-function/{function_name}?project_id=...
```
**Purpose**: Get a function and all functions it calls

**Output**: Function info + list of dependencies + query time

### 3. Health Check
```
GET /debug/health/neo4j
```
**Purpose**: Verify Neo4j connection status

## Quick Start

### 1. Start Services
```bash
docker-compose up -d
# Starts: Redis, Neo4j, API
```

### 2. Access Neo4j Browser
- URL: http://localhost:7474
- Login: neo4j/neo4j123

### 3. Test API
```bash
# Ingest symbols
curl -X POST http://localhost:8886/debug/ingest-symbols \
  -H "Content-Type: application/json" \
  -d '{"project_id":"test","symbols":[...],"calls":[],"imports":[]}'

# Query function
curl "http://localhost:8886/debug/query-function/my_function?project_id=test"
```

## Configuration

Environment variables in `.env`:
```env
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j123
NEO4J_DATABASE=neo4j
```

## File Locations

```
app/core/graph/
├── neo4j_client.py      # Neo4j connection management
└── graph_service.py     # Business logic for symbols

app/api/v1/
├── debug_routes.py      # Debug API endpoints
└── schemas.py           # Pydantic models (Neo4j section at end)

docker-compose.yml       # Neo4j service configuration
```

## Performance

- Batch insert: < 2 seconds for 100 nodes + 200 relationships
- Query latency: < 100ms for typical queries
- Memory: < 500MB

## Testing

```bash
# Unit tests (no Neo4j needed)
pytest tests/unit/core/graph/

# Integration tests (requires Neo4j running)
pytest tests/integration/test_neo4j_integration.py -m integration
```

## Use Cases

1. **Dependency Analysis**: Find all functions a given function depends on
2. **Impact Analysis**: Determine which tests to run when code changes
3. **Code Navigation**: Visualize call graphs and module relationships
4. **Refactoring**: Identify tightly coupled code

## Notes

- This is **Phase 0** - validation/testing phase
- Data persists in Docker volumes (`neo4j-data`)
- Uses MERGE instead of CREATE to avoid duplicates
- Transactions ensure atomic operations
- Indexes automatically created on startup
