"""
Developed by PowerShield, as an alternative to Django Database
"""

"""Database optimization tools including query tracking, indexing, and performance monitoring."""

from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import wraps
import time
import statistics


@dataclass
class QueryMetrics:
    """Metrics for a database query."""

    query: str
    execution_time: float  # in seconds
    timestamp: datetime
    rows_affected: Optional[int] = None
    table: Optional[str] = None
    operation: Optional[str] = None  # SELECT, INSERT, UPDATE, DELETE
    parameters: Optional[List[Any]] = None


@dataclass
class QueryStatistics:
    """Statistics for a specific query pattern."""

    query_pattern: str
    execution_count: int = 0
    total_time: float = 0.0
    min_time: float = float("inf")
    max_time: float = 0.0
    avg_time: float = 0.0
    last_execution: Optional[datetime] = None
    slow_query_threshold: float = 1.0  # seconds


class QueryTracker:
    """Track and analyze database queries."""

    def __init__(self, slow_query_threshold: float = 1.0) -> None:
        """Initialize query tracker.

        Args:
            slow_query_threshold: Threshold in seconds for slow queries
        """
        self.slow_query_threshold = slow_query_threshold
        self._queries: List[QueryMetrics] = []
        self._query_stats: Dict[str, QueryStatistics] = {}
        self._slow_queries: List[QueryMetrics] = []

    def _normalize_query(self, query: str) -> str:
        """Normalize a query to create a pattern.

        Args:
            query: SQL query string

        Returns:
            Normalized query pattern
        """
        import re

        # Replace parameter placeholders with ?
        normalized = re.sub(r"\$\d+", "?", query)

        # Replace quoted strings with ?
        normalized = re.sub(r"'[^']*'", "?", normalized)

        # Replace numbers with ?
        normalized = re.sub(r"\b\d+\b", "?", normalized)

        # Normalize whitespace
        normalized = " ".join(normalized.split())

        return normalized

    def track_query(self, metrics: QueryMetrics) -> None:
        """Track a database query.

        Args:
            metrics: Query metrics
        """
        self._queries.append(metrics)

        # Update statistics
        pattern = self._normalize_query(metrics.query)
        if pattern not in self._query_stats:
            self._query_stats[pattern] = QueryStatistics(
                query_pattern=pattern,
                slow_query_threshold=self.slow_query_threshold,
            )

        stats = self._query_stats[pattern]
        stats.execution_count += 1
        stats.total_time += metrics.execution_time
        stats.min_time = min(stats.min_time, metrics.execution_time)
        stats.max_time = max(stats.max_time, metrics.execution_time)
        stats.avg_time = stats.total_time / stats.execution_count
        stats.last_execution = metrics.timestamp

        # Track slow queries
        if metrics.execution_time > self.slow_query_threshold:
            self._slow_queries.append(metrics)

    def get_slow_queries(self, limit: Optional[int] = None) -> List[QueryMetrics]:
        """Get slow queries.

        Args:
            limit: Optional limit on number of results

        Returns:
            List of slow query metrics
        """
        queries = sorted(self._slow_queries, key=lambda x: x.execution_time, reverse=True)
        return queries[:limit] if limit else queries

    def get_most_frequent_queries(self, limit: int = 10) -> List[QueryStatistics]:
        """Get most frequently executed queries.

        Args:
            limit: Maximum number of results

        Returns:
            List of query statistics
        """
        stats = sorted(
            self._query_stats.values(),
            key=lambda x: x.execution_count,
            reverse=True,
        )
        return stats[:limit]

    def get_slowest_queries(self, limit: int = 10) -> List[QueryStatistics]:
        """Get queries with highest average execution time.

        Args:
            limit: Maximum number of results

        Returns:
            List of query statistics
        """
        stats = sorted(
            self._query_stats.values(),
            key=lambda x: x.avg_time,
            reverse=True,
        )
        return stats[:limit]

    def get_query_stats(self, query_pattern: Optional[str] = None) -> Dict[str, Any]:
        """Get query statistics.

        Args:
            query_pattern: Optional specific query pattern

        Returns:
            Statistics dictionary
        """
        if query_pattern:
            stats = self._query_stats.get(query_pattern)
            if not stats:
                return {}

            return {
                "pattern": stats.query_pattern,
                "count": stats.execution_count,
                "total_time": round(stats.total_time, 4),
                "avg_time": round(stats.avg_time, 4),
                "min_time": round(stats.min_time, 4),
                "max_time": round(stats.max_time, 4),
            }

        # Overall statistics
        total_queries = len(self._queries)
        slow_queries = len(self._slow_queries)

        return {
            "total_queries": total_queries,
            "slow_queries": slow_queries,
            "unique_patterns": len(self._query_stats),
            "slow_query_threshold": self.slow_query_threshold,
            "most_frequent": [
                {
                    "pattern": s.query_pattern[:100],
                    "count": s.execution_count,
                    "avg_time": round(s.avg_time, 4),
                }
                for s in self.get_most_frequent_queries(5)
            ],
            "slowest": [
                {
                    "pattern": s.query_pattern[:100],
                    "count": s.execution_count,
                    "avg_time": round(s.avg_time, 4),
                }
                for s in self.get_slowest_queries(5)
            ],
        }

    def clear_stats(self) -> None:
        """Clear all tracked queries and statistics."""
        self._queries.clear()
        self._query_stats.clear()
        self._slow_queries.clear()


