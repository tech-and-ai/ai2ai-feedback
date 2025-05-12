"""
Review Paper Processor

This module provides functionality to process review paper generation jobs.
It handles the orchestration of the review process, including
content extraction, analysis, and review pack generation.
"""

import logging
import time
import os
import asyncio
from typing import Dict, Any, Callable, List, Optional

# Import the LLM service
from app.services.llm import llm_service

# Import the document formatter
from app.services.document_formatter.document_formatter import DocumentFormatter

# Import the review storage service
from app.services.utils.review_storage_service import ReviewStorageService

# Configure logging
logger = logging.getLogger(__name__)


async def process_review_paper(job: Dict[str, Any], progress_callback: Callable[[float, str], None]) -> Dict[str, Any]:
    """
    Process a review paper job.

    Args:
        job: The job data from the queue
        progress_callback: Callback function to report progress

    Returns:
        Result data for the job
    """
    job_id = job.get('job_id')
    logger.info(f"Processing review paper job {job_id}")

    # Extract job parameters
    params = job.get('params', {})
    title = params.get('title', 'Untitled Paper')
    description = params.get('description', '')
    file_type = params.get('file_type', '.pdf')
    file_url = params.get('file_url', '')
    user_id = job.get('user_id')

    # Log job parameters
    logger.info(f"Job parameters: title={title}, file_type={file_type}, user_id={user_id}")

    try:
        # Initialize services
        review_storage_service = ReviewStorageService()
        formatter = DocumentFormatter()

        # Step 1: Download the uploaded paper (10%)
        progress_callback(5, "Downloading uploaded paper...")

        # Create a temporary directory for downloaded files
        os.makedirs("temp", exist_ok=True)
        temp_file_path = f"temp/user_paper_{job_id}{file_type}"

        # Download the paper from Supabase Storage
        paper_content = review_storage_service.download_file(
            bucket_name=review_storage_service.REVIEW_PAPERS_BUCKET,
            file_path=f"uploads/{user_id}/{job_id}{file_type}"
        )

        if not paper_content:
            logger.error(f"Failed to download paper for job {job_id}")
            return {
                "error": "Failed to download paper",
                "should_requeue": False
            }

        # Save the paper content to a temporary file
        with open(temp_file_path, "wb") as f:
            f.write(paper_content)

        logger.info(f"Downloaded paper to {temp_file_path}")
        progress_callback(10, "Paper downloaded successfully")

        # Step 2: Extract content from the paper (20%)
        progress_callback(15, "Extracting content from paper...")

        # TODO: Implement content extraction based on file type
        # For now, we'll simulate content extraction
        await asyncio.sleep(2)  # Simulate processing time

        # In a real implementation, we would use a library like PyPDF2 for PDFs,
        # python-docx for DOCX files, etc.

        # Simulate extracted content
        extracted_content = {
            "title": title,
            "sections": {
                "introduction": "This is the introduction section of the paper.",
                "methodology": "This is the methodology section of the paper.",
                "results": "This is the results section of the paper.",
                "discussion": "This is the discussion section of the paper.",
                "conclusion": "This is the conclusion section of the paper."
            }
        }

        logger.info(f"Extracted content from paper for job {job_id}")
        progress_callback(30, "Content extracted successfully")

        # Step 3: Analyze the paper content (30%)
        progress_callback(35, "Analyzing paper content...")

        # Use the LLM service to analyze the paper
        analysis_start_time = time.time()

        # In a real implementation, we would pass the extracted content to the LLM
        paper_analysis = llm_service.analyze_paper_content(extracted_content)

        analysis_time = time.time() - analysis_start_time
        logger.info(f"Paper analysis completed in {analysis_time:.2f} seconds")

        # Log analysis structure
        if isinstance(paper_analysis, dict):
            analysis_sections = paper_analysis.keys()
            logger.info(f"Generated analysis with sections: {', '.join(analysis_sections)}")

        progress_callback(65, "Paper analysis complete")

        # Step 4: Generate review comments (20%)
        progress_callback(70, "Generating review comments...")

        # Use the LLM service to generate review comments
        comments_start_time = time.time()

        review_comments = llm_service.generate_review_comments(extracted_content, paper_analysis)

        comments_time = time.time() - comments_start_time
        logger.info(f"Review comments generated in {comments_time:.2f} seconds")

        progress_callback(85, "Review comments generated")

        # Step 5: Format and save the review pack (20%)
        progress_callback(90, "Formatting review pack...")

        # Create a review pack object
        review_pack = {
            "title": f"Review of: {title}",
            "sections": {
                "summary": paper_analysis.get("summary", ""),
                "strengths": paper_analysis.get("strengths", ""),
                "weaknesses": paper_analysis.get("weaknesses", ""),
                "detailed_comments": review_comments,
                "recommendations": paper_analysis.get("recommendations", "")
            }
        }

        # Format the review pack into a document
        try:
            # Format the review pack
            file_paths = formatter.format_paper(
                paper=review_pack,
                author="Research Assistant",
                institution="researchassistant.uk",
                education_level="professional",
                user_id=user_id,
                paper_id=job_id
            )

            logger.info(f"Review pack formatting completed successfully: {file_paths}")

            # Log the file paths
            docx_path = file_paths.get('docx')
            pdf_path = file_paths.get('pdf')
            storage_urls = file_paths.get('storage_urls', {})

            if docx_path:
                logger.info(f"DOCX file saved to: {docx_path}")
            if pdf_path:
                logger.info(f"PDF file saved to: {pdf_path}")
            if storage_urls:
                logger.info(f"Storage URLs: {storage_urls}")

        except Exception as format_error:
            logger.error(f"Error formatting review pack: {str(format_error)}")
            # Continue with empty file paths if formatting fails
            file_paths = {
                "docx": None,
                "pdf": None,
                "storage_urls": {}
            }

        # Upload the review pack to Supabase Storage
        if docx_path:
            docx_url = review_storage_service.upload_review_pack(
                file_path=docx_path,
                user_id=user_id,
                paper_id=job_id,
                file_type="docx"
            )
            if docx_url:
                logger.info(f"Uploaded review pack DOCX to Supabase Storage: {docx_url}")

        if pdf_path:
            pdf_url = review_storage_service.upload_review_pack(
                file_path=pdf_path,
                user_id=user_id,
                paper_id=job_id,
                file_type="pdf"
            )
            if pdf_url:
                logger.info(f"Uploaded review pack PDF to Supabase Storage: {pdf_url}")

        progress_callback(95, "Review pack formatted and saved")

        # Clean up temporary files
        try:
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
        except Exception as cleanup_error:
            logger.warning(f"Error cleaning up temporary file: {str(cleanup_error)}")

        # Complete
        progress_callback(100, "Review pack generation complete")
        logger.info(f"Review pack generation complete for job {job_id}")

        # Prepare the result data
        result_data = {
            "title": title,
            "file_paths": {
                "docx": docx_path,
                "pdf": pdf_path
            },
            "storage_urls": {
                "docx": docx_url if 'docx_url' in locals() else None,
                "pdf": pdf_url if 'pdf_url' in locals() else None
            }
        }

        # Add URLs for the download endpoints
        if job_id:
            result_data["docx_url"] = f"/review/download/{job_id}/docx"
            result_data["pdf_url"] = f"/review/download/{job_id}/pdf"

        return result_data

    except Exception as e:
        logger.error(f"Error processing review paper job {job_id}: {str(e)}")
        raise
