# Lily AI Implementation Plan

## Overview

This document outlines the plan for implementing the remaining components of the Lily AI system, with a focus on connecting the web UI to the backend services and completing the Supabase integration. The goal is to create a fully functional SaaS platform that allows users to generate research packs through a seamless interface.

## Current Status

Based on codebase analysis, the following components have been implemented:
- Authentication system (login, registration)
- Core backend services (Research Pack Orchestrator, Document Formatter, Diagram Generator)
- Basic UI templates (home, login, register, dashboard)

The following components are missing or incomplete:
- Paper submission and management routes
- Research pack queue management integration with frontend
- Dashboard integration with Supabase for displaying user's papers
- API routes for paper submission and management

## Implementation Plan

### Phase 1: API Routes and Backend Integration

#### 1.1 Paper Submission API (1 week)

- **Create papers router**
  ```python
  # routes/papers.py
  from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
  from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
  from fastapi.templating import Jinja2Templates
  
  # Initialize router
  router = APIRouter(prefix="/papers", tags=["papers"])
  ```

- **Implement paper submission endpoint**
  ```python
  @router.post("/api/submit")
  async def submit_paper(
      request: Request,
      topic: str = Form(...),
      question: str = Form(...),
      education_level: str = Form("university"),
      include_diagrams: bool = Form(True),
      user = Depends(get_current_user)
  ):
      # Submit job to queue
      job_id = queue_manager.submit_job(
          user_id=user.id,
          job_type="research_pack",
          parameters={
              "topic": topic,
              "question": question,
              "education_level": education_level,
              "include_diagrams": include_diagrams,
              "premium": user.user_metadata.get("subscription_tier") == "premium"
          }
      )
      
      return {"job_id": job_id, "status": "queued"}
  ```

- **Implement paper retrieval endpoints**
  ```python
  @router.get("/api/list")
  async def list_papers(request: Request, user = Depends(get_current_user)):
      # Get papers from Supabase
      jobs = queue_manager.get_user_jobs(user.id)
      return {"papers": jobs}
      
  @router.get("/api/detail/{job_id}")
  async def paper_detail(job_id: str, request: Request, user = Depends(get_current_user)):
      # Get paper details from Supabase
      job = queue_manager.get_job(job_id)
      
      # Check if the job belongs to the user
      if job["user_id"] != user.id:
          raise HTTPException(status_code=403, content={"detail": "Not authorized to access this paper"})
      
      return job
  ```

- **Implement paper action endpoints**
  ```python
  @router.post("/api/cancel/{job_id}")
  async def cancel_paper(job_id: str, request: Request, user = Depends(get_current_user)):
      # Cancel job in queue
      success = queue_manager.cancel_job(job_id, user.id)
      return {"success": success}
      
  @router.post("/api/resubmit/{job_id}")
  async def resubmit_paper(job_id: str, request: Request, user = Depends(get_current_user)):
      # Resubmit job to queue with higher priority
      new_job_id = queue_manager.resubmit_job(job_id, user.id)
      return {"job_id": new_job_id, "status": "queued"}
  ```

#### 1.2 Queue Manager Integration (3 days)

- **Create queue manager service**
  ```python
  # app/services/queue_manager.py
  class QueueManager:
      def __init__(self):
          self.supabase = get_supabase_client()
          
      def submit_job(self, user_id, job_type, parameters):
          # Insert job into Supabase jobs table
          result = self.supabase.table("jobs").insert({
              "user_id": user_id,
              "job_type": job_type,
              "status": "queued",
              "priority": 3,  # Default priority
              "parameters": parameters,
              "created_at": datetime.now().isoformat()
          }).execute()
          
          return result.data[0]["job_id"]
  ```

- **Add methods for retrieving and updating jobs**
  ```python
  def get_user_jobs(self, user_id):
      # Get all jobs for a user
      result = self.supabase.table("jobs").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
      return result.data
      
  def get_job(self, job_id):
      # Get specific job
      result = self.supabase.table("jobs").select("*").eq("job_id", job_id).execute()
      if not result.data:
          return None
      return result.data[0]
  ```

