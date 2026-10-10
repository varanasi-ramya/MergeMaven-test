"""
Enhanced authentication module - PR #2: Role-Based Access Control (RBAC)
This branch adds RBAC system, permissions, and resource-level access control.
CONFLICTS with feature/user-auth (both modify auth module)
"""

from typing import Optional, Dict, List, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Permission(Enum):
    """System permissions."""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOG = "view_audit_log"
    MANAGE_SYSTEM = "manage_system"


class Role(Enum):
    """System roles."""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"
    GUEST = "guest"


# Role to permissions mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.SUPER_ADMIN: {p for p in Permission},
    Role.ADMIN: {
        Permission.READ, Permission.WRITE, Permission.DELETE,
        Permission.MANAGE_USERS, Permission.VIEW_AUDIT_LOG
    },
    Role.MODERATOR: {
        Permission.READ, Permission.WRITE, Permission.DELETE
    },
    Role.USER: {
        Permission.READ, Permission.WRITE
    },
    Role.GUEST: {
        Permission.READ
    }
}


@dataclass
class User:
    """User model with RBAC."""
    id: int
    username: str
    email: str
    password_hash: str
    role: Role = Role.USER
    created_at: datetime = field(default_factory=datetime.now)
    permissions: Set[Permission] = field(default_factory=set)  # Custom permissions
    is_active: bool = True
    last_login: Optional[datetime] = None


class AuthManager:
    """Manages user authentication with RBAC."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.role_assignments: Dict[str, Role] = {}  # username -> role
    
    def register_user(self, username: str, email: str, password: str, role: Role = Role.USER) -> User:
        """Register a new user with RBAC role."""
        if username in self.users:
            raise ValueError(f"User {username} already exists")
        
        user = User(
            id=len(self.users) + 1,
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            role=role,
            created_at=datetime.now()
        )
        self.users[username] = user
        self.role_assignments[username] = role
        return user
    
    def assign_role(self, username: str, role: Role, assigned_by: str) -> bool:
        """Assign role to user (requires admin permission)."""
        if not self.has_permission(assigned_by, Permission.MANAGE_USERS):
            raise PermissionError("Insufficient permissions to assign roles")
        
        user = self.users.get(username)
        if not user:
            return False
        
        user.role = role
        self.role_assignments[username] = role
        user.permissions.update(ROLE_PERMISSIONS[role])
        return True
    
    def grant_permission(self, username: str, permission: Permission, granted_by: str) -> bool:
        """Grant custom permission to user."""
        if not self.has_permission(granted_by, Permission.MANAGE_ROLES):
            raise PermissionError("Insufficient permissions to grant permissions")
        
        user = self.users.get(username)
        if not user:
            return False
        
        user.permissions.add(permission)
        return True
    
    def revoke_permission(self, username: str, permission: Permission, revoked_by: str) -> bool:
        """Revoke custom permission from user."""
        if not self.has_permission(revoked_by, Permission.MANAGE_ROLES):
            raise PermissionError("Insufficient permissions to revoke permissions")
        
        user = self.users.get(username)
        if not user:
            return False
        
        user.permissions.discard(permission)
        return True
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = self.users.get(username)
        if not user or not user.is_active:
            return None
        
        if self._verify_password(password, user.password_hash):
            self.failed_attempts[username] = 0
            user.last_login = datetime.now()
            return user
        
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
        if self.failed_attempts[username] >= 5:
            user.is_active = False
            raise Exception(f"Account locked for {username}")
        return None
    
    def has_permission(self, username: str, permission: Permission) -> bool:
        """Check if user has specific permission."""
        user = self.users.get(username)
        if not user:
            return False
        
        # Check role-based permissions
        role_perms = ROLE_PERMISSIONS.get(user.role, set())
        if permission in role_perms:
            return True
        
        # Check custom permissions
        return permission in user.permissions
    
    def _hash_password(self, password: str) -> str:
        """Hash password (simplified)."""
        return f"hashed_{password}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password."""
        return self._hash_password(password) == hashed
    
    def get_user_effective_permissions(self, username: str) -> Set[Permission]:
        """Get all effective permissions for a user (role + custom)."""
        user = self.users.get(username)
        if not user:
            return set()
        
        role_perms = ROLE_PERMISSIONS.get(user.role, set())
        return role_perms.union(user.permissions)


from typing import Optional