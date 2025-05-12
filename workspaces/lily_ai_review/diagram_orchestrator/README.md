# Diagram Orchestrator

The Diagram Orchestrator is a powerful tool for generating beautiful, interactive diagrams for research papers, presentations, and documentation.

## Features

- **Multiple Diagram Types**: Generate mind maps, journey maps, question breakdowns, argument mappings, and comparative analyses
- **AI-Powered Content**: Uses LLMs to generate intelligent diagram content
- **Interactive Visualizations**: Creates interactive HTML diagrams with D3.js and JSMind
- **PNG Export**: Converts HTML diagrams to PNG images for inclusion in documents

## Diagram Types

1. **Mind Maps**: Visualize concepts and their relationships
2. **Journey Maps**: Illustrate research or learning journeys
3. **Question Breakdowns**: Break down complex questions into manageable parts
4. **Argument Mappings**: Map out arguments, counterarguments, and evidence
5. **Comparative Analyses**: Compare and contrast different concepts or approaches

## Usage

```python
from diagram_orchestrator.orchestrator import generate_mind_map, generate_journey_map, generate_question_breakdown, generate_argument_mapping, generate_comparative_analysis

# Generate a mind map
mind_map_path = generate_mind_map("Artificial Intelligence Ethics")

# Generate a journey map
journey_map_path = generate_journey_map("Machine Learning Research Process")

# Generate a question breakdown
question_breakdown_path = generate_question_breakdown("How does climate change affect biodiversity?")

# Generate an argument mapping
argument_mapping_path = generate_argument_mapping("Should AI systems be regulated?")

# Generate a comparative analysis
comparative_analysis_path = generate_comparative_analysis("Supervised vs. Unsupervised Learning")
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

Diagrams are saved to the configured output directory (default: `/home/admin/projects/lily_ai/static/generated_diagrams`).