### Phase 2: Web UI Implementation

#### 2.1 Paper Submission Page (2 days)

- **Create paper submission template**
  ```html
  <!-- templates/papers/new.html -->
  {% extends "base.html" %}
  
  {% block title %}New Research Paper - Lily AI Research Assistant{% endblock %}
  
  {% block content %}
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
      <!-- Paper submission form -->
      <form action="/papers/api/submit" method="post" id="paper-form">
          <!-- Topic input -->
          <div class="input-focus-effect">
              <label for="topic" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Research Topic</label>
              <input id="topic" name="topic" type="text" required class="input-field" placeholder="e.g., Climate Change">
          </div>
          
          <!-- Question input -->
          <div class="input-focus-effect mt-4">
              <label for="question" class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Research Question</label>
              <textarea id="question" name="question" required class="input-field h-24" placeholder="e.g., What are the major causes of climate change and potential solutions?"></textarea>
          </div>
          
          <!-- Submit button -->
          <button type="submit" class="w-full btn-primary mt-6">Generate Research Pack</button>
      </form>
  </div>
  {% endblock %}
  ```

- **Implement route handler for submission page**
  ```python
  @router.get("/new", response_class=HTMLResponse)
  async def new_paper_page(request: Request, user = Depends(get_current_user)):
      # Check if user has reached their paper limit
      user_data = auth_service.get_user(user.id)
      subscription_tier = user_data.user_metadata.get("subscription_tier", "sample")
      papers_used = user_data.user_metadata.get("papers_used", 0)
      paper_limit = {
          "sample": 3,
          "basic": 5,
          "premium": 20,
          "pro": 999
      }.get(subscription_tier, 3)
      
      can_create = papers_used < paper_limit
      
      return templates.TemplateResponse(
          "papers/new.html",
          {
              "request": request,
              "user": user,
              "can_create": can_create,
              "papers_used": papers_used,
              "paper_limit": paper_limit
          }
      )
  ```

#### 2.2 Papers List Page (2 days)

- **Create papers list template**
  ```html
  <!-- templates/papers/index.html -->
  {% extends "base.html" %}
  
  {% block title %}My Papers - Lily AI Research Assistant{% endblock %}
  
  {% block content %}
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
      <!-- Papers list table -->
      <div class="overflow-x-auto">
          <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-900">
                  <tr>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Title</th>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Created</th>
                      <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                  </tr>
              </thead>
              <tbody id="papers-list" class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                  {% for paper in papers %}
                  <tr>
                      <td class="px-6 py-4 whitespace-nowrap">
                          <div class="text-sm font-medium text-gray-900 dark:text-white">{{ paper.parameters.topic }}</div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                          <span class="px-2.5 py-0.5 rounded-full text-xs font-medium 
                              {% if paper.status == 'completed' %}
                                  bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300
                              {% elif paper.status == 'in_progress' %}
                                  bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300
                              {% elif paper.status == 'queued' %}
                                  bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300
                              {% elif paper.status == 'errored' %}
                                  bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300
                              {% endif %}
                          ">
                              {{ paper.status|title }}
                          </span>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap">
                          <div class="text-sm text-gray-500 dark:text-gray-400">{{ paper.created_at|date }}</div>
                      </td>
                      <td class="px-6 py-4 whitespace-nowrap text-sm font-medium">
                          {% if paper.status == 'completed' %}
                              <a href="/papers/{{ paper.job_id }}" class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300 mr-3">View</a>
                              {% if paper.result.docx_url %}
                                  <a href="{{ paper.result.docx_url }}" class="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300 mr-3">Download DOCX</a>
                              {% endif %}
                              {% if paper.result.pdf_url %}
                                  <a href="{{ paper.result.pdf_url }}" class="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300">Download PDF</a>
                              {% endif %}
                          {% elif paper.status == 'errored' %}
                              <form action="/papers/api/resubmit/{{ paper.job_id }}" method="post" class="inline">
                                  <button type="submit" class="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300">Retry</button>
                              </form>
                          {% elif paper.status == 'queued' %}
                              <form action="/papers/api/cancel/{{ paper.job_id }}" method="post" class="inline">
                                  <button type="submit" class="text-red-600 hover:text-red-900 dark:text-red-400 dark:hover:text-red-300">Cancel</button>
                              </form>
                          {% endif %}
                      </td>
                  </tr>
                  {% endfor %}
              </tbody>
          </table>
      </div>
  </div>
  {% endblock %}
  ```

