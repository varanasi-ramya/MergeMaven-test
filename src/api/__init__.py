"""
Base API endpoints.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class HTTPMethod(Enum):
    """HTTP methods."""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"


@dataclass
class APIEndpoint:
    """API endpoint definition."""
    path: str
    method: HTTPMethod
    handler: str
    description: str
    requires_auth: bool = True


class APIRouter:
    """Routes API requests to handlers."""
    
    def __init__(self):
        self.routes: List[APIEndpoint] = []
    
    def add_route(self, endpoint: APIEndpoint):
        """Add an API route."""
        self.routes.append(endpoint)
    
    def get_routes(self) -> List[APIEndpoint]:
        """Get all registered routes."""
        return self.routes
    
    def find_route(self, path: str, method: HTTPMethod) -> Optional[APIEndpoint]:
        """Find matching route."""
        for route in self.routes:
            if route.path == path and route.method == method:
                return route
        return None


class ResponseBuilder:
    """Builds API responses."""
    
    @staticmethod
    def success(data: Any, message: str = "Success") -> Dict[str, Any]:
        """Build success response."""
        return {"status": "success", "message": message, "data": data}
    
    @staticmethod
    def error(message: str, code: int = 400) -> Dict[str, Any]:
        """Build error response."""
        return {"status": "error", "message": message, "code": code}