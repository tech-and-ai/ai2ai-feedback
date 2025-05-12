"""
Base Diagram Generator
Provides common functionality for all diagram types
"""

import os
import uuid
import logging
import json
from pathlib import Path

from .utils.cloudmersive_converter import html_to_png

# Set up logging
logger = logging.getLogger(__name__)

class BaseDiagramGenerator:
    """Base class for all diagram generators"""

    def __init__(self):
        """Initialize the base diagram generator.
        
        Each subclass should initialize its own content_generator attribute.
        """
        # Set the templates directory
        self.templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
        
        # Set output directory to the location where document formatter looks for images
        self.output_dir = "/home/admin/projects/kdd/app/static/generated_diagrams"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Template paths - common to all generators
        self.d3_template_path = os.path.join(self.templates_dir, "d3_template.html")
        self.mermaid_template_path = os.path.join(self.templates_dir, "mermaid_template.html")

    def generate_diagram(self, template_name, data, prefix="leo_diagram"):
        """
        Generate a diagram using a template and data

        Args:
            template_name (str): Name of the template to use
            data (dict): Data to populate the template with
            prefix (str): Prefix for the output filename

        Returns:
            str: Path to the generated PNG file or None if generation fails
        """
        try:
            # Generate a unique ID for the diagram
            unique_id = str(uuid.uuid4())[:8]

            # Create output paths
            html_path = os.path.join(self.output_dir, f"{prefix}_{unique_id}.html")
            png_path = os.path.join(self.output_dir, f"{prefix}_{unique_id}.png")

            # Get the template
            template_content = self._get_template(template_name)
            if not template_content:
                logger.error(f"Template not found: {template_name}")
                return None

            # Replace placeholders in the template
            html_content = self._populate_template(template_content, data)

            # Save the HTML file
            with open(html_path, 'w') as f:
                f.write(html_content)

            logger.info(f"Diagram HTML saved to {html_path}")

            # Convert HTML to PNG using Cloudmersive
            png_path = html_to_png(html_content, png_path)

            if not png_path:
                logger.error("Cloudmersive conversion failed")
                return None

            return png_path

        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}")
            return None
            
    def _get_template(self, template_name):
        """
        Get a template from the templates directory

        Args:
            template_name (str): Name of the template

        Returns:
            str: Template content or None if not found
        """
        try:
            # Look for templates in multiple possible locations with different naming conventions
            possible_paths = [
                # Direct template name
                os.path.join(self.templates_dir, f'{template_name}.html'),
                # Template with _template suffix
                os.path.join(self.templates_dir, f'{template_name}_template.html'),
                # Fallback path for testing
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'diagram_orchestrator', 'templates', f'{template_name}.html'),
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'diagram_orchestrator', 'templates', f'{template_name}_template.html')
            ]
            
            # Try each path
            for template_path in possible_paths:
                logger.info(f"Looking for template at: {template_path}")
                if os.path.exists(template_path):
                    with open(template_path, 'r') as f:
                        logger.info(f"Found template at: {template_path}")
                        return f.read()
            
            logger.error(f"Template {template_name} not found in any of the possible paths")
            return None
        except Exception as e:
            logger.error(f"Error loading template {template_name}: {str(e)}")
            return None

    def _populate_template(self, template_content, data):
        """
        Replace placeholders in a template with data

        Args:
            template_content (str): Template content
            data (dict): Data to populate the template with

        Returns:
            str: Populated template
        """
        try:
            # Start with the template content
            content = template_content
            
            # Replace each placeholder with its value
            for key, value in data.items():
                if isinstance(value, dict) or isinstance(value, list):
                    # Convert complex data structures to JSON
                    value = json.dumps(value)
                
                # Replace the placeholder with the value
                content = content.replace(f'{{{key}}}', str(value))
            
            return content
        except Exception as e:
            logger.error(f"Error populating template: {str(e)}")
            return None