- **Implement route handler for papers list**
  ```python
  @router.get("/", response_class=HTMLResponse)
  async def papers_list(request: Request, user = Depends(get_current_user)):
      # Get papers from Supabase
      papers = queue_manager.get_user_jobs(user.id)
      
      return templates.TemplateResponse(
          "papers/index.html",
          {
              "request": request,
              "user": user,
              "papers": papers
          }
      )
  ```

#### 2.3 Paper Detail Page (2 days)

- **Create paper detail template**
  ```html
  <!-- templates/papers/detail.html -->
  {% extends "base.html" %}
  
  {% block title %}{{ paper.parameters.topic }} - Lily AI Research Assistant{% endblock %}
  
  {% block content %}
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900">
      <!-- Paper detail page -->
      <div class="max-w-4xl mx-auto px-4 py-8">
          <h1 class="text-3xl font-bold text-gray-900 dark:text-white mb-6">{{ paper.parameters.topic }}</h1>
          
          <!-- Status indicator -->
          <div class="flex items-center mb-6">
              <span class="px-3 py-1 rounded-full text-sm font-medium 
                  {% if paper.status == 'completed' %}
                      bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300
                  {% elif paper.status == 'in_progress' %}
                      bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300
                  {% elif paper.status == 'queued' %}
                      bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-300
                  {% elif paper.status == 'errored' %}
                      bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300
                  {% endif %}
              ">
                  {{ paper.status|title }}
              </span>
              <span class="ml-4 text-sm text-gray-600 dark:text-gray-400">Created on {{ paper.created_at|date }}</span>
          </div>
          
          <!-- Download links (if completed) -->
          {% if paper.status == 'completed' %}
          <div class="flex space-x-4 mb-8">
              {% if paper.result.docx_url %}
                  <a href="{{ paper.result.docx_url }}" class="btn-primary">Download DOCX</a>
              {% endif %}
              {% if paper.result.pdf_url %}
                  <a href="{{ paper.result.pdf_url }}" class="btn-secondary">Download PDF</a>
              {% endif %}
          </div>
          {% endif %}
          
          <!-- Paper details -->
          <div class="bg-white dark:bg-gray-800 shadow-md rounded-lg p-6">
              <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-4">Research Question</h2>
              <p class="text-gray-700 dark:text-gray-300 mb-6">{{ paper.parameters.question }}</p>
              
              <!-- Progress display -->
              {% if paper.status == 'in_progress' %}
              <div class="mb-6">
                  <h3 class="text-lg font-medium text-gray-900 dark:text-white mb-2">Progress</h3>
                  <div class="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mb-2">
                      <div class="bg-blue-600 dark:bg-blue-500 h-2.5 rounded-full" style="width: 45%"></div>
                  </div>
                  <p class="text-sm text-gray-600 dark:text-gray-400">Your research pack is being generated. This may take 5-10 minutes.</p>
              </div>
              {% endif %}
              
              <!-- Error information (if errored) -->
              {% if paper.status == 'errored' %}
              <div class="mb-6">
                  <h3 class="text-lg font-medium text-red-600 dark:text-red-400 mb-2">Error Information</h3>
                  <p class="text-gray-700 dark:text-gray-300 mb-4">{{ paper.error_message }}</p>
                  <form action="/papers/api/resubmit/{{ paper.job_id }}" method="post">
                      <button type="submit" class="btn-primary">Retry</button>
                  </form>
              </div>
              {% endif %}
          </div>
      </div>
  </div>
  {% endblock %}
  ```

