# Documentation Context

This directory contains additional documentation for understanding the LLT-Assistant-Backend architecture and integrations.

## Documents

### [neo4j-integration.md](neo4j-integration.md)
**What**: Neo4j graph database integration
**Why**: Store and query code dependency relationships
**Tech**: Neo4j 5.13+, neo4j Python driver
**Status**: Phase 0 (validation/testing)

### [code-parsing-integration.md](code-parsing-integration.md)
**What**: How frontend LSP parsers integrate with backend
**Why**: Convert parsed code to graph database format
**Tech**: LSP/AST parsers → FastAPI → Neo4j

## Quick Links

- Main coding standards: [CLAUDE.md](../../CLAUDE.md)
- API documentation: [README.md](../../README.md)
- Neo4j Browser: http://localhost:7474 (when running)

## For New Contributors

1. Read [CLAUDE.md](../../CLAUDE.md) - coding standards
2. Read [neo4j-integration.md](neo4j-integration.md) - understand graph database
3. Read [code-parsing-integration.md](code-parsing-integration.md) - data flow
4. Start services: `docker-compose up -d`
5. Test API: See examples in the docs above
