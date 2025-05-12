"""
Database module for Lily AI.

This module provides database access functionality.
"""

from core.database.client import get_db_client, DatabaseClient

__all__ = ['get_db_client', 'DatabaseClient']
