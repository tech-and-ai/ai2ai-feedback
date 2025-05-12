"""
User Preference Manager

This module provides functionality for managing user notification preferences.
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class UserPreferenceManager:
    """
    Manages user notification preferences.
    """
    
    def __init__(self, db_client):
        """
        Initialize with database client.
        
        Args:
            db_client: Supabase client or other database client
        """
        self.db = db_client
        
    async def get_preferences(self, user_id: str) -> Dict[str, bool]:
        """
        Get notification preferences for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary of notification preferences
        """
        try:
            response = self.db.table('saas_user_notification_preferences') \
                .select('notification_type, enabled') \
                .eq('user_id', user_id) \
                .execute()
                
            preferences = {}
            if response.data:
                for pref in response.data:
                    preferences[pref['notification_type']] = pref['enabled']
                    
            return preferences
            
        except Exception as e:
            logger.error(f"Error getting preferences for user {user_id}: {str(e)}")
            return {}
        
    async def update_preference(self, user_id: str, notification_type: str, enabled: bool) -> bool:
        """
        Update a notification preference for a user.
        
        Args:
            user_id: ID of the user
            notification_type: Type of notification
            enabled: Whether the notification is enabled
            
        Returns:
            True if update was successful, False otherwise
        """
        try:
            # Check if preference already exists
            existing = self.db.table('saas_user_notification_preferences') \
                .select('*') \
                .eq('user_id', user_id) \
                .eq('notification_type', notification_type) \
                .execute()
                
            if existing.data and len(existing.data) > 0:
                # Update existing preference
                response = self.db.table('saas_user_notification_preferences') \
                    .update({'enabled': enabled}) \
                    .eq('user_id', user_id) \
                    .eq('notification_type', notification_type) \
                    .execute()
            else:
                # Create new preference
                response = self.db.table('saas_user_notification_preferences').insert({
                    'user_id': user_id,
                    'notification_type': notification_type,
                    'enabled': enabled
                }).execute()
                
            if response.data and len(response.data) > 0:
                logger.info(f"Updated preference for user {user_id}: {notification_type} = {enabled}")
                return True
            else:
                logger.error(f"Failed to update preference for user {user_id}: {notification_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating preference for user {user_id}: {str(e)}")
            return False
        
    async def can_notify(self, user_id: str, notification_type: str) -> bool:
        """
        Check if a user can be notified for a specific notification type.
        
        Args:
            user_id: ID of the user
            notification_type: Type of notification
            
        Returns:
            Boolean indicating whether the user can be notified
        """
        try:
            # Get user preference for this notification type
            response = self.db.table('saas_user_notification_preferences') \
                .select('enabled') \
                .eq('user_id', user_id) \
                .eq('notification_type', notification_type) \
                .execute()
                
            # If preference exists, return its value
            if response.data and len(response.data) > 0:
                return response.data[0]['enabled']
                
            # If no preference exists, check if this is a required notification
            if self._is_required_notification(notification_type):
                return True
                
            # Otherwise, return default preference (True for most notifications)
            return self._get_default_preference(notification_type)
            
        except Exception as e:
            logger.error(f"Error checking notification permission for user {user_id}: {str(e)}")
            # Default to allowing notification in case of error
            return True
            
    async def set_default_preferences(self, user_id: str) -> bool:
        """
        Set default notification preferences for a new user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Define default preferences
            default_preferences = {
                # User account notifications (mostly required)
                "user.signup": True,
                "user.email_verification": True,
                "user.email_verified": True,
                "user.password_reset_request": True,
                "user.password_reset_complete": True,
                "user.profile_updated": True,
                "user.email_changed": True,
                "user.email_change_verification": True,
                
                # Subscription notifications
                "subscription.created": True,
                "subscription.updated": True,
                "subscription.cancelled": True,
                "subscription.renewed": True,
                
                # Paper generation notifications
                "paper.queued": True,
                "paper.started": True,
                "paper.completed": True,
                "paper.failed": True,
                
                # Credit notifications
                "credits.purchased": True,
                "credits.low": True,
                "credits.depleted": True
            }
            
            # Insert all preferences
            preferences_to_insert = [
                {
                    'user_id': user_id,
                    'notification_type': notification_type,
                    'enabled': enabled
                }
                for notification_type, enabled in default_preferences.items()
            ]
            
            response = self.db.table('saas_user_notification_preferences') \
                .insert(preferences_to_insert) \
                .execute()
                
            if response.data and len(response.data) > 0:
                logger.info(f"Set default preferences for user {user_id}")
                return True
            else:
                logger.error(f"Failed to set default preferences for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error setting default preferences for user {user_id}: {str(e)}")
            return False
            
    def _is_required_notification(self, notification_type: str) -> bool:
        """
        Check if a notification type is required (cannot be disabled).
        
        Args:
            notification_type: Type of notification
            
        Returns:
            True if the notification is required, False otherwise
        """
        # Define required notification types
        required_notifications = [
            "user.email_verification",
            "user.email_change_verification",
            "user.password_reset_request"
        ]
        
        return notification_type in required_notifications
        
    def _get_default_preference(self, notification_type: str) -> bool:
        """
        Get the default preference for a notification type.
        
        Args:
            notification_type: Type of notification
            
        Returns:
            Default preference (True or False)
        """
        # Define notification types that are disabled by default
        disabled_by_default = [
            # None currently - most notifications are enabled by default
        ]
        
        return notification_type not in disabled_by_default
