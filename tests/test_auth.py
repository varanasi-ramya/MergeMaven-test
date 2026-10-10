"""
Tests for authentication module.
"""

import unittest
from src.auth import AuthManager, User


class TestAuthManager(unittest.TestCase):
    """Test cases for AuthManager."""
    
    def setUp(self):
        self.auth = AuthManager()
    
    def test_register_user(self):
        """Test user registration."""
        user = self.auth.register_user("testuser", "test@example.com", "password123")
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.role, "user")
    
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
    
    def test_authenticate_invalid_password(self):
        """Test invalid password authentication."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        user = self.auth.authenticate("testuser", "wrongpassword")
        self.assertIsNone(user)
    
    def test_get_user_permissions(self):
        """Test getting user permissions."""
        self.auth.register_user("admin", "admin@example.com", "admin123", "admin")
        perms = self.auth.get_user_permissions("admin")
        self.assertIn("read", perms)
        self.assertIn("write", perms)
        self.assertIn("delete", perms)
        self.assertIn("manage_users", perms)


if __name__ == "__main__":
    unittest.main()