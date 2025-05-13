"""
Search Service

This module provides search functionality for research.
"""

import logging
import aiohttp
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class SearchService:
    """Search service class."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the search service.
        
        Args:
            config: Service configuration
        """
        self.provider = config.get('provider', 'duckduckgo')
        self.timeout = config.get('timeout', 30)
        logger.info(f"Initialized search service with provider: {self.provider}")
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for information.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        if self.provider == 'duckduckgo':
            return await self._search_duckduckgo(query, num_results)
        else:
            logger.warning(f"Unknown search provider: {self.provider}")
            return []
    
    async def _search_duckduckgo(self, query: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search using DuckDuckGo.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results
        """
        url = "https://api.duckduckgo.com/"
        
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error searching DuckDuckGo: {error_text}")
                        return []
                    
                    result = await response.json()
                    
                    # Extract results
                    results = []
                    
                    # Add abstract if available
                    if result.get('Abstract'):
                        results.append({
                            'title': result.get('Heading', 'Abstract'),
                            'url': result.get('AbstractURL', ''),
                            'snippet': result.get('Abstract', '')
                        })
                    
                    # Add related topics
                    for topic in result.get('RelatedTopics', [])[:num_results - len(results)]:
                        if 'Text' in topic and 'FirstURL' in topic:
                            results.append({
                                'title': topic.get('Text', '').split(' - ')[0],
                                'url': topic.get('FirstURL', ''),
                                'snippet': topic.get('Text', '')
                            })
                    
                    return results[:num_results]
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            return []

class ContentExtractor:
    """Content extractor class."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the content extractor.
        
        Args:
            config: Service configuration
        """
        self.timeout = config.get('timeout', 30)
        logger.info("Initialized content extractor")
    
    async def extract_content(self, url: str) -> str:
        """
        Extract content from a URL.
        
        Args:
            url: URL to extract content from
            
        Returns:
            Extracted content
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error extracting content: {error_text}")
                        return ""
                    
                    html = await response.text()
                    
                    # Simple HTML content extraction
                    # In a real implementation, use a proper HTML parser
                    import re
                    
                    # Remove HTML tags
                    text = re.sub(r'<[^>]+>', ' ', html)
                    
                    # Remove extra whitespace
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    return text
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            return ""

class ResearchService:
    """Research service class."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the research service.
        
        Args:
            config: Service configuration
        """
        self.search_service = SearchService(config.get('search', {}))
        self.content_extractor = ContentExtractor(config.get('extractor', {}))
        logger.info("Initialized research service")
    
    async def research(self, query: str, num_results: int = 5, extract_content: bool = False) -> Dict[str, Any]:
        """
        Research a query.
        
        Args:
            query: Research query
            num_results: Number of results to return
            extract_content: Whether to extract content from URLs
            
        Returns:
            Research results
        """
        # Search for information
        search_results = await self.search_service.search(query, num_results)
        
        # Extract content if requested
        if extract_content:
            for result in search_results:
                if result.get('url'):
                    content = await self.content_extractor.extract_content(result['url'])
                    result['content'] = content
        
        return {
            'query': query,
            'results': search_results
        }
