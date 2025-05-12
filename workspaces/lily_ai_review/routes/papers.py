"""
Papers routes for Lily AI.

This module provides routes for managing and downloading research papers.
"""
import os
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from auth.dependencies import get_current_user
from app.services.utils.storage_service import StorageService
from app.services.queue_engine.queue_manager import QueueManager

# Set up logging
logger = logging.getLogger(__name__)

# Initialize router
router = APIRouter(tags=["papers"])

# Initialize services
storage_service = StorageService()
queue_manager = QueueManager()

@router.get("/my-papers/{paper_id}/download/{file_type}")
async def download_paper(
    request: Request,
    paper_id: str,
    file_type: str,
    user=Depends(get_current_user)
):
    """
    Download a paper in the specified format.
    
    Args:
        request: The incoming request
        paper_id: The ID of the paper to download
        file_type: The file type to download (pdf or docx)
        user: The current authenticated user
        
    Returns:
        FileResponse with the paper file or a redirect to the file URL
    """
    # Validate file type
    if file_type not in ["pdf", "docx"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type: {file_type}. Must be 'pdf' or 'docx'."
        )
    
    try:
        # Get the job details to verify ownership
        job = queue_manager.get_job_status(paper_id)
        
        if not job:
            logger.error(f"Paper {paper_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paper not found"
            )
        
        # Verify the paper belongs to the user
        if job.get("user_id") != user.get("id"):
            logger.error(f"User {user.get('id')} attempted to download paper {paper_id} belonging to user {job.get('user_id')}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to download this paper"
            )
        
        # Check if the paper is completed
        if job.get("status") != "completed":
            logger.error(f"Paper {paper_id} is not completed (status: {job.get('status')})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Paper is not ready for download"
            )
        
        # Get the file path from the job results
        results = job.get("results", {})
        file_paths = results.get("file_paths", {})
        
        # Check if we have a file path for the requested type
        if file_type not in file_paths or not file_paths[file_type]:
            logger.error(f"No {file_type} file path found for paper {paper_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No {file_type} file available for this paper"
            )
        
        file_path = file_paths[file_type]
        logger.info(f"File path for paper {paper_id} ({file_type}): {file_path}")
        
        # Check if the file exists locally
        if os.path.exists(file_path):
            # Serve the file directly
            logger.info(f"Serving local file: {file_path}")
            return FileResponse(
                path=file_path,
                filename=f"research_paper_{paper_id}.{file_type}",
                media_type=f"application/{'pdf' if file_type == 'pdf' else 'vnd.openxmlformats-officedocument.wordprocessingml.document'}"
            )
        
        # If not local, try to get from Supabase Storage
        logger.info(f"File not found locally, trying Supabase Storage")
        
        # Try to get a signed URL from Supabase Storage
        file_url = storage_service.get_research_paper_url(
            user_id=user.get("id"),
            paper_id=paper_id,
            file_type=file_type
        )
        
        if file_url:
            logger.info(f"Redirecting to Supabase Storage URL: {file_url}")
            return RedirectResponse(url=file_url)
        
        # If we get here, the file is not available
        logger.error(f"File not found in Supabase Storage for paper {paper_id} ({file_type})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found"
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log and return a generic error
        logger.error(f"Error downloading paper {paper_id} ({file_type}): {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while downloading the paper"
        )
