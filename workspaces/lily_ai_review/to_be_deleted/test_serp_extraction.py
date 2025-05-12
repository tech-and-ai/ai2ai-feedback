#!/usr/bin/env python3
"""
Test script for SERP API source extraction logic.

This script tests the updated extraction logic for handling different SERP API response structures.
It simulates various response formats and validates that our extraction logic correctly handles them.
"""

import json
import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_serp_extraction")

# Sample SERP API response structures
SAMPLE_DIRECT_RESPONSE = {
    "organic_results": [
        {
            "position": 1,
            "title": "The impact of artificial intelligence on education",
            "link": "https://example.com/paper1",
            "snippet": "This paper explores the impact of AI on education systems...",
            "publication_info": {
                "summary": "J Smith, A Johnson - Educational Technology, 2022 - example.com",
                "authors": [
                    {"name": "J Smith"},
                    {"name": "A Johnson"}
                ]
            },
            "inline_links": {
                "cited_by": {
                    "total": 45
                }
            }
        },
        {
            "position": 2,
            "title": "The impact of coffee on health",
            "link": "https://www.thieme-connect.com/products/ejournals/html/10.1055/s-0043-115007",
            "snippet": "... coffee, indicating that besides caffeine other components contribute to the health protecting effects. For adults consuming moderate amounts of coffee (… information about coffee on health…",
            "publication_info": {
                "summary": "K Nieber - Planta medica, 2017 - thieme-connect.com"
            },
            "resources": [
                {
                    "title": "thieme-connect.com",
                    "file_format": "PDF",
                    "link": "https://www.thieme-connect.com/products/ejournals/pdf/10.1055/s-0043-115007.pdf"
                }
            ],
            "inline_links": {
                "serpapi_cite_link": "https://serpapi.com/search.json?engine=google_scholar_cite&hl=en&q=KVT-hW9IrDoJ",
                "cited_by": {
                    "total": 338,
                    "link": "https://scholar.google.com/scholar?cites=4227833794020660265&as_sdt=2005&sciodt=0,5&hl=en",
                    "cites_id": "4227833794020660265",
                    "serpapi_scholar_link": "https://serpapi.com/search.json?as_sdt=2005&cites=4227833794020660265&engine=google_scholar&hl=en"
                }
            }
        }
    ]
}

SAMPLE_NESTED_RESPONSE = {
    "google_scholar": {
        "organic_results": [
            {
                "position": 1,
                "title": "Machine learning applications in education",
                "link": "https://example.org/paper2",
                "snippet": "This study reviews machine learning applications in educational contexts...",
                "publication_info": {
                    "summary": "R Brown, C Davis - Journal of AI in Education, 2021 - example.org",
                    "authors": [
                        {"name": "R Brown"},
                        {"name": "C Davis"}
                    ]
                },
                "inline_links": {
                    "cited_by": {
                        "total": 23
                    }
                }
            }
        ]
    }
}

SAMPLE_LIST_RESPONSE = {
    "google_scholar": [
        {
            "position": 1,
            "title": "AI-powered assessment in higher education",
            "link": "https://example.net/paper3",
            "snippet": "This paper examines the use of AI in assessment practices...",
            "publication_info": {
                "summary": "T Wilson - Educational Assessment, 2020 - example.net"
            },
            "inline_links": {
                "cited_by": {
                    "total": 12
                }
            }
        }
    ]
}

# Updated extraction logic
async def extract_academic_sources(results: Dict) -> List[Dict]:
    """
    Extract academic sources from search results.

    Args:
        results: Dictionary mapping engine names to search results or direct SERP API response

    Returns:
        List of academic sources with metadata
    """
    try:
        academic_sources = []

        # Save the raw response for debugging
        with open('/tmp/serp_response.json', 'w') as f:
            json.dump(results, f, indent=2)

        # Log the structure of the results for debugging
        logger.info(f"Results type: {type(results)}")
        if isinstance(results, dict):
            logger.info(f"Results keys: {list(results.keys())}")
            
        # Case 1: Direct SERP API response with organic_results at the top level
        if isinstance(results, dict) and "organic_results" in results:
            logger.info(f"Processing direct SERP API response with {len(results.get('organic_results', []))} results")
            for result in results.get("organic_results", []):
                # Extract source information
                source = _extract_source_from_result(result)
                if source:
                    academic_sources.append(source)
                    
        # Case 2: Nested structure with engine names as keys
        elif isinstance(results, dict):
            # Process each engine's results
            for engine, engine_results in results.items():
                if isinstance(engine_results, dict) and "organic_results" in engine_results:
                    logger.info(f"Processing {engine} results with {len(engine_results.get('organic_results', []))} items")
                    for result in engine_results.get("organic_results", []):
                        source = _extract_source_from_result(result)
                        if source:
                            academic_sources.append(source)
                elif isinstance(engine_results, list):
                    logger.info(f"Processing {engine} results list with {len(engine_results)} items")
                    for result in engine_results:
                        source = _extract_source_from_result(result)
                        if source:
                            academic_sources.append(source)

        logger.info(f"Extracted {len(academic_sources)} academic sources")
        return academic_sources

    except Exception as e:
        logger.error(f"Error extracting academic sources: {str(e)}")
        return []

def _extract_source_from_result(result: Dict) -> Optional[Dict]:
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

async def test_extraction():
    """Run tests on the extraction logic with different response formats."""
    print("\n=== Testing Direct Response Format ===")
    sources = await extract_academic_sources(SAMPLE_DIRECT_RESPONSE)
    print(f"Extracted {len(sources)} sources from direct response")
    for i, source in enumerate(sources):
        print(f"\nSource {i+1}:")
        print(f"  Title: {source['title']}")
        print(f"  Link: {source['link']}")
        print(f"  Authors: {', '.join(source['authors']) if source['authors'] else 'N/A'}")
        print(f"  Year: {source['year'] or 'N/A'}")
        print(f"  Publication Year: {source['publication_year'] or 'N/A'}")
        print(f"  Citations: {source['citations']}")
    
    print("\n=== Testing Nested Response Format ===")
    sources = await extract_academic_sources(SAMPLE_NESTED_RESPONSE)
    print(f"Extracted {len(sources)} sources from nested response")
    for i, source in enumerate(sources):
        print(f"\nSource {i+1}:")
        print(f"  Title: {source['title']}")
        print(f"  Link: {source['link']}")
        print(f"  Authors: {', '.join(source['authors']) if source['authors'] else 'N/A'}")
        print(f"  Year: {source['year'] or 'N/A'}")
        print(f"  Publication Year: {source['publication_year'] or 'N/A'}")
        print(f"  Citations: {source['citations']}")
    
    print("\n=== Testing List Response Format ===")
    sources = await extract_academic_sources(SAMPLE_LIST_RESPONSE)
    print(f"Extracted {len(sources)} sources from list response")
    for i, source in enumerate(sources):
        print(f"\nSource {i+1}:")
        print(f"  Title: {source['title']}")
        print(f"  Link: {source['link']}")
        print(f"  Authors: {', '.join(source['authors']) if source['authors'] else 'N/A'}")
        print(f"  Year: {source['year'] or 'N/A'}")
        print(f"  Publication Year: {source['publication_year'] or 'N/A'}")
        print(f"  Citations: {source['citations']}")

if __name__ == "__main__":
    asyncio.run(test_extraction())
