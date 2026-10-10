"""
Enhanced authentication module - PR #3: Session Management
This branch adds JWT tokens, refresh tokens, and session management.
CONFLICTS with both feature/user-auth and feature/rbac
"""

from typing import Optional, Dict, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import secrets
import jwt


# JWT Configuration
JWT_SECRET = "your-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


@dataclass
class TokenPair:
    """Access and refresh token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


@dataclass
class User:
    """User model with session support."""
    id: int
    username: str
    email: str
    password_hash: str
    role: str = "user"
    created_at: datetime = field(default_factory=datetime.now)
    refresh_tokens: Dict[str, datetime] = field(default_factory=dict)  # token -> expiry


class AuthManager:
    """Manages user authentication with JWT sessions."""
    
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
    
    def authenticate(self, username: str, password: str) -> Optional[TokenPair]:
        """Authenticate user and return token pair."""
        user = self.users.get(username)
        if not user or not self._verify_password(password, user.password_hash):
            self.failed_attempts[username] = self.failed_attempts.get(username, 0) + 1
            if self.failed_attempts[username] >= 5:
                raise Exception(f"Account locked for {username}")
            return None
        
        self.failed_attempts[username] = 0
        return self._create_token_pair(user)
    
    def _create_token_pair(self, user: User) -> TokenPair:
        """Create access and refresh token pair."""
        now = datetime.utcnow()
        access_expires = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_expires = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_payload = {
            "sub": user.username,
            "user_id": user.id,
            "role": user.role,
            "exp": access_expires,
            "iat": now,
            "type": "access"
        }
        
        refresh_payload = {
            "sub": user.username,
            "user_id": user.id,
            "exp": refresh_expires,
            "iat": now,
            "type": "refresh"
        }
        
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        
        # Store refresh token
        user.refresh_tokens[refresh_token] = refresh_expires
        
        return TokenPair(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    def refresh_access_token(self, refresh_token: str) -> Optional[TokenPair]:
        """Refresh access token using refresh token."""
        try:
            payload = jwt.decode(refresh_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "refresh":
                return None
        except jwt.InvalidTokenError:
            return None
        
        username = payload.get("sub")
        user = self.users.get(username)
        
        if not user or refresh_token not in user.refresh_tokens:
            return None
        
        # Check expiry
        if user.refresh_tokens[refresh_token] < datetime.utcnow():
            del user.refresh_tokens[refresh_token]
            return None
        
        # Create new token pair (rotate refresh token)
        del user.refresh_tokens[refresh_token]
        return self._create_token_pair(user)
    
    def revoke_refresh_token(self, username: str, refresh_token: str) -> bool:
        """Revoke a specific refresh token."""
        user = self.users.get(username)
        if not user:
            return False
        
        if refresh_token in user.refresh_tokens:
            del user.refresh_tokens[refresh_token]
            return True
        return False
    
    def revoke_all_refresh_tokens(self, username: str) -> bool:
        """Revoke all refresh tokens for a user."""
        user = self.users.get(username)
        if not user:
            return False
        
        user.refresh_tokens.clear()
        return True
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify and decode access token."""
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            if payload.get("type") != "access":
                return None
            return payload
        except jwt.InvalidTokenError:
            return None
    
    def get_user_from_token(self, token: str) -> Optional[User]:
        """Get user from access token."""
        payload = self.verify_token(token)
        if not payload:
            return None
        return self.users.get(payload.get("sub"))
    
    def _hash_password(self, password: str) -> str:
        """Hash password (simplified)."""
        return f"hashed_{password}"
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password."""
        return f"hashed_{password}" == hashed


from typing import Optional