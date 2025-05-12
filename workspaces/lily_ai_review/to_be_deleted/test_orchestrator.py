"""
Test script for the Research Pack Orchestrator.

This script tests the DOCX to PDF conversion and S3 upload functionality.
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the orchestrator
from research_pack.ResearchPackOrchestrator import ResearchPackOrchestrator

# Import the document formatter
from app.services.document_formatter.document_formatter import DocumentFormatter

# Import the storage service
from app.services.utils.storage_service import StorageService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_orchestrator():
    """Test the Research Pack Orchestrator."""
    logger.info("Testing Research Pack Orchestrator")
    
    # Create a document formatter
    document_formatter = DocumentFormatter()
    
    # Create a storage service
    try:
        storage_service = StorageService()
    except Exception as e:
        logger.error(f"Error creating storage service: {str(e)}")
        storage_service = None
    
    # Create an orchestrator
    orchestrator = ResearchPackOrchestrator(
        document_formatter=document_formatter,
        storage_service=storage_service
    )
    
    # Create a sample research pack
    sample_content = {
        "title": "Sample Research Pack",
        "sections": {
            "introduction": {
                "about_this_pack": "This is a sample research pack for testing.",
                "how_to_use": "Use this pack to test the orchestrator."
            },
            "topic_analysis": {
                "key_concepts": "These are the key concepts for the sample topic."
            }
        }
    }
    
    # Test document formatting
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(output_dir, exist_ok=True)
    document_path = os.path.join(output_dir, f"test_research_pack_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx")
    
    # Format and save the document
    document = document_formatter.format_research_pack(sample_content)
    document_formatter.save_document(document_path)
    logger.info(f"Document saved to {document_path}")
    
    # Test DOCX to PDF conversion
    pdf_path = await orchestrator._convert_to_pdf(document_path)
    if pdf_path:
        logger.info(f"DOCX converted to PDF: {pdf_path}")
    else:
        logger.error("Failed to convert DOCX to PDF")
    
    # Test file upload to Supabase S3
    if storage_service and pdf_path:
        docx_url = await orchestrator._upload_to_storage(
            document_path,
            "research-packs",
            f"test/test_research_pack_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
        )
        
        pdf_url = await orchestrator._upload_to_storage(
            pdf_path,
            "research-packs",
            f"test/test_research_pack_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        )
        
        if docx_url:
            logger.info(f"DOCX uploaded to Supabase S3: {docx_url}")
        else:
            logger.error("Failed to upload DOCX to Supabase S3")
        
        if pdf_url:
            logger.info(f"PDF uploaded to Supabase S3: {pdf_url}")
        else:
            logger.error("Failed to upload PDF to Supabase S3")
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(test_orchestrator())
