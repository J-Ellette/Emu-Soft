"""Query builder for constructing SQL queries programmatically."""

from typing import Any, Dict, List, Optional


class QueryBuilder:
    """Builds SQL queries programmatically with a fluent interface."""

    def __init__(self, table: str) -> None:
        """Initialize the query builder.

        Args:
            table: Table name to query
        """
        self.table = table
        self._select: List[str] = ["*"]
        self._where: List[tuple] = []
        self._order_by: List[tuple] = []
        self._limit_value: Optional[int] = None
        self._offset_value: Optional[int] = None
        self._values: Dict[str, Any] = {}
        self._operation: str = "SELECT"

    def select(self, *columns: str) -> "QueryBuilder":
        """Specify columns to select.

        Args:
            *columns: Column names to select

        Returns:
            Self for method chaining
        """
        if columns:
            self._select = list(columns)
        return self

    def where(self, column: str, operator: str = "=", value: Any = None) -> "QueryBuilder":
        """Add a WHERE clause.

        Args:
            column: Column name
            operator: Comparison operator (=, >, <, etc.)
            value: Value to compare against

        Returns:
            Self for method chaining
        """
        self._where.append((column, operator, value))
        return self

    def order_by(self, column: str, direction: str = "ASC") -> "QueryBuilder":
        """Add an ORDER BY clause.

        Args:
            column: Column name to order by
            direction: Sort direction ('ASC' or 'DESC')

        Returns:
            Self for method chaining
        """
        self._order_by.append((column, direction.upper()))
        return self

    def limit(self, count: int) -> "QueryBuilder":
        """Add a LIMIT clause.

        Args:
            count: Maximum number of rows to return

        Returns:
            Self for method chaining
        """
        self._limit_value = count
        return self

    def offset(self, count: int) -> "QueryBuilder":
        """Add an OFFSET clause.

        Args:
            count: Number of rows to skip

        Returns:
            Self for method chaining
        """
        self._offset_value = count
        return self

    def insert(self, values: Dict[str, Any]) -> "QueryBuilder":
        """Create an INSERT query.

        Args:
            values: Dictionary of column names and values

        Returns:
            Self for method chaining
        """
        self._operation = "INSERT"
        self._values = values
        return self

    def update(self, values: Dict[str, Any]) -> "QueryBuilder":
        """Create an UPDATE query.

        Args:
            values: Dictionary of column names and values

        Returns:
            Self for method chaining
        """
        self._operation = "UPDATE"
        self._values = values
        return self

    def delete(self) -> "QueryBuilder":
        """Create a DELETE query.

        Returns:
            Self for method chaining
        """
        self._operation = "DELETE"
        return self

    def build(self) -> tuple:
        """Build the final SQL query and parameters.

        Returns:
            Tuple of (query string, parameters list)
        """
        if self._operation == "SELECT":
            return self._build_select()
        elif self._operation == "INSERT":
            return self._build_insert()
        elif self._operation == "UPDATE":
            return self._build_update()
        elif self._operation == "DELETE":
            return self._build_delete()
        else:
            raise ValueError(f"Unknown operation: {self._operation}")

    def _build_select(self) -> tuple:
        """Build a SELECT query."""
        params = []
        query_parts = [f"SELECT {', '.join(self._select)}", f"FROM {self.table}"]

        if self._where:
            where_clauses = []
            for column, operator, value in self._where:
                params.append(value)
                where_clauses.append(f"{column} {operator} ${len(params)}")
            query_parts.append(f"WHERE {' AND '.join(where_clauses)}")

        if self._order_by:
            order_clauses = [f"{col} {direction}" for col, direction in self._order_by]
            query_parts.append(f"ORDER BY {', '.join(order_clauses)}")

        if self._limit_value is not None:
            query_parts.append(f"LIMIT {self._limit_value}")

        if self._offset_value is not None:
            query_parts.append(f"OFFSET {self._offset_value}")

        return " ".join(query_parts), params

    def _build_insert(self) -> tuple:
        """Build an INSERT query."""
        columns = list(self._values.keys())
        params = list(self._values.values())
        placeholders = [f"${i + 1}" for i in range(len(params))]

        query = (
            f"INSERT INTO {self.table} "
            f"({', '.join(columns)}) "
            f"VALUES ({', '.join(placeholders)}) "
            f"RETURNING *"
        )

        return query, params

    def _build_update(self) -> tuple:
        """Build an UPDATE query."""
        params = []
        set_clauses = []

        for column, value in self._values.items():
            params.append(value)
            set_clauses.append(f"{column} = ${len(params)}")

        query_parts = [f"UPDATE {self.table}", f"SET {', '.join(set_clauses)}"]

        if self._where:
            where_clauses = []
            for column, operator, value in self._where:
                params.append(value)
                where_clauses.append(f"{column} {operator} ${len(params)}")
            query_parts.append(f"WHERE {' AND '.join(where_clauses)}")

        query_parts.append("RETURNING *")

        return " ".join(query_parts), params

    def _build_delete(self) -> tuple:
        """Build a DELETE query."""
        params = []
        query_parts = [f"DELETE FROM {self.table}"]

        if self._where:
            where_clauses = []
            for column, operator, value in self._where:
                params.append(value)
                where_clauses.append(f"{column} {operator} ${len(params)}")
            query_parts.append(f"WHERE {' AND '.join(where_clauses)}")

        return " ".join(query_parts), params

    def __repr__(self) -> str:
        """Return string representation of the query builder."""
        query, _ = self.build()
        return f"<QueryBuilder {query}>"
