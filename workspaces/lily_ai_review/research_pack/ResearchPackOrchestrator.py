"""
Research Pack Orchestrator

This module orchestrates the generation of research packs by coordinating
the various components involved in the process. It serves as the central
coordinator for the entire research pack generation workflow.
"""

import os
import logging
import asyncio
import json
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import Supabase client
try:
    from app.utils.supabase_client import get_supabase_client
    supabase_client = get_supabase_client()
except ImportError:
    supabase_client = None
    logging.warning("Supabase client import failed. Some functionality may be limited.")


# Custom exception types for better error classification
class ResearchPackError(Exception):
    """Base exception for all research pack errors."""
    ERROR_CODE = "RP000"

    def __init__(self, message, error_code=None):
        self.error_code = error_code or self.ERROR_CODE
        self.message = message
        super().__init__(f"[{self.error_code}] {message}")


class ConfigurationError(ResearchPackError):
    """Exception raised for configuration errors."""
    ERROR_CODE = "RP001"


class ContentGenerationError(ResearchPackError):
    """Exception raised for content generation errors."""
    ERROR_CODE = "RP002"


class ContentValidationError(ResearchPackError):
    """Exception raised for content validation errors."""
    ERROR_CODE = "RP003"


class LilyCalloutError(ResearchPackError):
    """Exception raised for Lily callout errors."""
    ERROR_CODE = "RP004"


class DocumentFormattingError(ResearchPackError):
    """Exception raised for document formatting errors."""
    ERROR_CODE = "RP005"

# Import utilities
from app.services.utils.cloudmersive_converter import docx_to_pdf
from app.services.utils.storage_service import StorageService

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ResearchPackOrchestrator")

