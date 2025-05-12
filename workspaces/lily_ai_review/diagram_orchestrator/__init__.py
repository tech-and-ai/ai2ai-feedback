"""
Diagram Orchestrator Package
Provides a unified interface for generating beautiful diagrams using D3.js and Cloudmersive
"""

from .orchestrator import (
    generate_mind_map,
    generate_mind_map_with_content,
    generate_research_journey_map,
    generate_research_journey_map_with_content,
    generate_research_process_diagram,
    generate_research_process_diagram_with_content,
    generate_argument_map,
    generate_argument_map_with_content,
    generate_custom_diagram
)

__all__ = [
    'generate_mind_map',
    'generate_mind_map_with_content',
    'generate_research_journey_map',
    'generate_research_journey_map_with_content',
    'generate_research_process_diagram',
    'generate_research_process_diagram_with_content',
    'generate_argument_map',
    'generate_argument_map_with_content',
    'generate_custom_diagram'
]
