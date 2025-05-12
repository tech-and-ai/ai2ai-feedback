"""
Supabase Storage Service

This module provides utilities for uploading, downloading, and managing files in Supabase Storage.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from supabase import create_client
from dotenv import load_dotenv

# Set up logging
logger = logging.getLogger(__name__)

class StorageService:
    """
    Service for managing files in Supabase Storage.

    Features:
    - Upload files to Supabase Storage
    - Download files from Supabase Storage
    - Generate signed URLs for secure file access
    - Delete files from Supabase Storage
    """

    # Default bucket names
    RESEARCH_PAPERS_BUCKET = "research-papers"
    FREE_PACKS_BUCKET = "free-packs"

    # File size limit (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """
        Initialize the storage service.

        Args:
            supabase_url: URL for the Supabase API (optional, will use env var if not provided)
            supabase_key: API key for Supabase (optional, will use env var if not provided)
        """
        # Load environment variables
        env_file = '/home/admin/projects/lily_ai/.env'
        load_dotenv(env_file)

        # Use provided values or get from environment
        self.supabase_url = supabase_url or os.environ.get("SUPABASE_PROJECT_URL")
        self.supabase_key = supabase_key or os.environ.get("SUPABASE_API_KEY")

        if not self.supabase_url or not self.supabase_key:
            logger.error(f"Supabase URL or key not found in {env_file}")
            logger.error(f"Looking for SUPABASE_PROJECT_URL and SUPABASE_API_KEY environment variables")
            raise ValueError("Supabase URL and key are required")

        # Initialize Supabase client
        self.supabase = create_client(self.supabase_url, self.supabase_key)
        logger.info("Storage service initialized")

    def upload_file(self, file_path: str, bucket_name: str, destination_path: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to Supabase Storage.

        Args:
            file_path: Path to the file to upload
            bucket_name: Name of the bucket to upload to
            destination_path: Path within the bucket to upload to (optional)

        Returns:
            URL of the uploaded file or None if upload fails
        """
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                logger.error(f"File not found: {file_path}")
                return None

            # Check file size
            file_size = os.path.getsize(file_path)
            if file_size > self.MAX_FILE_SIZE:
                logger.error(f"File size ({file_size} bytes) exceeds maximum allowed size ({self.MAX_FILE_SIZE} bytes)")
                return None

            # If no destination path is provided, use the file name
            if destination_path is None:
                destination_path = os.path.basename(file_path)

            # Read the file
            with open(file_path, 'rb') as f:
                file_contents = f.read()

            # Verify bucket exists
            try:
                # Check if bucket exists by attempting to get its details
                self.supabase.storage.get_bucket(bucket_name)
            except Exception as bucket_error:
                logger.error(f"Error accessing bucket {bucket_name}: {str(bucket_error)}")
                return None

            # Upload the file
            response = self.supabase.storage.from_(bucket_name).upload(
                destination_path,
                file_contents,
                {"content-type": self._get_content_type(file_path)}
            )

            # Get a signed URL instead of public URL for better security
            signed_url_response = self.supabase.storage.from_(bucket_name).create_signed_url(
                path=destination_path,
                expires_in=3600  # 1 hour expiration
            )

            if signed_url_response and "signedURL" in signed_url_response:
                file_url = signed_url_response["signedURL"]
                logger.info(f"Successfully uploaded file to {bucket_name}/{destination_path} with signed URL")
            else:
                # Fallback to public URL only if bucket is public
                file_url = self.supabase.storage.from_(bucket_name).get_public_url(destination_path)
                logger.info(f"Successfully uploaded file to {bucket_name}/{destination_path} with public URL")

            return file_url

        except Exception as e:
            logger.error(f"Error uploading file to Supabase Storage: {str(e)}")
            return None

    def download_file(self, bucket_name: str, file_path: str) -> Optional[bytes]:
        """
        Download a file from Supabase Storage.

        Args:
            bucket_name: Name of the bucket to download from
            file_path: Path within the bucket to download from

        Returns:
            File contents as bytes or None if download fails
        """
        try:
            # Download the file
            file_data = self.supabase.storage.from_(bucket_name).download(file_path)

            logger.info(f"Successfully downloaded file from {bucket_name}/{file_path}")
            return file_data

        except Exception as e:
            logger.error(f"Error downloading file from Supabase Storage: {str(e)}")
            return None

    def get_file_url(self, bucket_name: str, file_path: str, signed: bool = True, expires_in: int = 900) -> Optional[str]:
        """
        Get a URL for a file in Supabase Storage.

        Args:
            bucket_name: Name of the bucket
            file_path: Path within the bucket
            signed: Whether to generate a signed URL (for private files)
            expires_in: Expiration time in seconds for signed URLs (default: 15 minutes)

        Returns:
            URL of the file or None if generation fails
        """
        try:
            if signed:
                # Generate a signed URL with expiration
                response = self.supabase.storage.from_(bucket_name).create_signed_url(
                    path=file_path,
                    expires_in=expires_in
                )

                if response and "signedURL" in response:
                    logger.info(f"Generated signed URL for {bucket_name}/{file_path}")
                    return response["signedURL"]
                else:
                    logger.warning(f"Failed to generate signed URL for {bucket_name}/{file_path}")
                    # Don't fall back to public URL for security reasons
                    return None
            else:
                # Get public URL
                return self.supabase.storage.from_(bucket_name).get_public_url(file_path)

        except Exception as e:
            logger.error(f"Error getting file URL from Supabase Storage: {str(e)}")
            return None

    def delete_file(self, bucket_name: str, file_path: str) -> bool:
        """
        Delete a file from Supabase Storage.

        Args:
            bucket_name: Name of the bucket
            file_path: Path within the bucket

        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Delete the file
            self.supabase.storage.from_(bucket_name).remove([file_path])

            logger.info(f"Successfully deleted file from {bucket_name}/{file_path}")
            return True

        except Exception as e:
            logger.error(f"Error deleting file from Supabase Storage: {str(e)}")
            return False

    def upload_research_paper(self, file_path: str, user_id: str, paper_id: str, file_type: str = "docx") -> Optional[str]:
        """
        Upload a research paper to Supabase Storage.

        Args:
            file_path: Path to the file to upload
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_type: Type of file (docx or pdf)

        Returns:
            URL of the uploaded file or None if upload fails
        """
        # Construct the destination path
        destination_path = f"{user_id}/{paper_id}.{file_type}"

        # Upload the file to the research papers bucket
        return self.upload_file(file_path, self.RESEARCH_PAPERS_BUCKET, destination_path)

    def get_research_paper_url(self, user_id: str, paper_id: str, file_type: str = "docx", signed: bool = True) -> Optional[str]:
        """
        Get a URL for a research paper in Supabase Storage.

        Args:
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_type: Type of file (docx or pdf)
            signed: Whether to generate a signed URL (for private files)

        Returns:
            URL of the file or None if generation fails
        """
        # Construct the file path
        file_path = f"{user_id}/{paper_id}.{file_type}"

        # Get the file URL
        return self.get_file_url(self.RESEARCH_PAPERS_BUCKET, file_path, signed)

    def download_research_paper(self, user_id: str, paper_id: str, file_type: str = "docx") -> Optional[bytes]:
        """
        Download a research paper from Supabase Storage.

        Args:
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_type: Type of file (docx or pdf)

        Returns:
            File contents as bytes or None if download fails
        """
        # Construct the file path
        file_path = f"{user_id}/{paper_id}.{file_type}"

        # Download the file
        return self.download_file(self.RESEARCH_PAPERS_BUCKET, file_path)

    def delete_research_paper(self, user_id: str, paper_id: str, file_type: str = "docx") -> bool:
        """
        Delete a research paper from Supabase Storage.

        Args:
            user_id: ID of the user who owns the paper
            paper_id: ID of the paper
            file_type: Type of file (docx or pdf)

        Returns:
            True if deletion was successful, False otherwise
        """
        # Construct the file path
        file_path = f"{user_id}/{paper_id}.{file_type}"

        # Delete the file
        return self.delete_file(self.RESEARCH_PAPERS_BUCKET, file_path)

    def get_sample_papers(self) -> List[Dict[str, Any]]:
        """
        Get a list of sample papers from the free-packs bucket.

        Returns:
            List of sample papers with their URLs and metadata
        """
        try:
            # List files in the free-packs bucket
            response = self.supabase.storage.from_(self.FREE_PACKS_BUCKET).list()

            # Filter for PDF and DOCX files
            sample_papers = []

            for file in response:
                file_name = file.get('name', '')
                file_path = file.get('name', '')

                # Skip if not a PDF or DOCX file
                if not (file_name.endswith('.pdf') or file_name.endswith('.docx')):
                    continue

                # Get file extension
                file_ext = os.path.splitext(file_name)[1].lower()

                # Get file URL
                file_url = self.get_file_url(self.FREE_PACKS_BUCKET, file_path, signed=True, expires_in=86400)  # 24 hours

                # Extract paper title from filename (remove extension and replace underscores with spaces)
                paper_title = os.path.splitext(file_name)[0].replace('_', ' ').title()

                # Add to sample papers list
                sample_papers.append({
                    'title': paper_title,
                    'url': file_url,
                    'file_type': file_ext[1:],  # Remove the dot
                    'file_name': file_name
                })

            logger.info(f"Found {len(sample_papers)} sample papers in the free-packs bucket")
            return sample_papers

        except Exception as e:
            logger.error(f"Error getting sample papers: {str(e)}")
            return []

    def _get_content_type(self, file_path: str) -> str:
        """
        Get the content type for a file based on its extension.

        Args:
            file_path: Path to the file

        Returns:
            Content type string
        """
        extension = os.path.splitext(file_path)[1].lower()

        content_types = {
            '.pdf': 'application/pdf',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.doc': 'application/msword',
            '.txt': 'text/plain',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.html': 'text/html',
            '.json': 'application/json'
        }

        return content_types.get(extension, 'application/octet-stream')