- **Implement route handler for paper detail**
  ```python
  @router.get("/{job_id}", response_class=HTMLResponse)
  async def paper_detail(job_id: str, request: Request, user = Depends(get_current_user)):
      # Get paper from Supabase
      paper = queue_manager.get_job(job_id)
      
      if not paper:
          return RedirectResponse(url="/papers", status_code=status.HTTP_303_SEE_OTHER)
      
      # Check if the paper belongs to the user
      if paper["user_id"] != user.id:
          return RedirectResponse(url="/papers", status_code=status.HTTP_303_SEE_OTHER)
      
      return templates.TemplateResponse(
          "papers/detail.html",
          {
              "request": request,
              "user": user,
              "paper": paper
          }
      )
  ```

### Phase 3: Supabase Integration and Real-time Updates (3 days)

#### 3.1 Supabase Schema Setup

- **Implement database migrations for jobs table**
  ```sql
  -- app/migrations/jobs_table.sql
  
  -- Jobs table for the queuing system
  CREATE TABLE IF NOT EXISTS jobs (
      -- Primary key and identifiers
      job_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id UUID NOT NULL,
      
      -- Job metadata
      job_type VARCHAR(50) NOT NULL,  -- e.g., 'research_pack', 'diagram', etc.
      status VARCHAR(20) NOT NULL CHECK (status IN ('queued', 'in_progress', 'completed', 'errored')),
      priority SMALLINT NOT NULL DEFAULT 3 CHECK (priority >= 0 AND priority <= 3),
      
      -- Timestamps for tracking and sorting
      created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
      started_at TIMESTAMP WITH TIME ZONE,
      completed_at TIMESTAMP WITH TIME ZONE,
      
      -- Job details
      parameters JSONB NOT NULL,  -- Topic, question, education level, etc.
      result JSONB,               -- Output file paths, URLs, etc.
      error_message TEXT,         -- Error details if status is 'errored'
      
      -- Worker tracking
      worker_id VARCHAR(100),     -- ID of the worker processing this job
      
      -- Foreign key to user
      CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE
  );
  
  -- Indexes for efficient querying
  CREATE INDEX IF NOT EXISTS idx_jobs_queue ON jobs (priority, created_at) WHERE status = 'queued';
  CREATE INDEX IF NOT EXISTS idx_jobs_user ON jobs (user_id, created_at DESC);
  CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs (status, updated_at DESC);
  ```

#### 3.2 Supabase Storage Setup

- **Create storage buckets**
  ```sql
  -- app/migrations/storage_buckets.sql
  
  -- Create the research packs bucket
  INSERT INTO storage.buckets (id, name, public)
  VALUES ('research-packs', 'Research Packs', true)
  ON CONFLICT DO NOTHING;
  
  -- Set up RLS policies
  CREATE POLICY "Users can view their own research packs"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (
      bucket_id = 'research-packs' AND
      (storage.foldername(name))[1] = auth.uid()::text
  );
  
  CREATE POLICY "Users can upload their own research packs"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
      bucket_id = 'research-packs' AND
      (storage.foldername(name))[1] = auth.uid()::text
  );
  ```

#### 3.3 Real-time Updates

- **Implement client-side real-time updates**
  ```javascript
  // static/js/papers.js
  
  // Initialize Supabase client
  const supabaseUrl = 'https://your-supabase-url.supabase.co';
  const supabaseKey = 'public-anon-key';
  const supabase = supabase.createClient(supabaseUrl, supabaseKey);
  
  // Subscribe to updates for user's jobs
  function subscribeToJobUpdates(userId) {
      supabase
          .from(`jobs:user_id=eq.${userId}`)
          .on('UPDATE', payload => {
              // Update UI with new job status
              updateJobInList(payload.new);
              
              // If on detail page for this job, update the details
              const jobId = window.location.pathname.split('/').pop();
              if (jobId === payload.new.job_id) {
                  updateJobDetail(payload.new);
              }
          })
          .subscribe();
  }
  ```

### Phase 4: Worker System Integration (2 days)

#### 4.1 Worker Daemon Integration

