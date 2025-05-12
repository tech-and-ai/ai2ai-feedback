"""
CSRF protection middleware for the application.

This module provides CSRF protection middleware to prevent cross-site request forgery attacks.
"""
import secrets
import time
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from app.config import config
from app.logging import get_logger

# Get logger
logger = get_logger(__name__)

# CSRF token cookie name
CSRF_TOKEN_COOKIE = "csrf_token"

# CSRF token form field name
CSRF_TOKEN_FIELD = "csrf_token"

# CSRF token expiration (seconds)
CSRF_TOKEN_EXPIRY = 3600  # 1 hour

# Paths that require CSRF protection (POST requests only)
CSRF_PROTECTED_PATHS = [
    "/auth/login",
    "/auth/register",
    "/auth/reset-password",
    "/auth/resend-verification",
    "/billing/",
]

class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection."""

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process the request and apply CSRF protection.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response: The response from the next middleware or route handler
        """
        # Get request path and method
        path = request.url.path
        method = request.method

        # Skip CSRF protection in development mode
        if config.is_development():
            logger.info(f"Skipping CSRF protection in development mode for {path}")
            return await call_next(request)

        # Only apply CSRF protection to POST requests to protected paths
        requires_csrf = method == "POST" and any(path.startswith(p) for p in CSRF_PROTECTED_PATHS)

        if requires_csrf:
            # Get CSRF token from cookie
            csrf_cookie = request.cookies.get(CSRF_TOKEN_COOKIE)

            # Get CSRF token from form data
            form_data = await request.form()
            csrf_form = form_data.get(CSRF_TOKEN_FIELD)

            # Validate CSRF token
            if not csrf_cookie or not csrf_form or csrf_cookie != csrf_form:
                # Log CSRF validation failure
                logger.warning(f"CSRF validation failed for {path}: cookie={csrf_cookie}, form={csrf_form}")

                # Redirect to error page
                return RedirectResponse(
                    url="/auth/login?error=csrf_validation_failed",
                    status_code=303
                )

        # Process the request
        response = await call_next(request)

        # Set CSRF token cookie for GET requests to pages that will need it
        if method == "GET" and any(path.startswith(p) for p in CSRF_PROTECTED_PATHS):
            # Generate new CSRF token
            csrf_token = secrets.token_hex(32)

            # Log the CSRF token
            logger.info(f"Generated CSRF token for {path}: {csrf_token[:10]}...")

            # Set CSRF token cookie
            response.set_cookie(
                key=CSRF_TOKEN_COOKIE,
                value=csrf_token,
                max_age=CSRF_TOKEN_EXPIRY,
                httponly=True,
                secure=not config.is_development(),
                samesite="lax"
            )

            # Log that we're setting the CSRF token cookie
            logger.info(f"Set CSRF token cookie for {path}")

            # If this is a template response, add CSRF token to context
            if hasattr(response, "context") and isinstance(response.context, dict):
                response.context["csrf_token"] = csrf_token
                # Log that we're setting the CSRF token in the context
                logger.info(f"Setting CSRF token in template context for {path}: {csrf_token[:10]}...")
            else:
                # Log that we're not setting the CSRF token in the context
                logger.warning(f"Cannot set CSRF token in template context for {path}: response has no context attribute or context is not a dict")

        return response


def get_csrf_middleware():
    """
    Get the CSRF middleware.

    Returns:
        CSRFMiddleware: The CSRF middleware
    """
    return CSRFMiddleware


def get_csrf_token(request: Request) -> Optional[str]:
    """
    Get the CSRF token from the request.

    Args:
        request: The incoming request

    Returns:
        Optional[str]: The CSRF token, or None if not found
    """
    return request.cookies.get(CSRF_TOKEN_COOKIE)
