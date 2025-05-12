"""
Cloudmersive Document Conversion Utilities

This module provides utilities for converting documents using the Cloudmersive API.
"""
import os
import logging
import tempfile
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

def docx_to_pdf(docx_path: str, output_path: Optional[str] = None) -> Optional[str]:
    """
    Convert a DOCX file to PDF using Cloudmersive API.
    
    Args:
        docx_path: Path to the DOCX file
        output_path: Path to save the PDF file (optional)
        
    Returns:
        Path to the generated PDF file or None if conversion fails
    """
    logger.info(f"Converting DOCX to PDF: {docx_path}")
    
    try:
        # Import required libraries
        import requests
        
        # Load environment variables from .env file
        env_file = '/home/admin/projects/lily_ai/.env'
        load_dotenv(env_file)
        
        # Get API key from environment
        api_key = os.environ.get("CLOUDMERSIVE_API_KEY")
        if not api_key:
            logger.error(f"Cloudmersive API key not found in {env_file}")
            return None
        
        logger.info(f"Using Cloudmersive API key: {'*' * 8}")
        
        # If no output path is provided, create one based on the input path
        if output_path is None:
            output_dir = os.path.dirname(docx_path)
            base_name = os.path.splitext(os.path.basename(docx_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        # API endpoint
        url = "https://api.cloudmersive.com/convert/docx/to/pdf"
        
        # Request headers
        headers = {
            "Apikey": api_key
        }
        
        # Make API request
        with open(docx_path, 'rb') as file:
            files = {
                'inputFile': (os.path.basename(docx_path), file, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')
            }
            response = requests.post(url, headers=headers, files=files)
        
        # Check if request was successful
        if response.status_code == 200:
            # Save the PDF
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"Successfully converted DOCX to PDF: {output_path}")
            return output_path
        else:
            logger.error(f"Cloudmersive API error: {response.status_code}, {response.text}")
            return None
    
    except ImportError:
        logger.error("Required libraries not installed")
        return None
    except Exception as e:
        logger.error(f"Error in docx_to_pdf: {str(e)}")
        return None
