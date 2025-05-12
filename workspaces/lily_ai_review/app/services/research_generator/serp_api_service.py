"""
SERP API Service Module

Handles interactions with the SERP API for efficient research data gathering.
Optimizes API usage to minimize costs while maximizing research quality.
"""
import os
import json
import logging
import aiohttp
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Setup logging
logger = logging.getLogger(__name__)

class SerpApiService:
    """
    Service for interacting with SERP API efficiently.

    Features:
    - Supports multiple search engines (Google, Google Scholar, Google News, YouTube)
    - Caches results to minimize API calls
    - Optimizes search parameters for academic research
    - Handles rate limiting and error recovery
    """

    def __init__(self, api_key=None, db_connection=None):
        """Initialize the SERP API service."""
        # API key
        self.api_key = api_key or os.getenv("SERP_API_KEY")

        # Database connection
        self.db_connection = db_connection

        # API endpoint
        self.api_endpoint = "https://serpapi.com/search.json"

        # Validate API key
        if not self.api_key:
            logger.warning("No SERP API key provided. Research capabilities will be limited.")

        # Initialize cache
        self.cache = {}
        self.cache_duration = timedelta(hours=72)  # Cache results for 72 hours

        # Default engines (used only if database configuration is unavailable)
        self.available_engines = {}

        # Load engine configuration from database
        asyncio.create_task(self.load_engine_config_from_db())

    async def load_engine_config_from_db(self):
        """Load engine configuration from the database."""
        if not self.db_connection:
            logger.warning("No database connection. Using default engine configuration.")
            # Set minimal default configuration
            self.available_engines = {
                "google_scholar": {
                    "name": "Google Scholar",
                    "enabled": True,
                    "priority": 1,
                    "params": {"gl": "us", "hl": "en"}
                }
            }
            return

        try:
            # Query the saas_serp_api_resources table
            query = """
            SELECT
                engine,
                name,
                description,
                enabled,
                api_parameters,
                priority
            FROM
                saas_serp_api_resources
            ORDER BY
                priority ASC
            """

            result = await self.db_connection.execute(query)
            rows = await result.fetchall()

            if not rows:
                logger.warning("No SERP API resources found in database. Using default configuration.")
                self.available_engines = {
                    "google_scholar": {
                        "name": "Google Scholar",
                        "enabled": True,
                        "priority": 1,
                        "params": {"gl": "us", "hl": "en"}
                    }
                }
                return

            # Update the available engines based on database configuration
            self.available_engines = {}
            for row in rows:
                engine = row['engine']
                self.available_engines[engine] = {
                    "name": row['name'],
                    "enabled": row['enabled'],
                    "priority": row['priority'],
                    "params": row['api_parameters'] or {"gl": "us", "hl": "en"}
                }

            logger.info(f"Loaded SERP API configuration from database: {len(rows)} resources")

        except Exception as e:
            logger.error(f"Error loading engine configuration from database: {str(e)}")
            # Set minimal default configuration
            self.available_engines = {
                "google_scholar": {
                    "name": "Google Scholar",
                    "enabled": True,
                    "priority": 1,
                    "params": {"gl": "us", "hl": "en"}
                }
            }

    async def get_enabled_services(self):
        """
        Get a list of enabled search services from the database.

        Returns:
            List of enabled service dictionaries
        """
        try:
            # Ensure engine configuration is loaded
            if not self.available_engines:
                await self.load_engine_config_from_db()

            # Filter to enabled engines
            enabled_services = []
            for engine, config in self.available_engines.items():
                if config["enabled"]:
                    enabled_services.append({
                        "engine": engine,
                        "name": config["name"],
                        "priority": config["priority"],
                        "params": config["params"]
                    })

            # Sort by priority
            enabled_services.sort(key=lambda s: s["priority"])

            return enabled_services

        except Exception as e:
            logger.error(f"Error getting enabled services: {str(e)}")
            return []

    async def allocate_search_calls(self, research_plan: Dict) -> Dict[str, int]:
        """
        Dynamically allocate search calls across enabled services.

        Args:
            research_plan: The research plan containing search queries

        Returns:
            Dictionary mapping service names to number of allocated calls
        """
        try:
            # Get enabled services
            enabled_services = await self.get_enabled_services()

            if not enabled_services:
                logger.warning("No enabled services found. Using Google Scholar as fallback.")
                return {"google_scholar": 10}  # Fallback to all calls on one service

            num_services = len(enabled_services)
            max_total_calls = 10  # Maximum total calls per paper

            # Calculate base allocation
            base_calls_per_service = max_total_calls // num_services
            remaining_calls = max_total_calls - (base_calls_per_service * num_services)

            # Allocate calls
            allocation = {}
            for service in enabled_services:
                service_name = service["engine"]
                allocation[service_name] = base_calls_per_service

                # Distribute remaining calls to highest priority services
                if remaining_calls > 0:
                    allocation[service_name] += 1
                    remaining_calls -= 1

            logger.info(f"Search call allocation: {allocation}")
            return allocation

        except Exception as e:
            logger.error(f"Error allocating search calls: {str(e)}")
            return {"google_scholar": 5, "google_light": 5}  # Default fallback

    async def search(self,
                   query: str,
                   engine: str = "google_scholar",
                   num_results: int = 100,
                   additional_params: Dict = None) -> Dict:
        """
        Perform a search using SERP API.

        Args:
            query: The search query
            engine: The search engine to use
            num_results: Number of results to request
            additional_params: Additional parameters to include in the request

        Returns:
            Dictionary containing the search results
        """
        try:
            # Ensure engine configuration is loaded
            if not self.available_engines:
                await self.load_engine_config_from_db()

            # Check if engine is available
            if engine not in self.available_engines:
                logger.error(f"Engine {engine} is not available")
                return {"error": f"Engine {engine} is not available"}

            # Check if engine is enabled
            if not self.available_engines[engine]["enabled"]:
                logger.error(f"Engine {engine} is disabled")
                return {"error": f"Engine {engine} is disabled"}

            # Check cache
            cache_key = f"{engine}_{query}_{num_results}_{json.dumps(additional_params or {})}"
            if cache_key in self.cache:
                cache_entry = self.cache[cache_key]
                if datetime.now() - cache_entry["timestamp"] < self.cache_duration:
                    logger.info(f"Using cached results for {engine} search: {query}")
                    return cache_entry["results"]

            logger.info(f"Performing {engine} search for: {query}")

            # Prepare parameters
            params = {
                "engine": engine,
                "q": query,
                "api_key": self.api_key,
                "num": num_results
            }

            # Add specific parameters for Google Scholar to improve academic results
            if engine == "google_scholar":
                params.update({
                    "as_ylo": 2018,  # Articles published since 2018
                    "as_vis": 1,     # Include citations
                    "scisbd": 1,     # Sort by date (recent first)
                    "hl": "en",      # English results
                    "num": min(num_results, 20)  # Google Scholar works better with smaller result sets
                })

            # Add engine-specific parameters
            if engine in self.available_engines:
                params.update(self.available_engines[engine]["params"])

            # Add additional parameters
            if additional_params:
                params.update(additional_params)

            # Make the actual API call
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(self.api_endpoint, params=params, timeout=30) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Error from SERP API: Status {response.status}, Response: {error_text}")
                            return {"error": f"API returned status {response.status}: {error_text[:100]}..."}

                        # Parse the response
                        results = await response.json()

                        # Cache the results
                        self.cache[cache_key] = {
                            "timestamp": datetime.now(),
                            "results": results
                        }

                        return results
                except asyncio.TimeoutError:
                    logger.error(f"Timeout while calling SERP API for {engine} search: {query}")
                    return {"error": "API request timed out"}

        except Exception as e:
            logger.error(f"Error performing {engine} search for {query}: {str(e)}")
            return {"error": f"Error during search: {str(e)}"}

    async def multi_engine_search(self,
                                query: str,
                                engines: List[str] = None,
                                num_results: int = 100,
                                research_plan: Dict = None) -> Dict:
        """
        Perform a search across multiple engines.

        Args:
            query: The search query
            engines: List of engines to use (default: use all enabled engines)
            num_results: Number of results to request per engine
            research_plan: Optional research plan for call allocation

        Returns:
            Dictionary mapping engine names to search results
        """
        try:
            # Ensure engine configuration is loaded
            if not self.available_engines:
                await self.load_engine_config_from_db()

            # If no engines specified, use all enabled engines
            if not engines:
                enabled_services = await self.get_enabled_services()
                engines = [service["engine"] for service in enabled_services]
            else:
                # Filter to enabled engines
                enabled_services = await self.get_enabled_services()
                enabled_engine_names = [service["engine"] for service in enabled_services]
                engines = [e for e in engines if e in enabled_engine_names]

            if not engines:
                logger.warning("No enabled engines found")
                return {"error": "No enabled engines available"}

            # Allocate search calls if research plan is provided
            engine_allocation = None
            if research_plan:
                engine_allocation = await self.allocate_search_calls(research_plan)
                logger.info(f"Using dynamic allocation for search calls: {engine_allocation}")

            logger.info(f"Performing multi-engine search for '{query}' using engines: {engines}")

            # Perform searches in parallel
            tasks = []
            for engine in engines:
                tasks.append(self.search(query, engine, num_results))

            # Wait for all searches to complete
            results = await asyncio.gather(*tasks)

            # Combine results
            combined_results = {}
            for i, engine in enumerate(engines):
                combined_results[engine] = results[i]

            return combined_results

        except Exception as e:
            logger.error(f"Error performing multi-engine search for {query}: {str(e)}")
            return {"error": f"Error during multi-engine search: {str(e)}"}

    async def extract_academic_sources(self, results: Dict) -> List[Dict]:
        """
        Extract academic sources from search results.

        Args:
            results: Dictionary mapping engine names to search results or direct SERP API response

        Returns:
            List of academic sources with metadata
        """
        try:
            academic_sources = []
            request_id = f"serp_{int(datetime.now().timestamp())}"

            # Save the raw response for debugging
            with open('/tmp/serp_response.json', 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"[{request_id}] Saved raw SERP API response to /tmp/serp_response.json")

            # Log the structure of the results for debugging
            logger.info(f"[{request_id}] Results type: {type(results)}")
            if isinstance(results, dict):
                logger.info(f"[{request_id}] Results keys: {list(results.keys())}")

            # Case 1: Direct SERP API response with organic_results at the top level
            if isinstance(results, dict) and "organic_results" in results:
                logger.info(f"[{request_id}] Processing direct SERP API response with {len(results.get('organic_results', []))} results")
                for result in results.get("organic_results", []):
                    # Extract source information
                    source = self._extract_source_from_result(result)
                    if source:
                        academic_sources.append(source)

            # Case 2: Nested structure with engine names as keys
            elif isinstance(results, dict):
                # Process each engine's results
                for engine, engine_results in results.items():
                    logger.info(f"[{request_id}] Processing engine: {engine}, type: {type(engine_results)}")
                    if isinstance(engine_results, dict) and "organic_results" in engine_results:
                        logger.info(f"[{request_id}] Processing {engine} results with {len(engine_results.get('organic_results', []))} items")
                        for result in engine_results.get("organic_results", []):
                            source = self._extract_source_from_result(result)
                            if source:
                                academic_sources.append(source)
                    elif isinstance(engine_results, list):
                        logger.info(f"[{request_id}] Processing {engine} results list with {len(engine_results)} items")
                        for result in engine_results:
                            source = self._extract_source_from_result(result)
                            if source:
                                academic_sources.append(source)

            logger.info(f"[{request_id}] Extracted {len(academic_sources)} academic sources")

            # Log a sample of the extracted sources for debugging
            if academic_sources:
                sample_source = academic_sources[0]
                logger.info(f"[{request_id}] Sample source: title='{sample_source.get('title', 'N/A')}', url='{sample_source.get('url', 'N/A')}', link='{sample_source.get('link', 'N/A')}', year='{sample_source.get('year', 'N/A')}', publication_year='{sample_source.get('publication_year', 'N/A')}'")

                # Check if both url and link fields are present
                url_count = sum(1 for s in academic_sources if 'url' in s)
                link_count = sum(1 for s in academic_sources if 'link' in s)
                logger.info(f"[{request_id}] Sources with url field: {url_count}/{len(academic_sources)}")
                logger.info(f"[{request_id}] Sources with link field: {link_count}/{len(academic_sources)}")

                # Check if both year and publication_year fields are present
                year_count = sum(1 for s in academic_sources if 'year' in s)
                pub_year_count = sum(1 for s in academic_sources if 'publication_year' in s)
                logger.info(f"[{request_id}] Sources with year field: {year_count}/{len(academic_sources)}")
                logger.info(f"[{request_id}] Sources with publication_year field: {pub_year_count}/{len(academic_sources)}")

            return academic_sources

        except Exception as e:
            logger.error(f"[{request_id}] Error extracting academic sources: {str(e)}")
            return []

    def _extract_source_from_result(self, result: Dict) -> Optional[Dict]:
        """
        Extract source information from a single result.

        Args:
            result: A single result from the SERP API

        Returns:
            Source dictionary or None if not a valid source
        """
        try:
            # Skip if no title or link
            if not result.get("title") or not (result.get("link") or result.get("url")):
                return None

            # Extract basic information
            title = result.get("title", "")
            link = result.get("link", result.get("url", ""))
            snippet = result.get("snippet", "")

            # Extract authors and publication info
            authors = []
            publication_year = ""
            publication_venue = ""

            # Extract publication info if available
            publication_info = result.get("publication_info", {})
            if publication_info:
                # Extract authors
                if "authors" in publication_info and isinstance(publication_info["authors"], list):
                    authors = [author.get("name", "") for author in publication_info["authors"] if "name" in author]

                # Extract year and venue from summary
                summary = publication_info.get("summary", "")
                if summary:
                    import re
                    year_match = re.search(r'\b(19|20)\d{2}\b', summary)
                    if year_match:
                        publication_year = year_match.group(0)

                    # Extract publication venue
                    if " - " in summary and "," in summary:
                        try:
                            venue_part = summary.split(" - ")[1].split(",")[0].strip()
                            if venue_part:
                                publication_venue = venue_part
                        except:
                            pass

            # Extract citation count if available
            citations = 0
            if "inline_links" in result and "cited_by" in result["inline_links"]:
                citations = result["inline_links"]["cited_by"].get("total", 0)

            # Create source object
            source = {
                "title": title,
                "link": link,
                "url": link,  # Add url field for compatibility
                "snippet": snippet,
                "source_type": "academic_paper",
                "authors": authors,
                "publication_year": publication_year,
                "year": publication_year,  # Add year field for compatibility
                "publication_venue": publication_venue,
                "citations": citations
            }
            return source

        except Exception as e:
            logger.error(f"Error extracting source from result: {str(e)}")
            return None
