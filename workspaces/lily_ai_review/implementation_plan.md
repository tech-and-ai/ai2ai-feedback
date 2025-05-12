# SERP API Integration Fix Implementation Plan

## Overview

This document outlines the implementation plan for fixing the SERP API integration issues in the research pack generation system. The issues involve:

1. The SERP API source extraction not handling different response structures correctly
2. Field name mismatches between the research context and content generation
3. URL/link field inconsistencies in the content extractor

## Test Results Summary

We've created and run test scripts to validate our proposed solutions:

1. **SERP API Extraction Test**: Successfully extracted academic sources from different response formats (direct, nested, and list)
2. **Content Extractor Test**: Successfully handled different field names (url vs link) in source dictionaries
3. **Research Context Test**: Successfully fixed the field mapping issue in content generation

## Implementation Steps

### 1. Update `serp_api_service.py`

#### File: `app/services/research_generator/serp_api_service.py`

1. Modify the `extract_academic_sources` method to handle different response structures:
   - Direct SERP API response with `organic_results` at the top level
   - Nested structure with engine names as keys
   - List structure for engine results

2. Extract the source extraction logic into a separate helper method `_extract_source_from_result`

3. Ensure both `url` and `link` fields are included in the extracted sources

4. Add both `publication_year` and `year` fields with the same value for compatibility

### 2. Update `ResearchPackOrchestrator.py`

#### File: `research_pack/ResearchPackOrchestrator.py`

1. Modify the `_generate_content` method to use `publication_year` instead of `year` when creating the research context for the content prompt

2. Alternatively, ensure both fields are available in the research context

### 3. Update `content_extractor.py`

#### File: `app/services/research_generator/content_extractor.py`

1. Modify the `process_source_batch` method to handle both `url` and `link` fields consistently

2. Ensure both fields are added to the source dictionary for compatibility

## Code Changes

### 1. Update to `serp_api_service.py`

```python
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
                source = self._extract_source_from_result(result)
                if source:
                    academic_sources.append(source)
                    
        # Case 2: Nested structure with engine names as keys
        elif isinstance(results, dict):
            # Process each engine's results
            for engine, engine_results in results.items():
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
```

### 2. Update to `ResearchPackOrchestrator.py`

```python
# Add research context if available
if research_context:
    content_prompt += f"""

    Use the following research sources in your paper:

    Sources:
    {json.dumps([{
        "title": source.get("title", ""),
        "authors": source.get("authors", []),
        "year": source.get("publication_year", ""),  # Use publication_year as year
        "summary": source.get("snippet", "")
    } for source in research_context["sources"][:10]], indent=2)}

    Citations:
    {json.dumps(research_context["citations"].get(research_context["primary_citation_style"], [])[:10], indent=2)}
    """
```

### 3. Update to `content_extractor.py`

```python
async def process_source_batch(self, sources: List[Dict], session_id: str = None) -> List[Dict]:
    """
    Process a batch of sources by extracting their content.

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
            logger.warning(f"Source has no URL or link: {source.get('title', 'Unknown')}")

    logger.info(f"Extracting content from {len(tasks)} sources")

    # Process in parallel with rate limiting
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
```

## Testing Plan

1. Make the code changes as outlined above
2. Restart the server
3. Submit a test job with the topic "The impact of artificial intelligence on education"
4. Monitor the logs to verify:
   - Academic sources are being extracted correctly
   - Content is being generated with proper citations
   - The document is being formatted correctly
5. Examine the generated document to ensure it includes academic sources and citations

## Rollback Plan

If issues arise after implementation:

1. Revert the changes to the original files
2. Restart the server
3. Test with a simple job to ensure the system is functioning as before

## Conclusion

This implementation plan addresses the identified issues with the SERP API integration and should result in a properly functioning research pack generation system. The test scripts have validated the proposed solutions, and the code changes are minimal and focused on the specific issues.