def track_query(tracker: QueryTracker) -> Callable:
    """Decorator to track query execution.

    Args:
        tracker: Query tracker instance

    Returns:
        Decorator function
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Extract query from arguments
            query = None
            if args:
                query = args[0] if isinstance(args[0], str) else None

            if query:
                metrics = QueryMetrics(
                    query=query,
                    execution_time=execution_time,
                    timestamp=datetime.now(timezone.utc),
                )
                tracker.track_query(metrics)

            return result

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time

            # Extract query from arguments
            query = None
            if args:
                query = args[0] if isinstance(args[0], str) else None

            if query:
                metrics = QueryMetrics(
                    query=query,
                    execution_time=execution_time,
                    timestamp=datetime.now(timezone.utc),
                )
                tracker.track_query(metrics)

            return result

        # Return appropriate wrapper based on whether function is async
        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class IndexManager:
    """Manage database indexes."""

    def __init__(self, db_connection: Any) -> None:
        """Initialize index manager.

        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        self._index_recommendations: List[Dict[str, Any]] = []

    async def list_indexes(self, table: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all indexes in the database.

        Args:
            table: Optional table name to filter by

        Returns:
            List of index information
        """
        # PostgreSQL query to list indexes
        query = """
            SELECT
                schemaname,
                tablename,
                indexname,
                indexdef
            FROM pg_indexes
            WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        """

        if table:
            query += f" AND tablename = '{table}'"

        query += " ORDER BY tablename, indexname"

        try:
            result = await self.db.execute(query)
            return [
                {
                    "schema": row[0],
                    "table": row[1],
                    "name": row[2],
                    "definition": row[3],
                }
                for row in result
            ]
        except Exception:
            # Return empty list if query fails
            return []

    async def analyze_missing_indexes(
        self,
        query_tracker: QueryTracker,
    ) -> List[Dict[str, Any]]:
        """Analyze queries to recommend missing indexes.

        Args:
            query_tracker: Query tracker with execution data

        Returns:
            List of index recommendations
        """
        recommendations = []

        # Analyze slow queries for potential index candidates
        slow_queries = query_tracker.get_slow_queries(limit=50)

        for query_metrics in slow_queries:
            # Simple heuristic: look for WHERE clauses without indexes
            import re

            where_match = re.search(r"WHERE\s+(\w+)\s*=", query_metrics.query, re.IGNORECASE)
            if where_match:
                column = where_match.group(1)
                table_match = re.search(r"FROM\s+(\w+)", query_metrics.query, re.IGNORECASE)
                if table_match:
                    table = table_match.group(1)
                    recommendations.append(
                        {
                            "table": table,
                            "column": column,
                            "reason": f"Slow query with WHERE clause on {column}",
                            "query_time": query_metrics.execution_time,
                            "recommendation": (
                                f"CREATE INDEX idx_{table}_{column} "
                                f"ON {table}({column})"
                            ),
                        }
                    )

        self._index_recommendations = recommendations
        return recommendations

    def get_recommendations(self) -> List[Dict[str, Any]]:
        """Get stored index recommendations.

        Returns:
            List of index recommendations
        """
        return self._index_recommendations


class QueryOptimizer:
    """Analyze and optimize database queries."""

    def __init__(self, db_connection: Any) -> None:
        """Initialize query optimizer.

        Args:
            db_connection: Database connection
        """
        self.db = db_connection

    async def explain_query(self, query: str, analyze: bool = False) -> Dict[str, Any]:
        """Get query execution plan.

        Args:
            query: SQL query to explain
            analyze: Whether to actually execute the query

        Returns:
            Query plan information
        """
        explain_cmd = "EXPLAIN (FORMAT JSON, ANALYZE TRUE)" if analyze else "EXPLAIN (FORMAT JSON)"
        explain_query = f"{explain_cmd} {query}"

        try:
            result = await self.db.execute(explain_query)
            if result and len(result) > 0:
                return result[0][0]  # PostgreSQL returns JSON as first column
            return {}
        except Exception as e:
            return {"error": str(e)}

    def analyze_query_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query execution plan for optimization opportunities.

        Args:
            plan: Query execution plan from EXPLAIN

        Returns:
            Analysis with optimization suggestions
        """
        suggestions = []

        if not plan or "error" in plan:
            return {"suggestions": suggestions, "plan": plan}

        # Extract plan from JSON structure
        if isinstance(plan, dict) and "Plan" in plan:
            plan_node = plan["Plan"]

            # Check for sequential scans
            if plan_node.get("Node Type") == "Seq Scan":
                suggestions.append(
                    {
                        "type": "index_missing",
                        "message": "Sequential scan detected - consider adding index",
                        "table": plan_node.get("Relation Name"),
                    }
                )

            # Check for high cost
            if plan_node.get("Total Cost", 0) > 1000:
                suggestions.append(
                    {
                        "type": "high_cost",
                        "message": "High query cost detected",
                        "cost": plan_node.get("Total Cost"),
                    }
                )

        return {"suggestions": suggestions, "plan": plan}


class ConnectionPoolMonitor:
    """Monitor database connection pool performance."""

    def __init__(self) -> None:
        """Initialize connection pool monitor."""
        self._connections_created: int = 0
        self._connections_closed: int = 0
        self._connections_in_use: int = 0
        self._max_connections_used: int = 0
        self._wait_times: List[float] = []
        self._start_time = time.time()

    def record_connection_created(self) -> None:
        """Record that a connection was created."""
        self._connections_created += 1
        self._connections_in_use += 1
        self._max_connections_used = max(self._max_connections_used, self._connections_in_use)

    def record_connection_closed(self) -> None:
        """Record that a connection was closed."""
        self._connections_closed += 1
        self._connections_in_use = max(0, self._connections_in_use - 1)

    def record_wait_time(self, wait_time: float) -> None:
        """Record time spent waiting for a connection.

        Args:
            wait_time: Wait time in seconds
        """
        self._wait_times.append(wait_time)

    def get_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics.

        Returns:
            Statistics dictionary
        """
        uptime = time.time() - self._start_time

        avg_wait_time = statistics.mean(self._wait_times) if self._wait_times else 0
        max_wait_time = max(self._wait_times) if self._wait_times else 0

        return {
            "connections_created": self._connections_created,
            "connections_closed": self._connections_closed,
            "connections_in_use": self._connections_in_use,
            "max_connections_used": self._max_connections_used,
            "avg_wait_time_ms": round(avg_wait_time * 1000, 2),
            "max_wait_time_ms": round(max_wait_time * 1000, 2),
            "uptime_seconds": round(uptime, 2),
        }

    def reset(self) -> None:
        """Reset all statistics."""
        self._connections_created = 0
        self._connections_closed = 0
        self._connections_in_use = 0
        self._max_connections_used = 0
        self._wait_times.clear()
        self._start_time = time.time()


# Global instances
_query_tracker = QueryTracker()
_connection_monitor = ConnectionPoolMonitor()


def get_query_tracker() -> QueryTracker:
    """Get global query tracker instance.

    Returns:
        Query tracker
    """
    return _query_tracker


def get_connection_monitor() -> ConnectionPoolMonitor:
    """Get global connection pool monitor.

    Returns:
        Connection pool monitor
    """
    return _connection_monitor
