"""
Cloudmersive API Service

This module provides utilities for using the Cloudmersive API for document conversion.
"""
import os
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class CloudmersiveService:
    """
    Service for using Cloudmersive API for document conversion.
    """
    
    def __init__(self):
        """
        Initialize the Cloudmersive service.
        """
        self.api_key = os.getenv("CLOUDMERSIVE_API_KEY", "")
        if not self.api_key:
            logger.warning("Cloudmersive API key not found in environment variables")
    
    def convert_docx_to_pdf(self, docx_path: str, pdf_path: str) -> bool:
        """
        Convert a DOCX file to PDF using Cloudmersive API.
        
        Args:
            docx_path: Path to the DOCX file
            pdf_path: Path to save the PDF file
            
        Returns:
            True if conversion was successful, False otherwise
        """
        if not self.api_key:
            logger.error("Cloudmersive API key not available")
            return False
        
        try:
            # Check if the DOCX file exists
            if not os.path.exists(docx_path):
                logger.error(f"DOCX file not found: {docx_path}")
                return False
            
            # API endpoint
            url = "https://api.cloudmersive.com/convert/docx/to/pdf"
            
            # Headers with API key
            headers = {
                "Apikey": self.api_key
            }
            
            # Open the DOCX file
            with open(docx_path, "rb") as docx_file:
                # Make the API request
                logger.info(f"Sending DOCX file to Cloudmersive API for conversion: {docx_path}")
                response = requests.post(url, headers=headers, files={"inputFile": docx_file})
                
                # Check if the request was successful
                if response.status_code == 200:
                    # Save the PDF file
                    with open(pdf_path, "wb") as pdf_file:
                        pdf_file.write(response.content)
                    
                    logger.info(f"Successfully converted DOCX to PDF using Cloudmersive API: {pdf_path}")
                    return True
                else:
                    logger.error(f"Cloudmersive API request failed with status code {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error converting DOCX to PDF using Cloudmersive API: {str(e)}")
            return False
