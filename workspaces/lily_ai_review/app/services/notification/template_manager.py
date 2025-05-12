"""
Template Manager

This module provides functionality for managing email templates stored in the database.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from jinja2 import Template
import re

logger = logging.getLogger(__name__)

class TemplateManager:
    """
    Manages email templates stored in the database.
    """
    
    def __init__(self, db_client):
        """
        Initialize with database client.
        
        Args:
            db_client: Supabase client or other database client
        """
        self.db = db_client
        
    async def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by name.
        
        Args:
            template_name: Name of the template
            
        Returns:
            Template object or None if not found
        """
        try:
            response = self.db.table('saas_notification_templates') \
                .select('*') \
                .eq('name', template_name) \
                .eq('is_active', True) \
                .order('version', desc=True) \
                .limit(1) \
                .execute()
                
            if response.data and len(response.data) > 0:
                return response.data[0]
            else:
                logger.warning(f"Template not found: {template_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting template {template_name}: {str(e)}")
            return None
        
    async def get_template_for_event(self, event_type: str) -> Optional[Dict[str, Any]]:
        """
        Get the template associated with an event type.
        
        Args:
            event_type: Type of event
            
        Returns:
            Template object or None if not found
        """
        try:
            # First get the template ID for this event
            event_response = self.db.table('saas_notification_events') \
                .select('template_id') \
                .eq('event_type', event_type) \
                .eq('is_active', True) \
                .limit(1) \
                .execute()
                
            if not event_response.data or len(event_response.data) == 0:
                logger.warning(f"No template mapping found for event: {event_type}")
                return None
                
            template_id = event_response.data[0]['template_id']
            
            # Now get the template
            template_response = self.db.table('saas_notification_templates') \
                .select('*') \
                .eq('id', template_id) \
                .eq('is_active', True) \
                .limit(1) \
                .execute()
                
            if template_response.data and len(template_response.data) > 0:
                return template_response.data[0]
            else:
                logger.warning(f"Template not found for ID: {template_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting template for event {event_type}: {str(e)}")
            return None
        
    async def render_template(self, template: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, str]:
        """
        Render a template with data.
        
        Args:
            template: Template object
            data: Dictionary of data to include in the template
            
        Returns:
            Dictionary with rendered subject, html_content, and text_content
        """
        try:
            # Render subject
            subject_template = Template(template['subject'])
            rendered_subject = subject_template.render(**data)
            
            # Render HTML content
            html_template = Template(template['html_content'])
            rendered_html = html_template.render(**data)
            
            # Render text content
            text_template = Template(template['text_content'])
            rendered_text = text_template.render(**data)
            
            return {
                'subject': rendered_subject,
                'html_content': rendered_html,
                'text_content': rendered_text
            }
            
        except Exception as e:
            logger.error(f"Error rendering template {template.get('name', 'unknown')}: {str(e)}")
            # Return unrendered template as fallback
            return {
                'subject': template['subject'],
                'html_content': template['html_content'],
                'text_content': template['text_content']
            }
            
    async def create_template(self, name: str, subject: str, html_content: str, 
                             text_content: str = None, description: str = None) -> Optional[Dict[str, Any]]:
        """
        Create a new template.
        
        Args:
            name: Template name
            subject: Email subject
            html_content: HTML content
            text_content: Plain text content (auto-generated from HTML if None)
            description: Template description
            
        Returns:
            Created template or None if creation failed
        """
        try:
            # Generate text content from HTML if not provided
            if text_content is None:
                text_content = self._html_to_text(html_content)
                
            # Create the template
            response = self.db.table('saas_notification_templates').insert({
                'name': name,
                'description': description,
                'subject': subject,
                'html_content': html_content,
                'text_content': text_content,
                'version': 1,
                'is_active': True
            }).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Created template: {name}")
                return response.data[0]
            else:
                logger.error(f"Failed to create template: {name}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating template {name}: {str(e)}")
            return None
            
    async def update_template(self, template_id: str, subject: str = None, 
                             html_content: str = None, text_content: str = None, 
                             description: str = None, is_active: bool = None) -> Optional[Dict[str, Any]]:
        """
        Update an existing template.
        
        Args:
            template_id: ID of the template to update
            subject: New subject (if None, keep existing)
            html_content: New HTML content (if None, keep existing)
            text_content: New text content (if None, keep existing)
            description: New description (if None, keep existing)
            is_active: New active status (if None, keep existing)
            
        Returns:
            Updated template or None if update failed
        """
        try:
            # Get the current template
            current_template = self.db.table('saas_notification_templates') \
                .select('*') \
                .eq('id', template_id) \
                .limit(1) \
                .execute().data[0]
                
            # Create a new version with updated fields
            update_data = {
                'name': current_template['name'],
                'version': current_template['version'] + 1,
                'subject': subject if subject is not None else current_template['subject'],
                'html_content': html_content if html_content is not None else current_template['html_content'],
                'text_content': text_content if text_content is not None else current_template['text_content'],
                'description': description if description is not None else current_template['description'],
                'is_active': is_active if is_active is not None else current_template['is_active']
            }
            
            # If HTML was updated but text wasn't, regenerate text
            if html_content is not None and text_content is None:
                update_data['text_content'] = self._html_to_text(html_content)
                
            # Insert new version
            response = self.db.table('saas_notification_templates').insert(update_data).execute()
            
            if response.data and len(response.data) > 0:
                # Deactivate the old version
                self.db.table('saas_notification_templates') \
                    .update({'is_active': False}) \
                    .eq('id', template_id) \
                    .execute()
                    
                logger.info(f"Updated template: {current_template['name']} (new version: {update_data['version']})")
                return response.data[0]
            else:
                logger.error(f"Failed to update template: {current_template['name']}")
                return None
                
        except Exception as e:
            logger.error(f"Error updating template {template_id}: {str(e)}")
            return None
            
    async def map_event_to_template(self, event_type: str, template_id: str) -> bool:
        """
        Map an event type to a template.
        
        Args:
            event_type: Event type
            template_id: Template ID
            
        Returns:
            True if mapping was successful, False otherwise
        """
        try:
            # Check if mapping already exists
            existing = self.db.table('saas_notification_events') \
                .select('id') \
                .eq('event_type', event_type) \
                .limit(1) \
                .execute()
                
            if existing.data and len(existing.data) > 0:
                # Update existing mapping
                response = self.db.table('saas_notification_events') \
                    .update({'template_id': template_id, 'is_active': True}) \
                    .eq('event_type', event_type) \
                    .execute()
            else:
                # Create new mapping
                response = self.db.table('saas_notification_events').insert({
                    'event_type': event_type,
                    'template_id': template_id,
                    'is_active': True
                }).execute()
                
            if response.data and len(response.data) > 0:
                logger.info(f"Mapped event {event_type} to template {template_id}")
                return True
            else:
                logger.error(f"Failed to map event {event_type} to template {template_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error mapping event {event_type} to template {template_id}: {str(e)}")
            return False
            
    def _html_to_text(self, html: str) -> str:
        """
        Convert HTML to plain text.
        
        Args:
            html: HTML content
            
        Returns:
            Plain text version
        """
        # Simple conversion from HTML to text
        text = html.replace('<br>', '\n').replace('</p>', '\n\n').replace('<li>', '\n- ')
        
        # Remove HTML tags
        text = re.sub('<[^<]+?>', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\n\s+\n', '\n\n', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
