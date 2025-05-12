"""
Review Storage Service

This module provides utilities for managing review paper uploads and downloads
using Supabase Storage.
"""
import os
import logging
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client

# Import the base storage service for common functionality
from app.services.utils.storage_service import StorageService

# Set up logging
logger = logging.getLogger(__name__)

class ReviewStorageService(StorageService):
    """
    Service for managing review paper files in Supabase Storage.

    Features:
    - Upload user papers for review
    - Store generated review packs
    - Generate secure download links
    - Track file metadata
    """

    # Default bucket name for review papers
    REVIEW_PAPERS_BUCKET = "review"

    # Allowed file types for paper uploads
    ALLOWED_UPLOAD_TYPES = ['.pdf', '.docx', '.doc', '.txt']
    
    # Maximum file size for uploads (10MB)
    MAX_UPLOAD_SIZE = 10 * 1024 * 1024

    def upload_user_paper(self, file_path: str, user_id: str, paper_id: str) -> Optional[str]:
        """
        Upload a user's paper for review to Supabase Storage.

        Args:
            file_path: Path to the file to upload
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper

        Returns:
            URL of the uploaded file or None if upload fails
        """
        # Validate file type
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in self.ALLOWED_UPLOAD_TYPES:
            logger.error(f"Invalid file type for review paper upload: {file_ext}")
            return None
            
        # Validate file size
        if os.path.getsize(file_path) > self.MAX_UPLOAD_SIZE:
            logger.error(f"File size exceeds maximum allowed size for review paper upload")
            return None

        # Construct the destination path
        destination_path = f"uploads/{user_id}/{paper_id}{file_ext}"

        # Upload the file to the review papers bucket
        return self.upload_file(file_path, self.REVIEW_PAPERS_BUCKET, destination_path)

    def upload_review_pack(self, file_path: str, user_id: str, paper_id: str, file_type: str = "pdf") -> Optional[str]:
        """
        Upload a generated review pack to Supabase Storage.

        Args:
            file_path: Path to the file to upload
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_type: Type of file (pdf or docx)

        Returns:
            URL of the uploaded file or None if upload fails
        """
        # Construct the destination path
        destination_path = f"reviews/{user_id}/{paper_id}.{file_type}"

        # Upload the file to the review papers bucket
        return self.upload_file(file_path, self.REVIEW_PAPERS_BUCKET, destination_path)

    def get_user_paper_url(self, user_id: str, paper_id: str, file_ext: str, signed: bool = True) -> Optional[str]:
        """
        Get a URL for a user's uploaded paper in Supabase Storage.

        Args:
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_ext: File extension including the dot (e.g., '.pdf')
            signed: Whether to generate a signed URL (for private files)

        Returns:
            URL of the file or None if generation fails
        """
        # Construct the file path
        file_path = f"uploads/{user_id}/{paper_id}{file_ext}"

        # Get the file URL
        return self.get_file_url(self.REVIEW_PAPERS_BUCKET, file_path, signed)

    def get_review_pack_url(self, user_id: str, paper_id: str, file_type: str = "pdf", signed: bool = True) -> Optional[str]:
        """
        Get a URL for a review pack in Supabase Storage.

        Args:
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_type: Type of file (pdf or docx)
            signed: Whether to generate a signed URL (for private files)

        Returns:
            URL of the file or None if generation fails
        """
        # Construct the file path
        file_path = f"reviews/{user_id}/{paper_id}.{file_type}"

        # Get the file URL
        return self.get_file_url(self.REVIEW_PAPERS_BUCKET, file_path, signed)

    def delete_user_paper(self, user_id: str, paper_id: str, file_ext: str) -> bool:
        """
        Delete a user's uploaded paper from Supabase Storage.

        Args:
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_ext: File extension including the dot (e.g., '.pdf')

        Returns:
            True if deletion was successful, False otherwise
        """
        # Construct the file path
        file_path = f"uploads/{user_id}/{paper_id}{file_ext}"

        # Delete the file
        return self.delete_file(self.REVIEW_PAPERS_BUCKET, file_path)

    def delete_review_pack(self, user_id: str, paper_id: str, file_type: str = "pdf") -> bool:
        """
        Delete a review pack from Supabase Storage.

        Args:
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_type: Type of file (pdf or docx)

        Returns:
            True if deletion was successful, False otherwise
        """
        # Construct the file path
        file_path = f"reviews/{user_id}/{paper_id}.{file_type}"

        # Delete the file
        return self.delete_file(self.REVIEW_PAPERS_BUCKET, file_path)

    def list_user_papers(self, user_id: str) -> List[Dict[str, Any]]:
        """
        List all papers uploaded by a user.

        Args:
            user_id: ID of the user

        Returns:
            List of file metadata dictionaries
        """
        try:
            # Construct the path prefix
            path_prefix = f"uploads/{user_id}/"
            
            # List files with the prefix
            response = self.supabase.storage.from_(self.REVIEW_PAPERS_BUCKET).list(path_prefix)
            
            if response:
                return response
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error listing user papers: {str(e)}")
            return []
