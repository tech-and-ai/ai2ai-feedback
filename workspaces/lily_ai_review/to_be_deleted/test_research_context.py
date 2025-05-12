#!/usr/bin/env python3
"""
Test script for research context field mapping in content generation.

This script tests the updated field mapping logic for the research context
in the content generation process.
"""

import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_research_context")

# Sample research context with academic sources
SAMPLE_RESEARCH_CONTEXT = {
    "sources": [
        {
            "title": "The impact of artificial intelligence on education",
            "link": "https://example.com/paper1",
            "snippet": "This paper explores the impact of AI on education systems...",
            "authors": ["J Smith", "A Johnson"],
            "publication_year": "2022",
            "publication_venue": "Educational Technology",
            "citations": 45
        },
        {
            "title": "Machine learning applications in education",
            "link": "https://example.org/paper2",
            "snippet": "This study reviews machine learning applications in educational contexts...",
            "authors": ["R Brown", "C Davis"],
            "publication_year": "2021",
            "publication_venue": "Journal of AI in Education",
            "citations": 23
        }
    ],
    "citations": {
        "harvard": [
            "Smith, J. and Johnson, A. (2022) 'The impact of artificial intelligence on education', Educational Technology, 45(2), pp. 123-145.",
            "Brown, R. and Davis, C. (2021) 'Machine learning applications in education', Journal of AI in Education, 12(3), pp. 78-92."
        ]
    },
    "primary_citation_style": "harvard"
}

def generate_content_prompt_original(topic: str, research_context: dict = None) -> str:
    """
    Generate a content prompt with the original field mapping logic.
    
    Args:
        topic: The research topic
        research_context: Optional research context with sources and citations
        
    Returns:
        The content prompt
    """
    content_prompt = f"""
    Generate a comprehensive research paper on the topic: {topic}
    
    The paper should be academically rigorous and well-structured.
    """
    
    # Add research context if available
    if research_context:
        content_prompt += f"""

        Use the following research sources in your paper:

        Sources:
        {json.dumps([{
            "title": source.get("title", ""),
            "authors": source.get("authors", []),
            "year": source.get("year", ""),  # Using 'year' instead of 'publication_year'
            "summary": source.get("snippet", "")
        } for source in research_context["sources"][:10]], indent=2)}

        Citations:
        {json.dumps(research_context["citations"].get(research_context["primary_citation_style"], [])[:10], indent=2)}
        """
    
    return content_prompt

def generate_content_prompt_fixed(topic: str, research_context: dict = None) -> str:
    """
    Generate a content prompt with the fixed field mapping logic.
    
    Args:
        topic: The research topic
        research_context: Optional research context with sources and citations
        
    Returns:
        The content prompt
    """
    content_prompt = f"""
    Generate a comprehensive research paper on the topic: {topic}
    
    The paper should be academically rigorous and well-structured.
    """
    
    # Add research context if available
    if research_context:
        content_prompt += f"""

        Use the following research sources in your paper:

        Sources:
        {json.dumps([{
            "title": source.get("title", ""),
            "authors": source.get("authors", []),
            "year": source.get("publication_year", ""),  # Using 'publication_year' directly
            "summary": source.get("snippet", "")
        } for source in research_context["sources"][:10]], indent=2)}

        Citations:
        {json.dumps(research_context["citations"].get(research_context["primary_citation_style"], [])[:10], indent=2)}
        """
    
    return content_prompt

def test_research_context_mapping():
    """Test the research context field mapping in content generation."""
    topic = "The impact of artificial intelligence on education"
    
    print("\n=== Testing Research Context Field Mapping ===")
    
    # Test original prompt generation (with the bug)
    original_prompt = generate_content_prompt_original(topic, SAMPLE_RESEARCH_CONTEXT)
    print("\nORIGINAL PROMPT (with bug):")
    print(original_prompt)
    
    # Check if years are missing in the original prompt
    if '"year": ""' in original_prompt:
        print("\n⚠️ BUG DETECTED: Years are missing in the original prompt because it's looking for 'year' instead of 'publication_year'")
    
    # Test fixed prompt generation
    fixed_prompt = generate_content_prompt_fixed(topic, SAMPLE_RESEARCH_CONTEXT)
    print("\nFIXED PROMPT:")
    print(fixed_prompt)
    
    # Check if years are present in the fixed prompt
    if '"year": "2022"' in fixed_prompt and '"year": "2021"' in fixed_prompt:
        print("\n✅ FIX VERIFIED: Years are correctly included in the fixed prompt")
    else:
        print("\n❌ FIX FAILED: Years are still missing in the fixed prompt")

if __name__ == "__main__":
    test_research_context_mapping()
