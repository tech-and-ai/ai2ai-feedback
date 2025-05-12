# Research Pack Generator

The Research Pack Generator is a powerful tool for creating comprehensive research packs on any topic. It leverages LLMs to generate high-quality academic content, complete with diagrams, citations, and proper formatting.

## Components

1. **Research Pack Orchestrator**: Coordinates the entire research pack generation process
2. **Paper Generator**: Generates the content for the research pack
   - **Content Generator**: Creates the actual content using LLMs
   - **Paper Orchestrator**: Coordinates the paper generation process
   - **Research Service**: Handles research-related functionality
   - **Section Planner**: Plans the sections of the research pack
3. **Document Formatter**: Formats the research pack into a professional document

## Usage

```python
from research_pack.research_pack_orchestrator import ResearchPackOrchestrator

# Initialize the orchestrator
orchestrator = ResearchPackOrchestrator()

# Generate a research pack
research_pack = orchestrator.generate_research_pack(
    topic="Artificial Intelligence Ethics",
    question="What are the key ethical considerations in AI development?",
    user_id="user123"
)

# Get the path to the generated research pack
research_pack_path = research_pack["document_path"]
```

## Requirements

- Python 3.8+
- OpenRouter or Requesty API key for LLM content generation
- Cloudmersive API key for HTML to PNG conversion

## Configuration

Set the following environment variables:

```
OPENROUTER_API_KEY=your_openrouter_api_key
REQUESTY_API_KEY=your_requesty_api_key
CLOUDMERSIVE_API_KEY=your_cloudmersive_api_key
```

## Output

Research packs are saved to the configured output directory and include:
- A professionally formatted document (DOCX)
- Diagrams and visualizations
- Citations and references
- Table of contents
- Executive summary
