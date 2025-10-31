"""Database migration system."""

from typing import List
from datetime import datetime
from database.connection import db


class Migration:
    """Represents a database migration."""

    def __init__(self, name: str, version: str) -> None:
        """Initialize a migration.

        Args:
            name: Migration name
            version: Migration version (timestamp)
        """
        self.name = name
        self.version = version
        self.up_sql: List[str] = []
        self.down_sql: List[str] = []

    def up(self, sql: str) -> None:
        """Add an up migration SQL statement.

        Args:
            sql: SQL statement to execute
        """
        self.up_sql.append(sql)

    def down(self, sql: str) -> None:
        """Add a down migration SQL statement.

        Args:
            sql: SQL statement to execute
        """
        self.down_sql.append(sql)

    async def apply(self) -> None:
        """Apply the migration."""
        for sql in self.up_sql:
            await db.execute(sql)

    async def rollback(self) -> None:
        """Rollback the migration."""
        for sql in self.down_sql:
            await db.execute(sql)

    def __repr__(self) -> str:
        """Return string representation of the migration."""
        return f"<Migration {self.version}_{self.name}>"


class MigrationManager:
    """Manages database migrations."""

    def __init__(self, migrations_dir: str = "migrations") -> None:
        """Initialize the migration manager.

        Args:
            migrations_dir: Directory to store migration files
        """
        self.migrations_dir = migrations_dir
        self.migrations: List[Migration] = []

    async def init(self) -> None:
        """Initialize the migrations table in the database."""
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS migrations (
                id SERIAL PRIMARY KEY,
                version VARCHAR(255) NOT NULL UNIQUE,
                name VARCHAR(255) NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

    async def get_applied_migrations(self) -> List[str]:
        """Get list of applied migration versions.

        Returns:
            List of applied migration versions
        """
        try:
            rows = await db.fetch_all("SELECT version FROM migrations ORDER BY applied_at")
            return [row["version"] for row in rows]
        except Exception:
            # Migrations table doesn't exist yet
            return []

    async def apply_migration(self, migration: Migration) -> None:
        """Apply a migration and record it.

        Args:
            migration: Migration to apply
        """
        await migration.apply()
        await db.execute(
            "INSERT INTO migrations (version, name) VALUES ($1, $2)",
            migration.version,
            migration.name,
        )

    async def rollback_migration(self, migration: Migration) -> None:
        """Rollback a migration and remove its record.

        Args:
            migration: Migration to rollback
        """
        await migration.rollback()
        await db.execute("DELETE FROM migrations WHERE version = $1", migration.version)

    async def migrate(self) -> None:
        """Apply all pending migrations."""
        await self.init()
        applied = await self.get_applied_migrations()

        for migration in self.migrations:
            if migration.version not in applied:
                print(f"Applying migration: {migration.version}_{migration.name}")
                await self.apply_migration(migration)

    async def rollback(self, steps: int = 1) -> None:
        """Rollback the last N migrations.

        Args:
            steps: Number of migrations to rollback
        """
        applied = await self.get_applied_migrations()

        # Get the last N migrations to rollback
        to_rollback = applied[-steps:] if steps < len(applied) else applied

        for version in reversed(to_rollback):
            # Find the migration object
            migration = None
            for m in self.migrations:
                if m.version == version:
                    migration = m
                    break

            if migration:
                print(f"Rolling back migration: {migration.version}_{migration.name}")
                await self.rollback_migration(migration)

    def create_migration(self, name: str) -> Migration:
        """Create a new migration.

        Args:
            name: Migration name

        Returns:
            New Migration instance
        """
        version = datetime.now().strftime("%Y%m%d%H%M%S")
        migration = Migration(name, version)
        self.migrations.append(migration)
        return migration

    def add_migration(self, migration: Migration) -> None:
        """Add an existing migration to the manager.

        Args:
            migration: Migration to add
        """
        self.migrations.append(migration)

    def __repr__(self) -> str:
        """Return string representation of the migration manager."""
        return f"<MigrationManager {len(self.migrations)} migrations>"


# Global migration manager instance
migration_manager = MigrationManager()
