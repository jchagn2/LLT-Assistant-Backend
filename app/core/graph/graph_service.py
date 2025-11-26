"""
Graph database service for managing code symbols and relationships.

This service provides high-level operations for storing and querying
code dependencies in the Neo4j graph database.

Phase 1 enhancements:
- Batch operations with UNWIND for performance
- Incremental update support
- Project versioning for optimistic locking
- Enhanced query operations
"""

import logging
import time
from typing import Any, Dict, List, Optional

from app.core.error_handlers import Neo4jQueryError
from app.core.graph.neo4j_client import Neo4jClient, Neo4jClientError
from app.models.context import SymbolChange

logger = logging.getLogger(__name__)

# Batch size configuration for optimal performance
SYMBOL_BATCH_SIZE = 100
RELATIONSHIP_BATCH_SIZE = 500


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

    async def batch_create_symbols(
        self,
        project_id: str,
        symbols_data: List[Dict[str, Any]],
    ) -> int:
        """
        Create multiple Symbol nodes in a single transaction using UNWIND.

        Args:
            project_id: Project identifier
            symbols_data: List of symbol dictionaries

        Returns:
            Number of nodes created/updated
        """
        if not symbols_data:
            return 0

        query = """
        UNWIND $symbols AS symbol
        MERGE (s:Symbol {qualified_name: symbol.qualified_name})
        SET s.name = symbol.name,
            s.kind = symbol.kind,
            s.signature = symbol.signature,
            s.file_path = symbol.file_path,
            s.line_start = symbol.line_start,
            s.line_end = symbol.line_end,
            s.project_id = $project_id,
            s.updated_at = datetime()
        RETURN count(s) AS created
        """

        try:
            async with self.client.session() as session:
                result = await session.run(
                    query,
                    {"project_id": project_id, "symbols": symbols_data},
                )
                record = await result.single()
                return record["created"] if record else 0
        except Exception as e:
            logger.error("Batch create symbols failed: %s", e)
            raise

    async def batch_create_symbols_chunked(
        self,
        project_id: str,
        all_symbols: List[Dict[str, Any]],
    ) -> int:
        """
        Insert symbols in chunks to avoid transaction timeout.

        Args:
            project_id: Project identifier
            all_symbols: All symbols to insert

        Returns:
            Total number of symbols created
        """
        total_created = 0

        for i in range(0, len(all_symbols), SYMBOL_BATCH_SIZE):
            chunk = all_symbols[i : i + SYMBOL_BATCH_SIZE]
            created = await self.batch_create_symbols(project_id, chunk)
            total_created += created

        logger.info(
            "Batch symbol creation completed: total=%d, chunks=%d",
            total_created,
            (len(all_symbols) + SYMBOL_BATCH_SIZE - 1) // SYMBOL_BATCH_SIZE,
        )

        return total_created

    async def create_call_relationships(
        self,
        project_id: str,
        relationships: List[Dict[str, Any]],
    ) -> int:
        """
        Create CALLS relationships between symbols using batch UNWIND.

        Args:
            project_id: Project identifier
            relationships: List of relationship dictionaries

        Returns:
            Number of relationships created
        """
        if not relationships:
            return 0

        query = """
        UNWIND $relationships AS rel
        MATCH (caller:Symbol {
            project_id: $project_id,
            qualified_name: rel.caller_qualified_name
        })
        MATCH (callee:Symbol {
            project_id: $project_id,
            qualified_name: rel.callee_qualified_name
        })
        MERGE (caller)-[r:CALLS {line: rel.line}]->(callee)
        RETURN count(r) AS created
        """

        try:
            async with self.client.session() as session:
                result = await session.run(
                    query,
                    {"project_id": project_id, "relationships": relationships},
                )
                record = await result.single()
                count = record["created"] if record else 0

                if count < len(relationships):
                    logger.warning(
                        "Some relationships not created: expected=%d, actual=%d (missing targets)",
                        len(relationships),
                        count,
                    )

                return count
        except Exception as e:
            logger.error("Create relationships failed: %s", e)
            raise

    async def update_file_symbols(
        self,
        project_id: str,
        file_path: str,
        changes: List[SymbolChange],
    ) -> Dict[str, int]:
        """
        Apply incremental changes to file's symbols.

        Args:
            project_id: Project identifier
            file_path: File path
            changes: List of symbol changes

        Returns:
            Dictionary with counts: {added: int, modified: int, deleted: int}
        """
        stats = {"added": 0, "modified": 0, "deleted": 0}

        async with self.client.session() as session:
            tx = await session.begin_transaction()
            try:
                for change in changes:
                    if change.action == "deleted":
                        await self._delete_symbol_tx(
                            tx, project_id, file_path, change.symbol.name
                        )
                        stats["deleted"] += 1

                    elif change.action == "added":
                        await self._add_symbol_tx(
                            tx, project_id, file_path, change.symbol.model_dump()
                        )
                        stats["added"] += 1

                    elif change.action == "modified":
                        await self._update_symbol_tx(
                            tx, project_id, file_path, change.symbol.model_dump()
                        )
                        stats["modified"] += 1

                await tx.commit()
            except Exception as e:
                await tx.rollback()
                logger.error("File symbol update failed: %s", e)
                raise

        logger.info(
            "File symbols updated: file=%s, added=%d, modified=%d, deleted=%d",
            file_path,
            stats["added"],
            stats["modified"],
            stats["deleted"],
        )

        return stats

    async def _delete_symbol_tx(
        self, tx, project_id: str, file_path: str, name: str
    ) -> None:
        """Delete symbol and its relationships (transaction helper)."""
        query = """
        MATCH (s:Symbol {
            project_id: $project_id,
            file_path: $file_path,
            name: $name
        })
        DETACH DELETE s
        """
        await tx.run(
            query,
            {
                "project_id": project_id,
                "file_path": file_path,
                "name": name,
            },
        )

    async def _add_symbol_tx(
        self, tx, project_id: str, file_path: str, symbol_data: Dict[str, Any]
    ) -> None:
        """Add new symbol (transaction helper)."""
        qualified_name = f"{file_path}::{symbol_data['name']}"

        query = """
        CREATE (s:Symbol {
            project_id: $project_id,
            file_path: $file_path,
            name: $name,
            kind: $kind,
            signature: $signature,
            line_start: $line_start,
            line_end: $line_end,
            qualified_name: $qualified_name,
            created_at: datetime(),
            updated_at: datetime()
        })
        """
        await tx.run(
            query,
            {
                "project_id": project_id,
                "file_path": file_path,
                "name": symbol_data["name"],
                "kind": symbol_data["kind"],
                "signature": symbol_data.get("signature", ""),
                "line_start": symbol_data["line_start"],
                "line_end": symbol_data["line_end"],
                "qualified_name": qualified_name,
            },
        )

    async def _update_symbol_tx(
        self, tx, project_id: str, file_path: str, symbol_data: Dict[str, Any]
    ) -> None:
        """Update existing symbol (transaction helper)."""
        query = """
        MATCH (s:Symbol {
            project_id: $project_id,
            file_path: $file_path,
            name: $name
        })
        SET s.signature = $signature,
            s.line_start = $line_start,
            s.line_end = $line_end,
            s.kind = $kind,
            s.updated_at = datetime()
        """
        await tx.run(
            query,
            {
                "project_id": project_id,
                "file_path": file_path,
                "name": symbol_data["name"],
                "kind": symbol_data["kind"],
                "signature": symbol_data.get("signature", ""),
                "line_start": symbol_data["line_start"],
                "line_end": symbol_data["line_end"],
            },
        )

    async def delete_file_symbols(self, project_id: str, file_path: str) -> int:
        """
        Delete all symbols from a file.

        Args:
            project_id: Project identifier
            file_path: File path

        Returns:
            Number of symbols deleted
        """
        query = """
        MATCH (s:Symbol {project_id: $project_id, file_path: $file_path})
        WITH s, count(s) AS total
        DETACH DELETE s
        RETURN total
        """

        async with self.client.session() as session:
            result = await session.run(
                query,
                {"project_id": project_id, "file_path": file_path},
            )
            record = await result.single()
            deleted = record["total"] if record else 0

            logger.info(
                "File symbols deleted: file=%s, count=%d",
                file_path,
                deleted,
            )

            return deleted

    async def get_project_statistics(self, project_id: str) -> Dict[str, int]:
        """
        Get project-level statistics.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary with total_files, total_symbols, total_relationships
        """
        query = """
        MATCH (s:Symbol {project_id: $project_id})
        RETURN
            count(DISTINCT s.file_path) AS total_files,
            count(s) AS total_symbols,
            count{(s)-[:CALLS]->()} AS total_relationships
        """

        result = await self.client.execute_query(query, {"project_id": project_id})

        if result and len(result) > 0:
            record = result[0]
            return {
                "total_files": record.get("total_files", 0),
                "total_symbols": record.get("total_symbols", 0),
                "total_relationships": record.get("total_relationships", 0),
            }

        return {"total_files": 0, "total_symbols": 0, "total_relationships": 0}

    async def delete_project(self, project_id: str) -> int:
        """
        Delete entire project including all symbols and relationships.

        This operation is idempotent - safe to call multiple times.
        Uses DETACH DELETE to automatically remove all relationships.

        Args:
            project_id: Project to delete

        Returns:
            Number of symbols deleted (0 if project didn't exist)

        Raises:
            Neo4jQueryError: If database operation fails
        """
        # Single query to delete all project data atomically
        query = """
        MATCH (s:Symbol {project_id: $project_id})
        WITH s, count(s) AS symbol_count
        DETACH DELETE s
        WITH symbol_count
        OPTIONAL MATCH (p:Project {project_id: $project_id})
        DETACH DELETE p
        RETURN symbol_count
        """

        try:
            async with self.client.session() as session:
                result = await session.run(query, {"project_id": project_id})
                record = await result.single()

                if record and record["symbol_count"] is not None:
                    deleted_count = record["symbol_count"]
                else:
                    deleted_count = 0

                logger.info(
                    "Deleted project data: project_id=%s, symbols=%d",
                    project_id,
                    deleted_count,
                )

                return deleted_count

        except Exception as e:
            logger.error(
                "Failed to delete project: project_id=%s, error=%s",
                project_id,
                str(e),
                exc_info=True,
            )
            raise Neo4jQueryError(
                query="DELETE project and symbols",
                error=f"Project deletion failed: {str(e)}",
            )

    async def check_project_exists(self, project_id: str) -> bool:
        """
        Check if project has any indexed data.

        Args:
            project_id: Project identifier

        Returns:
            True if project exists, False otherwise
        """
        query = """
        MATCH (s:Symbol {project_id: $project_id})
        RETURN count(s) > 0 AS exists
        """

        result = await self.client.execute_query(query, {"project_id": project_id})
        return result[0]["exists"] if result else False

    async def get_project_version(self, project_id: str) -> int:
        """
        Get current version number for optimistic locking.

        Args:
            project_id: Project identifier

        Returns:
            Current version number (0 if project doesn't exist)
        """
        query = """
        MATCH (p:Project {project_id: $project_id})
        RETURN p.version AS version
        """

        result = await self.client.execute_query(query, {"project_id": project_id})
        return result[0]["version"] if result else 0

    async def get_project_data(self, project_id: str) -> dict:
        """
        Get complete project data including all files and symbols.

        This method retrieves all symbols for a project and groups them by file_path,
        allowing the frontend to rebuild its local cache.

        Args:
            project_id: Project identifier

        Returns:
            Dictionary with project_id, version, workspace_path, and files

        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        from app.core.error_handlers import ProjectNotFoundError

        # First check if project exists
        exists = await self.check_project_exists(project_id)
        if not exists:
            raise ProjectNotFoundError(project_id)

        # Get project metadata (version and workspace_path)
        metadata_query = """
        MATCH (p:Project {project_id: $project_id})
        RETURN p.version AS version, p.workspace_path AS workspace_path
        """

        metadata_result = await self.client.execute_query(
            metadata_query, {"project_id": project_id}
        )

        if not metadata_result:
            raise ProjectNotFoundError(project_id)

        version = metadata_result[0]["version"]
        workspace_path = metadata_result[0].get("workspace_path")

        # Get all symbols for the project
        symbols_query = """
        MATCH (s:Symbol {project_id: $project_id})
        OPTIONAL MATCH (s)-[c:CALLS]->(called:Symbol)
        RETURN
            s.name AS name,
            s.kind AS kind,
            s.signature AS signature,
            s.file_path AS file_path,
            s.line_start AS line_start,
            s.line_end AS line_end,
            collect(called.name) AS calls
        ORDER BY s.file_path, s.line_start
        """

        symbols_result = await self.client.execute_query(
            symbols_query, {"project_id": project_id}
        )

        # Group symbols by file_path
        files_dict = {}
        for record in symbols_result:
            file_path = record["file_path"]

            if file_path not in files_dict:
                files_dict[file_path] = {
                    "path": file_path,
                    "symbols": [],
                }

            # Filter out None values from calls list
            calls = [c for c in record["calls"] if c is not None]

            symbol_data = {
                "name": record["name"],
                "kind": record["kind"],
                "signature": record.get("signature") or None,
                "line_start": record["line_start"],
                "line_end": record["line_end"],
                "calls": calls,
            }

            files_dict[file_path]["symbols"].append(symbol_data)

        # Convert dict to list
        files = list(files_dict.values())

        logger.info(
            "Retrieved project data: project_id=%s, version=%d, files=%d, symbols=%d",
            project_id,
            version,
            len(files),
            len(symbols_result),
        )

        return {
            "project_id": project_id,
            "version": version,
            "workspace_path": workspace_path,
            "files": files,
        }

    async def increment_project_version(self, project_id: str) -> int:
        """
        Increment and return new version number.

        Args:
            project_id: Project identifier

        Returns:
            New version number
        """
        query = """
        MERGE (p:Project {project_id: $project_id})
        ON CREATE SET p.version = 1, p.created_at = datetime()
        ON MATCH SET p.version = p.version + 1
        SET p.updated_at = datetime()
        RETURN p.version AS version
        """

        async with self.client.session() as session:
            result = await session.run(query, {"project_id": project_id})
            record = await result.single()
            version = record["version"] if record else 1

            logger.info(
                "Project version incremented: project=%s, version=%d",
                project_id,
                version,
            )

            return version

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
