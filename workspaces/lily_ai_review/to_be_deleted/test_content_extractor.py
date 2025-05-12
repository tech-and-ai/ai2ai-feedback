#!/usr/bin/env python3
"""
Test script for Content Extractor URL/link field handling.

This script tests the updated content extractor logic for handling different field names
in source dictionaries (url vs link).
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_content_extractor")

# Sample sources with different field structures
SAMPLE_SOURCES = [
    {
        "title": "Source with URL field",
        "url": "https://example.com/paper1",
        "snippet": "This is a sample paper with the URL field."
    },
    {
        "title": "Source with Link field",
        "link": "https://example.com/paper2",
        "snippet": "This is a sample paper with the Link field."
    },
    {
        "title": "Source with both fields",
        "url": "https://example.com/paper3a",
        "link": "https://example.com/paper3b",
        "snippet": "This is a sample paper with both URL and Link fields."
    },
    {
        "title": "Source with no URL or Link",
        "snippet": "This is a sample paper with no URL or Link field."
    }
]

class MockContentExtractor:
    """Mock content extractor for testing URL/link field handling."""
    
    async def extract_content(self, url: str, session_id: str = None) -> Dict:
        """Mock content extraction that returns success for any URL."""
        logger.info(f"Extracting content from: {url}")
        return {
            "url": url,
            "extraction_success": True,
            "content": f"Mock content for {url}",
            "content_type": "text/html",
            "extraction_method": "mock",
            "extraction_duration_ms": 100,
            "content_length": 100
        }
    
    async def process_source_batch(self, sources: List[Dict], session_id: str = None) -> List[Dict]:
        """
        Process a batch of sources by extracting their content.
        This is the updated version that handles both url and link fields.

        Args:
            sources: List of source dictionaries with URLs (either as "url" or "link")
            session_id: Optional session ID to associate with these extractions

        Returns:
            List of sources with extracted content
        """
        tasks = []
        source_urls = []

        for source in sources:
            # Get URL (handle different field names: url or link)
            url = source.get("url", source.get("link", None))
            if url:
                tasks.append(self.extract_content(url, session_id))
                source_urls.append(url)
                # Add both url and link fields for compatibility
                source["url"] = url
                source["link"] = url
            else:
                logger.warning(f"Source has no URL or link: {source['title']}")

        logger.info(f"Extracting content from {len(tasks)} sources")

        # Process in parallel
        if tasks:
            results = await asyncio.gather(*tasks)

            # Combine results with sources
            for i, source in enumerate(sources):
                url = source.get("url", source.get("link", None))
                if url and url in source_urls:
                    # Find the corresponding result
                    result_index = source_urls.index(url)
                    if result_index < len(results) and results[result_index]["extraction_success"]:
                        source["full_content"] = results[result_index].get("content", "")
                        source["extraction_metadata"] = {
                            "content_type": results[result_index].get("content_type", ""),
                            "extraction_method": results[result_index].get("extraction_method", ""),
                            "extraction_duration_ms": results[result_index].get("extraction_duration_ms", 0),
                            "content_length": results[result_index].get("content_length", 0)
                        }
                        logger.info(f"Successfully extracted content from {url} ({results[result_index].get('content_length', 0)} characters)")
                    else:
                        logger.warning(f"Failed to extract content from {url}")
        else:
            logger.warning("No valid URLs found in sources")

        return sources

async def test_content_extractor():
    """Test the content extractor with different source structures."""
    extractor = MockContentExtractor()
    
    print("\n=== Testing Content Extractor URL/Link Handling ===")
    processed_sources = await extractor.process_source_batch(SAMPLE_SOURCES)
    
    print(f"\nProcessed {len(processed_sources)} sources:")
    for i, source in enumerate(processed_sources):
        print(f"\nSource {i+1}: {source['title']}")
        print(f"  URL field: {source.get('url', 'N/A')}")
        print(f"  Link field: {source.get('link', 'N/A')}")
        print(f"  Has content: {'Yes' if 'full_content' in source else 'No'}")
        if 'full_content' in source:
            print(f"  Content: {source['full_content']}")
            print(f"  Metadata: {source.get('extraction_metadata', {})}")

if __name__ == "__main__":
    asyncio.run(test_content_extractor())
