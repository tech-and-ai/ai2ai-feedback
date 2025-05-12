# URGENT README FIRST

## Application Overview

This application generates research papers based on user input. It has two API endpoints: one for UI requests and another for direct enterprise API access. Both use the same core functionality but handle authentication and credit checks differently.

## API Routes

### UI API Route

The main API route is used by the UI and handles credit checks and usage tracking:

```
/api/research-paper/generate
```

### Enterprise API Route

A separate enterprise API route is available for direct API access:

```
/api/direct/research-paper/generate
```

This enterprise route:
- Bypasses credit checks
- Doesn't increment usage counters
- Returns JSON responses instead of redirects
- Requires API key authentication

### API Authentication

For enterprise API access, use the admin API key from the .env file:

```bash
curl -X POST https://your-app-url.com/api/direct/research-paper/generate \
  -H "Authorization: Bearer lily_api_key_55b4ec8c2cf540fe871875fe45f49a69" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Artificial Intelligence Ethics",
    "education_level": "postgraduate",
    "include_diagrams": true,
    "key_points": ["Impact on society", "Regulatory frameworks"]
  }'
```

### Checking Job Status

You can check the status of a job using:

```bash
curl -X GET https://your-app-url.com/api/direct/research-paper/status/{job_id} \
  -H "Authorization: Bearer lily_api_key_55b4ec8c2cf540fe871875fe45f49a69"
```

This approach:
- Uses a simple API key authentication
- Avoids the complexity of JWT tokens
- Provides admin-level access for API calls
- Returns JSON responses for easy integration

## Application Flow

### 1. User Request
- User submits a request with:
  - Topic
  - Question/prompt
  - Education level
  - Other parameters

### 2. API Endpoint (`/api/research-paper/generate`)
- Receives the request
- Validates user permissions
- Submits a job to the queue
- Returns a job ID to the user

### 3. Queue Manager
- Stores the job in the database
- Makes it available for processing by workers

### 4. Worker Process
- Worker polls the queue for new jobs
- When a job is found, it's assigned to the worker
- The worker initializes the ResearchPackOrchestrator

### 5. ResearchPackOrchestrator
- **This is the ONLY orchestrator that should be used**
- Coordinates the entire paper generation process:
  1. Plans the research pack structure
  2. Creates diagrams (mind maps, process flows)
  3. Produces content with Lily callouts
  4. Calls the document formatter

### 6. Document Formatter
- **Only use the formatter with random Lily quotes in the footer**
- Located at: `/app/services/document_formatter/document_formatter.py`
- Formats the content into a professional document:
  1. Creates title page with logo
  2. Formats sections and subsections
  3. Adds headers and footers with random Lily quotes
  4. Generates table of contents
  5. Saves as DOCX and PDF

### 7. Result Storage
- Documents are saved locally and/or to Supabase Storage
- URLs are stored in the job results

### 8. User Access
- User can view and download the completed paper
- Papers are available in both DOCX and PDF formats

## Component Relationships

```
User Request → API Endpoint → Queue Manager → Worker → ResearchPackOrchestrator → Document Formatter → Final Paper
```

## Important Notes

1. **Single Orchestrator**: Only the ResearchPackOrchestrator should be used. All other orchestrators should be in the 'to_be_deleted' folder.

2. **Single Document Formatter**: Only use the document formatter with random Lily quotes in the footer. All other formatters should be in the 'to_be_deleted' folder.

3. **API Routes**: There are two API routes:
   - `/api/research-paper/generate`: For UI requests (with credit checks)
   - `/api/direct/research-paper/generate`: For enterprise API access (bypasses credit checks)

4. **Worker Process**: The worker_launcher.py initializes the worker, which uses the ResearchPackOrchestrator to generate papers.

5. **Queue System**: All paper generation requests go through the queue system to ensure proper load balancing and job tracking.

## Legacy Code Warning

Any code that uses other orchestrators or document formatters should be considered legacy and moved to the 'to_be_deleted' folder.

## API Access for Enterprise Users

### Authentication Approach

**IMPORTANT: For enterprise API access, use existing Supabase authentication instead of creating a separate API key system.**

1. For enterprise packages, create an auth user in Supabase and provide those credentials
2. The JWT token from their Supabase auth can be used as the API key
3. This maintains a single authentication flow for both UI and API access

### Admin User Authentication

For testing and development, use the admin user's authentication:

- **Admin User**: Leo Ruocco (pantaleone@btinternet.com)
- **User ID**: 55b4ec8c-2cf5-40fe-8718-75fe45f49a69

To get a valid JWT token:
1. Log in to the application as the admin user
2. Open browser developer tools and check the local storage for the JWT token
3. Look for the key `sb-<project-ref>-auth-token` in local storage

### Example API Call

```bash
curl -X POST https://your-app-url.com/api/research-paper/generate \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Artificial Intelligence Ethics",
    "education_level": "postgraduate",
    "include_diagrams": true,
    "key_points": ["Impact on society", "Regulatory frameworks"]
  }'
```

### Benefits of This Approach

- Simplified architecture (no separate API key system)
- Unified access control
- Leverages existing Supabase security features
- Easy to manage user permissions
