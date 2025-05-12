# Lily AI System Architecture

## Overview

Lily AI is a comprehensive research assistant platform that generates high-quality research packs for students. The system follows a modular architecture with several key components working together to produce academically rigorous content. This document provides a detailed overview of the system architecture, component interactions, and data flow.

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
- `create_research_plan()`: Generates a structured research plan
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

## API Endpoints

### UI Endpoint
- **Route**: `/api/research-paper/generate`
- **Purpose**: Used by the UI for research paper generation
- **Authentication**: Uses session-based authentication
- **Credit Handling**: Checks and decrements user credits

### Direct API Endpoint
- **Route**: `/api/direct/research-paper/generate`
- **Purpose**: Used for direct API access (enterprise)
- **Authentication**: Uses API key authentication
- **Credit Handling**: Bypasses credit checks

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

## Error Handling

### Critical Failures
- If any critical step fails (research, content generation), the process should fail gracefully
- Job status is updated to "errored" with appropriate error message
- User is notified of failure
- No inferior product is delivered to the user

### Retryable Failures
- SERP API errors are retried up to 3 times
- If retry limit is reached, job is marked as "errored"
- Temporary network issues are handled with exponential backoff

## Database Schema

### Key Tables
- `saas_job_tracking`: Tracks job status and progress
- `saas_prompts`: Stores prompts for different contexts
- `saas_researchpack_sections`: Defines the structure of research packs
- `saas_lily_callout_types`: Defines the types of callouts Lily can insert
- `saas_serp_api_resources`: Stores configuration for search API resources

## Deployment Architecture

### Components
- **Web Server**: Handles HTTP requests and serves the UI
- **Worker Process**: Processes jobs from the queue
- **Database**: Stores application data
- **Storage**: Stores generated documents

### Scaling
- Multiple worker processes can be deployed to handle increased load
- Workers can be distributed across multiple servers
- Database and storage can be scaled independently
