"""
Notification Package

This package provides functionality for sending notifications to users.
"""

from app.services.notification.events import NotificationEvents
from app.services.notification.notification_service import NotificationService
from app.services.notification.template_manager import TemplateManager
from app.services.notification.user_preference_manager import UserPreferenceManager

__all__ = [
    'NotificationEvents',
    'NotificationService',
    'TemplateManager',
    'UserPreferenceManager'
]
