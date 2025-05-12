# Research Pack Architecture

## Overview

The Research Pack Generator is a sophisticated system designed to produce high-quality research packs for students. This document provides a detailed overview of the architecture, components, and workflow of the Research Pack Generator.

## Core Components

### 1. ResearchPackOrchestrator

The ResearchPackOrchestrator is the central coordinator of the entire system. It orchestrates the generation of research packs by coordinating all other components in a specific sequence:

1. **Diagram Generation**: Generates visual aids using the DiagramOrchestrator
2. **Research Planning**: Creates a structured research plan using LLM
3. **SERP API Research**: Gathers academic sources and extracts content
4. **Content Generation**: Produces the main content using LLM
5. **Lily Callout Processing**: Enhances content with contextual callouts
6. **Document Formatting**: Formats the content into a professional document

#### Key Methods:
- `generate_research_pack()`: Main entry point that coordinates the entire process
- `_generate_diagrams()`: Handles diagram generation
- `_generate_content()`: Manages research and content generation
- `_process_with_lily_callout_engine()`: Enhances content with callouts
- `_format_document()`: Creates the final document

### 2. DiagramOrchestrator

The DiagramOrchestrator generates various types of diagrams to enhance the research pack:

- **Mind Maps**: Visual representation of key concepts and relationships
- **Journey Maps**: Visualization of the research journey
- **Argument Maps**: Structured representation of arguments and counterarguments
- **Comparative Analysis**: Visual comparison of different perspectives

#### Process Flow:
1. Receives topic and question from ResearchPackOrchestrator
2. Determines which diagrams to generate based on topic
3. Calls appropriate diagram generators (MindMapGenerator, JourneyMapGenerator, etc.)
4. Returns generated diagrams to ResearchPackOrchestrator

### 3. ResearchGenerator

The ResearchGenerator handles the research process, gathering academic sources and extracting relevant content:

#### Process Flow:
1. **Moderation**: Ensures the topic is appropriate for academic research
2. **Research Planning**: Creates a structured research plan
3. **Source Gathering**: Uses SERP API to search for academic sources
4. **Content Extraction**: Extracts and processes content from sources
5. **Citation Extraction**: Formats citations according to academic standards

#### Key Methods:
- `conduct_research()`: Main method that coordinates the research process
- `create_research_session()`: Creates a session for tracking research
- `search_sources()`: Searches for academic sources using SERP API
- `extract_content()`: Extracts content from sources
- `extract_citations()`: Formats citations according to academic standards

### 4. SerpApiService

The SerpApiService handles interactions with the SERP API for efficient research data gathering:

- Supports multiple search engines (Google Scholar, Google, etc.)
- Optimizes API usage to minimize costs
- Caches results to avoid duplicate requests
- Extracts academic sources from search results

#### Key Methods:
- `search()`: Performs a search using the specified engine
- `allocate_search_calls()`: Allocates search calls across different engines
- `extract_academic_sources()`: Extracts academic sources from search results

### 5. LLMService

The LLMService provides a unified interface for interacting with large language models:

- Supports multiple providers (OpenRouter, Requesty)
- Handles fallback between providers
- Manages different configuration profiles for different use cases
- Provides specialized methods for different content generation tasks

#### Key Methods:
- `generate_content()`: General method for generating content
- `generate_research_plan()`: Specialized method for research planning
- `generate_paper_content()`: Specialized method for paper content generation

### 6. LilyCalloutEngine

The LilyCalloutEngine enhances content with contextual callouts:

- Analyzes content to identify opportunities for enhancement
- Inserts callouts based on content analysis
- Supports different types of callouts (definitions, examples, etc.)
- Maintains academic tone and rigor

### 7. DocumentFormatter

The DocumentFormatter formats the content into a professional document:

- Creates title page with logo
- Formats sections and subsections
- Adds headers and footers with random Lily quotes
- Generates table of contents
- Saves as DOCX and PDF

## Data Flow

### 1. Job Submission
- User submits a research paper request via UI or API
- Request is validated and a job is created in the queue
- Job is assigned a priority and status is set to "queued"

### 2. Job Processing
- Worker polls the queue for jobs
- When a job is found, status is updated to "in_progress"
- Worker calls ResearchPackOrchestrator to generate the research pack
- Progress updates are sent to the database

### 3. Research Process
- ResearchPackOrchestrator initiates diagram generation
- Research plan is created using LLMService
- ResearchGenerator searches for sources using SerpApiService
- Content is extracted from sources
- Citations are formatted according to academic standards

### 4. Content Generation
- LLMService generates content based on research
- Content is structured according to predefined sections
- LilyCalloutEngine enhances content with callouts
- DocumentFormatter creates the final document

### 5. Job Completion
- Document is saved to storage
- Job status is updated to "completed"
- User is notified of completion
- Document URLs are returned to the user

## Current Issues and Improvements

### Issues Identified
1. **SERP API Integration**: The system is making calls to SERP API but not finding any academic sources
2. **Research Plan Utilization**: The research plan is generated but not effectively used to guide the search process
3. **Error Handling**: The system continues even when critical steps fail, producing inferior content
4. **Content Generation Without Research**: When research fails, the system generates boilerplate content

### Planned Improvements
1. **Enhance SERP API Integration**: Improve the search query generation and source extraction
2. **Better Research Plan Utilization**: Use the research plan to generate more targeted search queries
3. **Robust Error Handling**: Implement proper validation and error handling for critical steps
4. **Minimum Quality Thresholds**: Define minimum quality thresholds for research and content generation
