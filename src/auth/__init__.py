"""
Base authentication module.
This will be modified by multiple PRs to create conflicts.
"""

from typing import Optional, Dict, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """User model."""
    id: int
    username: str
    email: str
    password_hash: str
    role: str
    created_at: datetime


class AuthManager:
    """Manages user authentication."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.failed_attempts: Dict[str, int] = {}
    
    def register_user(self, username: str, email: str, password: str, role: str = "user") -> User:
        """Register a new user."""
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
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = self.users.get(username)
        if user and self._verify_password(password, user.password_hash):
            self.failed_attempts[username] = 0
            return user
        
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
        if self.failed_attempts[username] >= 5:
            raise Exception(f"Account locked for {username}")
        return None
    
    def _hash_password(self, password: str) -> str:
        """Hash password (simplified)."""
        return f"hashed_{password}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password."""
        return self._hash_password(password) == hashed
    
    def get_user_permissions(self, username: str) -> List[str]:
        """Get user permissions based on role."""
        user = self.users.get(username)
        if not user:
            return []
        
        role_permissions = {
            "admin": ["read", "write", "delete", "manage_users"],
            "moderator": ["read", "write", "delete"],
            "user": ["read", "write"],
            "guest": ["read"]
        }
        return role_permissions.get(user.role, ["read"])