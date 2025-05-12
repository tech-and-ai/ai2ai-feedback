# Lily AI - Research Assistant UK Architectural Design

## System Overview

Research Assistant UK is a SaaS platform powered by Lily AI that helps students with their research by providing comprehensive research packs. The system is designed to be scalable, maintainable, and focused on delivering high-quality research content.

## Core Components

### 1. User Management & Authentication
- **Technology**: Supabase Auth
- **Purpose**: Handle user registration, login, and session management
- **Features**:
  - Email/password authentication
  - Social login options
  - JWT token management
  - User profile management

### 2. Database & Storage
- **Technology**: Supabase PostgreSQL
- **Purpose**: Store all application data in structured tables
- **Key Tables**:
  - `saas_prompts`: Stores prompts used for different contexts
  - `saas_researchpack_sections`: Defines the structure of research packs
  - `saas_lily_callout_types`: Defines the types of callouts Lily can insert
  - `saas_serp_api_resources`: Stores configuration for search API resources

### 3. Research Pack Orchestrator
- **Purpose**: Coordinates the generation of research packs
- **Process Flow**:
  1. Accepts user topic and questions
  2. Initiates diagram generation early in the process
  3. Coordinates content generation for each section
  4. Applies Lily callouts to enhance content
  5. Formats the final research pack

### 4. Content Generator
- **Purpose**: Creates high-quality, well-researched content
- **Features**:
  - Uses OpenRouter to access advanced LLMs
  - Incorporates SERP API for real-time research
  - Generates content based on word count targets
  - Includes proper citations and references

### 5. Lily Callout Engine
- **Purpose**: Enhances content with helpful callouts
- **Features**:
  - Analyzes content to identify appropriate callout opportunities
  - Inserts various callout types (tips, insights, warnings, etc.)
  - Maintains appropriate callout density

### 6. Format Generator
- **Purpose**: Converts generated content into final deliverable format
- **Features**:
  - Creates well-formatted documents
  - Incorporates diagrams
  - Applies consistent styling

### 7. Diagram Generator
- **Purpose**: Creates visual aids to enhance research packs
- **Features**:
  - Generates multiple diagram types (mind maps, flowcharts, etc.)
  - Uses Mermaid syntax for interactive visualizations

### 8. Payment Processing
- **Technology**: Stripe
- **Purpose**: Handle subscription and one-time payments
- **Features**:
  - Monthly subscription management
  - Add-on credit purchases
  - Payment history

## Subscription Model

### Free Tier
- Access to 3 pre-made sample research packs (arts, science, humanities)
- No customization or additional functionality
- Demonstrates service value

### Premium Tier (£20/month)
- 20 custom research packs per month
- Each pack approximately 20-25K words
- Full functionality with personalized questions
- All sections included

### Add-on Credits
- Option to purchase additional research packs beyond the 20/month limit

## Research Pack Structure

1. **Research Pack Introduction**
   - About This Research Pack
   - How to Use This Document
   - Research Journey Map

2. **Personalized Questions & Answers**
   - Direct responses to student-submitted questions
   - Thoroughly researched answers with citations

3. **Comprehensive Topic Analysis**
   - Key Concepts & Definitions
   - Historical Development of the Topic
   - Current State of Research
   - Major Debates & Perspectives

4. **Literature Review & Key Sources**
   - Key Authors & Seminal Works
   - Critical Analysis of Major Publications
   - Direct Quotations from Important Sources
   - Synthesis of Existing Literature

5. **Research Methodology**
   - Common Research Methods in This Field
   - Data Collection Techniques
   - Analysis Frameworks
   - Methodological Debates & Considerations

6. **Evidence & Data Analysis**
   - Key Statistics & Findings
   - Data Interpretation
   - Evidence Evaluation
   - Comparative Analysis of Results

7. **Argument Development**
   - Thesis Development
   - Evidence Integration
   - Counterarguments & Rebuttals
   - Synthesis of Perspectives

8. **Writing Examples & Templates**
   - Introduction Examples
   - Analysis Examples
   - Conclusion Examples
   - Academic Style Guide

9. **Application & Implications**
   - Practical Applications
   - Theoretical Implications
   - Ethical Considerations
   - Future Research Directions

10. **Comprehensive References**
    - Annotated Bibliography
    - Additional Resources
    - Citation Guide

## External Service Integrations

1. **Supabase**
   - Authentication
   - Database
   - Storage

2. **OpenRouter**
   - Access to advanced LLMs for content generation

3. **SERP API**
   - Real-time research capabilities
   - Access to Google Search, Google Scholar, etc.

4. **Stripe**
   - Payment processing
   - Subscription management

5. **Cloudmersive**
   - Document processing

## Ethical Considerations

The system is designed to be an educational tool that provides research guidance while maintaining academic integrity:

- Clear disclaimers about proper use and citation
- Institutional partnerships and enterprise options
- Focus on learning and understanding, not replacing student work
- Comprehensive citations and references

