"""
Enhanced authentication module - PR #1: User Authentication System
This branch adds password reset, email verification, and login history.
"""

from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets


@dataclass
class User:
    """User model."""
    id: int
    username: str
    email: str
    password_hash: str
    role: str
    created_at: datetime
    email_verified: bool = False
    verification_token: Optional[str] = None
    last_login: Optional[datetime] = None
    login_history: List[Dict] = field(default_factory=list)


class AuthManager:
    """Manages user authentication."""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.failed_attempts: Dict[str, int] = {}
        self.reset_tokens: Dict[str, str] = {}  # token -> username
    
    def register_user(self, username: str, email: str, password: str, role: str = "user") -> User:
        """Register a new user with email verification."""
        if username in self.users:
            raise ValueError(f"User {username} already exists")
        
        user = User(
            id=len(self.users) + 1,
            username=username,
            email=email,
            password_hash=self._hash_password(password),
            role=role,
            created_at=datetime.now(),
            verification_token=secrets.token_urlsafe(32)
        )
        self.users[username] = user
        return user
    
    def verify_email(self, token: str) -> bool:
        """Verify user email with token."""
        for user in self.users.values():
            if user.verification_token == token:
                user.email_verified = True
                user.verification_token = None
                return True
        return False
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Authenticate user credentials."""
        user = self.users.get(username)
        if user and self._verify_password(password, user.password_hash):
            self.failed_attempts[username] = 0
            user.last_login = datetime.now()
            user.login_history.append({
                "timestamp": datetime.now().isoformat(),
                "ip": "unknown",
                "success": True
            })
            return user
        
        self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
        if self.failed_attempts[username] >= 5:
            raise Exception(f"Account locked for {username}")
        return None
    
    def request_password_reset(self, username: str) -> Optional[str]:
        """Request password reset token."""
        user = self.users.get(username)
        if not user:
            return None
        
        token = secrets.token_urlsafe(32)
        self.reset_tokens[token] = username
        return token
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset password with token."""
        username = self.reset_tokens.get(token)
        if not username:
            return False
        
        user = self.users[username]
        user.password_hash = self._hash_password(new_password)
        del self.reset_tokens[token]
        return True
    
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
    
    def get_login_history(self, username: str, limit: int = 10) -> List[Dict]:
        """Get user login history."""
        user = self.users.get(username)
        if not user:
            return []
        return user.login_history[-limit:]