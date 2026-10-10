"""
Tests for session management module.
"""

import unittest
import jwt
from datetime import datetime, timedelta
from src.auth import AuthManager, User, TokenPair, JWT_SECRET, JWT_ALGORITHM


class TestAuthManager(unittest.TestCase):
    """Test cases for AuthManager with session management."""
    
    def setUp(self):
        self.auth = AuthManager()
    
    def test_register_user(self):
        """Test user registration."""
        user = self.auth.register_user("testuser", "test@example.com", "password123")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "user")
        self.assertEqual(user.refresh_tokens, {})
    
    def test_authenticate_returns_token_pair(self):
        """Test authentication returns token pair."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens = self.auth.authenticate("testuser", "password123")
        
        self.assertIsNotNone(tokens)
        self.assertIsInstance(tokens, TokenPair)
        self.assertIsNotNone(tokens.access_token)
        self.assertIsNotNone(tokens.refresh_token)
        self.assertEqual(tokens.token_type, "bearer")
    
    def test_authenticate_invalid_credentials(self):
        """Test authentication with invalid credentials."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens = self.auth.authenticate("testuser", "wrongpassword")
        self.assertIsNone(tokens)
    
    def test_refresh_access_token(self):
        """Test refreshing access token."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens = self.auth.authenticate("testuser", "password123")
        
        new_tokens = self.auth.refresh_access_token(tokens.refresh_token)
        
        self.assertIsNotNone(new_tokens)
        self.assertNotEqual(new_tokens.access_token, tokens.access_token)
        self.assertNotEqual(new_tokens.refresh_token, tokens.refresh_token)
    
    def test_refresh_token_invalid(self):
        """Test refreshing with invalid token."""
        result = self.auth.refresh_access_token("invalid_token")
        self.assertIsNone(result)
    
    def test_refresh_token_expired(self):
        """Test refreshing with expired token."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens = self.auth.authenticate("testuser", "password123")
        
        # Manually expire the refresh token
        user = self.auth.users["testuser"]
        for token, expiry in user.refresh_tokens.items():
            user.refresh_tokens[token] = datetime.utcnow() - timedelta(days=1)
        
        result = self.auth.refresh_access_token(tokens.refresh_token)
        self.assertIsNone(result)
    
    def test_revoke_refresh_token(self):
        """Test revoking specific refresh token."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens = self.auth.authenticate("testuser", "password123")
        
        result = self.auth.revoke_refresh_token("testuser", tokens.refresh_token)
        self.assertTrue(result)
        
        # Token should no longer work
        new_tokens = self.auth.refresh_access_token(tokens.refresh_token)
        self.assertIsNone(new_tokens)
    
    def test_revoke_all_refresh_tokens(self):
        """Test revoking all refresh tokens."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens1 = self.auth.authenticate("testuser", "password123")
        tokens2 = self.auth.authenticate("testuser", "password123")
        
        result = self.auth.revoke_all_refresh_tokens("testuser")
        self.assertTrue(result)
        
        # Both tokens should be invalid
        self.assertIsNone(self.auth.refresh_access_token(tokens1.refresh_token))
        self.assertIsNone(self.auth.refresh_access_token(tokens2.refresh_token))
    
    def test_verify_access_token(self):
        """Test verifying access token."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens = self.auth.authenticate("testuser", "password123")
        
        payload = self.auth.verify_token(tokens.access_token)
        
        self.assertIsNotNone(payload)
        self.assertEqual(payload["sub"], "testuser")
        self.assertEqual(payload["type"], "access")
    
    def test_verify_invalid_token(self):
        """Test verifying invalid token."""
        payload = self.auth.verify_token("invalid_token")
        self.assertIsNone(payload)
    
    def test_get_user_from_token(self):
        """Test getting user from access token."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        tokens = self.auth.authenticate("testuser", "password123")
        
        user = self.auth.get_user_from_token(tokens.access_token)
        
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
    
    def test_multiple_sessions(self):
        """Test multiple concurrent sessions."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        
        tokens1 = self.auth.authenticate("testuser", "password123")
        tokens2 = self.auth.authenticate("testuser", "password123")
        
        # Both refresh tokens should be stored
        user = self.auth.users["testuser"]
        self.assertEqual(len(user.refresh_tokens), 2)
        
        # Both should work
        new1 = self.auth.refresh_access_token(tokens1.refresh_token)
        new2 = self.auth.refresh_access_token(tokens2.refresh_token)
        
        self.assertIsNotNone(new1)
        self.assertIsNotNone(new2)


if __name__ == "__main__":
    unittest.main()