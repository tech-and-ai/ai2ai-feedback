"""
Notification Events

This module defines constants for all notification event types used in the system.
"""

class NotificationEvents:
    """Constants for notification event types."""
    
    # User account events
    USER_SIGNUP = "user.signup"
    EMAIL_VERIFICATION = "user.email_verification"
    EMAIL_VERIFIED = "user.email_verified"
    PASSWORD_RESET_REQUEST = "user.password_reset_request"
    PASSWORD_RESET_COMPLETE = "user.password_reset_complete"
    PROFILE_UPDATED = "user.profile_updated"
    EMAIL_CHANGED = "user.email_changed"
    EMAIL_CHANGE_VERIFICATION = "user.email_change_verification"
    
    # Subscription events
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    
    # Paper generation events
    PAPER_QUEUED = "paper.queued"
    PAPER_STARTED = "paper.started"
    PAPER_COMPLETED = "paper.completed"
    PAPER_FAILED = "paper.failed"
    
    # Credit events
    CREDITS_PURCHASED = "credits.purchased"
    CREDITS_LOW = "credits.low"
    CREDITS_DEPLETED = "credits.depleted"
    
    @classmethod
    def get_all_events(cls):
        """
        Get all notification event types.
        
        Returns:
            List of all event type constants
        """
        return [value for name, value in vars(cls).items() 
                if not name.startswith('_') and isinstance(value, str)]
                
    @classmethod
    def get_user_events(cls):
        """
        Get all user-related event types.
        
        Returns:
            List of user-related event type constants
        """
        return [value for name, value in vars(cls).items() 
                if not name.startswith('_') and isinstance(value, str) and value.startswith('user.')]
                
    @classmethod
    def get_subscription_events(cls):
        """
        Get all subscription-related event types.
        
        Returns:
            List of subscription-related event type constants
        """
        return [value for name, value in vars(cls).items() 
                if not name.startswith('_') and isinstance(value, str) and value.startswith('subscription.')]
                
    @classmethod
    def get_paper_events(cls):
        """
        Get all paper-related event types.
        
        Returns:
            List of paper-related event type constants
        """
        return [value for name, value in vars(cls).items() 
                if not name.startswith('_') and isinstance(value, str) and value.startswith('paper.')]
                
    @classmethod
    def get_credit_events(cls):
        """
        Get all credit-related event types.
        
        Returns:
            List of credit-related event type constants
        """
        return [value for name, value in vars(cls).items() 
                if not name.startswith('_') and isinstance(value, str) and value.startswith('credits.')]