- **Modify worker daemon to process jobs from Supabase**
  ```python
  # worker_daemon.py
  
  class WorkerDaemon:
      def __init__(self):
          self.supabase = get_supabase_client()
          self.worker_id = str(uuid.uuid4())
          
      async def run(self):
          """Main daemon loop"""
          while True:
              try:
                  # Get the next job from the queue
                  job = await self.get_next_job()
                  
                  if job:
                      # Update job status to in_progress
                      await self.update_job_status(job["job_id"], "in_progress")
                      
                      # Process the job
                      try:
                          result = await self.process_job(job)
                          
                          # Update job with result
                          await self.complete_job(job["job_id"], result)
                      except Exception as e:
                          # Update job with error
                          await self.fail_job(job["job_id"], str(e))
                  
                  # Wait a short time before checking for more jobs
                  await asyncio.sleep(1)
              except Exception as e:
                  logger.error(f"Error in worker daemon: {str(e)}")
                  await asyncio.sleep(5)
      
      async def get_next_job(self):
          """Get the next job from the queue"""
          # Get job with highest priority and oldest created_at
          result = self.supabase.table("jobs")\
              .select("*")\
              .eq("status", "queued")\
              .order("priority")\
              .order("created_at")\
              .limit(1)\
              .execute()
              
          if not result.data:
              return None
              
          return result.data[0]
  ```

#### 4.2 Research Pack Integration

- **Integrate research pack orchestrator with worker**
  ```python
  async def process_job(self, job):
      """Process a job based on its type"""
      if job["job_type"] == "research_pack":
          # Initialize orchestrator
          orchestrator = ResearchPackOrchestrator()
          
          # Generate research pack
          research_pack = await orchestrator.generate_research_pack(
              topic=job["parameters"]["topic"],
              question=job["parameters"]["question"],
              user_id=job["user_id"],
              education_level=job["parameters"].get("education_level", "university"),
              include_diagrams=job["parameters"].get("include_diagrams", True),
              premium=job["parameters"].get("premium", False)
          )
          
          return research_pack
      else:
          raise ValueError(f"Unknown job type: {job['job_type']}")
  ```

### Phase 5: Testing and Refinement (3 days)

#### 5.1 Integration Testing

- Create test cases for the complete flow:
  - User authentication
  - Paper submission
  - Queue processing
  - Research pack generation
  - Result retrieval and display

#### 5.2 UI Refinements

- Add loading indicators
- Implement error handling
- Add progress indicators for long-running operations

#### 5.3 Documentation

- Update README with installation and usage instructions
- Document API endpoints
- Create user guide for the web UI

## Timeline

| Phase | Task | Duration | Dependencies |
|-------|------|----------|--------------|
| 1.1 | Paper Submission API | 1 week | - |
| 1.2 | Queue Manager Integration | 3 days | - |
| 2.1 | Paper Submission Page | 2 days | 1.1 |
| 2.2 | Papers List Page | 2 days | 1.1, 1.2 |
| 2.3 | Paper Detail Page | 2 days | 1.1, 1.2 |
| 3.1 | Supabase Schema Setup | 1 day | - |
| 3.2 | Supabase Storage Setup | 1 day | 3.1 |
| 3.3 | Real-time Updates | 1 day | 3.1, 2.2, 2.3 |
| 4.1 | Worker Daemon Integration | 1 day | 1.2, 3.1 |
| 4.2 | Research Pack Integration | 1 day | 4.1 |
| 5.1 | Integration Testing | 1 day | All above |
| 5.2 | UI Refinements | 1 day | All above |
| 5.3 | Documentation | 1 day | All above |

Total estimated time: **3-4 weeks**

## Implementation Order

1. Backend foundations (Phase 1 + 3.1, 3.2)
2. Worker integration (Phase 4)
3. Frontend implementation (Phase 2)
4. Real-time updates (Phase 3.3)
5. Testing and refinement (Phase 5)

## Success Criteria

- Users can sign up and log in
- Users can submit research pack requests
- Requests are queued and processed in order of priority
- Users can view their papers in progress and completed papers
- Users can download completed research packs in DOCX and PDF formats
- Users can resubmit failed jobs
- UI updates in real-time as job status changes 