import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.append(os.path.abspath('.'))

try:
    # Import the storage service
    from app.services.utils.storage_service import StorageService
    
    # Initialize the service
    logger.info("Initializing StorageService...")
    storage_service = StorageService()
    
    # List buckets to test connection
    logger.info("Testing connection to Supabase Storage...")
    
    # Try to get bucket info
    try:
        # Check if the research-papers bucket exists
        bucket_name = storage_service.RESEARCH_PAPERS_BUCKET
        logger.info(f"Checking if bucket '{bucket_name}' exists...")
        
        # Try to upload a test file
        test_file_path = "test_storage.py"
        logger.info(f"Uploading test file '{test_file_path}' to bucket '{bucket_name}'...")
        
        result = storage_service.upload_file(
            file_path=test_file_path,
            bucket_name=bucket_name,
            destination_path="test_upload.txt"
        )
        
        if result:
            logger.info(f"Successfully uploaded test file. URL: {result}")
            logger.info("Connection to Supabase Storage is working!")
        else:
            logger.error("Failed to upload test file.")
            
    except Exception as bucket_error:
        logger.error(f"Error accessing bucket: {str(bucket_error)}")
        
except Exception as e:
    logger.error(f"Error: {str(e)}")
