"""
Tests for API v2 module.
"""

import unittest
from src.api import (
    HTTPMethod, APIVersion, PaginationParams, FilterParams,
    PaginatedResponse, APIEndpoint, RateLimiter, APIRouter,
    ResponseBuilder, APIVersionManager
)


class TestAPIVersionManager(unittest.TestCase):
    """Test cases for APIVersionManager."""
    
    def setUp(self):
        self.version_manager = APIVersionManager()
    
    def test_get_version_info(self):
        """Test getting version info."""
        v1_info = self.version_manager.get_version_info(APIVersion.V1)
        self.assertEqual(v1_info["status"], "deprecated")
        
        v2_info = self.version_manager.get_version_info(APIVersion.V2)
        self.assertEqual(v2_info["status"], "current")
    
    def test_is_version_supported(self):
        """Test version support check."""
        self.assertFalse(self.version_manager.is_version_supported(APIVersion.V1))
        self.assertTrue(self.version_manager.is_version_supported(APIVersion.V2))


class TestPaginationParams(unittest.TestCase):
    """Test cases for PaginationParams."""
    
    def test_default_values(self):
        """Test default pagination values."""
        params = PaginationParams()
        self.assertEqual(params.page, 1)
        self.assertEqual(params.per_page, 20)
        self.assertEqual(params.max_per_page, 100)
    
    def test_custom_values(self):
        """Test custom pagination values."""
        params = PaginationParams(page=3, per_page=50)
        self.assertEqual(params.page, 3)
        self.assertEqual(params.per_page, 50)
    
    def test_per_page_capped_at_max(self):
        """Test per_page capped at max_per_page."""
        params = PaginationParams(per_page=200, max_per_page=100)
        self.assertEqual(params.per_page, 100)
    
    def test_page_minimum_one(self):
        """Test page minimum is 1."""
        params = PaginationParams(page=0)
        self.assertEqual(params.page, 1)
        params = PaginationParams(page=-5)
        self.assertEqual(params.page, 1)


class TestFilterParams(unittest.TestCase):
    """Test cases for FilterParams."""
    
    def test_add_filter(self):
        """Test adding filters."""
        params = FilterParams()
        params.add_filter("status", "active")
        params.add_filter("role", "admin")
        
        self.assertEqual(params.filters["status"], "active")
        self.assertEqual(params.filters["role"], "admin")
    
    def test_sort_options(self):
        """Test sort options."""
        params = FilterParams(sort_by="created_at", sort_order="desc")
        self.assertEqual(params.sort_by, "created_at")
        self.assertEqual(params.sort_order, "desc")


class TestRateLimiter(unittest.TestCase):
    """Test cases for RateLimiter."""
    
    def test_rate_limit_allowed(self):
        """Test rate limiter allows requests under limit."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        for _ in range(5):
            self.assertTrue(limiter.is_allowed("client1"))
    
    def test_rate_limit_blocked(self):
        """Test rate limiter blocks excess requests."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        for _ in range(3):
            self.assertTrue(limiter.is_allowed("client1"))
        
        self.assertFalse(limiter.is_allowed("client1"))
    
    def test_rate_limit_window_reset(self):
        """Test rate limiter window reset (manual)."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        self.assertTrue(limiter.is_allowed("client1"))
        self.assertTrue(limiter.is_allowed("client1"))
        self.assertFalse(limiter.is_allowed("client1"))
        
        # Can't easily test time-based reset in unit test
        # but we can verify remaining count
        remaining = limiter.get_remaining("client1")
        self.assertEqual(remaining, 0)
    
    def test_different_clients_separate_limits(self):
        """Test different clients have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)
        
        self.assertTrue(limiter.is_allowed("client1"))
        self.assertTrue(limiter.is_allowed("client1"))
        
        self.assertTrue(limiter.is_allowed("client2"))
        self.assertTrue(limiter.is_allowed("client2"))
        
        self.assertFalse(limiter.is_allowed("client1"))
        self.assertFalse(limiter.is_allowed("client2"))