## Deployment

- Hosted on Digital Ocean
- Containerized deployment for scalability
- CI/CD pipeline for automated testing and deployment

## Future Enhancements

1. Institutional API access
2. Enhanced analytics for usage patterns
3. Additional diagram types
4. Expanded search capabilities
5. Mobile application
# Lily AI System Architecture

## Overview

Lily AI is a SaaS platform that helps undergraduates with their studying by generating research packs. The system consists of several key components that work together to provide a seamless experience for users.

## System Components

### 1. Queuing Engine

The Queuing Engine manages the processing of research pack requests. It ensures that premium users' requests are prioritized and that the system can handle multiple requests efficiently.

#### Key Features:
- **Priority-based Queuing**: Jobs are prioritized based on their status and subscription tier
  - Priority 2: Errored jobs that have been resubmitted
  - Priority 3: New jobs
- **Job Status Tracking**: Jobs can be in one of four states:
  - `queued`: Waiting to be processed
  - `in_progress`: Currently being processed
  - `completed`: Successfully completed
  - `errored`: Failed during processing
- **Parallel Processing**: Up to 4 jobs can be processed simultaneously
- **Automatic Retries**: Failed jobs can be resubmitted with higher priority

#### Implementation:
- Supabase PostgreSQL table for job storage
- Queue Manager for job submission and retrieval
- Worker system for processing jobs

### 2. Research Engine

The Research Engine is responsible for generating the content of research packs. It coordinates several sub-components to produce comprehensive research materials.

#### Sub-components:
- **Planning/Research**: Gathers resources and plans the research pack
- **Content Generator**: Generates the main content of the research pack
- **Lily Callout Engine**: Enhances content with contextual callouts
- **Document Formatter**: Formats the content into a professional document
- **Diagram Engine**: Generates visual aids for the research pack

#### Implementation:
- Research Pack Orchestrator coordinates all sub-components
- Integration with external APIs (OpenRouter, SERP API)
- Document generation using python-docx
- PDF conversion using Cloudmersive

### 3. Storage System

The Storage System handles the storage and retrieval of generated research packs and associated files.

#### Key Features:
- **Document Storage**: Stores DOCX and PDF files
- **Metadata Storage**: Stores information about research packs
- **User Access Control**: Ensures users can only access their own files

#### Implementation:
- Supabase Storage for file storage
- Supabase PostgreSQL for metadata storage

### 4. User Interface

The User Interface provides a clean, intuitive way for users to interact with the system.

#### Key Pages:
- **Research Pack Submission**: Simple form for submitting research pack requests
- **My Papers**: View and manage research packs
  - In-progress papers with status indicators
  - Completed papers with download links
  - Simple search functionality

#### Implementation:
- HTML/CSS/JavaScript for frontend
- Integration with backend APIs

## Data Flow

1. **User Submits Request**:
   - User fills out the research pack form
   - Request is submitted to the API
   - Job is created with status `queued` and priority 3

2. **Job Processing**:
   - Worker picks up the job from the queue
   - Job status is updated to `in_progress`
   - Research Engine generates the research pack
   - DOCX and PDF files are created and uploaded to storage
   - Job status is updated to `completed`

3. **Error Handling**:
   - If an error occurs during processing, job status is updated to `errored`
   - User can resubmit the job, which sets priority to 2
   - Resubmitted job is processed before new jobs

4. **User Access**:
   - User can view their in-progress and completed research packs
   - User can download DOCX and PDF files for completed research packs

## Database Schema

### Jobs Table

```sql
CREATE TABLE jobs (
    job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('queued', 'in_progress', 'completed', 'errored')),
    priority SMALLINT NOT NULL DEFAULT 3 CHECK (priority >= 0 AND priority <= 3),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    parameters JSONB NOT NULL,
    result JSONB,
    error_message TEXT,
    worker_id VARCHAR(100),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
);

CREATE INDEX idx_jobs_queue ON jobs (priority, created_at) WHERE status = 'queued';
CREATE INDEX idx_jobs_user ON jobs (user_id, created_at DESC);
CREATE INDEX idx_jobs_status ON jobs (status, updated_at DESC);
```

## Deployment Architecture

The system is deployed on Digital Ocean with the following components:

- **Web Server**: Handles HTTP requests and serves the UI
- **Worker Processes**: Process jobs from the queue
- **Supabase**: Provides database and storage services
- **External APIs**:
  - Cloudmersive for DOCX to PDF conversion
  - OpenRouter for LLM access
  - SERP API for research data

## Future Enhancements

1. **Scalability Improvements**:
   - Increase the number of parallel workers based on system load
   - Implement auto-scaling for worker processes

2. **Feature Enhancements**:
   - Additional diagram types
   - More customization options for research packs
   - Integration with citation management systems

3. **Performance Optimizations**:
   - Caching frequently used research data
   - Optimizing document generation process
