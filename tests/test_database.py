"""
Tests for database module.
"""

import unittest
from src.database import DatabaseManager, DatabaseConfig


class TestDatabaseManager(unittest.TestCase):
    """Test cases for DatabaseManager."""
    
    def setUp(self):
        self.config = DatabaseConfig(
            host="localhost",
            port=5432,
            database="test_db",
            user="test_user",
            password="test_pass"
        )
        self.db = DatabaseManager(self.config)
    
    def test_connect(self):
        """Test database connection."""
        result = self.db.connect()
        self.assertTrue(result)
    
    def test_disconnect(self):
        """Test database disconnection."""
        self.db.connect()
        self.db.disconnect()
        self.assertIsNone(self.db.connection)
    
    def test_get_user_by_id(self):
        """Test getting user by ID."""
        self.db.connect()
        user = self.db.get_user_by_id(1)
        self.assertIsNotNone(user)
        self.assertEqual(user["id"], 1)
    
    def test_create_user(self):
        """Test creating user."""
        self.db.connect()
        user_id = self.db.create_user("testuser", "test@example.com", "hashed_password")
        self.assertEqual(user_id, 1)


if __name__ == "__main__":
    unittest.main()