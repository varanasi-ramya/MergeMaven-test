"""
Tests for RBAC authentication module.
"""

import unittest
from src.auth import AuthManager, User, Role, Permission


class TestAuthManager(unittest.TestCase):
    """Test cases for AuthManager with RBAC."""
    
    def setUp(self):
        self.auth = AuthManager()
    
    def test_register_user_with_role(self):
        """Test user registration with role."""
        user = self.auth.register_user("admin", "admin@example.com", "password123", Role.ADMIN)
        self.assertEqual(user.username, "admin")
        self.assertEqual(user.role, Role.ADMIN)
    
    def test_default_user_role(self):
        """Test default user role."""
        user = self.auth.register_user("testuser", "test@example.com", "password123")
        self.assertEqual(user.role, Role.USER)
    
    def test_assign_role(self):
        """Test role assignment."""
        self.auth.register_user("admin", "admin@example.com", "password123", Role.ADMIN)
        self.auth.register_user("testuser", "test@example.com", "password123")
        
        result = self.auth.assign_role("testuser", Role.MODERATOR, "admin")
        self.assertTrue(result)
        
        user = self.auth.users["testuser"]
        self.assertEqual(user.role, Role.MODERATOR)
    
    def test_assign_role_insufficient_permissions(self):
        """Test role assignment without permissions."""
        self.auth.register_user("user1", "user1@example.com", "password123")
        self.auth.register_user("user2", "user2@example.com", "password123")
        
        with self.assertRaises(PermissionError):
            self.auth.assign_role("user2", Role.ADMIN, "user1")
    
    def test_grant_custom_permission(self):
        """Test granting custom permission."""
        self.auth.register_user("admin", "admin@example.com", "password123", Role.ADMIN)
        self.auth.register_user("testuser", "test@example.com", "password123")
        
        result = self.auth.grant_permission("testuser", Permission.MANAGE_ROLES, "admin")
        self.assertTrue(result)
        
        user = self.auth.users["testuser"]
        self.assertIn(Permission.MANAGE_ROLES, user.permissions)
    
    def test_revoke_custom_permission(self):
        """Test revoking custom permission."""
        self.auth.register_user("admin", "admin@example.com", "password123", Role.ADMIN)
        self.auth.register_user("testuser", "test@example.com", "password123")
        
        self.auth.grant_permission("testuser", Permission.MANAGE_ROLES, "admin")
        result = self.auth.revoke_permission("testuser", Permission.MANAGE_ROLES, "admin")
        self.assertTrue(result)
        
        user = self.auth.users["testuser"]
        self.assertNotIn(Permission.MANAGE_ROLES, user.permissions)
    
    def test_authenticate_valid(self):
        """Test valid authentication."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        user = self.auth.authenticate("testuser", "password123")
        self.assertIsNotNone(user)
        self.assertEqual(user.username, "testuser")
    
    def test_authenticate_invalid(self):
        """Test invalid authentication."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        user = self.auth.authenticate("testuser", "wrongpassword")
        self.assertIsNone(user)
    
    def test_account_lockout(self):
        """Test account lockout after failed attempts."""
        self.auth.register_user("testuser", "test@example.com", "password123")
        
        for _ in range(5):
            self.auth.authenticate("testuser", "wrongpassword")
        
        user = self.auth.users["testuser"]
        self.assertFalse(user.is_active)
    
    def test_has_permission_role_based(self):
        """Test role-based permissions."""
        self.auth.register_user("admin", "admin@example.com", "password123", Role.ADMIN)
        self.auth.register_user("user", "user@example.com", "password123", Role.USER)
        
        self.assertTrue(self.auth.has_permission("admin", Permission.MANAGE_USERS))
        self.assertFalse(self.auth.has_permission("user", Permission.MANAGE_USERS))
        self.assertTrue(self.auth.has_permission("user", Permission.READ))
        self.assertTrue(self.auth.has_permission("user", Permission.WRITE))
    
    def test_has_permission_custom(self):
        """Test custom permissions."""
        self.auth.register_user("admin", "admin@example.com", "password123", Role.ADMIN)
        self.auth.register_user("user", "user@example.com", "password123")
        
        self.auth.grant_permission("user", Permission.MANAGE_USERS, "admin")
        
        self.assertTrue(self.auth.has_permission("user", Permission.MANAGE_USERS))
    
    def test_effective_permissions(self):
        """Test effective permissions (role + custom)."""
        self.auth.register_user("admin", "admin@example.com", "password123", Role.ADMIN)
        self.auth.register_user("user", "user@example.com", "password123")
        
        admin_perms = self.auth.get_user_effective_permissions("admin")
        self.assertIn(Permission.MANAGE_USERS, admin_perms)
        
        user_perms = self.auth.get_user_effective_permissions("user")
        self.assertIn(Permission.READ, user_perms)
        self.assertIn(Permission.WRITE, user_perms)


if __name__ == "__main__":
    unittest.main()