class ResearchPackOrchestrator:
    """
    Orchestrates the generation of research packs by coordinating all components.

    The orchestrator follows these steps:
    1. Generate diagrams using the Diagram Orchestrator
    2. Generate content using the Content Generator
    3. Process content through the Lily Callout Engine
    4. Format the document using the Document Formatter
    5. Convert DOCX to PDF using Cloudmersive
    6. Upload both files to Supabase S3
    7. Return the completed research pack with file URLs
    """

    def __init__(
            self,
            diagram_orchestrator=None,
            content_generator=None,
            lily_callout_engine=None,
            document_formatter=None,
            storage_service=None,
            openrouter_key: Optional[str] = None,
            serp_key: Optional[str] = None,
            supabase_url: Optional[str] = None,
            supabase_key: Optional[str] = None
        ):
        """
        Initialize the Research Pack Orchestrator.

        Args:
            diagram_orchestrator: The diagram orchestrator component
            content_generator: The content generator component
            lily_callout_engine: The Lily Callout Engine component
            document_formatter: The document formatter component
            storage_service: The storage service for uploading files
            openrouter_key: API key for OpenRouter
            serp_key: API key for SERP API
            supabase_url: URL for Supabase
            supabase_key: API key for Supabase
        """
        self.diagram_orchestrator = diagram_orchestrator
        self.content_generator = content_generator
        self.lily_callout_engine = lily_callout_engine
        self.document_formatter = document_formatter
        self.openrouter_key = openrouter_key
        self.serp_key = serp_key

        # Initialize storage service if not provided
        if storage_service:
            self.storage_service = storage_service
        else:
            try:
                self.storage_service = StorageService(supabase_url, supabase_key)
                logger.info("Storage service initialized")
            except Exception as e:
                logger.error(f"Error initializing storage service: {str(e)}")
                self.storage_service = None

        # Log initialization
        logger.info("Research Pack Orchestrator initialized")

        # Log key information without exposing the full keys
        if openrouter_key:
            key_prefix = openrouter_key[:4] if len(openrouter_key) > 4 else "***"
            logger.info(f"Using OpenRouter API key (prefix: {key_prefix}...)")
        else:
            logger.warning("No OpenRouter API key provided")

        if serp_key:
            key_prefix = serp_key[:4] if len(serp_key) > 4 else "***"
            logger.info(f"Using SERP API key (prefix: {key_prefix}...)")
        else:
            logger.warning("No SERP API key provided")

    async def generate_research_pack(
            self,
            topic: str,
            question: str,
            user_id: str,
            education_level: str = "university",
            include_diagrams: bool = True,
            premium: bool = False,
            personalized_questions: List[str] = None
        ) -> Dict[str, Any]:
        """
        Generate a research pack for the given topic and question.

        Args:
            topic: The research topic
            question: The research question
            user_id: The ID of the user requesting the research pack
            education_level: The education level (high-school, college, university)
            include_diagrams: Whether to include diagrams in the research pack
            premium: Whether this is a premium request
            personalized_questions: List of personalized questions from the user

        Returns:
            A dictionary containing the research pack details
        """
        logger.info(f"Generating research pack for topic: {topic}, question: {question}")

        # Track timing for performance analysis
        start_time = datetime.now()

        # Create a dictionary to store all components of the research pack
        research_pack = {
            "topic": topic,
            "question": question,
            "user_id": user_id,
            "education_level": education_level,
            "premium": premium,
            "personalized_questions": personalized_questions or [],
            "diagrams": [],
            "content": {},
            "document_path": None,
            "pdf_path": None,
            "docx_url": None,
            "pdf_url": None,
            "created_at": start_time.isoformat()
        }

        try:
            # STEP 1: Generate diagrams (first priority)
            if include_diagrams and self.diagram_orchestrator:
                logger.info("Starting diagram generation")
                research_pack["diagrams"] = await self._generate_diagrams(topic, question)
                logger.info(f"Generated {len(research_pack['diagrams'])} diagrams")

            # STEP 2: Generate content
            if self.content_generator:
                logger.info("Starting content generation")
                research_pack["content"] = await self._generate_content(topic, question, education_level, premium, user_id)
                logger.info("Content generation completed")

            # STEP 3: Generate answers to personalized questions
            if research_pack["personalized_questions"] and research_pack["content"]:
                logger.info("Generating answers to personalized questions")
                await self._generate_personalized_answers(
                    research_pack=research_pack,
                    topic=topic,
                    education_level=education_level
                )
                logger.info("Personalized answers generation completed")

            # STEP 4: Process content through Lily Callout Engine
            if self.lily_callout_engine and research_pack["content"]:
                logger.info("Processing content through Lily Callout Engine")
                research_pack["content"] = await self._process_with_lily_callout_engine(
                    content=research_pack["content"],
                    topic=topic,
                    education_level=education_level
                )
                logger.info("Lily Callout Engine processing completed")

            # STEP 4: Format the document
            if self.document_formatter and research_pack["content"]:
                logger.info("Formatting document")
                research_pack["document_path"] = await self._format_document(
                    research_pack["content"],
                    topic,
                    user_id,
                    research_pack["diagrams"],
                    question
                )
                logger.info(f"Document formatted and saved to {research_pack['document_path']}")

                # STEP 5: Convert DOCX to PDF
                if research_pack["document_path"]:
                    logger.info("Converting DOCX to PDF")
                    research_pack["pdf_path"] = await self._convert_to_pdf(research_pack["document_path"])
                    if research_pack["pdf_path"]:
                        logger.info(f"DOCX converted to PDF: {research_pack['pdf_path']}")
                    else:
                        logger.error("Failed to convert DOCX to PDF")

                # STEP 6: Upload files to Supabase S3
                if self.storage_service:
                    logger.info("Uploading files to Supabase S3")

                    # Get paper ID if available
                    paper_id = research_pack.get("content", {}).get("paper_id", None)

                    # Upload DOCX
                    if research_pack["document_path"]:
                        research_pack["docx_url"] = await self._upload_to_storage(
                            research_pack["document_path"],
                            "research-packs",
                            f"{user_id}/{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx",
                            paper_id
                        )

                    # Upload PDF
                    if research_pack["pdf_path"]:
                        research_pack["pdf_url"] = await self._upload_to_storage(
                            research_pack["pdf_path"],
                            "research-packs",
                            f"{user_id}/{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf",
                            paper_id
                        )

                    logger.info("File uploads completed")

            # Calculate and log total generation time
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            research_pack["generation_time"] = duration
            logger.info(f"Research pack generation completed in {duration:.2f} seconds")

            return research_pack

        except Exception as e:
            logger.error(f"Error generating research pack: {str(e)}", exc_info=True)
            raise

    async def _generate_diagrams(self, topic: str, question: str) -> List[Dict[str, Any]]:
        """
        Generate diagrams for the research pack.

        Args:
            topic: The research topic
            question: The research question

        Returns:
            A list of dictionaries containing diagram details
        """
        logger.info(f"Generating diagrams for topic: {topic}")

        # Placeholder for diagram generation
        diagrams = []

        try:
            if self.diagram_orchestrator:
                # Generate mind map
                mind_map = await self.diagram_orchestrator.generate_mind_map(topic)
                if mind_map:
                    diagrams.append({
                        "type": "mind_map",
                        "path": mind_map,
                        "title": f"Mind Map: {topic}"
                    })

                # Generate journey map
                journey_map = await self.diagram_orchestrator.generate_journey_map(topic)
                if journey_map:
                    diagrams.append({
                        "type": "journey_map",
                        "path": journey_map,
                        "title": f"Research Journey Map: {topic}"
                    })

                # Generate question breakdown
                question_breakdown = await self.diagram_orchestrator.generate_question_breakdown(question)
                if question_breakdown:
                    diagrams.append({
                        "type": "question_breakdown",
                        "path": question_breakdown,
                        "title": f"Question Breakdown: {question}"
                    })

                # Generate argument mapping
                argument_mapping = await self.diagram_orchestrator.generate_argument_mapping(topic)
                if argument_mapping:
                    diagrams.append({
                        "type": "argument_mapping",
                        "path": argument_mapping,
                        "title": f"Argument Mapping: {topic}"
                    })

                # Generate comparative analysis
                comparative_analysis = await self.diagram_orchestrator.generate_comparative_analysis(topic)
                if comparative_analysis:
                    diagrams.append({
                        "type": "comparative_analysis",
                        "path": comparative_analysis,
                        "title": f"Comparative Analysis: {topic}"
                    })

                logger.info(f"Generated {len(diagrams)} diagrams")
            else:
                logger.warning("No diagram orchestrator provided, skipping diagram generation")

        except Exception as e:
            logger.error(f"Error generating diagrams: {str(e)}", exc_info=True)
            # Continue with the process even if diagram generation fails

        return diagrams

    async def _get_static_content(self, section_name: str) -> Optional[str]:
        """
        Retrieve static content from the database.

        Args:
            section_name: The name of the section to retrieve

        Returns:
            The static content or None if not found
        """
        try:
            # Import the config service
            from app.services.config import config_service

            # First try using Supabase directly (preferred method)
            try:
                # Check if Supabase client is available
                if supabase_client:
                    logger.info(f"[STATIC_CONTENT] Retrieving static content for section '{section_name}' using Supabase")

                    response = supabase_client.table('saas_static_content').select('content').eq('name', section_name).eq('content_type', 'research_pack_section').eq('is_current_version', True).order('version', desc=True).limit(1).execute()

                    if response.data and len(response.data) > 0:
                        content = response.data[0]['content']
                        logger.info(f"[STATIC_CONTENT] Successfully retrieved static content for section '{section_name}' ({len(content)} chars)")
                        return content
                    else:
                        logger.warning(f"[STATIC_CONTENT] No data found in Supabase for section: {section_name}")
                else:
                    logger.warning("[STATIC_CONTENT] Supabase client not available")
            except Exception as e:
                logger.error(f"[STATIC_CONTENT] Error retrieving from Supabase: {str(e)}")

            # Fallback to database connection if available
            if hasattr(config_service, 'db_connection') and config_service.db_connection:
                try:
                    logger.info(f"[STATIC_CONTENT] Falling back to database connection for section '{section_name}'")

                    query = """
                    SELECT content
                    FROM saas_static_content
                    WHERE name = %s
                    AND content_type = 'research_pack_section'
                    AND is_current_version = true
                    ORDER BY version DESC
                    LIMIT 1
                    """

                    result = config_service.db_connection.execute(query, (section_name,)).fetchone()

                    if result:
                        content = result[0]
                        logger.info(f"[STATIC_CONTENT] Successfully retrieved static content from database for section '{section_name}' ({len(content)} chars)")
                        return content
                    else:
                        logger.warning(f"[STATIC_CONTENT] No data found in database for section: {section_name}")
                except Exception as e:
                    logger.error(f"[STATIC_CONTENT] Error executing database query: {str(e)}")
            else:
                logger.warning("[STATIC_CONTENT] Database connection not available")

            # If we get here, provide default content as a last resort
            logger.warning(f"[STATIC_CONTENT] Using default content for section: {section_name}")

            # Default content for each section
            default_content = {
                "about_lily": "# About Lily AI\n\nLily AI is your academic research assistant, designed to help you with your research papers and assignments. Lily uses advanced AI to generate comprehensive research packs on a wide range of topics.",
                "how_to_use": "# How to Use This Pack\n\nThis research pack is designed to provide you with a comprehensive overview of the topic. Each section covers different aspects of the subject, and you can use this information as a starting point for your own research.",
                "appendices": "# Appendices\n\nThis section contains additional information and resources that may be useful for your research."
            }

            if section_name in default_content:
                logger.info(f"[STATIC_CONTENT] Returning default content for section '{section_name}'")
                return default_content[section_name]
            else:
                logger.error(f"[STATIC_CONTENT] No default content available for section: {section_name}")
                return None

        except Exception as e:
            logger.error(f"[STATIC_CONTENT] Error retrieving static content: {str(e)}")
            return None

    async def _generate_content(self, topic: str, question: str, education_level: str, premium: bool, user_id: str = None) -> Dict[str, Any]:
        """
        Generate content for the research pack.

        Args:
            topic: The research topic
            question: The research question
            education_level: The education level
            premium: Whether this is a premium request
            user_id: The ID of the user requesting the research pack

        Returns:
            A dictionary containing the generated content
        """
        request_id = f"req_{int(datetime.now().timestamp())}"
        logger.info(f"[{request_id}] Generating content for topic: {topic}, question: {question}, education_level: {education_level}, premium: {premium}")

        try:
            # Import the LLM service
            from app.services.llm import llm_service

            # Import the research generator
            from app.services.research_generator.research_generator import ResearchGenerator

            # Step 1: Generate a comprehensive research plan
            logger.info(f"[{request_id}] Generating comprehensive research plan for topic: {topic}")
            # Store the research plan in a variable for future use
            research_plan = llm_service.generate_research_plan(topic, [question])
            logger.info(f"[{request_id}] Research plan generated successfully")

            # Step 1.5: Plan sections in detail to avoid repetition
            logger.info(f"[{request_id}] Planning sections in detail")

            # Import the section planner
            from research_pack.paper_generator.section_planner import SectionPlanner

            # Initialize the section planner
            section_planner = SectionPlanner(openrouter_key=self.openrouter_key)

            # Define the sections to plan
            sections = [
                "introduction",
                "topic_analysis",
                "methodological_approaches",
                "key_arguments",
                "citations_resources",
                "personalized_questions"
            ]

            # Plan the sections with awareness of previous sections to avoid repetition
            tier_name = "premium" if premium else "standard"
            section_plans = await section_planner.plan_paper_sections(topic, sections, tier_name)

            logger.info(f"[{request_id}] Successfully planned {len(section_plans)} sections")

            # Step 2: Conduct research if we have a SERP API key
            research_context = None
            if self.serp_key:
                try:
                    # Initialize the research generator
                    research_generator = ResearchGenerator(
                        openrouter_key=self.openrouter_key,
                        serp_api_key=self.serp_key
                    )

                    # Create a research session (session ID not used directly but needed for the API)
                    session_id = await research_generator.create_research_session(topic, [question])

                    # Conduct research using the research plan we already generated
                    logger.info(f"[SERP_API] Conducting research for topic: {topic}")
                    logger.info(f"[SERP_API] Using SERP API key: {self.serp_key[:5]}...")
                    logger.info(f"[SERP_API] Using OpenRouter key: {self.openrouter_key[:5]}...")

                    # First, let's search for sources using our research plan
                    logger.info(f"[SERP_API] Searching for sources using research plan")
                    logger.info(f"[SERP_API] Research plan: {research_plan[:200]}...")
                    logger.info(f"[SERP_API] Session ID: {session_id}")

                    search_results = await research_generator.search_sources(research_plan, session_id)

                    logger.info(f"[SERP_API] Search results received: {len(str(search_results))} bytes")

                    if "error" in search_results:
                        logger.error(f"[SERP_API] Error during source search: {search_results['error']}")
                        research_context = None
                    else:
                        # Extract content from sources
                        sources = search_results.get("academic_sources", [])
                        logger.info(f"[SERP_API] Found {len(sources)} academic sources, extracting content")

                        # Log the first few sources
                        for i, source in enumerate(sources[:3]):
                            logger.info(f"[SERP_API] Source {i+1}: {source.get('title', 'No title')} - {source.get('url', 'No URL')}")

                        sources_with_content = await research_generator.extract_content(sources, session_id)
                        logger.info(f"[SERP_API] Content extraction complete for {len(sources_with_content)} sources")

                        # Extract citations
                        logger.info(f"Extracting citations from sources")
                        citations = await research_generator.extract_citations(sources_with_content, session_id)

                        # Get the enabled citation style
                        from app.services.config import config_service
                        citation_style = config_service.get_enabled_citation_style()
                        primary_style = citation_style["name"].lower()

                        # Create research context
                        research_context = {
                            "sources": sources_with_content,
                            "citations": citations,
                            "primary_citation_style": primary_style
                        }

                        # Store research context in Supabase
                        try:
                            # Check if Supabase client is available
                            if not supabase_client:
                                logger.warning("Supabase client not available. Skipping research context storage.")
                                logger.info(f"Research completed with {len(sources_with_content)} sources")
                                return research_context

                            # Generate a unique ID for this research context
                            research_context_id = str(uuid.uuid4())

                            # Store in saas_research_context table
                            logger.info(f"[SUPABASE_TRANSACTION] Storing research context in Supabase with ID: {research_context_id}")
                            logger.info(f"[SUPABASE_TRANSACTION] Topic: {topic}, User ID: {user_id}")
                            logger.info(f"[SUPABASE_TRANSACTION] Research context has {len(sources_with_content)} sources and {len(citations)} citations")

                            # Create the data to store
                            research_data = {
                                "id": research_context_id,
                                "user_id": user_id,  # Use the provided user ID
                                "paper_id": None,  # Will be updated when paper ID is available
                                "topic": topic,
                                "content": research_context,
                                "created_at": datetime.now().isoformat(),
                                "updated_at": datetime.now().isoformat()
                            }

                            # Log the data being stored (without the full content)
                            log_data = research_data.copy()
                            log_data["content"] = f"<Content with {len(sources_with_content)} sources>"
                            logger.info(f"[SUPABASE_TRANSACTION] Data to store: {json.dumps(log_data)}")

                            # Store in Supabase
                            logger.info(f"[SUPABASE_TRANSACTION] Executing insert into saas_research_context table")
                            response = supabase_client.table('saas_research_context').insert(research_data).execute()

                            if response.data:
                                logger.info(f"[SUPABASE_TRANSACTION] Research context stored successfully in Supabase with ID: {research_context_id}")
                                logger.info(f"[SUPABASE_TRANSACTION] Response data: {json.dumps(response.data)}")
                                # Add the ID to the research context for reference
                                research_context["id"] = research_context_id
                            else:
                                logger.error(f"[SUPABASE_TRANSACTION] Failed to store research context in Supabase: {response.error}")
                        except Exception as e:
                            logger.error(f"[SUPABASE_TRANSACTION] Error storing research context in Supabase: {str(e)}")
                            import traceback
                            logger.error(f"[SUPABASE_TRANSACTION] Traceback: {traceback.format_exc()}")

                        logger.info(f"Research completed with {len(sources_with_content)} sources")


                except Exception as e:
                    logger.error(f"Error during research: {str(e)}")
                    research_context = None
            else:
                logger.warning("No SERP API key provided, skipping research phase")

            # Step 3: Generate content
            logger.info(f"Generating content for topic: {topic}")

            # Create a system prompt
            system_prompt = f"""
            You are an academic writing assistant specializing in {education_level} level research papers.
            Your task is to generate well-structured, academically rigorous research papers.
            Include proper citations, academic language, and appropriate depth for the {education_level} level.
            """

            # Get sections from the database
            from app.services.config import config_service

            # Get the content generation prompt from the database
            prompt_data = config_service.get_prompt("research_pack", "content_generation")

            if not prompt_data:
                logger.warning("No content generation prompt found in database. Using default prompt.")
                # Create a default prompt
                prompt_data = {
                    "name": "Default Content Generation Prompt",
                    "prompt_text": """
                    You are Lily, an academic research assistant specializing in {education_level} level research.

                    Your task is to create a comprehensive research pack on the topic: {topic}

                    {question}

                    The research pack should be structured with the following sections:
                    {sections_list}

                    Please generate content for each section. The content should be academically rigorous, well-structured, and appropriate for {education_level} level research.

                    Format your response as a JSON object with the following structure:
                    ```json
                    {{
                      "title": "Research Pack: {topic}",
                      "sections": {{
                    {sections_json_format}
                      }}
                    }}
                    ```

                    Each section should include:
                    1. A clear, informative heading
                    2. Well-structured content with appropriate academic language
                    3. Relevant examples, case studies, or data where appropriate
                    4. Citations to academic sources where relevant

                    Your response should ONLY contain the JSON object, nothing else.
                    """
                }

            # Get sections from the database using Supabase
            try:
                if not hasattr(config_service, 'supabase') or not config_service.supabase:
                    logger.error("No Supabase connection available. Using default sections.")
                    # Create default sections
                    sections = [
                        ("introduction", "Introduction", 1),
                        ("background", "Background", 2),
                        ("literature_review", "Literature Review", 3),
                        ("methodology", "Methodology", 4),
                        ("findings", "Findings", 5),
                        ("discussion", "Discussion", 6),
                        ("conclusion", "Conclusion", 7),
                        ("references", "References", 8)
                    ]
                else:
                    # Build the query using Supabase
                    query = config_service.supabase.table('saas_researchpack_sections').select('name,display_name,section_order').eq('enabled', True)

                    # Add education level filter if provided
                    if education_level:
                        query = query.or_(f"education_level_minimum.is.null,education_level_minimum.eq.,education_level_minimum.eq.{education_level}")

                    # Add premium filter
                    query = query.or_(f"premium_only.eq.false,premium_only.eq.{str(premium).lower()}")

                    # Order by section_order
                    query = query.order('section_order')

                    # Execute the query
                    result = query.execute()

                    if result.data and len(result.data) > 0:
                        # Convert to the same format as the SQLAlchemy result
                        sections = [(section['name'], section['display_name'], section['section_order']) for section in result.data]
                    else:
                        logger.error("No sections found in database. Using default sections.")
                        # Create default sections
                        sections = [
                            ("introduction", "Introduction", 1),
                            ("background", "Background", 2),
                            ("literature_review", "Literature Review", 3),
                            ("methodology", "Methodology", 4),
                            ("findings", "Findings", 5),
                            ("discussion", "Discussion", 6),
                            ("conclusion", "Conclusion", 7),
                            ("references", "References", 8)
                        ]
            except Exception as e:
                logger.error(f"Error retrieving sections: {str(e)}. Using default sections.")
                # Create default sections
                sections = [
                    ("introduction", "Introduction", 1),
                    ("background", "Background", 2),
                    ("literature_review", "Literature Review", 3),
                    ("methodology", "Methodology", 4),
                    ("findings", "Findings", 5),
                    ("discussion", "Discussion", 6),
                    ("conclusion", "Conclusion", 7),
                    ("references", "References", 8)
                ]

            logger.info(f"Retrieved {len(sections)} sections for content generation")

            # Create sections list for the prompt
            sections_list = "\n".join([f"{i+1}. {section[1]}" for i, section in enumerate(sections)])

            # Create sections JSON format for the prompt with already escaped braces
            sections_json_format = ""
            for i, section in enumerate(sections):
                section_name = section[0]
                section_heading = section[1]
                comma = "," if i < len(sections) - 1 else ""
                sections_json_format += f'        "{section_name}": {{\n            "heading": "{section_heading}",\n            "content": "{section_heading} content..."\n        }}{comma}\n'

            # Pre-process the prompt to handle any potential formatting issues
            try:
                # Get the prompt text
                prompt_text = prompt_data["prompt_text"]

                # Replace all placeholders manually to avoid format string issues
                content_prompt = prompt_text

                # Replace the sections_json_format placeholder first if it exists
                if "{sections_json_format}" in content_prompt:
                    content_prompt = content_prompt.replace("{sections_json_format}", sections_json_format)

                # Replace the other placeholders
                content_prompt = content_prompt.replace("{topic}", str(topic))
                content_prompt = content_prompt.replace("{question}", str(question) if question else "")
                content_prompt = content_prompt.replace("{education_level}", str(education_level))
                content_prompt = content_prompt.replace("{sections_list}", str(sections_list))
            except Exception as e:
                logger.error(f"[{request_id}] Error pre-processing prompt: {str(e)}")
                raise ContentGenerationError(f"Error pre-processing prompt: {str(e)}", "RP002_PROMPT_ERROR")

            # Add research context if available
            if research_context:
                logger.info(f"[{request_id}] Adding research context to content prompt with {len(research_context['sources'])} sources")

                # Create a simplified version of the sources for the prompt
                simplified_sources = []
                for source in research_context["sources"][:10]:
                    simplified_source = {
                        "title": source.get("title", ""),
                        "authors": source.get("authors", []),
                        "year": source.get("publication_year", source.get("year", "")),
                        "summary": source.get("snippet", "")
                    }
                    simplified_sources.append(simplified_source)
                    logger.info(f"[{request_id}] Added source to context: '{simplified_source['title'][:30]}...' by {simplified_source['authors']} ({simplified_source['year']})")

                # Get citations in the primary style
                primary_style = research_context["primary_citation_style"]
                citations = research_context["citations"].get(primary_style, [])
                logger.info(f"[{request_id}] Adding {len(citations[:10])} citations in {primary_style} style to content prompt")

                # Add the research context to the prompt
                content_prompt += f"""

                Use the following research sources in your paper:

                Sources:
                {json.dumps(simplified_sources, indent=2)}

                Citations:
                {json.dumps(citations[:10], indent=2)}
                """

                # Log a sample of the citations
                if citations:
                    sample_citation = citations[0]
                    logger.info(f"[{request_id}] Sample citation: formatted='{sample_citation.get('formatted_citation', '')[:50]}...', in-text='{sample_citation.get('in_text_citation', '')}'")
            else:
                logger.warning(f"[{request_id}] No research context available for content generation")

            # Generate the content using section plans to avoid repetition
            try:
                logger.info(f"[OPENROUTER_API] Generating content with OpenRouter API using section plans")
                logger.info(f"[OPENROUTER_API] System prompt: {system_prompt}")
                logger.info(f"[OPENROUTER_API] Content prompt length: {len(content_prompt)} characters")
                logger.info(f"[OPENROUTER_API] Content prompt first 200 chars: {content_prompt[:200]}...")

                # Add section plans to the prompt to guide content generation
                if section_plans:
                    section_plans_text = "\n\nDetailed section plans to follow:\n\n"
                    for section_name, plan in section_plans.items():
                        section_plans_text += f"--- {section_name.upper()} PLAN ---\n{plan[:500]}...\n\n"

                    content_prompt += section_plans_text
                    logger.info(f"[OPENROUTER_API] Added {len(section_plans)} section plans to prompt")

                # Generate content section by section to avoid repetition
                if section_plans:
                    logger.info(f"[OPENROUTER_API] Generating content section by section using plans")

                    # Initialize the response structure
                    content_sections = {}

                    # Track previously generated sections to avoid repetition
                    previous_sections = {}

                    # Generate each section separately
                    for section_name, plan in section_plans.items():
                        logger.info(f"[OPENROUTER_API] Generating content for section: {section_name}")

                        # Create a section-specific prompt
                        section_prompt = f"""
                        Generate content for the {section_name} section of a research paper on {topic}.

                        Follow this detailed plan:
                        {plan}

                        Your content should be academically rigorous, well-structured, and appropriate for {education_level} level research.
                        """

                        # Add previous sections context to avoid repetition
                        if previous_sections:
                            section_prompt += "\n\nPreviously generated sections (DO NOT REPEAT THIS CONTENT):\n\n"
                            for prev_name, prev_content in previous_sections.items():
                                section_prompt += f"--- {prev_name.upper()} ---\n{prev_content[:300]}...\n\n"

                        # Generate the section content
                        section_response = llm_service.generate_content(
                            section_prompt,
                            config_type='content',
                            system_prompt=system_prompt
                        )

                        # Store the section content
                        content_sections[section_name] = {
                            "heading": section_name.replace('_', ' ').title(),
                            "content": section_response
                        }

                        # Add to previous sections for context in next section
                        previous_sections[section_name] = section_response

                        logger.info(f"[OPENROUTER_API] Generated content for section {section_name}: {len(section_response)} characters")

                    # Create a JSON response structure
                    response_obj = {
                        "title": f"Research Pack: {topic}",
                        "sections": content_sections
                    }

                    # Convert to JSON string
                    response = json.dumps(response_obj)

                    logger.info(f"[OPENROUTER_API] Generated content for all sections: {len(response)} characters")
                else:
                    # Fall back to generating all content at once if no section plans
                    response = llm_service.generate_content(content_prompt, config_type='content', system_prompt=system_prompt)
                    logger.info(f"[OPENROUTER_API] Response received from OpenRouter API")
                    logger.info(f"[OPENROUTER_API] Response length: {len(response)} characters")

                # Log the full response for debugging
                logger.info(f"[OPENROUTER_API] Raw LLM response first 500 chars: {response[:500]}...")

                # Parse the response as JSON
                try:
                    # Check if the response starts with ```json and ends with ```
                    if response.strip().startswith("```json") and "```" in response:
                        # Extract the JSON part
                        json_start = response.find("```json") + 7
                        json_end = response.find("```", json_start)
                        json_str = response[json_start:json_end].strip()
                        logger.info(f"Extracted JSON string: {json_str[:100]}...")
                        content = json.loads(json_str)
                    elif response.strip().startswith("```") and "```" in response:
                        # Extract the JSON part without the json tag
                        json_start = response.find("```") + 3
                        json_end = response.find("```", json_start)
                        json_str = response[json_start:json_end].strip()
                        logger.info(f"Extracted JSON string from code block: {json_str[:100]}...")
                        content = json.loads(json_str)
                    else:
                        # Try to parse the whole response as JSON
                        # First, try to find a JSON object in the response
                        json_start = response.find("{")
                        json_end = response.rfind("}") + 1
                        if json_start >= 0 and json_end > json_start:
                            json_str = response[json_start:json_end]
                            logger.info(f"Extracted JSON string from response: {json_str[:100]}...")
                            content = json.loads(json_str)
                        else:
                            # Try to parse the whole response as JSON
                            content = json.loads(response)

                    # Validate the content structure
                    if 'sections' not in content:
                        logger.error(f"[{request_id}] Content does not have a 'sections' key")
                        raise ContentValidationError("Invalid content structure: missing 'sections' key", "RP003_NO_SECTIONS")

                    if not content.get('sections'):
                        logger.error(f"[{request_id}] Content has empty 'sections'")
                        raise ContentValidationError("Invalid content structure: empty 'sections'", "RP003_EMPTY_SECTIONS")

                    # Add static content sections
                    static_sections = ['about_lily', 'how_to_use', 'appendices']
                    for section_name in static_sections:
                        static_content = await self._get_static_content(section_name)
                        if static_content:
                            display_name = section_name.replace('_', ' ').title()
                            if section_name == 'about_lily':
                                display_name = 'About Lily AI'
                            elif section_name == 'how_to_use':
                                display_name = 'How to Use This Pack'

                            content['sections'][section_name] = {
                                'heading': display_name,
                                'content': static_content
                            }
                            logger.info(f"Added static content for section: {section_name}")

                    # Generate diagrams for the content
                    logger.info(f"Generating diagrams for topic: {topic}")
                    diagrams = await self._generate_diagrams(topic, question)
                    if diagrams:
                        logger.info(f"Generated {len(diagrams)} diagrams")
                        # Add diagrams to the content
                        content['diagrams'] = diagrams

                        # Log the diagrams
                        for i, diagram in enumerate(diagrams):
                            diagram_type = diagram.get("type", "unknown")
                            diagram_path = diagram.get("path", "unknown")
                            logger.info(f"Diagram {i+1}: type={diagram_type}, path={diagram_path}")

                            # Associate diagrams with specific sections based on type
                            if diagram_type == "mind_map" and "topic_analysis" in content['sections']:
                                content['sections']["topic_analysis"]["diagram"] = diagram
                                logger.info(f"Associated mind map diagram with topic_analysis section")
                            elif diagram_type == "question_breakdown" and "introduction" in content['sections']:
                                content['sections']["introduction"]["diagram"] = diagram
                                logger.info(f"Associated question breakdown diagram with introduction section")
                            elif diagram_type == "journey_map" and "methodological_approaches" in content['sections']:
                                content['sections']["methodological_approaches"]["diagram"] = diagram
                                logger.info(f"Associated journey map diagram with methodological_approaches section")
                            elif diagram_type == "argument_mapping" and "key_arguments" in content['sections']:
                                content['sections']["key_arguments"]["diagram"] = diagram
                                logger.info(f"Associated argument mapping diagram with key_arguments section")
                            elif diagram_type == "comparative_analysis" and "key_arguments" in content['sections']:
                                content['sections']["key_arguments"]["comparative_diagram"] = diagram
                                logger.info(f"Associated comparative analysis diagram with key_arguments section")
                    else:
                        logger.warning("No diagrams were generated")
                        content['diagrams'] = []

                    logger.info(f"Content generated successfully with {len(content.get('sections', {}))} sections")
                    logger.info(f"Content sections: {list(content.get('sections', {}).keys())}")

                    # Store generated content in Supabase
                    try:
                        # Check if Supabase client is available
                        if not supabase_client:
                            logger.warning("Supabase client not available. Skipping content storage.")
                            return content

                        # Generate a unique ID for this paper
                        paper_id = str(uuid.uuid4())

                        # Store in saas_papers table
                        logger.info(f"Storing generated content in Supabase with ID: {paper_id}")

                        # Create the data to store
                        paper_data = {
                            "id": paper_id,
                            "user_id": user_id,  # Use the provided user ID
                            "title": f"Research Pack: {topic}",
                            "topic": topic,
                            "content": json.dumps(content),
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat(),
                            "is_research_pack": True,
                            "status": "generated"
                        }

                        # Store in Supabase
                        response = supabase_client.table('saas_papers').insert(paper_data).execute()

                        if response.data:
                            logger.info(f"Generated content stored successfully in Supabase with ID: {paper_id}")
                            # Add the ID to the content for reference
                            content["paper_id"] = paper_id

                            # If we have a research context ID, update the research context with the paper ID
                            if research_context and "id" in research_context:
                                research_context_id = research_context["id"]
                                logger.info(f"Updating research context {research_context_id} with paper ID {paper_id}")

                                update_response = supabase_client.table('saas_research_context').update({"paper_id": paper_id}).eq("id", research_context_id).execute()

                                if update_response.data:
                                    logger.info(f"Research context updated successfully with paper ID: {paper_id}")
                                else:
                                    logger.error(f"Failed to update research context with paper ID: {update_response.error}")
                        else:
                            logger.error(f"Failed to store generated content in Supabase: {response.error}")
                    except Exception as e:
                        logger.error(f"Error storing generated content in Supabase: {str(e)}")

                    # Log a sample of each section and validate structure
                    for section_name, section_data in content.get('sections', {}).items():
                        if not isinstance(section_data, dict):
                            logger.error(f"[{request_id}] Section '{section_name}' is not a dictionary: {type(section_data)}")
                            raise ContentValidationError(
                                f"Invalid section structure: '{section_name}' is not a dictionary",
                                f"RP003_SECTION_TYPE_{section_name.upper()}"
                            )

                        if 'content' not in section_data:
                            logger.error(f"[{request_id}] Section '{section_name}' does not have a 'content' key")
                            raise ContentValidationError(
                                f"Invalid section structure: missing 'content' key in '{section_name}'",
                                f"RP003_NO_CONTENT_{section_name.upper()}"
                            )

                        if 'heading' not in section_data:
                            logger.error(f"[{request_id}] Section '{section_name}' does not have a 'heading' key")
                            raise ContentValidationError(
                                f"Invalid section structure: missing 'heading' key in '{section_name}'",
                                f"RP003_NO_HEADING_{section_name.upper()}"
                            )

                        section_content = section_data.get('content', '')
                        logger.info(f"Section '{section_name}' content sample: {section_content[:100]}...")

                    # Check if all required sections are present
                    try:
                        if not hasattr(config_service, 'supabase') or not config_service.supabase:
                            logger.error("No Supabase connection available. Using default required sections.")
                            # Create default required sections
                            required_sections = [
                                ("introduction", "Introduction"),
                                ("conclusion", "Conclusion")
                            ]
                        else:
                            # Build the query using Supabase
                            query = config_service.supabase.table('saas_researchpack_sections').select('name,display_name').eq('enabled', True).eq('required', True)

                            # Add education level filter if provided
                            if education_level:
                                query = query.or_(f"education_level_minimum.is.null,education_level_minimum.eq.,education_level_minimum.eq.{education_level}")

                            # Add premium filter
                            query = query.or_(f"premium_only.eq.false,premium_only.eq.{str(premium).lower()}")

                            # Order by section_order
                            query = query.order('section_order')

                            # Execute the query
                            result = query.execute()

                            if result.data and len(result.data) > 0:
                                # Convert to the same format as the SQLAlchemy result
                                required_sections = [(section['name'], section['display_name']) for section in result.data]
                            else:
                                logger.error("No required sections found in database. Using default required sections.")
                                # Create default required sections
                                required_sections = [
                                    ("introduction", "Introduction"),
                                    ("conclusion", "Conclusion")
                                ]
                    except Exception as e:
                        logger.error(f"Error retrieving required sections: {str(e)}. Using default required sections.")
                        # Create default required sections
                        required_sections = [
                            ("introduction", "Introduction"),
                            ("conclusion", "Conclusion")
                        ]

                    logger.info(f"Retrieved {len(required_sections)} required sections for validation")

                    # Check if all required sections are present
                    missing_sections = []
                    for section_name, _ in required_sections:  # display_name not used here
                        if section_name not in content.get('sections', {}):
                            missing_sections.append(section_name)

                    if missing_sections:
                        logger.error(f"[{request_id}] Missing required sections: {missing_sections}")
                        raise ContentValidationError(
                            f"Missing required sections: {', '.join(missing_sections)}",
                            "RP003_MISSING_SECTIONS"
                        )
                except json.JSONDecodeError as e:
                    logger.error(f"[{request_id}] Error parsing content as JSON: {str(e)}")
                    logger.error(f"[{request_id}] Response sample: {response[:500]}...")
                    raise ContentValidationError(
                        f"Failed to parse LLM response as JSON: {str(e)}",
                        "RP003_JSON_PARSE_ERROR"
                    )
            except (ContentValidationError, ConfigurationError) as e:
                # Re-raise these specific exceptions without wrapping
                raise
            except Exception as e:
                logger.error(f"[{request_id}] Error generating content: {str(e)}")
                raise ContentGenerationError(f"Failed to generate content: {str(e)}", "RP002_GENERATION_ERROR")

            return content

        except (ContentValidationError, ConfigurationError, ContentGenerationError) as e:
            # Re-raise these specific exceptions without wrapping
            logger.error(f"[{request_id}] Error in _generate_content: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[{request_id}] Error in _generate_content: {str(e)}")
            raise ContentGenerationError(f"Unexpected error in content generation: {str(e)}", "RP002_UNEXPECTED_ERROR")

    async def _generate_personalized_answers(self, research_pack: Dict[str, Any], topic: str, education_level: str = "university") -> None:
        """
        Generate answers to personalized questions from the user.

        Args:
            research_pack: The research pack dictionary
            topic: The research topic
            education_level: The education level

        Returns:
            None (updates the research_pack dictionary in place)
        """
        request_id = f"req_{int(datetime.now().timestamp())}"
        logger.info(f"[{request_id}] Generating answers to personalized questions for topic: {topic}")

        if not research_pack["personalized_questions"]:
            logger.info("No personalized questions to answer")
            return

        try:
            # Import the LLM service
            from app.services.llm import llm_service

            # Create a system prompt
            system_prompt = f"""
            You are Lily, an academic research assistant specializing in {education_level} level research.
            Your task is to provide thoughtful, well-researched answers to personalized questions about the topic.
            Include academic language and appropriate depth for the {education_level} level.
            Be concise but thorough in your responses.
            """

            # Create a dictionary to store the answers
            answers = {}

            # Generate an answer for each question
            for i, question in enumerate(research_pack["personalized_questions"]):
                logger.info(f"Generating answer for question {i+1}: {question}")

                # Create a prompt for this question
                prompt = f"""
                Topic: {topic}

                Please provide a thoughtful, well-researched answer to the following question:

                Question: {question}

                Your answer should be academically rigorous, well-structured, and appropriate for {education_level} level research.
                Include relevant concepts, theories, and examples in your answer.
                """

                # Generate the answer
                answer = llm_service.generate_content(prompt, config_type='content', system_prompt=system_prompt)

                # Add the answer to the dictionary
                answers[f"question_{i+1}"] = {
                    "question": question,
                    "answer": answer
                }

                logger.info(f"Generated answer for question {i+1}")

            # Add the answers to the research pack content
            if "sections" not in research_pack["content"]:
                research_pack["content"]["sections"] = {}

            research_pack["content"]["sections"]["personalized_questions"] = {
                "heading": "Personalized Questions",
                "content": "Answers to your personalized questions about this topic.",
                "questions": answers
            }

            logger.info(f"Added {len(answers)} personalized question answers to the research pack")

        except Exception as e:
            logger.error(f"[{request_id}] Error generating personalized answers: {str(e)}")
            logger.warning("Continuing without personalized answers")

    async def _process_with_lily_callout_engine(self, content: Dict[str, Any], topic: str = "", education_level: str = "university") -> Dict[str, Any]:
        """
        Process content through the Lily Callout Engine.

        Args:
            content: The content to process
            topic: The research topic
            education_level: The education level (university, postgraduate, etc.)

        Returns:
            The processed content
        """
        request_id = f"req_{int(datetime.now().timestamp())}"
        logger.info(f"[LILY_ENGINE] [{request_id}] Processing content with Lily Callout Engine")
        logger.info(f"[LILY_ENGINE] [{request_id}] Topic: {topic}, Education level: {education_level}")
        logger.info(f"[LILY_ENGINE] [{request_id}] Content has {len(content.get('sections', {}))} sections")

        if not self.lily_callout_engine:
            logger.error("[LILY_ENGINE] No Lily Callout Engine provided")
            raise ConfigurationError("Lily Callout Engine not provided", "RP001_NO_LILY_ENGINE")

        # Log sections before processing
        for section_name, section_data in content.get('sections', {}).items():
            section_content = section_data.get('content', '')
            logger.info(f"[LILY_ENGINE] [{request_id}] Section '{section_name}' before processing, content length: {len(section_content)} chars")

        # Process the content through the Lily Callout Engine
        logger.info(f"[LILY_ENGINE] [{request_id}] Calling _enhance_with_callouts method")
        processed_content = self.lily_callout_engine._enhance_with_callouts(content, topic, education_level)
        logger.info(f"[LILY_ENGINE] [{request_id}] Content processed through Lily Callout Engine successfully")

        # Count the number of callouts added
        callout_count = str(processed_content).count("LILY_CALLOUT")
        logger.info(f"[LILY_ENGINE] [{request_id}] Added {callout_count} Lily callouts to the content")

        # Log sections after processing
        for section_name, section_data in processed_content.get('sections', {}).items():
            section_content = section_data.get('content', '')
            section_callout_count = section_content.count("LILY_CALLOUT")
            logger.info(f"[LILY_ENGINE] [{request_id}] Section '{section_name}' after processing, content length: {len(section_content)} chars, callouts: {section_callout_count}")

        # Update the content in Supabase if paper_id is available
        paper_id = content.get("paper_id", None)
        if paper_id and supabase_client:
            try:
                logger.info(f"[{request_id}] Updating paper {paper_id} with Lily callouts in Supabase")

                # Create the data to update
                update_data = {
                    "content": json.dumps(processed_content),
                    "updated_at": datetime.now().isoformat()
                }

                # Update the paper in Supabase
                response = supabase_client.table('saas_papers').update(update_data).eq("id", paper_id).execute()

                if response.data:
                    logger.info(f"[{request_id}] Paper {paper_id} updated with Lily callouts successfully")
                else:
                    logger.error(f"[{request_id}] Failed to update paper {paper_id} with Lily callouts: {response.error}")
            except Exception as e:
                logger.error(f"[{request_id}] Error updating paper with Lily callouts: {str(e)}")
        else:
            logger.warning(f"[{request_id}] No paper_id available, skipping Supabase update for Lily callouts")

        return processed_content

    async def _format_document(
            self,
            content: Dict[str, Any],
            topic: str,
            user_id: str,
            diagrams: List[Dict[str, Any]] = None,
            question: str = ""
        ) -> str:
        """
        Format the document using the document formatter.

        Args:
            content: The content to format
            topic: The research topic
            user_id: The user ID
            diagrams: The diagrams to include
            question: The research question

        Returns:
            The path to the formatted document
        """
        request_id = f"req_{int(datetime.now().timestamp())}"
        logger.info(f"[{request_id}] Formatting document for topic: {topic}, user_id: {user_id}")

        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)

        # Get paper ID if available
        paper_id = content.get("paper_id", None)

        # If paper_id is available, try to retrieve the content from Supabase
        if paper_id and supabase_client:
            try:
                logger.info(f"[{request_id}] Retrieving content from Supabase for paper {paper_id}")
                response = supabase_client.table('saas_papers').select('content').eq('id', paper_id).execute()

                if response.data and len(response.data) > 0:
                    stored_content = response.data[0].get('content')
                    if stored_content:
                        try:
                            # If stored_content is a string, parse it as JSON
                            if isinstance(stored_content, str):
                                stored_content = json.loads(stored_content)

                            logger.info(f"[{request_id}] Successfully retrieved content from Supabase for paper {paper_id}")

                            # Preserve the paper_id in the retrieved content
                            stored_content["paper_id"] = paper_id

                            # Use the retrieved content instead of the provided content
                            content = stored_content
                        except json.JSONDecodeError as e:
                            logger.error(f"[{request_id}] Error parsing content from Supabase: {str(e)}")
                    else:
                        logger.warning(f"[{request_id}] No content found in Supabase for paper {paper_id}")
                else:
                    logger.warning(f"[{request_id}] No paper found in Supabase with ID {paper_id}")
            except Exception as e:
                logger.error(f"[{request_id}] Error retrieving content from Supabase: {str(e)}")

        # Generate document path
        if paper_id:
            document_path = os.path.join(output_dir, f"research_pack_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx")
            logger.info(f"[{request_id}] Using paper ID {paper_id} for document formatting")
        else:
            document_path = os.path.join(output_dir, f"research_pack_{user_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx")

        if not self.document_formatter:
            logger.error("No document formatter provided")
            raise ConfigurationError("Document formatter not provided", "RP001_NO_DOC_FORMATTER")

        try:
            # Add diagrams to the content if available
            if diagrams and isinstance(diagrams, list) and len(diagrams) > 0:
                logger.info(f"[{request_id}] Adding {len(diagrams)} diagrams to content for document formatting")
                # Ensure content has a diagrams field
                content["diagrams"] = diagrams

                # Log the diagrams being added
                for i, diagram in enumerate(diagrams):
                    diagram_type = diagram.get("type", "unknown")
                    diagram_path = diagram.get("path", "unknown")
                    logger.info(f"[{request_id}] Diagram {i+1}: type={diagram_type}, path={diagram_path}")
            else:
                logger.warning(f"[{request_id}] No diagrams available for document formatting")
                content["diagrams"] = []

            # Format the document using the document formatter
            self.document_formatter.format_research_pack(content)

            # Save the document
            self.document_formatter.save_document(document_path)
        except Exception as e:
            logger.error(f"[{request_id}] Error formatting document: {str(e)}")
            raise DocumentFormattingError(f"Failed to format document: {str(e)}", "RP005_FORMAT_ERROR")
        logger.info(f"Document saved to {document_path}")

        return document_path

    async def _convert_to_pdf(self, docx_path: str) -> Optional[str]:
        """
        Convert a DOCX file to PDF using Cloudmersive.

        Args:
            docx_path: Path to the DOCX file

        Returns:
            Path to the PDF file or None if conversion fails
        """
        logger.info(f"Converting DOCX to PDF: {docx_path}")

        try:
            # Generate PDF path based on DOCX path
            pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

            # Convert DOCX to PDF
            pdf_path = docx_to_pdf(docx_path, pdf_path)

            if pdf_path:
                logger.info(f"DOCX converted to PDF: {pdf_path}")
                return pdf_path
            else:
                logger.error("Failed to convert DOCX to PDF")
                return None
        except Exception as e:
            logger.error(f"Error converting DOCX to PDF: {str(e)}")
            return None

    async def _upload_to_storage(self, file_path: str, bucket_name: str, destination_path: Optional[str] = None, paper_id: Optional[str] = None) -> Optional[str]:
        """
        Upload a file to Supabase Storage.

        Args:
            file_path: Path to the file to upload
            bucket_name: Name of the bucket to upload to
            destination_path: Path within the bucket to upload to (optional)
            paper_id: ID of the paper to update with the file URL (optional)

        Returns:
            URL of the uploaded file or None if upload fails
        """
        logger.info(f"Uploading file to Supabase Storage: {file_path}")

        try:
            if not self.storage_service:
                logger.error("No storage service available")
                return None

            # Upload the file
            file_url = self.storage_service.upload_file(file_path, bucket_name, destination_path)

            if file_url:
                logger.info(f"File uploaded to Supabase Storage: {file_url}")

                # Update the paper record with the file URL if paper_id is provided
                if paper_id and supabase_client:
                    try:
                        # Determine if this is a DOCX or PDF file
                        is_docx = file_path.lower().endswith('.docx')
                        is_pdf = file_path.lower().endswith('.pdf')

                        update_data = {}
                        if is_docx:
                            update_data["docx_url"] = file_url
                            update_data["docx_storage_path"] = destination_path
                        elif is_pdf:
                            update_data["pdf_url"] = file_url
                            update_data["pdf_storage_path"] = destination_path

                        if update_data:
                            logger.info(f"Updating paper {paper_id} with file URL: {file_url}")
                            response = supabase_client.table('saas_papers').update(update_data).eq("id", paper_id).execute()

                            if response.data:
                                logger.info(f"Paper {paper_id} updated with file URL successfully")
                            else:
                                logger.error(f"Failed to update paper {paper_id} with file URL: {response.error}")
                    except Exception as e:
                        logger.error(f"Error updating paper with file URL: {str(e)}")

                return file_url
            else:
                logger.error("Failed to upload file to Supabase Storage")
                return None
        except Exception as e:
            logger.error(f"Error uploading file to Supabase Storage: {str(e)}")
            return None

# Example usage
if __name__ == "__main__":
    # This is just an example of how to use the Research Pack Orchestrator
    # In a real application, you would initialize it with actual components
    orchestrator = ResearchPackOrchestrator()

    # Example of generating a research pack
    import asyncio
    research_pack = asyncio.run(orchestrator.generate_research_pack(
        topic="Artificial Intelligence Ethics",
        question="What are the key ethical considerations in AI development?",
        user_id="user123"
    ))

    print(f"Research pack generated: {research_pack}")
