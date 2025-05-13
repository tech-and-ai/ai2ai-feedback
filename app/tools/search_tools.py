"""
Search tools for autonomous agents

This module provides tools for agents to search the internet for information.
"""

import logging
import requests
from typing import Dict, List, Optional, Any, Tuple
import json
import time

# Configure logging
logger = logging.getLogger("agent-tools")

class SearchTools:
    """Tools for searching the internet"""
    
    @staticmethod
    def duckduckgo_search(query: str, num_results: int = 5) -> Tuple[bool, List[Dict[str, str]]]:
        """
        Search the internet using DuckDuckGo
        
        Args:
            query: Search query
            num_results: Number of results to return (default: 5)
            
        Returns:
            Tuple[bool, List[Dict]]: (Success, List of search results)
        """
        try:
            # Use the DuckDuckGo API
            url = "https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': 1,
                'skip_disambig': 1
            }
            
            logger.info(f"Searching DuckDuckGo for: {query}")
            response = requests.get(url, params=params)
            
            if response.status_code != 200:
                logger.error(f"DuckDuckGo search failed with status code: {response.status_code}")
                return False, []
            
            data = response.json()
            
            # Extract results
            results = []
            
            # Add the abstract if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('Heading', 'Abstract'),
                    'snippet': data.get('Abstract'),
                    'url': data.get('AbstractURL', '')
                })
            
            # Add related topics
            for topic in data.get('RelatedTopics', [])[:num_results]:
                if 'Text' in topic and 'FirstURL' in topic:
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0] if ' - ' in topic.get('Text', '') else topic.get('Text', ''),
                        'snippet': topic.get('Text', ''),
                        'url': topic.get('FirstURL', '')
                    })
                    
            # If we still need more results and have an API answer
            if len(results) < num_results and data.get('Answer'):
                results.append({
                    'title': 'Direct Answer',
                    'snippet': data.get('Answer'),
                    'url': data.get('AnswerURL', '')
                })
                
            # Limit to requested number of results
            results = results[:num_results]
            
            if not results:
                logger.warning(f"No results found for query: {query}")
                
            return True, results
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")
            return False, []
    
    @staticmethod
    def fetch_webpage_content(url: str) -> Tuple[bool, str]:
        """
        Fetch the content of a webpage
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple[bool, str]: (Success, Content or error message)
        """
        try:
            logger.info(f"Fetching webpage content from: {url}")
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch webpage with status code: {response.status_code}")
                return False, f"Failed to fetch webpage. Status code: {response.status_code}"
            
            return True, response.text
        except Exception as e:
            logger.error(f"Error fetching webpage: {e}")
            return False, f"Error fetching webpage: {str(e)}"
