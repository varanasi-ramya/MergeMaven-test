"""
API v2 endpoints - PR #4: RESTful API v2 with enhanced features
This branch adds pagination, filtering, versioning, and rate limiting.
CONFLICTS with base API module
"""

from typing import List, Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from urllib.parse import urlencode


T = TypeVar('T')


class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class APIVersion(Enum):
    """API versions."""
    V1 = "v1"
    V2 = "v2"


@dataclass
class PaginationParams:
    """Pagination parameters."""
    page: int = 1
    per_page: int = 20
    max_per_page: int = 100
    
    def __post_init__(self):
        if self.per_page > self.max_per_page:
            self.per_page = self.max_per_page
        if self.page < 1:
            self.page = 1


@dataclass
class FilterParams:
    """Filter parameters."""
    filters: Dict[str, Any] = field(default_factory=dict)
    sort_by: Optional[str] = None
    sort_order: str = "asc"  # asc, desc
    
    def add_filter(self, key: str, value: Any):
        self.filters[key] = value


@dataclass
class PaginatedResponse(Generic[T]):
    """Paginated API response."""
    data: List[T]
    pagination: Dict[str, Any]
    links: Dict[str, str] = field(default_factory=dict)


@dataclass
class APIEndpoint:
    """API endpoint definition (enhanced)."""
    path: str
    method: HTTPMethod
    handler: str
    description: str
    version: APIVersion = APIVersion.V1
    requires_auth: bool = True
    rate_limit: Optional[int] = None  # requests per minute
    deprecated: bool = False
    tags: List[str] = field(default_factory=list)


class RateLimiter:
    """Rate limiting for API endpoints."""
    
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[datetime]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = datetime.now()
        window_start = now - timedelta(seconds=self.window_seconds)
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if req_time > window_start
        ]
        
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests in window."""
        return max(0, self.max_requests - len(self.requests.get(key, [])))


class APIRouter:
    """Enhanced API router with versioning, pagination, filtering, and rate limiting."""
    
    def __init__(self):
        self.routes: List[APIEndpoint] = []
        self.rate_limiter = RateLimiter()
        self.version = APIVersion.V2
    
    def add_route(self, endpoint: APIEndpoint):
        """Add an API route."""
        self.routes.append(endpoint)
    
    def get_routes(self, version: Optional[APIVersion] = None) -> List[APIEndpoint]:
        """Get all registered routes, optionally filtered by version."""
        if version:
            return [r for r in self.routes if r.version == version]
        return self.routes
    
    def find_route(self, path: str, method: HTTPMethod, version: APIVersion = APIVersion.V2) -> Optional[APIEndpoint]:
        """Find matching route."""
        for route in self.routes:
            if route.path == path and route.method == method and route.version == version:
                if route.deprecated:
                    continue
            return route
        return None
    
    def check_rate_limit(self, client_id: str, limit: Optional[int] = None) -> bool:
        """Check rate limit for client."""
        return self.rate_limiter.is_allowed(client_id)
    
    def build_paginated_response(
        self,
        data: List[Any],
        pagination: PaginationParams,
        base_url: str,
        total: int
    ) -> PaginatedResponse:
        """Build paginated response with links."""
        total_pages = (total + pagination.per_page - 1) // pagination.per_page
        
        links = {
            "self": f"{base_url}?page={pagination.page}&per_page={pagination.per_page}",
            "first": f"{base_url}?page=1&per_page={pagination.per_page}",
            "last": f"{base_url}?page={total_pages}&per_page={pagination.per_page}"
        }
        
        if pagination.page > 1:
            links["prev"] = f"{base_url}?page={pagination.page - 1}&per_page={pagination.per_page}"
        
        if pagination.page < total_pages:
            links["next"] = f"{base_url}?page={pagination.page + 1}&per_page={pagination.per_page}"
        
        return PaginatedResponse(
            data=data,
            pagination={
                "page": pagination.page,
                "per_page": pagination.per_page,
                "total": total,
                "total_pages": total_pages
            },
            links=links
        )


class ResponseBuilder:
    """Builds API responses (enhanced)."""
    
    @staticmethod
    def success(data: Any, message: str = "Success", meta: Optional[Dict] = None) -> Dict[str, Any]:
        """Build success response."""
        response = {"status": "success", "message": message, "data": data}
        if meta:
            response["meta"] = meta
        return response
    
    @staticmethod
    def error(message: str, code: int = 400, errors: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """Build error response."""
        response = {"status": "error", "message": message, "code": code}
        if errors:
            response["errors"] = errors
        return response
    
    @staticmethod
    def paginated(data: List[Any], pagination: Dict[str, Any], links: Dict[str, str]) -> Dict[str, Any]:
        """Build paginated response."""
        return {
            "status": "success",
            "data": data,
            "pagination": pagination,
            "links": links
        }
    
    @staticmethod
    def rate_limited(retry_after: int) -> Dict[str, Any]:
        """Build rate limit response."""
        return {
            "status": "error",
            "message": "Rate limit exceeded",
            "code": 429,
            "retry_after": retry_after
        }


class APIVersionManager:
    """Manages API versioning."""
    
    def __init__(self):
        self.versions: Dict[APIVersion, Dict[str, Any]] = {
            APIVersion.V1: {"status": "deprecated", "sunset_date": "2026-12-31"},
            APIVersion.V2: {"status": "current", "release_date": "2026-01-15"}
        }
    
    def get_version_info(self, version: APIVersion) -> Dict[str, Any]:
        """Get version information."""
        return self.versions.get(version, {"status": "unknown"})
    
    def is_version_supported(self, version: APIVersion) -> bool:
        """Check if version is supported."""
        info = self.get_version_info(version)
        return info.get("status") != "deprecated"