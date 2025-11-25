"""
Graph database service for managing code symbols and relationships.

This service provides high-level operations for storing and querying
code dependencies in the Neo4j graph database.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.core.graph.neo4j_client import Neo4jClient, Neo4jClientError

logger = logging.getLogger(__name__)


class GraphService:
    """
    Service for managing code symbols and dependencies in graph database.

    Provides methods for:
    - Ingesting symbol information (nodes and relationships)
    - Querying function dependencies
    - Performance optimization through indexing
    """

    def __init__(self, neo4j_client: Optional[Neo4jClient] = None):
        """
        Initialize graph service.

        Args:
            neo4j_client: Optional Neo4jClient instance
        """
        from app.core.graph.neo4j_client import create_neo4j_client

        self.client = neo4j_client or create_neo4j_client()
        self._connected = False

    async def connect(self) -> None:
        """Connect to Neo4j database."""
        if not self._connected:
            await self.client.connect()
            self._connected = True
            logger.info("GraphService connected to Neo4j")

    async def create_indexes(self) -> None:
        """
        Create indexes and constraints for performance optimization.

        Creates:
        - Unique constraint on Symbol.qualified_name
        - Index on Symbol.name
        - Index on Symbol.project_id
        """
        logger.info("Creating Neo4j indexes and constraints...")

        queries = [
            # Unique constraint on qualified_name
            """
            CREATE CONSTRAINT symbol_qualified_name_unique IF NOT EXISTS
            FOR (s:Symbol)
            REQUIRE s.qualified_name IS UNIQUE
            """,
            # Index on name for fast lookups
            """
            CREATE INDEX symbol_name_index IF NOT EXISTS
            FOR (s:Symbol)
            ON (s.name)
            """,
            # Index on project_id for multi-tenant queries
            """
            CREATE INDEX symbol_project_id_index IF NOT EXISTS
            FOR (s:Symbol)
            ON (s.project_id)
            """,
        ]

        for query in queries:
            try:
                await self.client.execute_query(query)
                logger.debug("Index/constraint created successfully")
            except Exception as e:
                logger.warning("Index creation skipped (may already exist): %s", e)

        logger.info("Index creation completed")

    async def ingest_symbols(
        self,
        symbols: List[Dict[str, Any]],
        calls: List[Dict[str, Any]],
        imports: List[Dict[str, Any]],
        project_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Ingest symbols and relationships into graph database.

        Uses MERGE to avoid duplicates and transactions for atomicity.

        Args:
            symbols: List of symbol nodes to create
            calls: List of CALLS relationships
            imports: List of IMPORTS relationships
            project_id: Project identifier

        Returns:
            Statistics dictionary with counts and processing time
        """
        start_time = time.time()

        logger.info(
            "Ingesting symbols: symbols=%d, calls=%d, imports=%d, project_id=%s",
            len(symbols),
            len(calls),
            len(imports),
            project_id,
        )

        nodes_created = 0
        relationships_created = 0

        async with self.client.session() as session:
            # Start transaction
            tx = await session.begin_transaction()
            try:
                # Create symbol nodes
                for symbol in symbols:
                    query = """
                    MERGE (s:Symbol {qualified_name: $qualified_name})
                    SET s.name = $name,
                        s.kind = $kind,
                        s.signature = $signature,
                        s.file_path = $file_path,
                        s.line_start = $line_start,
                        s.line_end = $line_end,
                        s.project_id = $project_id,
                        s.updated_at = datetime()
                    RETURN s
                    """

                    params = {
                        "qualified_name": symbol["qualified_name"],
                        "name": symbol["name"],
                        "kind": symbol["kind"],
                        "signature": symbol.get("signature", ""),
                        "file_path": symbol["file_path"],
                        "line_start": symbol["line_start"],
                        "line_end": symbol["line_end"],
                        "project_id": project_id,
                    }

                    result = await tx.run(query, params)
                    await result.data()
                    nodes_created += 1

                # Create CALLS relationships
                for call in calls:
                    query = """
                    MATCH (caller:Symbol {qualified_name: $caller_qualified_name})
                    MATCH (callee:Symbol {qualified_name: $callee_qualified_name})
                    MERGE (caller)-[r:CALLS {line: $line}]->(callee)
                    RETURN r
                    """

                    params = {
                        "caller_qualified_name": call["caller_qualified_name"],
                        "callee_qualified_name": call["callee_qualified_name"],
                        "line": call["line"],
                    }

                    result = await tx.run(query, params)
                    await result.data()
                    relationships_created += 1

                # Create IMPORTS relationships
                for imp in imports:
                    query = """
                    MATCH (file:Symbol {qualified_name: $file_qualified_name})
                    MERGE (module:Symbol {qualified_name: $module_qualified_name})
                    ON CREATE SET module.name = $module_name,
                                  module.kind = 'module',
                                  module.project_id = $project_id
                    MERGE (file)-[r:IMPORTS {names: $names}]->(module)
                    RETURN r
                    """

                    params = {
                        "file_qualified_name": imp["file_qualified_name"],
                        "module_qualified_name": imp["module_qualified_name"],
                        "module_name": imp["module_name"],
                        "names": imp["names"],
                        "project_id": project_id,
                    }

                    result = await tx.run(query, params)
                    await result.data()
                    relationships_created += 1

                # Commit transaction
                await tx.commit()
            except Exception as e:
                # Rollback on error
                await tx.rollback()
                logger.error("Transaction failed, rolling back: %s", e)
                raise

        processing_time_ms = int((time.time() - start_time) * 1000)

        logger.info(
            "Symbol ingestion completed: nodes=%d, relationships=%d, time_ms=%d",
            nodes_created,
            relationships_created,
            processing_time_ms,
        )

        return {
            "nodes_created": nodes_created,
            "relationships_created": relationships_created,
            "processing_time_ms": processing_time_ms,
        }

    async def query_function_dependencies(
        self,
        function_name: str,
        project_id: str = "default",
        depth: int = 1,
    ) -> Dict[str, Any]:
        """
        Query function and its dependencies.

        Args:
            function_name: Name of the function to query
            project_id: Project identifier
            depth: Depth of dependency traversal (1 = direct dependencies)

        Returns:
            Dictionary with function info and dependencies
        """
        start_time = time.time()

        logger.info(
            "Querying function dependencies: function=%s, project=%s, depth=%d",
            function_name,
            project_id,
            depth,
        )

        query = f"""
        MATCH (f:Symbol {{name: $function_name, project_id: $project_id}})
        WHERE f.kind IN ['function', 'method']
        OPTIONAL MATCH path = (f)-[:CALLS*1..{depth}]->(dep:Symbol)
        RETURN f, collect(DISTINCT dep) as dependencies
        """

        params = {
            "function_name": function_name,
            "project_id": project_id,
        }

        results = await self.client.execute_query(query, params)

        query_time_ms = int((time.time() - start_time) * 1000)

        if not results:
            logger.warning("Function not found: %s", function_name)
            return {
                "function": None,
                "dependencies": [],
                "query_time_ms": query_time_ms,
            }

        function_data = results[0]["f"]
        dependencies_data = results[0]["dependencies"]

        logger.info(
            "Query completed: dependencies=%d, time_ms=%d",
            len(dependencies_data),
            query_time_ms,
        )

        return {
            "function": function_data,
            "dependencies": dependencies_data,
            "query_time_ms": query_time_ms,
        }

    async def query_reverse_dependencies(
        self,
        function_name: str,
        project_id: str = "default",
    ) -> Dict[str, Any]:
        """
        Query which functions call this function (reverse lookup).

        Args:
            function_name: Name of the function
            project_id: Project identifier

        Returns:
            Dictionary with callers information
        """
        start_time = time.time()

        query = """
        MATCH (f:Symbol {name: $function_name, project_id: $project_id})
        OPTIONAL MATCH (caller:Symbol)-[:CALLS]->(f)
        RETURN f, collect(DISTINCT caller) as callers
        """

        params = {
            "function_name": function_name,
            "project_id": project_id,
        }

        results = await self.client.execute_query(query, params)
        query_time_ms = int((time.time() - start_time) * 1000)

        if not results:
            return {
                "function": None,
                "callers": [],
                "query_time_ms": query_time_ms,
            }

        return {
            "function": results[0]["f"],
            "callers": results[0]["callers"],
            "query_time_ms": query_time_ms,
        }

    async def close(self) -> None:
        """Close Neo4j client."""
        await self.client.close()
        self._connected = False
