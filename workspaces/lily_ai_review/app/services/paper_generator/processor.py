"""
Paper Generator Processor

This module provides functionality to process research paper generation jobs.
It handles the orchestration of the paper generation process, including
research, content generation, and formatting.
"""

import logging
import time
import json
import asyncio
import os
from typing import Dict, Any, Callable, List, Optional

# Import the LLM service
from app.services.llm import llm_service

# Import the research generator
from app.services.research_generator.research_generator import ResearchGenerator

# Import the document formatter
from app.services.document_formatter.document_formatter import DocumentFormatter

# Configure logging
logger = logging.getLogger(__name__)


async def process_research_paper(job: Dict[str, Any], progress_callback: Callable[[float, str], None]) -> Dict[str, Any]:
    """
    Process a research paper generation job.

    Args:
        job: The job data from the queue
        progress_callback: Callback function to report progress

    Returns:
        Result data for the job
    """
    job_id = job.get('job_id')
    logger.info(f"Processing research paper job {job_id}")

    # Extract job parameters
    params = job.get('params', {})
    topic = params.get('topic', 'Unknown Topic')
    custom_title = params.get('custom_title', topic)
    education_level = params.get('education_level', 'undergraduate')
    include_diagrams = params.get('include_diagrams', True)
    include_research = params.get('include_research', True)
    key_points = params.get('key_points', [])
    retry_count = job.get('retry_count', 0)

    # Log job parameters
    logger.info(f"Job parameters: topic={topic}, education_level={education_level}, "
                f"include_diagrams={include_diagrams}, include_research={include_research}, "
                f"retry_count={retry_count}")

    try:
        # Step 1: Research phase (20%)
        progress_callback(5, "Starting research phase...")

        # Generate a research plan using the LLM service
        logger.info(f"Generating research plan for topic: {topic}")
        start_time = time.time()
        research_plan = llm_service.generate_research_plan(topic, key_points)
        logger.info(f"Research plan generated in {time.time() - start_time:.2f} seconds")

        # Log the research areas
        if isinstance(research_plan, dict) and "research_areas" in research_plan:
            research_areas = [area.get("area") for area in research_plan.get("research_areas", [])]
            logger.info(f"Research areas: {', '.join(research_areas)}")

        progress_callback(10, "Gathering information from academic sources...")

        # Use the research generator to gather information if include_research is True
        research_context = None
        if include_research:
            try:
                # Initialize the research generator
                research_generator = ResearchGenerator()

                # Create a research session
                session_id = await research_generator.create_research_session(topic, key_points)

                # Conduct research using the research plan
                logger.info(f"Starting SERP API searches for job {job_id}")
                start_time = time.time()
                research_results = await research_generator.search_sources(research_plan, session_id)
                search_time = time.time() - start_time
                logger.info(f"SERP API searches completed in {search_time:.2f} seconds for job {job_id}")

                # Check if there was an error with SERP API
                if "error" in research_results and "SERP API" in research_results["error"]:
                    # If we've already retried 3 times, mark as error
                    if retry_count >= 3:
                        logger.error(f"SERP API error after 3 retries for job {job_id}: {research_results['error']}")
                        return {
                            "error": f"SERP API error after 3 retries: {research_results['error']}",
                            "retry_count": retry_count,
                            "should_requeue": False
                        }
                    else:
                        # Requeue the job with incremented retry count
                        logger.warning(f"SERP API error for job {job_id}, retry {retry_count + 1}: {research_results['error']}")
                        return {
                            "error": f"SERP API error: {research_results['error']}",
                            "retry_count": retry_count + 1,
                            "should_requeue": True
                        }

                # Log search results summary
                if "all_results" in research_results:
                    for engine, results in research_results["all_results"].items():
                        result_count = len(results) if isinstance(results, list) else 0
                        logger.info(f"Retrieved {result_count} results from {engine} for job {job_id}")

                # Extract academic sources
                academic_sources = await research_generator.serp_api_service.extract_academic_sources(research_results["all_results"])

                # Extract content from sources
                sources_with_content = await research_generator.extract_content(academic_sources, session_id)

                # Extract citations (using Harvard format)
                citations = await research_generator.extract_citations(sources_with_content, session_id)

                # Format the research results for the LLM
                research_context = {
                    "sources": [
                        {
                            "title": source.get("title", ""),
                            "authors": source.get("authors", []),
                            "publication_year": source.get("publication_year", ""),
                            "snippet": source.get("snippet", ""),
                            "content_excerpt": source.get("full_content", "")[:500] + "..." if source.get("full_content") else ""
                        }
                        for source in sources_with_content[:20]  # Limit to top 20 sources
                    ],
                    "citations": citations.get("harvard", [])[:20]  # Use Harvard format and limit to top 20 citations
                }

                logger.info(f"Research completed for job {job_id}: {len(research_context['sources'])} sources gathered")

            except Exception as e:
                logger.error(f"Error during research phase for job {job_id}: {str(e)}")
                # Continue without research context if there's an error
                research_context = None

        progress_callback(20, "Research phase complete")

        # Step 2: Content generation phase (50%)
        progress_callback(25, "Starting content generation...")

        # Generate the paper content using the LLM service
        logger.info(f"Generating paper content for topic: {topic}")

        # Log research context stats if available
        if research_context:
            source_count = len(research_context.get("sources", []))
            citation_count = len(research_context.get("citations", []))
            logger.info(f"Using {source_count} sources and {citation_count} citations for content generation")

            # Log top sources being used (first 3)
            if source_count > 0:
                top_sources = research_context.get("sources", [])[:3]
                for i, source in enumerate(top_sources):
                    logger.info(f"Top source {i+1}: {source.get('title', 'Unknown')} ({source.get('publication_year', 'Unknown')})")

        # Start content generation
        start_time = time.time()

        # Pass research context if available
        if research_context:
            paper_content = llm_service.generate_paper_content(topic, research_plan, education_level, research_context)
        else:
            paper_content = llm_service.generate_paper_content(topic, research_plan, education_level)

        generation_time = time.time() - start_time
        logger.info(f"Paper content generated in {generation_time:.2f} seconds")

        # Log content structure
        if isinstance(paper_content, dict):
            sections = [key for key in paper_content.keys() if key not in ['title', 'abstract']]
            logger.info(f"Generated paper with {len(sections)} sections: {', '.join(sections)}")

        progress_callback(35, "Generating introduction...")
        # In a real implementation, we would process each section separately

        progress_callback(45, "Generating main sections...")
        # In a real implementation, we would process each section separately

        progress_callback(55, "Generating conclusion...")
        # In a real implementation, we would process each section separately

        progress_callback(70, "Content generation complete")

        # Step 3: Formatting phase (20%)
        progress_callback(75, "Starting formatting phase...")
        logger.info(f"Starting document formatting for job {job_id}")
        start_time = time.time()

        # Format the paper content into a document using DocumentFormatter
        formatter = DocumentFormatter()

        # Use the title from the generated content if available
        final_title = paper_content.get('title', custom_title)

        # Get user information from the job
        user_id = job.get('user_id')
        job_id_str = str(job_id)

        progress_callback(85, "Formatting document...")

        # Format the paper into a document
        try:
            # Create a paper object with sections
            paper_obj = {
                "title": final_title,
                "sections": paper_content
            }

            # Format the paper
            file_paths = formatter.format_paper(
                paper=paper_obj,
                author=job.get('user_name', 'Researcher'),
                institution="researchassistant.uk",
                education_level=education_level,
                user_id=user_id,
                paper_id=job_id_str
            )

            logger.info(f"Document formatting completed successfully: {file_paths}")

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
            logger.error(f"Error formatting document: {str(format_error)}")
            # Continue with empty file paths if formatting fails
            file_paths = {
                "docx": None,
                "pdf": None,
                "storage_urls": {}
            }

        formatting_time = time.time() - start_time
        logger.info(f"Document formatting completed in {formatting_time:.2f} seconds")

        progress_callback(90, "Formatting complete")

        # Step 4: Final processing (10%)
        progress_callback(95, "Finalizing document...")
        logger.info(f"Finalizing document for job {job_id}")
        start_time = time.time()

        # Create static directory if it doesn't exist
        os.makedirs("static/generated_papers", exist_ok=True)

        # Complete
        progress_callback(100, "Research paper generation complete")
        logger.info(f"Research paper generation complete for job {job_id}")

        # Prepare the result data
        result_data = {
            "title": final_title,
            "topic": topic,
            "education_level": education_level,
            "file_paths": {
                "docx": file_paths.get('docx'),
                "pdf": file_paths.get('pdf')
            },
            "storage_urls": file_paths.get('storage_urls', {})
        }

        # Add URLs for the download endpoints
        if job_id_str:
            result_data["docx_url"] = f"/my-papers/{job_id_str}/download/docx"
            result_data["pdf_url"] = f"/my-papers/{job_id_str}/download/pdf"

        return result_data

    except Exception as e:
        logger.error(f"Error processing research paper job {job_id}: {str(e)}")

        # Check if it's a SERP API error
        if "SERP API" in str(e):
            # If we've already retried 3 times, mark as error
            if retry_count >= 3:
                logger.error(f"SERP API error after 3 retries for job {job_id}: {str(e)}")
                return {
                    "error": f"SERP API error after 3 retries: {str(e)}",
                    "retry_count": retry_count,
                    "should_requeue": False
                }
            else:
                # Requeue the job with incremented retry count
                logger.warning(f"SERP API error for job {job_id}, retry {retry_count + 1}: {str(e)}")
                return {
                    "error": f"SERP API error: {str(e)}",
                    "retry_count": retry_count + 1,
                    "should_requeue": True
                }

        # For other errors, just raise
        raise