class TestAPIRouter(unittest.TestCase):
    """Test cases for APIRouter."""
    
    def setUp(self):
        self.router = APIRouter()
    
    def test_add_route(self):
        """Test adding routes."""
        endpoint = APIEndpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            handler="get_users",
            description="Get all users",
            version=APIVersion.V2
        )
        self.router.add_route(endpoint)
        
        routes = self.router.get_routes()
        self.assertEqual(len(routes), 1)
        self.assertEqual(routes[0].path, "/api/users")
    
    def test_find_route(self):
        """Test finding route."""
        endpoint = APIEndpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            handler="get_users",
            description="Get all users",
            version=APIVersion.V2
        )
        self.router.add_route(endpoint)
        
        found = self.router.find_route("/api/users", HTTPMethod.GET, APIVersion.V2)
        self.assertIsNotNone(found)
        self.assertEqual(found.handler, "get_users")
    
    def test_version_filtering(self):
        """Test version filtering."""
        endpoint_v1 = APIEndpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            handler="get_users_v1",
            description="Get all users v1",
            version=APIVersion.V1
        )
        endpoint_v2 = APIEndpoint(
            path="/api/users",
            method=HTTPMethod.GET,
            handler="get_users_v2",
            description="Get all users v2",
            version=APIVersion.V2
        )
        
        self.router.add_route(endpoint_v1)
        self.router.add_route(endpoint_v2)
        
        v1_routes = self.router.get_routes(APIVersion.V1)
        v2_routes = self.router.get_routes(APIVersion.V2)
        
        self.assertEqual(len(v1_routes), 1)
        self.assertEqual(len(v2_routes), 1)
    
    def test_deprecated_route_skipped(self):
        """Test deprecated routes are skipped."""
        endpoint = APIEndpoint(
            path="/api/old",
            method=HTTPMethod.GET,
            handler="old_handler",
            description="Old endpoint",
            version=APIVersion.V2,
            deprecated=True
        )
        self.router.add_route(endpoint)
        
        found = self.router.find_route("/api/old", HTTPMethod.GET, APIVersion.V2)
        self.assertIsNone(found)
    
    def test_rate_limiting(self):
        """Test rate limiting."""
        endpoint = APIEndpoint(
            path="/api/limited",
            method=HTTPMethod.GET,
            handler="limited_handler",
            description="Rate limited endpoint",
            version=APIVersion.V2,
            rate_limit=5
        )
        self.router.add_route(endpoint)
        
        # Simulate requests
        for _ in range(5):
            self.assertTrue(self.router.check_rate_limit("test_client"))
        
        # 6th request should be blocked
        self.assertFalse(self.router.check_rate_limit("test_client"))


class TestPaginatedResponse(unittest.TestCase):
    """Test cases for paginated response building."""
    
    def test_build_paginated_response(self):
        """Test building paginated response."""
        router = APIRouter()
        data = [{"id": i, "name": f"Item {i}"} for i in range(1, 6)]
        pagination = PaginationParams(page=1, per_page=5)
        
        response = router.build_paginated_response(
            data=data,
            pagination=pagination,
            base_url="/api/items",
            total=100
        )
        
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.pagination["total"], 100)
        self.assertEqual(response.pagination["page"], 1)
        self.assertEqual(response.pagination["per_page"], 5)
        self.assertEqual(response.pagination["total_pages"], 20)
        
        self.assertIn("self", response.links)
        self.assertIn("first", response.links)
        self.assertIn("last", response.links)
        self.assertIn("next", response.links)
        self.assertNotIn("prev", response.links)  # First page
    
    def test_pagination_links(self):
        """Test pagination link generation."""
        router = APIRouter()
        data = [{"id": i} for i in range(1, 6)]
        pagination = PaginationParams(page=5, per_page=5)
        
        response = router.build_paginated_response(
            data=data,
            pagination=pagination,
            base_url="/api/items",
            total=100
        )
        
        self.assertIn("prev", response.links)
        self.assertIn("next", response.links)
        self.assertEqual(response.links["prev"], "/api/items?page=4&per_page=5")
        self.assertEqual(response.links["next"], "/api/items?page=6&per_page=5")


class TestResponseBuilder(unittest.TestCase):
    """Test cases for ResponseBuilder."""
    
    def test_success_response(self):
        """Test success response."""
        response = ResponseBuilder.success(
            data={"id": 1, "name": "Test"},
            message="User created",
            meta={"version": "2.0"}
        )
        
        self.assertEqual(response["status"], "success")
        self.assertEqual(response["message"], "User created")
        self.assertEqual(response["data"]["id"], 1)
        self.assertEqual(response["meta"]["version"], "2.0")
    
    def test_error_response(self):
        """Test error response."""
        response = ResponseBuilder.error(
            message="Validation failed",
            code=422,
            errors=[{"field": "email", "message": "Invalid email"}]
        )
        
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["code"], 422)
        self.assertEqual(len(response["errors"]), 1)
    
    def test_paginated_response(self):
        """Test paginated response."""
        response = ResponseBuilder.paginated(
            data=[{"id": 1}, {"id": 2}],
            pagination={"page": 1, "per_page": 10, "total": 50, "total_pages": 5},
            links={"self": "/api/items?page=1", "next": "/api/items?page=2"}
        )
        
        self.assertEqual(response["status"], "success")
        self.assertEqual(len(response["data"]), 2)
        self.assertEqual(response["pagination"]["total"], 50)
        self.assertIn("next", response["links"])
    
    def test_rate_limited_response(self):
        """Test rate limited response."""
        response = ResponseBuilder.rate_limited(retry_after=60)
        
        self.assertEqual(response["status"], "error")
        self.assertEqual(response["code"], 429)
        self.assertEqual(response["retry_after"], 60)


if __name__ == "__main__":
    unittest.main()