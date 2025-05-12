# Document Formatter

This module handles the formatting of research packs into well-structured documents.

## Features

- Professional title page
- Table of contents with proper page numbers
- Consistent section numbering
- Headers and footers
- Support for Lily callout boxes
- Figure and diagram integration

## Usage

```python
from document_formatter import DocumentFormatter

# Create a formatter
formatter = DocumentFormatter()

# Format a research pack
document = formatter.format_research_pack(research_pack)

# Save the document
formatter.save_document("output/research_pack.docx")
```

## Research Pack Structure

The document formatter expects a research pack with the following structure:

```python
research_pack = {
    "title": "Research Pack Title",
    "author": "Author Name",
    "date_generated": "May 5, 2025",
    "sections": {
        # Section 1: Introduction (500-750 words)
        "introduction": {
            "overview": "Overview of the research topic...",
            "key_questions": "Key questions to be addressed...",
            # Other introduction subsections or a single string for the entire section
        },

        # Section 2: Topic Analysis (5000-7000 words)
        "topic_analysis": {
            "key_concepts": "Key concepts content...",
            "theoretical_frameworks": "Theoretical frameworks...",
            "literature_review": "Comprehensive literature review...",
            # Other topic analysis subsections or a single string for the entire section
        },

        # Section 3: Methodological Approaches (3000-4000 words)
        "methodological_approaches": {
            "research_methods": "Research methods content...",
            "data_collection": "Data collection techniques...",
            "analytical_frameworks": "Analytical frameworks...",
            # Other methodology subsections or a single string for the entire section
        },

        # Section 4: Key Arguments (5000-7000 words)
        "key_arguments": {
            "main_arguments": "Main arguments content...",
            "counterarguments": "Counterarguments and rebuttals...",
            "evidence_analysis": "Evidence analysis...",
            "practical_applications": "Practical applications...",
            # Other arguments subsections or a single string for the entire section
        },

        # Section 5: Citations and Resources (1000-2000 words)
        "citations_resources": {
            "annotated_bibliography": "Annotated bibliography...",
            "book_recommendations": "Book recommendations...",
            "citation_examples": "Citation examples in appropriate format...",
            # Other citations subsections or a single string for the entire section
        }
    },

    # Diagrams - automatically placed in appropriate sections based on type
    "diagrams": [
        {
            "path": "/path/to/mind_map.png",
            "caption": "Topic Analysis Mind Map",
            "type": "mind_map"  # Will be placed in Topic Analysis section
        },
        {
            "path": "/path/to/process_flow.png",
            "caption": "Research Methodology Process Flow",
            "type": "process_flow"  # Will be placed in Methodological Approaches section
        },
        {
            "path": "/path/to/comparative_analysis.png",
            "caption": "Comparative Analysis of Key Arguments",
            "type": "comparative_analysis"  # Will be placed in Key Arguments section
        },
        {
            "path": "/path/to/other_diagram.png",
            "caption": "Additional Diagram",
            "type": "general"  # Will be placed in Additional Diagrams section
        }
    ]
}
```

## Lily Callouts

The document formatter supports Lily callouts in the content. Callouts should be formatted as follows:

```
[[LILY_CALLOUT type="tip" title="Research Tip"]]
This is a research tip from Lily.
[[/LILY_CALLOUT]]
```

Supported callout types:
- tip
- insight
- question
- warning
- confidence
- brainstorm
- research
- guidance
- reflection
- connection
- example
- definition
- caution

## Testing

Run the test script to verify the document formatter:

```bash
python test_formatter.py
```

This will create a sample research pack and format it into a document in the `output` directory.
