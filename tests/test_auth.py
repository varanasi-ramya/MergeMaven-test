"""
Tests for enhanced authentication module.
"""

import unittest
from datetime import datetime
from src.auth import AuthManager, User


class TestAuthManager(unittest.TestCase):
    """Test cases for AuthManager."""
    
    def setUp(self):
        self.auth = AuthManager()
    
    def test_register_user(self):
        """Test user registration with email verification."""
        user = self.auth.register_user("testuser", "test@example.com", "password123")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "user")
        self.assertFalse(user.email_verified)
        self.assertIsNotNone(user.verification_token)
    
    def test_verify_email(self):
        """Test email verification."""
        user = self.auth.register_user("testuser", "test@example.com", "password123")
        token = user.verification_token
        result = self.auth.verify_email(token)
        self.assertTrue(result)
        self.assertTrue(user.email_verified)
        self.assertIsNone(user.verification_token)
    
    def test_register_duplicate_user(self):
        """Test registering duplicate user raises error."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        with self.assertRaises(ValueError):
            self.auth.register_user("testuser", "test2@example.com", "password123")
    
    def test_authenticate_valid(self):
        """Test valid authentication."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        user = self.auth.authenticate("testuser", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
        self.assertIsNotNone(user.last_login)
        self.assertEqual(len(user.login_history), 1)
    
    def test_authenticate_invalid_password(self):
        """Test invalid password authentication."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        user = self.auth.authenticate("testuser", "wrongpassword")
        self.assertIsNone(user)
    
    def test_password_reset_flow(self):
        """Test password reset request and reset."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        
        # Request reset
        token = self.auth.request_password_reset("testuser")
        self.assertIsNotNone(token)
        
        # Reset password
        result = self.auth.reset_password(token, "newpassword123")
        self.assertTrue(result)
        
        # Verify new password works
        user = self.auth.authenticate("testuser", "newpassword123")
        self.assertIsNotNone(user)
    
    def test_get_user_permissions(self):
        """Test getting user permissions."""
        self.auth.register_user("admin", "admin@example.com", "admin123", "admin")
        perms = self.auth.get_user_permissions("admin")
        self.assertIn("read", perms)
        self.assertIn("write", perms)
        self.assertIn("delete", perms)
        self.assertIn("manage_users", perms)
    
    def test_login_history(self):
        """Test login history tracking."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        self.auth.authenticate("testuser", "password123")
        self.auth.authenticate("testuser", "password123")
        
        history = self.auth.get_login_history("testuser")
        self.assertEqual(len(history), 2)
    
    def test_account_lockout(self):
        """Test account lockout after failed attempts."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        
        for _ in range(5):
            self.auth.authenticate("testuser", "wrongpassword")
        
        with self.assertRaises(Exception):
            self.auth.authenticate("testuser", "wrongpassword")


if __name__ == "__main__":
    unittest.main()