"""
Rate limiting middleware for the application.

This module provides a rate limiting middleware to prevent brute force attacks
and other forms of abuse.
"""
import time
from typing import Dict, Any, List, Tuple
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response, RedirectResponse

from app.config import config
from app.logging import get_logger
from app.exceptions import RateLimitError

# Get logger
logger = get_logger(__name__)

# In-memory storage for rate limiting
# In a production environment, this should be replaced with Redis or similar
# Format: {ip_address: [(timestamp1, path1), (timestamp2, path2), ...]}
request_history: Dict[str, List[Tuple[float, str]]] = {}

# Rate limit configuration
# Format: {path_prefix: (max_requests, window_seconds, block_seconds)}
RATE_LIMITS = {
    "/auth/login": (5, 60, 300),  # 5 requests per minute, block for 5 minutes
    "/auth/register": (3, 60, 300),  # 3 requests per minute, block for 5 minutes
    "/auth/resend-verification": (3, 60, 300),  # 3 requests per minute, block for 5 minutes
    "/auth/reset-password": (3, 60, 300),  # 3 requests per minute, block for 5 minutes
}

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for rate limiting requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and apply rate limiting.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the next middleware or route handler
        """
        # Skip rate limiting in development mode
        if config.is_development():
            return await call_next(request)

        # Get client IP address
        client_ip = request.client.host if request.client else "unknown"

        # Get request path
        path = request.url.path

        # Check if path is subject to rate limiting
        rate_limit_key = None
        for prefix, limits in RATE_LIMITS.items():
            if path.startswith(prefix):
                rate_limit_key = prefix
                max_requests, window_seconds, block_seconds = limits
                break

        # If path is not subject to rate limiting, proceed
        if not rate_limit_key:
            return await call_next(request)

        # Check if client is rate limited
        if client_ip in request_history:
            # Get request history for this client
            history = request_history[client_ip]

            # Remove old entries
            current_time = time.time()
            history = [(ts, p) for ts, p in history if current_time - ts < window_seconds]

            # Count requests for this path prefix
            path_count = sum(1 for ts, p in history if p.startswith(rate_limit_key))

            # Check if client is blocked
            if path_count >= max_requests:
                # Calculate time until unblocked
                oldest_relevant = min([ts for ts, p in history if p.startswith(rate_limit_key)])
                time_until_unblocked = window_seconds - (current_time - oldest_relevant)

                # Log rate limit exceeded
                logger.warning(f"Rate limit exceeded for {client_ip} on {path}: {path_count} requests in {window_seconds} seconds")

                # If this is an API request, return a JSON response
                if path.startswith("/api/"):
                    return Response(
                        status_code=429,
                        content={"error": "Too many requests", "retry_after": int(time_until_unblocked)},
                        media_type="application/json"
                    )

                # For regular requests, redirect to an error page
                return RedirectResponse(
                    url=f"/auth/rate-limited?retry_after={int(time_until_unblocked)}",
                    status_code=303
                )

            # Update request history
            request_history[client_ip] = history + [(current_time, path)]
        else:
            # Initialize request history for this client
            request_history[client_ip] = [(time.time(), path)]

        # Proceed with the request
        return await call_next(request)


def get_rate_limit_middleware():
    """
    Get the rate limit middleware.

    Returns:
        RateLimitMiddleware: The rate limit middleware
    """
    return RateLimitMiddleware
