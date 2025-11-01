"""
Developed by PowerShield, as an alternative to Django Database
"""

"""Database connection management."""

from typing import Any, Dict, Optional
import asyncpg
from config.settings import settings


class DatabaseConnection:
    """Manages database connections and connection pooling."""

    def __init__(self) -> None:
        """Initialize database connection manager."""
        self.pool: Optional[asyncpg.Pool] = None
        self._config: Dict[str, Any] = settings.DATABASE

    async def connect(self) -> None:
        """Create a connection pool to the database."""
        if self.pool is None:
            self.pool = await asyncpg.create_pool(
                host=self._config["host"],
                port=self._config["port"],
                database=self._config["database"],
                user=self._config["user"],
                password=self._config["password"],
                min_size=self._config["min_pool_size"],
                max_size=self._config["max_pool_size"],
            )

    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    async def execute(self, query: str, *args: Any) -> str:
        """Execute a query that doesn't return results.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Status string from the database
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

    async def fetch_one(self, query: str, *args: Any) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Dictionary representing the row, or None if not found
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *args)
            return dict(row) if row else None

    async def fetch_all(self, query: str, *args: Any) -> list:
        """Fetch all rows from the database.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            List of dictionaries representing rows
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *args)
            return [dict(row) for row in rows]

    async def fetch_val(self, query: str, *args: Any) -> Any:
        """Fetch a single value from the database.

        Args:
            query: SQL query string
            *args: Query parameters

        Returns:
            Single value from the query result
        """
        if self.pool is None:
            await self.connect()

        async with self.pool.acquire() as connection:
            return await connection.fetchval(query, *args)

    def __repr__(self) -> str:
        """Return string representation of the connection."""
        return f"<DatabaseConnection {self._config['database']}@{self._config['host']}>"


# Global database connection instance
db = DatabaseConnection()
