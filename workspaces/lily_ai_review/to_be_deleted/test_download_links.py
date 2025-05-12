import os
import sys
import logging
import requests
import time

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
    
    # Create a test file
    test_file_path = "test_download.txt"
    with open(test_file_path, "w") as f:
        f.write("This is a test file for download link testing.")
    
    # Test user and paper IDs
    test_user_id = "test_user_123"
    test_paper_id = "test_paper_456"
    
    # Upload the test file as a research paper
    logger.info(f"Uploading test file as a research paper for user {test_user_id} and paper {test_paper_id}...")
    
    upload_result = storage_service.upload_research_paper(
        file_path=test_file_path,
        user_id=test_user_id,
        paper_id=test_paper_id,
        file_type="txt"
    )
    
    if upload_result:
        logger.info(f"Successfully uploaded test file. URL: {upload_result}")
        
        # Get a downloadable link for the file
        logger.info("Generating downloadable link...")
        
        download_url = storage_service.get_research_paper_url(
            user_id=test_user_id,
            paper_id=test_paper_id,
            file_type="txt",
            signed=True
        )
        
        if download_url:
            logger.info(f"Successfully generated downloadable link: {download_url}")
            
            # Test the download link
            logger.info("Testing the download link...")
            
            try:
                response = requests.get(download_url)
                
                if response.status_code == 200:
                    logger.info("Download link works! Content retrieved successfully.")
                    logger.info(f"Content: {response.text[:100]}...")
                else:
                    logger.error(f"Failed to download file. Status code: {response.status_code}")
                    logger.error(f"Response: {response.text}")
            except Exception as download_error:
                logger.error(f"Error testing download link: {str(download_error)}")
        else:
            logger.error("Failed to generate downloadable link.")
    else:
        logger.error("Failed to upload test file.")
    
    # Clean up
    try:
        os.remove(test_file_path)
        logger.info(f"Cleaned up local test file: {test_file_path}")
        
        # Delete the file from storage
        delete_result = storage_service.delete_research_paper(
            user_id=test_user_id,
            paper_id=test_paper_id,
            file_type="txt"
        )
        
        if delete_result:
            logger.info("Cleaned up remote test file from storage.")
        else:
            logger.warning("Failed to clean up remote test file from storage.")
    except Exception as cleanup_error:
        logger.error(f"Error during cleanup: {str(cleanup_error)}")
    
except Exception as e:
    logger.error(f"Error: {str(e)}")
