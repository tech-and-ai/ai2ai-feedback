"""
Research Generator Module

Handles the research process for generating research packs, including:
1. Content moderation
2. Research planning
3. SERP API integration for gathering sources
4. Citation extraction and formatting
5. Database storage of research data

Process Flow:
1. Moderation → Planning → Research → Content Generation
2. Early diagram generation
3. Database-centric approach for scalability
4. Optimized SERP API usage (Google Scholar + Google Search)
5. Efficient content extraction with rate limiting
6. Citation management for accuracy
"""
import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import uuid

# Import our components
from .content_extractor import ContentExtractor
from .db_manager import ResearchDBManager
from .serp_api_service import SerpApiService

# Setup logging
logger = logging.getLogger(__name__)

class ResearchGenerator:
    """
    Handles the research process for generating research packs.

    The research process follows these steps:
    1. Moderate the topic to ensure it's appropriate for academic research
    2. Create a research plan based on the topic and questions
    3. Gather sources from multiple search engines via SERP API
    4. Extract and format citations from the sources
    5. Store all research data in the database for use in content generation
    """

    def __init__(self, openrouter_key=None, serp_api_key=None, db_connection=None):
        """Initialize the research generator."""
        # API keys
        self.openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
        self.serp_api_key = serp_api_key or os.getenv("SERP_API_KEY")

        # Database connection
        self.db_connection = db_connection

        # API endpoints
        self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"

        # Initialize components
        self.serp_api_service = SerpApiService(self.serp_api_key, self.db_connection)
        self.content_extractor = ContentExtractor(self.db_connection)
        self.db_manager = ResearchDBManager(self.db_connection) if self.db_connection else None

        # Validate API keys
        if not self.openrouter_key:
            logger.warning("No OpenRouter API key provided. Moderation and planning capabilities will be limited.")

        if not self.serp_api_key:
            logger.warning("No SERP API key provided. Research capabilities will be limited.")

        # Initialize cache
        self.moderation_cache = {}

    async def moderate_topic(self, topic: str) -> Tuple[bool, str]:
        """
        Moderate the topic to ensure it's appropriate for academic research.

        Args:
            topic: The research topic to moderate

        Returns:
            Tuple of (is_appropriate, reason)
        """
        # Check if we've already moderated this topic
        if topic in self.moderation_cache:
            logger.info(f"Using cached moderation result for topic: {topic}")
            return self.moderation_cache[topic]

        # Check if the topic exists in the database
        if self.db_manager:
            db_result = await self.db_manager.get_moderation_result(topic)
            if db_result:
                logger.info(f"Using database moderation result for topic: {topic}")
                self.moderation_cache[topic] = db_result
                return db_result

        # If no cached result, perform moderation
        try:
            logger.info(f"Moderating topic: {topic}")

            # Get the moderation prompt from the database
            from app.services.config import config_service
            prompt_data = config_service.get_prompt("serp_api", "moderation")

            if not prompt_data:
                logger.warning("No moderation prompt found in database. Using default prompt.")
                # Use default prompt if not found in database
                moderation_prompt = f"""Evaluate if the following academic paper topic is appropriate for research in an ACADEMIC CONTEXT:

                Topic: {topic}

                IMPORTANT: This is for ACADEMIC RESEARCH. Many sensitive topics are valid for academic study.

                SPECIFICALLY ALLOWED academic topics include:
                - Analysis of combat sports (UFC, boxing, martial arts) including safety and health impacts
                - Academic studies of sexuality, gender, and reproductive health
                - Medical and psychological research on topics like suicide, self-harm, or mental health conditions
                - Sociological or criminological studies of violence, crime, or illegal activities
                - Political, historical, or cultural analysis of controversial subjects
                - Research on sensitive topics like rape, abortion, or drug use in appropriate academic contexts

                Only flag topics that:
                1. Explicitly request INSTRUCTIONS for illegal activities
                2. Directly promote or glorify harmful actions
                3. Specifically target individuals or groups with derogatory language
                4. Ask for help with academic dishonesty (e.g., "write my essay for me")
                5. Have NO legitimate academic or research purpose

                If the topic violates these guidelines, respond with "INAPPROPRIATE: [specific reason]"
                If the topic is appropriate for academic study, respond with "APPROPRIATE"

                Provide only one of these responses with no additional text.
                """
                temperature = 0.1
                max_tokens = 50
            else:
                # Use the prompt from the database
                logger.info(f"Using moderation prompt from database: {prompt_data['name']}")
                moderation_prompt = prompt_data["prompt_text"].format(topic=topic)
                temperature = prompt_data.get("temperature", 0.1)
                max_tokens = prompt_data.get("max_tokens", 50)

            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            # Get model from configuration service
            try:
                from app.services.config.config_service import config_service
                model = config_service.get_config('default_llm_model', 'google/gemini-2.5-flash-preview')
                logger.info(f"Using model from config: {model}")
            except Exception as e:
                logger.warning(f"Could not load model from config service: {str(e)}")
                model = "google/gemini-2.5-flash-preview"  # Fallback model
                logger.info(f"Using fallback model: {model}")

            payload = {
                "model": model,  # Use the model from config
                "messages": [
                    {"role": "user", "content": moderation_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.openrouter_endpoint, headers=headers, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Error from OpenRouter API: Status {response.status}")
                        return (False, f"Error during moderation: API returned status {response.status}")

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return (False, "Error during moderation: No response from API")

                    result = data["choices"][0]["message"]["content"].strip()

                    # Parse the result
                    if result.startswith("APPROPRIATE"):
                        is_appropriate = True
                        reason = "APPROPRIATE"
                    else:
                        is_appropriate = False
                        reason = result.replace("INAPPROPRIATE:", "").strip()

            # Cache the result
            self.moderation_cache[topic] = (is_appropriate, reason)

            # Store in database if connection exists
            if self.db_manager:
                await self.db_manager.store_moderation_result(topic, is_appropriate, reason)

            return (is_appropriate, reason)

        except Exception as e:
            logger.error(f"Error moderating topic: {str(e)}")
            return (False, f"Error during moderation: {str(e)}")

    async def create_research_session(self, topic: str, questions: List[str] = None) -> str:
        """
        Create a new research session for a topic.

        Args:
            topic: The research topic
            questions: Optional list of specific questions to research

        Returns:
            Session ID for the research session
        """
        if self.db_manager:
            session_id = await self.db_manager.create_research_session(topic, questions)
        else:
            # Generate a session ID if no database
            session_id = str(uuid.uuid4())
            logger.info(f"Created in-memory research session {session_id} for topic: {topic}")

        return session_id

    async def create_research_plan(self, topic: str, questions: List[str] = None, session_id: str = None) -> Dict:
        """
        Create a research plan based on the topic and questions.

        Args:
            topic: The research topic
            questions: Optional list of specific questions to research
            session_id: Optional session ID to associate with this plan

        Returns:
            Dictionary containing the research plan
        """
        try:
            logger.info(f"Creating research plan for topic: {topic}")

            # Format questions for the prompt
            questions_text = ""
            if questions and len(questions) > 0:
                questions_text = "\n".join([f"- {q}" for q in questions])
                questions_text = f"\n\nSpecific questions to address:\n{questions_text}"

            # Get the research planning prompt from the database
            from app.services.config import config_service
            prompt_data = config_service.get_prompt("serp_api", "research_planning")

            if not prompt_data:
                logger.warning("No research planning prompt found in database. Using default prompt.")
                # Use default prompt if not found in database
                planning_prompt = f"""Create a comprehensive research plan for the topic: "{topic}"{questions_text}

                Your plan should include:

                1. Key research areas to explore
                2. Specific search queries to use for each area
                3. Types of sources to prioritize (academic papers, news articles, books, etc.)
                4. Key concepts and terminology to focus on
                5. Potential perspectives or viewpoints to consider

                Format your response as a structured JSON object with the following schema:
                {{
                    "research_areas": [
                        {{
                            "area": "Name of research area",
                            "description": "Brief description of this research area",
                            "search_queries": ["query 1", "query 2", ...],
                            "source_types": ["academic_paper", "news", "book", ...],
                            "key_concepts": ["concept 1", "concept 2", ...],
                            "perspectives": ["perspective 1", "perspective 2", ...]
                        }},
                        ...
                    ],
                    "section_specific_research": {{
                        "section_name": {{
                            "focus": "What to focus on for this section",
                            "search_queries": ["query 1", "query 2", ...],
                            "key_concepts": ["concept 1", "concept 2", ...]
                        }},
                        ...
                    }}
                }}

                Ensure your plan is comprehensive and will yield high-quality research results.
                """
                temperature = 0.7
                max_tokens = 4000
            else:
                # Use the prompt from the database
                logger.info(f"Using research planning prompt from database: {prompt_data['name']}")
                planning_prompt = prompt_data["prompt_text"].format(topic=topic, questions_text=questions_text)
                temperature = prompt_data.get("temperature", 0.7)
                max_tokens = prompt_data.get("max_tokens", 4000)

            # Call OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            # Get model from configuration service
            try:
                from app.services.config.config_service import config_service
                model = config_service.get_config('default_llm_model', 'google/gemini-2.5-flash-preview')
                logger.info(f"Using model from config: {model}")
            except Exception as e:
                logger.warning(f"Could not load model from config service: {str(e)}")
                model = "google/gemini-2.5-flash-preview"  # Fallback model
                logger.info(f"Using fallback model: {model}")

            payload = {
                "model": model,  # Use the model from config
                "messages": [
                    {"role": "user", "content": planning_prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(self.openrouter_endpoint, headers=headers, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Error from OpenRouter API: Status {response.status}")
                        return {"error": f"Error during planning: API returned status {response.status}"}

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return {"error": "Error during planning: No response from API"}

                    result = data["choices"][0]["message"]["content"].strip()

                    # Extract JSON from the response
                    try:
                        # Find JSON in the response
                        json_start = result.find("{")
                        json_end = result.rfind("}") + 1

                        if json_start >= 0 and json_end > json_start:
                            json_str = result[json_start:json_end]
                            research_plan = json.loads(json_str)
                        else:
                            # If no JSON found, use the whole response
                            research_plan = {"error": "Could not extract JSON from response", "raw_response": result}
                    except json.JSONDecodeError:
                        research_plan = {"error": "Invalid JSON in response", "raw_response": result}

            # Store in database if connection exists
            if self.db_manager and session_id:
                await self.db_manager.store_research_plan(session_id, research_plan)

            return research_plan

        except Exception as e:
            logger.error(f"Error creating research plan: {str(e)}")
            return {"error": f"Error during planning: {str(e)}"}

    async def search_sources(self,
                           research_plan: Dict,
                           session_id: str = None,
                           engines: List[str] = None) -> Dict:
        """
        Search for sources using SERP API based on the research plan.

        Args:
            research_plan: The research plan containing search queries
            session_id: Optional session ID to associate with these sources
            engines: List of search engines to use (default: use all enabled engines)

        Returns:
            Dictionary containing the search results
        """
        try:
            # Get enabled engines and allocate search calls
            engine_allocation = await self.serp_api_service.allocate_search_calls(research_plan)

            if not engine_allocation:
                logger.error("Failed to allocate search calls")
                return {"error": "Failed to allocate search calls"}

            logger.info(f"Search call allocation: {engine_allocation}")

            # Extract search queries from the research plan
            search_queries = []
            for area in research_plan.get("research_areas", []):
                search_queries.extend(area.get("search_queries", []))

            for section_data in research_plan.get("section_specific_research", {}).values():
                search_queries.extend(section_data.get("search_queries", []))

            # Remove duplicates and sort by relevance (simple approach: shorter queries first)
            search_queries = list(set(search_queries))
            search_queries.sort(key=len)

            logger.info(f"Total search queries available: {len(search_queries)}")

            # If no search queries found, generate default queries based on the topic
            if not search_queries:
                logger.warning(f"No search queries found in research plan. Generating default queries for topic: {research_plan.get('topic', 'unknown')}")
                # Generate a few basic queries based on the topic
                topic = research_plan.get('topic', '')
                if not topic and isinstance(research_plan, dict) and 'raw_response' in research_plan:
                    # Try to extract topic from raw response
                    raw_text = research_plan.get('raw_response', '')
                    if 'topic:' in raw_text.lower():
                        topic_line = [line for line in raw_text.split('\n') if 'topic:' in line.lower()]
                        if topic_line:
                            topic = topic_line[0].split('topic:', 1)[1].strip()

                # If we still don't have a topic, use a generic one
                if not topic:
                    topic = "artificial intelligence education impact"

                # Generate default queries with academic focus
                search_queries = [
                    f"{topic} filetype:pdf",
                    f"{topic} research paper filetype:pdf",
                    f"{topic} academic journal filetype:pdf",
                    f"{topic} scholarly article filetype:pdf",
                    f"{topic} literature review filetype:pdf",
                    f"{topic} meta-analysis filetype:pdf",
                    f"{topic} recent studies filetype:pdf",
                    f"{topic} research methodology filetype:pdf",
                    f"{topic} case study filetype:pdf",
                    f"{topic} empirical research filetype:pdf"
                ]
                logger.info(f"Generated {len(search_queries)} default search queries based on topic: {topic}")

            # Initialize results
            all_results = {}

            # For each engine, perform the allocated number of searches
            for engine, num_calls in engine_allocation.items():
                # Ensure we have enough queries
                engine_queries = search_queries[:num_calls]
                if len(engine_queries) < num_calls:
                    # If we don't have enough unique queries, duplicate the most relevant ones
                    while len(engine_queries) < num_calls:
                        engine_queries.append(engine_queries[0])

                logger.info(f"Using {len(engine_queries)} queries for engine {engine}")

                # Initialize results for this engine
                all_results[engine] = []
                existing_urls = set()

                # Perform searches for this engine
                for query in engine_queries:
                    logger.info(f"Searching for: {query} using {engine}")
                    result = await self.serp_api_service.search(query, engine, 100)

                    # Add results if not already present (by URL)
                    for item in result.get("organic_results", []):
                        if item.get("link") not in existing_urls:
                            all_results[engine].append(item)
                            existing_urls.add(item.get("link"))

            # Extract academic sources
            academic_sources = await self.serp_api_service.extract_academic_sources(all_results)

            # Log the number of sources found
            logger.info(f"Research completed with {len(academic_sources)} sources")

            # If no academic sources found, try a fallback approach with more generic queries
            if len(academic_sources) == 0:
                logger.warning("No academic sources found. Trying fallback approach...")

                # Generate more generic queries
                fallback_queries = [
                    f"{topic} pdf",
                    f"{topic} research",
                    f"{topic} study",
                    f"{topic} analysis",
                    f"{topic} overview"
                ]

                # Perform fallback searches
                fallback_results = {}
                for engine, _ in engine_allocation.items():
                    fallback_results[engine] = []
                    for query in fallback_queries[:2]:  # Limit to 2 queries per engine
                        logger.info(f"Fallback search for: {query} using {engine}")
                        result = await self.serp_api_service.search(query, engine, 100)
                        fallback_results[engine].extend(result.get("organic_results", []))

                # Extract academic sources from fallback results
                fallback_academic_sources = await self.serp_api_service.extract_academic_sources(fallback_results)
                logger.info(f"Fallback research completed with {len(fallback_academic_sources)} sources")

                # Combine with any previously found sources
                academic_sources.extend(fallback_academic_sources)

            # Store in database if connection exists
            if self.db_manager and session_id:
                source_ids = await self.db_manager.store_sources(session_id, academic_sources)

            return {
                "all_results": all_results,
                "academic_sources": academic_sources
            }

        except Exception as e:
            logger.error(f"Error searching for sources: {str(e)}")
            return {"error": f"Error during source search: {str(e)}"}

    async def extract_content(self, sources: List[Dict], session_id: str = None, max_sources: int = 20) -> List[Dict]:
        """
        Extract content from source URLs.

        Args:
            sources: List of source dictionaries
            session_id: Optional session ID
            max_sources: Maximum number of sources to process

        Returns:
            List of sources with extracted content
        """
        try:
            request_id = f"extract_{int(datetime.now().timestamp())}"
            logger.info(f"[{request_id}] Starting content extraction for {len(sources)} sources")

            # Limit to top sources
            if len(sources) > max_sources:
                logger.info(f"[{request_id}] Limiting from {len(sources)} to {max_sources} sources for content extraction")
                sources = sources[:max_sources]

            # Process sources in batches
            logger.info(f"[{request_id}] Processing {len(sources)} sources in batches")
            processed_sources = await self.content_extractor.process_source_batch(sources, session_id)
            logger.info(f"[{request_id}] Processed {len(processed_sources)} sources")

            # Count sources with content
            sources_with_content = sum(1 for s in processed_sources if "full_content" in s and s["full_content"])
            logger.info(f"[{request_id}] {sources_with_content}/{len(processed_sources)} sources have content")

            # For each source with content, split into chunks and store
            total_chunks = 0
            for source in processed_sources:
                if "full_content" in source and source["full_content"]:
                    # Split content into chunks
                    chunks = self.content_extractor.split_content_into_chunks(source["full_content"])
                    total_chunks += len(chunks)

                    # Store chunks in database
                    if self.db_manager and "id" in source:
                        chunk_ids = await self.db_manager.store_content_chunks(source["id"], chunks)
                        source["chunk_ids"] = chunk_ids
                        logger.info(f"[{request_id}] Stored {len(chunks)} chunks for source '{source.get('title', 'Unknown')[:30]}...'")

            logger.info(f"[{request_id}] Content extraction completed: {sources_with_content} sources with content, {total_chunks} total chunks")

            # Log a sample of the processed sources
            if processed_sources:
                sample_source = next((s for s in processed_sources if "full_content" in s and s["full_content"]), processed_sources[0])
                content_sample = sample_source.get("full_content", "")[:100] + "..." if "full_content" in sample_source else "No content"
                logger.info(f"[{request_id}] Sample source: title='{sample_source.get('title', 'N/A')}', content_length={len(sample_source.get('full_content', ''))}, sample='{content_sample}'")

            return processed_sources

        except Exception as e:
            logger.error(f"Error extracting content: {str(e)}")
            return []

    async def extract_citations(self, sources: List[Dict], session_id: str = None) -> Dict:
        """
        Extract and format citations from the sources.

        Args:
            sources: List of source dictionaries
            session_id: Optional session ID

        Returns:
            Dictionary containing formatted citations
        """
        try:
            request_id = f"cite_{int(datetime.now().timestamp())}"
            logger.info(f"[{request_id}] Extracting citations from {len(sources)} sources")

            # Get the enabled citation style
            from app.services.config import config_service
            citation_style = config_service.get_enabled_citation_style()
            logger.info(f"[{request_id}] Using citation style: {citation_style['name']}")

            # Initialize citations
            citations = {
                "apa": [],
                "mla": [],
                "chicago": [],
                "harvard": []
            }

            # Set the primary citation style
            primary_style = citation_style["name"].lower()
            logger.info(f"[{request_id}] Primary citation style: {primary_style}")

            # Count valid sources
            valid_sources = sum(1 for s in sources if s.get("title") and s.get("url", s.get("link")))
            logger.info(f"[{request_id}] {valid_sources}/{len(sources)} sources have valid title and URL")

            # Process each source
            for i, source in enumerate(sources):
                # Skip sources without enough information
                if not source.get("title") or not source.get("url", source.get("link")):
                    logger.info(f"[{request_id}] Skipping source {i+1}: missing title or URL")
                    continue

                # Get URL (handle different field names)
                url = source.get("url", source.get("link", ""))
                title = source.get("title", "Untitled")
                logger.info(f"[{request_id}] Processing source {i+1}: '{title[:30]}...'")

                # Format citations based on source type
                if source.get("source_type") == "academic_paper":
                    # Academic paper citation
                    authors = source.get("authors", ["Unknown Author"])
                    if isinstance(authors, str):
                        authors = [authors]

                    year = source.get("publication_year", source.get("year", "n.d."))
                    venue = source.get("publication_venue", "Unknown Journal")
                    logger.info(f"[{request_id}] Academic paper: authors={authors}, year={year}, venue={venue}")

                    # APA format
                    apa = f"{', '.join(authors)} ({year}). {title}. {venue}. {url}"
                    citations["apa"].append({
                        "formatted_citation": apa,
                        "in_text_citation": f"({authors[0].split()[-1]}, {year})",
                        "source_id": source.get("id", ""),
                        "source_data": source
                    })

                    # MLA format
                    mla = f"{', '.join(authors)}. \"{title}.\" {venue}, {year}. Web."
                    citations["mla"].append({
                        "formatted_citation": mla,
                        "in_text_citation": f"({authors[0].split()[-1]})",
                        "source_id": source.get("id", ""),
                        "source_data": source
                    })

                    # Chicago format
                    chicago = f"{', '.join(authors)}. \"{title}.\" {venue} ({year})."
                    citations["chicago"].append({
                        "formatted_citation": chicago,
                        "in_text_citation": f"({authors[0].split()[-1]} {year})",
                        "source_id": source.get("id", ""),
                        "source_data": source
                    })

                    # Use the generic citation formatting prompt from the database
                    from app.services.config import config_service
                    prompt_data = config_service.get_prompt("serp_api", "citation_formatting")

                    # Get the enabled citation style
                    citation_style_data = config_service.get_enabled_citation_style()
                    style_name = citation_style_data["name"]
                    style_key = style_name.lower()

                    if prompt_data:
                        try:
                            # Format the citation using the LLM
                            logger.info(f"[{request_id}] Using citation formatting prompt from database: {prompt_data['name']} for {style_name} style")

                            # Prepare the citation data
                            citation_data = {
                                "citation_style": style_name,
                                "title": title,
                                "authors": ', '.join(authors),
                                "publication_year": year,
                                "publication_venue": venue,
                                "url": url,
                                "access_date": datetime.now().strftime('%d %B %Y'),
                                "source_type": "academic_paper"
                            }

                            # Format the prompt
                            citation_prompt = prompt_data["prompt_text"].format(**citation_data)

                            # Call the LLM service to format the citation
                            from app.services.llm import llm_service
                            logger.info(f"[{request_id}] Calling LLM service to format citation for source {i+1}")
                            citation_result = await llm_service.generate_text(
                                prompt=citation_prompt,
                                max_tokens=prompt_data.get("max_tokens", 2000),
                                temperature=prompt_data.get("temperature", 0.3)
                            )
                            logger.info(f"[{request_id}] LLM service returned citation result for source {i+1}")

                            # Parse the JSON response
                            try:
                                import json
                                citation_json = json.loads(citation_result)
                                formatted_citation = citation_json.get("reference_list_entry", "")
                                in_text_citation = citation_json.get("in_text_citation", {}).get("information_prominent", "")
                                logger.info(f"[{request_id}] Successfully parsed citation JSON for source {i+1}")

                                if formatted_citation and in_text_citation:
                                    # Add to the appropriate citation style
                                    citations[style_key].append({
                                        "formatted_citation": formatted_citation,
                                        "in_text_citation": in_text_citation,
                                        "source_id": source.get("id", ""),
                                        "source_data": source
                                    })
                                    logger.info(f"[{request_id}] Added formatted citation for source {i+1} in {style_key} style")

                                    # Skip the fallbacks for this style
                                    continue
                            except Exception as e:
                                logger.error(f"[{request_id}] Error parsing citation JSON for source {i+1}: {str(e)}")
                                # Fall back to the default format
                        except Exception as e:
                            logger.error(f"[{request_id}] Error formatting citation for source {i+1}: {str(e)}")
                            # Fall back to the default format

                    # Fallback to default formats if the LLM formatting failed
                    if style_key == "harvard" and not any(c.get("source_id") == source.get("id", "") for c in citations["harvard"]):
                        harvard = f"{', '.join(authors)} {year}, '{title}', {venue}, viewed {datetime.now().strftime('%d %B %Y')}, <{url}>."
                        citations["harvard"].append({
                            "formatted_citation": harvard,
                            "in_text_citation": f"({authors[0].split()[-1]}, {year})",
                            "source_id": source.get("id", ""),
                            "source_data": source
                        })
                        logger.info(f"[{request_id}] Added fallback Harvard citation for source {i+1}")
                else:
                    # Web page citation
                    logger.info(f"[{request_id}] Web page: title={title}")

                    # Use the generic citation formatting prompt from the database
                    from app.services.config import config_service
                    prompt_data = config_service.get_prompt("serp_api", "citation_formatting")

                    # Get the enabled citation style
                    citation_style_data = config_service.get_enabled_citation_style()
                    style_name = citation_style_data["name"]
                    style_key = style_name.lower()

                    if prompt_data:
                        try:
                            # Format the citation using the LLM
                            logger.info(f"[{request_id}] Using citation formatting prompt from database: {prompt_data['name']} for {style_name} style (web page)")

                            # Prepare the citation data
                            citation_data = {
                                "citation_style": style_name,
                                "title": title,
                                "authors": "Website",
                                "publication_year": datetime.now().strftime('%Y'),
                                "publication_venue": "",
                                "url": url,
                                "access_date": datetime.now().strftime('%d %B %Y'),
                                "source_type": "webpage"
                            }

                            # Format the prompt
                            citation_prompt = prompt_data["prompt_text"].format(**citation_data)

                            # Call the LLM service to format the citation
                            from app.services.llm import llm_service
                            logger.info(f"[{request_id}] Calling LLM service to format web page citation for source {i+1}")
                            citation_result = await llm_service.generate_text(
                                prompt=citation_prompt,
                                max_tokens=prompt_data.get("max_tokens", 2000),
                                temperature=prompt_data.get("temperature", 0.3)
                            )
                            logger.info(f"[{request_id}] LLM service returned web page citation result for source {i+1}")

                            # Parse the JSON response
                            try:
                                import json
                                citation_json = json.loads(citation_result)
                                formatted_citation = citation_json.get("reference_list_entry", "")
                                in_text_citation = citation_json.get("in_text_citation", {}).get("information_prominent", "")
                                logger.info(f"[{request_id}] Successfully parsed web page citation JSON for source {i+1}")

                                if formatted_citation and in_text_citation:
                                    # Add to the appropriate citation style
                                    citations[style_key].append({
                                        "formatted_citation": formatted_citation,
                                        "in_text_citation": in_text_citation,
                                        "source_id": source.get("id", ""),
                                        "source_data": source
                                    })
                                    logger.info(f"[{request_id}] Added formatted web page citation for source {i+1} in {style_key} style")

                                    # Skip the fallbacks
                                    continue
                            except Exception as e:
                                logger.error(f"[{request_id}] Error parsing web page citation JSON for source {i+1}: {str(e)}")
                                # Fall back to the default format
                        except Exception as e:
                            logger.error(f"[{request_id}] Error formatting web page citation for source {i+1}: {str(e)}")
                            # Fall back to the default format

                    # Fallback to default formats if the LLM formatting failed
                    # APA format
                    if style_key == "apa" and not any(c.get("source_id") == source.get("id", "") for c in citations["apa"]):
                        apa = f"{title}. Retrieved from {url}"
                        citations["apa"].append({
                            "formatted_citation": apa,
                            "in_text_citation": f"(\"{title.split()[0]}...\")",
                            "source_id": source.get("id", ""),
                            "source_data": source
                        })
                        logger.info(f"[{request_id}] Added fallback APA citation for web page source {i+1}")

                    # MLA format
                    if style_key == "mla" and not any(c.get("source_id") == source.get("id", "") for c in citations["mla"]):
                        mla = f"\"{title}.\" Web. {datetime.now().strftime('%d %B %Y')}."
                        citations["mla"].append({
                            "formatted_citation": mla,
                            "in_text_citation": f"(\"{title.split()[0]}...\")",
                            "source_id": source.get("id", ""),
                            "source_data": source
                        })
                        logger.info(f"[{request_id}] Added fallback MLA citation for web page source {i+1}")

                    # Chicago format
                    if style_key == "chicago" and not any(c.get("source_id") == source.get("id", "") for c in citations["chicago"]):
                        chicago = f"\"{title}.\" Accessed {datetime.now().strftime('%B %d, %Y')}. {url}."
                        citations["chicago"].append({
                            "formatted_citation": chicago,
                            "in_text_citation": f"(\"{title.split()[0]}...\")",
                            "source_id": source.get("id", ""),
                            "source_data": source
                        })
                        logger.info(f"[{request_id}] Added fallback Chicago citation for web page source {i+1}")

                    # Harvard format
                    if style_key == "harvard" and not any(c.get("source_id") == source.get("id", "") for c in citations["harvard"]):
                        harvard = f"{title} {datetime.now().strftime('%Y')}, viewed {datetime.now().strftime('%d %B %Y')}, <{url}>."
                        citations["harvard"].append({
                            "formatted_citation": harvard,
                            "in_text_citation": f"({title.split()[0]}..., {datetime.now().strftime('%Y')})",
                            "source_id": source.get("id", ""),
                            "source_data": source
                        })
                        logger.info(f"[{request_id}] Added fallback Harvard citation for web page source {i+1}")

            # Count citations by style
            for style, style_citations in citations.items():
                logger.info(f"[{request_id}] Generated {len(style_citations)} citations in {style} style")

            # Store in database if connection exists
            if self.db_manager and session_id:
                source_ids = [source.get("id") for source in sources if "id" in source]
                await self.db_manager.store_citations(source_ids, citations)
                logger.info(f"[{request_id}] Stored citations in database for session {session_id}")

            # Log a sample citation for each style
            for style, style_citations in citations.items():
                if style_citations:
                    sample = style_citations[0]
                    logger.info(f"[{request_id}] Sample {style} citation: formatted='{sample['formatted_citation'][:50]}...', in-text='{sample['in_text_citation']}'")

            logger.info(f"[{request_id}] Citation extraction completed successfully")
            return citations

        except Exception as e:
            logger.error(f"Error extracting citations: {str(e)}")
            return {"error": f"Error during citation extraction: {str(e)}"}

    async def generate_section_plans(self,
                                   topic: str,
                                   research_plan: Dict,
                                   sources: List[Dict],
                                   sections: List[str],
                                   session_id: str = None) -> Dict:
        """
        Generate detailed plans for each section based on the research.

        Args:
            topic: The research topic
            research_plan: The research plan
            sources: The gathered sources
            sections: List of sections to plan
            session_id: Optional session ID to associate with these plans

        Returns:
            Dictionary mapping section names to detailed plans
        """
        try:
            logger.info(f"Generating section plans for topic: {topic}")

            # Initialize section plans
            section_plans = {}

            # For each section, generate a plan
            for section in sections:
                logger.info(f"Generating plan for section: {section}")

                # Get section-specific research if available
                section_research = research_plan.get("section_specific_research", {}).get(section, {})

                # Count sources by type
                source_types = {}
                for source in sources:
                    source_type = source.get("source_type", "unknown")
                    source_types[source_type] = source_types.get(source_type, 0) + 1

                # Prepare planning prompt
                planning_prompt = f"""Create a detailed outline for the "{section}" section of a research pack on the topic: "{topic}"

                Research focus for this section: {section_research.get('focus', f'General information about {topic}')}

                Key concepts to include: {', '.join(section_research.get('key_concepts', ['']))}

                Available sources:
                {json.dumps(source_types)}

                Your outline should:
                1. Be comprehensive and well-structured
                2. Include key points to cover
                3. Reference specific types of sources to cite
                4. Address any relevant questions or perspectives
                5. Be appropriate for academic research

                Format your response as a detailed outline with main points and sub-points.
                """

                # Call OpenRouter API
                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }

                # Get model from configuration service - use planning model for section planning
                try:
                    from app.services.config.config_service import config_service
                    model = config_service.get_config('planning_llm_model', 'google/gemini-2.5-flash-preview')
                    logger.info(f"Using planning model from config: {model}")
                except Exception as e:
                    logger.warning(f"Could not load planning model from config service: {str(e)}")
                    model = "google/gemini-2.5-flash-preview"  # Fallback model
                    logger.info(f"Using fallback planning model: {model}")

                payload = {
                    "model": model,  # Use the model from config
                    "messages": [
                        {"role": "user", "content": planning_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(self.openrouter_endpoint, headers=headers, json=payload) as response:
                        if response.status != 200:
                            logger.error(f"Error from OpenRouter API: Status {response.status}")
                            continue

                        data = await response.json()

                        if "choices" not in data or not data["choices"]:
                            logger.error("No choices in OpenRouter API response")
                            continue

                        plan = data["choices"][0]["message"]["content"].strip()

                # Add to section plans
                section_plans[section] = plan

                # Store in database if connection exists
                if self.db_manager and session_id:
                    await self.db_manager.store_section_plan(session_id, section, plan)

            return section_plans

        except Exception as e:
            logger.error(f"Error generating section plans: {str(e)}")
            return {"error": f"Error during section planning: {str(e)}"}

    async def conduct_research(self,
                             topic: str,
                             questions: List[str] = None,
                             sections: List[str] = None) -> Dict:
        """
        Conduct a complete research process for a topic.

        Args:
            topic: The research topic
            questions: Optional list of specific questions to research
            sections: Optional list of sections to plan

        Returns:
            Dictionary containing all research results
        """
        try:
            # Step 1: Moderate the topic
            is_appropriate, reason = await self.moderate_topic(topic)
            if not is_appropriate:
                return {"error": f"Topic moderation failed: {reason}"}

            # Step 2: Create a research session
            session_id = await self.create_research_session(topic, questions)

            # Step 3: Create a research plan
            research_plan = await self.create_research_plan(topic, questions, session_id)

            # Step 4: Search for sources
            search_results = await self.search_sources(research_plan, session_id)

            # Step 5: Extract content from sources
            sources_with_content = await self.extract_content(search_results.get("academic_sources", []), session_id)

            # Step 6: Extract citations
            citations = await self.extract_citations(sources_with_content, session_id)

            # Get the enabled citation style
            from app.services.config import config_service
            citation_style = config_service.get_enabled_citation_style()
            primary_style = citation_style["name"].lower()

            # Step 7: Generate section plans (if sections provided)
            section_plans = {}
            if sections:
                section_plans = await self.generate_section_plans(topic, research_plan, sources_with_content, sections, session_id)

            # Return all research results
            return {
                "session_id": session_id,
                "topic": topic,
                "questions": questions,
                "is_appropriate": is_appropriate,
                "research_plan": research_plan,
                "sources": sources_with_content,
                "citations": citations,
                "primary_citation_style": primary_style,
                "section_plans": section_plans
            }

        except Exception as e:
            logger.error(f"Error conducting research: {str(e)}")
            return {"error": f"Error during research process: {str(e)}"}

    async def get_section_context(self, session_id: str, section_name: str, citation_style: str = None) -> Dict:
        """
        Get context for generating a section.

        Args:
            session_id: The research session ID
            section_name: The name of the section
            citation_style: The citation style to use (optional, will use enabled style if not provided)

        Returns:
            Dictionary containing context for the section
        """
        try:
            if not self.db_manager:
                return {"error": "No database connection available"}

            # Get the enabled citation style if not provided
            if not citation_style:
                from app.services.config import config_service
                style = config_service.get_enabled_citation_style()
                citation_style = style["name"].lower()

            logger.info(f"Using citation style: {citation_style} for section context")

            # Get section plan
            section_plan = await self.db_manager.get_section_plan(session_id, section_name)

            # Get relevant chunks
            chunks = await self.db_manager.get_relevant_chunks(session_id, section_name)

            # Get citations
            citations = await self.db_manager.get_citations_for_session(session_id, citation_style)

            return {
                "section_plan": section_plan,
                "chunks": chunks,
                "citations": citations,
                "citation_style": citation_style
            }

        except Exception as e:
            logger.error(f"Error getting section context: {str(e)}")
            return {"error": f"Error getting section context: {str(e)}"}
