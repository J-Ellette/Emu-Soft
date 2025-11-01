"""
Developed by PowerShield, as an alternative to Django Auth
"""

"""User, Role, and Permission models for authentication and authorization."""

from typing import Any, List
from database.orm import (
    Model,
    CharField,
    IntegerField,
    TextField,
    BooleanField,
    DateTimeField,
)


class Permission(Model):
    """Permission model for granular access control."""

    _table_name = "permissions"

    id = IntegerField(primary_key=True)
    name = CharField(max_length=100, unique=True)
    codename = CharField(max_length=100, unique=True)
    description = TextField(null=True)

    def __str__(self) -> str:
        """Return string representation."""
        return f"{self.name} ({self.codename})"


class Role(Model):
    """Role model for role-based access control."""

    _table_name = "roles"

    id = IntegerField(primary_key=True)
    name = CharField(max_length=100, unique=True)
    description = TextField(null=True)
    is_active = BooleanField(default=True)
    created_at = DateTimeField(auto_now=True)

    async def get_permissions(self) -> List[Permission]:
        """Get all permissions associated with this role.

        Returns:
            List of Permission instances
        """
        # Query role_permissions table to get permission IDs
        from database.query import QueryBuilder

        qb = QueryBuilder("role_permissions")
        qb.select("permission_id").where("role_id", "=", self.id)
        query, params = qb.build()

        from database.connection import db

        rows = await db.fetch_all(query, *params)
        permission_ids = [row["permission_id"] for row in rows]

        if not permission_ids:
            return []

        # Get permissions by IDs
        qb = QueryBuilder("permissions")
        qb.where("id", "IN", permission_ids)
        query, params = qb.build()
        rows = await db.fetch_all(query, *params)

        return [Permission(**row) for row in rows]

    async def add_permission(self, permission: Permission) -> None:
        """Add a permission to this role.

        Args:
            permission: Permission instance to add
        """
        from database.query import QueryBuilder
        from database.connection import db

        qb = QueryBuilder("role_permissions")
        qb.insert({"role_id": self.id, "permission_id": permission.id})
        query, params = qb.build()
        await db.execute(query, *params)

    async def remove_permission(self, permission: Permission) -> None:
        """Remove a permission from this role.

        Args:
            permission: Permission instance to remove
        """
        from database.query import QueryBuilder
        from database.connection import db

        qb = QueryBuilder("role_permissions")
        qb.delete().where("role_id", "=", self.id).where("permission_id", "=", permission.id)
        query, params = qb.build()
        await db.execute(query, *params)

    def __str__(self) -> str:
        """Return string representation."""
        return self.name


class User(Model):
    """User model for authentication."""

    _table_name = "users"

    id = IntegerField(primary_key=True)
    username = CharField(max_length=150, unique=True)
    email = CharField(max_length=255, unique=True)
    password_hash = CharField(max_length=255)
    first_name = CharField(max_length=100, null=True)
    last_name = CharField(max_length=100, null=True)
    is_active = BooleanField(default=True)
    is_staff = BooleanField(default=False)
    is_superuser = BooleanField(default=False)
    last_login = DateTimeField(null=True)
    created_at = DateTimeField(auto_now=True)
    updated_at = DateTimeField(auto_now=True)

    def __init__(self, **kwargs: Any) -> None:
        """Initialize user instance.

        Args:
            **kwargs: Field values
        """
        # Don't allow setting password_hash directly
        if "password" in kwargs:
            from auth.password import hash_password

            kwargs["password_hash"] = hash_password(kwargs.pop("password"))

        super().__init__(**kwargs)

    def set_password(self, password: str) -> None:
        """Set user password (hashed).

        Args:
            password: Plain text password
        """
        from auth.password import hash_password

        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash.

        Args:
            password: Plain text password to verify

        Returns:
            True if password matches, False otherwise
        """
        from auth.password import verify_password

        return verify_password(password, self.password_hash)

    async def get_roles(self) -> List[Role]:
        """Get all roles assigned to this user.

        Returns:
            List of Role instances
        """
        from database.query import QueryBuilder
        from database.connection import db

        qb = QueryBuilder("user_roles")
        qb.select("role_id").where("user_id", "=", self.id)
        query, params = qb.build()
        rows = await db.fetch_all(query, *params)
        role_ids = [row["role_id"] for row in rows]

        if not role_ids:
            return []

        qb = QueryBuilder("roles")
        qb.where("id", "IN", role_ids)
        query, params = qb.build()
        rows = await db.fetch_all(query, *params)

        return [Role(**row) for row in rows]

    async def add_role(self, role: Role) -> None:
        """Add a role to this user.

        Args:
            role: Role instance to add
        """
        from database.query import QueryBuilder
        from database.connection import db

        qb = QueryBuilder("user_roles")
        qb.insert({"user_id": self.id, "role_id": role.id})
        query, params = qb.build()
        await db.execute(query, *params)

    async def remove_role(self, role: Role) -> None:
        """Remove a role from this user.

        Args:
            role: Role instance to remove
        """
        from database.query import QueryBuilder
        from database.connection import db

        qb = QueryBuilder("user_roles")
        qb.delete().where("user_id", "=", self.id).where("role_id", "=", role.id)
        query, params = qb.build()
        await db.execute(query, *params)

    async def get_permissions(self) -> List[Permission]:
        """Get all permissions for this user (via roles).

        Returns:
            List of Permission instances
        """
        if self.is_superuser:
            # Superusers have all permissions
            return await Permission.all()

        roles = await self.get_roles()
        all_permissions: List[Permission] = []
        permission_ids = set()

        for role in roles:
            permissions = await role.get_permissions()
            for perm in permissions:
                if perm.id not in permission_ids:
                    permission_ids.add(perm.id)
                    all_permissions.append(perm)

        return all_permissions

    async def has_permission(self, permission_codename: str) -> bool:
        """Check if user has a specific permission.

        Args:
            permission_codename: Permission codename to check

        Returns:
            True if user has permission, False otherwise
        """
        if self.is_superuser:
            return True

        permissions = await self.get_permissions()
        return any(p.codename == permission_codename for p in permissions)

    def get_full_name(self) -> str:
        """Get user's full name.

        Returns:
            Full name or username if names not set
        """
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.username

    def __str__(self) -> str:
        """Return string representation."""
        return self.username
