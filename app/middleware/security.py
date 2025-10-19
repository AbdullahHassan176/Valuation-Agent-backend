"""Security middleware for request size limits and rate limiting."""

import time
import asyncio
from typing import Dict, Optional
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to limit request body size."""
    
    def __init__(self, app, max_size: int = 10 * 1024 * 1024):  # 10MB default
        """Initialize request size limit middleware.
        
        Args:
            app: FastAPI application
            max_size: Maximum request size in bytes
        """
        super().__init__(app)
        self.max_size = max_size
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and check size limit.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
            
        Raises:
            HTTPException: 413 if request size exceeds limit
        """
        # Check content length header
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_size:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request too large. Maximum size: {self.max_size // (1024*1024)}MB"
                    )
            except ValueError:
                # Invalid content-length header, let it pass
                pass
        
        # Process request
        response = await call_next(request)
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting middleware."""
    
    def __init__(self, app, requests_per_minute: int = 60, burst_size: int = 10):
        """Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            requests_per_minute: Maximum requests per minute per IP
            burst_size: Maximum burst requests allowed
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.tokens: Dict[str, float] = {}  # IP -> token count
        self.last_refill: Dict[str, float] = {}  # IP -> last refill time
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and check rate limit.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response from next handler
            
        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check rate limit
        if not self._check_rate_limit(client_ip):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Process request
        response = await call_next(request)
        return response
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client is within rate limit.
        
        Args:
            client_ip: Client IP address
            
        Returns:
            True if within rate limit, False otherwise
        """
        current_time = time.time()
        
        # Initialize token bucket for new IP
        if client_ip not in self.tokens:
            self.tokens[client_ip] = self.burst_size
            self.last_refill[client_ip] = current_time
            return True
        
        # Refill tokens based on time elapsed
        time_elapsed = current_time - self.last_refill[client_ip]
        tokens_to_add = time_elapsed * (self.requests_per_minute / 60.0)
        
        self.tokens[client_ip] = min(
            self.burst_size,
            self.tokens[client_ip] + tokens_to_add
        )
        self.last_refill[client_ip] = current_time
        
        # Check if tokens available
        if self.tokens[client_ip] >= 1.0:
            self.tokens[client_ip] -= 1.0
            return True
        
        return False


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler
            
        Returns:
            Response with security headers
        """
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response
