"""
Custom exceptions for the application.

This module defines custom exception classes that can be used throughout the application
to provide more specific error handling and better error messages.
"""
from typing import Dict, Any, Optional, List, Union
from fastapi import HTTPException, status


class AppException(Exception):
    """Base exception class for application-specific exceptions."""
    
    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            status_code: HTTP status code
            detail: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.detail = detail or {}
        super().__init__(self.message)
    
    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException."""
        return HTTPException(
            status_code=self.status_code,
            detail={
                "message": self.message,
                "detail": self.detail
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "message": self.message,
            "status_code": self.status_code,
            "detail": self.detail
        }


class AuthenticationError(AppException):
    """Exception raised for authentication errors."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        detail: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception."""
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class AuthorizationError(AppException):
    """Exception raised for authorization errors."""
    
    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        detail: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception."""
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class ValidationError(AppException):
    """Exception raised for validation errors."""
    
    def __init__(
        self,
        message: str = "Validation error",
        detail: Optional[Dict[str, Any]] = None,
        field_errors: Optional[Dict[str, List[str]]] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            detail: Additional error details
            field_errors: Validation errors by field
        """
        detail = detail or {}
        if field_errors:
            detail["field_errors"] = field_errors
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class NotFoundError(AppException):
    """Exception raised when a resource is not found."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        detail: Optional[Dict[str, Any]] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[Union[str, int]] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            detail: Additional error details
            resource_type: Type of resource that was not found
            resource_id: ID of resource that was not found
        """
        detail = detail or {}
        if resource_type:
            detail["resource_type"] = resource_type
        if resource_id:
            detail["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class PaymentError(AppException):
    """Exception raised for payment processing errors."""
    
    def __init__(
        self,
        message: str = "Payment processing error",
        detail: Optional[Dict[str, Any]] = None,
        payment_provider: Optional[str] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            detail: Additional error details
            payment_provider: Name of the payment provider (e.g., "stripe")
        """
        detail = detail or {}
        if payment_provider:
            detail["payment_provider"] = payment_provider
        
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class SubscriptionError(AppException):
    """Exception raised for subscription-related errors."""
    
    def __init__(
        self,
        message: str = "Subscription error",
        detail: Optional[Dict[str, Any]] = None
    ):
        """Initialize the exception."""
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class RateLimitError(AppException):
    """Exception raised when rate limits are exceeded."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        detail: Optional[Dict[str, Any]] = None,
        retry_after: Optional[int] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            detail: Additional error details
            retry_after: Seconds until the rate limit resets
        """
        detail = detail or {}
        if retry_after:
            detail["retry_after"] = retry_after
        
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail
        )
