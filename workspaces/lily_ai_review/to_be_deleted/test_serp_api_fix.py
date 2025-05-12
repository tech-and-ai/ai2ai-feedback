#!/usr/bin/env python3
"""
Test script to verify our SERP API integration fixes.

This script:
1. Loads the SERP API response from /tmp/serp_response.json
2. Calls our updated extract_academic_sources method
3. Prints the extracted sources
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SerpApiTester:
    """Test class for SERP API integration."""

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

            # Log the structure of the results for debugging
            logger.info(f"Results type: {type(results)}")
            if isinstance(results, dict):
                logger.info(f"Results keys: {list(results.keys())}")
                
            # Case 1: Direct SERP API response with organic_results at the top level
            if isinstance(results, dict) and "organic_results" in results:
                logger.info(f"Processing direct SERP API response with {len(results.get('organic_results', []))} results")
                for result in results.get("organic_results", []):
                    # Extract source information
                    source = self._extract_source_from_result(result)
                    if source:
                        academic_sources.append(source)
                        
            # Case 2: Nested structure with engine names as keys
            elif isinstance(results, dict):
                # Process each engine's results
                for engine, engine_results in results.items():
                    logger.info(f"Processing engine: {engine}, type: {type(engine_results)}")
                    if isinstance(engine_results, dict) and "organic_results" in engine_results:
                        logger.info(f"Processing {engine} results with {len(engine_results.get('organic_results', []))} items")
                        for result in engine_results.get("organic_results", []):
                            source = self._extract_source_from_result(result)
                            if source:
                                academic_sources.append(source)
                    elif isinstance(engine_results, list):
                        logger.info(f"Processing {engine} results list with {len(engine_results)} items")
                        for result in engine_results:
                            source = self._extract_source_from_result(result)
                            if source:
                                academic_sources.append(source)

            logger.info(f"Extracted {len(academic_sources)} academic sources")
            return academic_sources

        except Exception as e:
            logger.error(f"Error extracting academic sources: {str(e)}")
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

async def main():
    """Main function to test SERP API integration."""
    try:
        # Load the SERP API response from /tmp/serp_response.json
        with open('/tmp/serp_response.json', 'r') as f:
            serp_response = json.load(f)
        
        # Create a tester instance
        tester = SerpApiTester()
        
        # Extract academic sources
        sources = await tester.extract_academic_sources(serp_response)
        
        # Print the extracted sources
        print(f"\nExtracted {len(sources)} academic sources:")
        for i, source in enumerate(sources[:5]):  # Print first 5 sources
            print(f"\nSource {i+1}:")
            print(f"  Title: {source['title']}")
            print(f"  Link: {source['link']}")
            print(f"  URL: {source['url']}")
            print(f"  Authors: {source['authors']}")
            print(f"  Year: {source['year']}")
            print(f"  Publication Year: {source['publication_year']}")
            
        # Check if both url and link fields are present
        url_count = sum(1 for s in sources if 'url' in s)
        link_count = sum(1 for s in sources if 'link' in s)
        print(f"\nSources with url field: {url_count}/{len(sources)}")
        print(f"Sources with link field: {link_count}/{len(sources)}")
        
        # Check if both year and publication_year fields are present
        year_count = sum(1 for s in sources if 'year' in s)
        pub_year_count = sum(1 for s in sources if 'publication_year' in s)
        print(f"Sources with year field: {year_count}/{len(sources)}")
        print(f"Sources with publication_year field: {pub_year_count}/{len(sources)}")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
