"""
Task Processor - Handles the execution of tasks by AI agents.

This module:
1. Picks up tasks from the queue
2. Assigns them to available agents
3. Executes the task workflow (planning, research, execution, review)
4. Saves outputs
5. Updates task status
"""

import os
import json
import time
import logging
import asyncio
import sqlite3
import requests
from datetime import datetime
import shutil
import uuid
import markdown
from bs4 import BeautifulSoup
import re
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("task_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("task-processor")

# Constants
DB_PATH = 'ai2ai_feedback.db'
OUTPUT_BASE_DIR = 'task_outputs'
RESEARCH_DIR = 'research_data'
# Use alternative Ollama servers instead of localhost
OLLAMA_ENDPOINT = 'http://ruocco.uk:11434/api/generate'  # Remote server
# OLLAMA_ENDPOINT = 'http://192.168.0.39:11434/api/generate'  # DeepSeek server
SEARCH_API_URL = 'https://duckduckgo.com/html/'

# Ensure output directories exist
os.makedirs(OUTPUT_BASE_DIR, exist_ok=True)
os.makedirs(RESEARCH_DIR, exist_ok=True)

class TaskProcessor:
    def __init__(self):
        """Initialize the task processor."""
        self.conn = None
        self.cursor = None
        self.connect_db()

    def connect_db(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close_db(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def get_next_task(self):
        """Get the next available task from the queue."""
        self.cursor.execute(
            'SELECT * FROM tasks WHERE status = "not_started" ORDER BY priority DESC, created_at ASC LIMIT 1'
        )
        return self.cursor.fetchone()

    def get_available_agent(self, task_complexity):
        """Get an available agent that can handle the task complexity."""
        self.cursor.execute(
            'SELECT * FROM agents WHERE status = "available" AND min_complexity <= ? AND max_complexity >= ? LIMIT 1',
            (task_complexity, task_complexity)
        )
        return self.cursor.fetchone()

    def assign_task_to_agent(self, task_id, agent_id):
        """Assign a task to an agent and update statuses."""
        try:
            # Update task
            self.cursor.execute(
                'UPDATE tasks SET assigned_agent_id = ?, status = "design", updated_at = ? WHERE id = ?',
                (agent_id, datetime.now().isoformat(), task_id)
            )

            # Update agent
            self.cursor.execute(
                'UPDATE agents SET status = "busy", last_active = ? WHERE id = ?',
                (datetime.now().isoformat(), agent_id)
            )

            # Generate a unique ID for the task update
            update_id = str(uuid.uuid4())

            # Create task update
            self.cursor.execute(
                'INSERT INTO task_updates (id, task_id, agent_id, update_type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (update_id, task_id, agent_id, "status_change", f"Task assigned to agent {agent_id} and moved to design stage", datetime.now().isoformat())
            )

            self.conn.commit()
            logger.info(f"Task {task_id} assigned to agent {agent_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error assigning task: {e}")
            return False

    def update_task_status(self, task_id, status, progress, message, agent_id):
        """Update the status of a task."""
        try:
            # Update task
            self.cursor.execute(
                'UPDATE tasks SET status = ?, stage_progress = ?, updated_at = ? WHERE id = ?',
                (status, progress, datetime.now().isoformat(), task_id)
            )

            # If task is complete, update completed_at and set agent to available
            if status == "complete":
                self.cursor.execute(
                    'UPDATE tasks SET completed_at = ? WHERE id = ?',
                    (datetime.now().isoformat(), task_id)
                )
                self.cursor.execute(
                    'UPDATE agents SET status = "available", last_active = ? WHERE id = ?',
                    (datetime.now().isoformat(), agent_id)
                )

            # Generate a unique ID for the task update
            update_id = str(uuid.uuid4())

            # Create task update
            self.cursor.execute(
                'INSERT INTO task_updates (id, task_id, agent_id, update_type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (update_id, task_id, agent_id, "status_change", message, datetime.now().isoformat())
            )

            self.conn.commit()
            logger.info(f"Task {task_id} status updated to {status} ({progress}%)")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating task status: {e}")
            return False

    def create_task_update(self, task_id, agent_id, update_type, content):
        """Create a task update."""
        try:
            # Generate a unique ID for the task update
            update_id = str(uuid.uuid4())

            self.cursor.execute(
                'INSERT INTO task_updates (id, task_id, agent_id, update_type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (update_id, task_id, agent_id, update_type, content, datetime.now().isoformat())
            )
            self.conn.commit()
            logger.info(f"Created task update for task {task_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error creating task update: {e}")
            return False

    def update_task_result_path(self, task_id, result_path):
        """Update the result path of a task."""
        try:
            self.cursor.execute(
                'UPDATE tasks SET result_path = ? WHERE id = ?',
                (result_path, task_id)
            )
            self.conn.commit()
            logger.info(f"Updated result path for task {task_id}: {result_path}")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating task result path: {e}")
            return False

    def get_agent_model(self, agent_id):
        """Get the model name for an agent."""
        self.cursor.execute(
            'SELECT model FROM agents WHERE id = ?',
            (agent_id,)
        )
        agent = self.cursor.fetchone()
        return agent['model'] if agent else None

    def get_task_details(self, task_id):
        """Get detailed information about a task."""
        self.cursor.execute(
            'SELECT * FROM tasks WHERE id = ?',
            (task_id,)
        )
        return self.cursor.fetchone()

    def search_web(self, query, num_results=5):
        """Search the web using DuckDuckGo."""
        try:
            encoded_query = quote_plus(query)
            response = requests.get(
                SEARCH_API_URL,
                params={'q': encoded_query},
                headers={'User-Agent': 'Mozilla/5.0'}
            )

            if response.status_code != 200:
                logger.error(f"Search request failed with status code {response.status_code}")
                return []

            # Parse the HTML response
            soup = BeautifulSoup(response.text, 'html.parser')
            results = []

            # Extract search results
            for result in soup.select('.result')[:num_results]:
                title_elem = result.select_one('.result__title')
                link_elem = result.select_one('.result__url')
                snippet_elem = result.select_one('.result__snippet')

                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')

                    # Fix URL if it's missing the scheme
                    if link.startswith('//'):
                        link = 'https:' + link

                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""

                    results.append({
                        'title': title,
                        'url': link,
                        'snippet': snippet
                    })

            logger.info(f"Found {len(results)} search results for query: {query}")
            return results
        except Exception as e:
            logger.error(f"Error searching web: {e}")
            return []



    def fetch_webpage_content(self, url):
        """Fetch and extract content from a webpage."""
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

            if response.status_code != 200:
                logger.error(f"Web fetch failed with status code {response.status_code}")
                return ""

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()

            # Get text
            text = soup.get_text()

            # Break into lines and remove leading and trailing space
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Remove blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)

            logger.info(f"Successfully fetched content from {url}")
            return text
        except Exception as e:
            logger.error(f"Error fetching webpage: {e}")
            return ""

    def query_llm(self, model, prompt, system_prompt=None, max_tokens=4000, timeout=60, retries=3, backoff=2):
        """
        Query the LLM using Ollama API with timeout, retries and backoff.

        Args:
            model: The model to use
            prompt: The prompt to send
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            timeout: Timeout in seconds for the request
            retries: Number of retries if the request fails
            backoff: Backoff multiplier for retries
        """
        # Try with a smaller model if the original model is too large
        fallback_models = {
            "gemma3:4b": "gemma3:1b",
            "deepseek-coder-v2:16b": "gemma3:1b"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens
            }
        }

        if system_prompt:
            payload["system"] = system_prompt

        # Try with the requested model first
        for attempt in range(retries):
            try:
                logger.info(f"Querying LLM with model {model}, attempt {attempt+1}/{retries}")
                response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=timeout)

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"LLM query successful with model {model}")
                    return result.get('response', '')
                else:
                    logger.warning(f"LLM query failed with status code {response.status_code}, attempt {attempt+1}/{retries}")
            except requests.exceptions.Timeout:
                logger.warning(f"LLM query timed out after {timeout} seconds, attempt {attempt+1}/{retries}")
            except Exception as e:
                logger.warning(f"Error querying LLM: {e}, attempt {attempt+1}/{retries}")

            # Wait before retrying with exponential backoff
            if attempt < retries - 1:
                wait_time = backoff ** attempt
                logger.info(f"Waiting {wait_time} seconds before retrying")
                time.sleep(wait_time)

        # If all attempts with the original model failed, try with a fallback model
        fallback_model = fallback_models.get(model)
        if fallback_model:
            logger.info(f"Trying fallback model {fallback_model}")
            payload["model"] = fallback_model

            try:
                response = requests.post(OLLAMA_ENDPOINT, json=payload, timeout=timeout)

                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"LLM query successful with fallback model {fallback_model}")
                    return result.get('response', '')
                else:
                    logger.error(f"LLM query with fallback model failed with status code {response.status_code}")
            except Exception as e:
                logger.error(f"Error querying LLM with fallback model: {e}")

        # If everything fails, return empty string and let the caller handle it
        logger.error("All LLM query attempts failed, returning empty string")
        return ""

    def create_task_output_dir(self, task_id):
        """Create a directory for task outputs."""
        output_dir = os.path.join(OUTPUT_BASE_DIR, task_id)
        os.makedirs(output_dir, exist_ok=True)
        return output_dir

    def save_output_file(self, output_dir, filename, content):
        """Save content to a file in the output directory."""
        try:
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Saved output to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving output file: {e}")
            return None

    def generate_html_from_markdown(self, markdown_content):
        """Convert markdown to HTML."""
        try:
            html = markdown.markdown(markdown_content)
            return html
        except Exception as e:
            logger.error(f"Error converting markdown to HTML: {e}")
            return markdown_content

    def planning_phase(self, task, agent, output_dir):
        """
        Planning phase of task execution.

        1. Analyze the task requirements
        2. Create a detailed plan
        3. Identify research needs
        4. Define output structure
        """
        task_id = task['id']
        agent_id = agent['id']
        model = agent['model']

        logger.info(f"Starting planning phase for task {task_id}")

        # Create planning prompt
        planning_prompt = f"""
        # Task Planning

        ## Task Details
        - Title: {task['title']}
        - Description: {task['description']}
        - Complexity: {task['complexity']}

        ## Instructions
        You are an AI agent tasked with creating a detailed plan for completing this task.

        First, analyze the task requirements carefully. What is the core objective? What specific deliverables are required?

        Then, create a comprehensive plan with these components:

        1. Task Analysis: Provide a detailed analysis of what the task requires, including:
           - Core objective
           - Key deliverables
           - Target audience
           - Scope and constraints
           - Success criteria

        2. Research Needs: List specific topics, questions, and information that need to be researched, including:
           - Primary research questions (3-5 specific questions)
           - Key topics to investigate
           - Types of sources needed (academic, news, statistics, etc.)
           - Specific search terms to use

        3. Execution Steps: Break down the task into clear, sequential steps with estimated effort:
           1. [Step 1] - [Estimated effort]
           2. [Step 2] - [Estimated effort]
           ...

        4. Output Structure: Define the structure of the final output, including:
           - Format (essay, report, web page, etc.)
           - Main sections and subsections
           - Approximate length for each section
           - Any specific elements to include (diagrams, tables, code, etc.)

        5. Quality Criteria: Define how to evaluate if the task is completed successfully:
           - Completeness criteria
           - Accuracy requirements
           - Style and formatting standards
           - Any specific requirements from the task description

        Your plan should be detailed, specific, and actionable. It will guide all subsequent phases of the task execution.
        """

        # Query LLM for planning
        system_prompt = "You are an expert project planner and researcher. Your job is to create detailed, actionable plans for complex tasks. Be specific, thorough, and practical in your planning."
        plan_response = self.query_llm(model, planning_prompt, system_prompt, max_tokens=2000)

        if not plan_response:
            logger.error(f"Failed to generate plan for task {task_id}")
            return None

        # Save the plan
        plan_file = self.save_output_file(output_dir, "plan.md", plan_response)

        # Create task update
        self.create_task_update(
            task_id,
            agent_id,
            "progress_update",
            f"Created task plan: {plan_response[:200]}..."
        )

        logger.info(f"Planning phase completed for task {task_id}")
        return plan_response

    def research_phase(self, task, agent, plan, output_dir):
        """
        Research phase of task execution.

        1. Extract research questions from plan
        2. Search the web for relevant information
        3. Fetch and process content from relevant pages
        4. Organize research findings
        5. Create a comprehensive research summary
        """
        task_id = task['id']
        agent_id = agent['id']
        model = agent['model']

        logger.info(f"Starting research phase for task {task_id}")

        # Extract research questions
        research_prompt = f"""
        # Research Planning

        ## Task Plan
        {plan}

        ## Instructions
        Based on the task plan above, extract 5-8 specific search queries that would help gather the necessary information to complete this task.

        For each query:
        1. Make it specific and focused on a particular aspect of the task
        2. Phrase it to maximize relevant search results
        3. Include any necessary context or qualifiers
        4. Consider both broad overview queries and specific detail queries

        ## Output Format
        Provide your search queries in the following format:

        1. [Search query 1] - [Brief explanation of what information this query aims to find]
        2. [Search query 2] - [Brief explanation of what information this query aims to find]
        3. [Search query 3] - [Brief explanation of what information this query aims to find]
        ...
        """

        # Query LLM for research questions
        system_prompt = "You are an expert researcher with extensive experience in information gathering and synthesis. Your job is to formulate effective search queries that will yield comprehensive, relevant, and high-quality information."
        research_questions = self.query_llm(model, research_prompt, system_prompt, max_tokens=2000)

        if not research_questions:
            logger.error(f"Failed to generate research questions for task {task_id}")
            self.create_task_update(task_id, agent_id, "note", "Failed to generate research questions")
            return {}

        # Save research questions
        self.save_output_file(output_dir, "research_questions.md", research_questions)
        self.create_task_update(task_id, agent_id, "progress_update", f"Generated research questions: {research_questions[:200]}...")

        # Extract queries from the response
        queries = []
        for line in research_questions.split('\n'):
            line = line.strip()
            if re.match(r'^\d+\.', line):
                # Extract just the query part (before any explanation)
                query_parts = re.sub(r'^\d+\.\s*', '', line).split(' - ', 1)
                query = query_parts[0].strip()
                queries.append(query)

        # If no queries were found, create a default one from the task title
        if not queries:
            queries = [task['title']]

        # Update progress
        self.update_task_status(task_id, "build", 20, "Generated research questions", agent_id)

        # Perform searches and gather information
        research_data = {}
        for i, query in enumerate(queries[:8]):  # Allow up to 8 queries
            logger.info(f"Searching for: {query}")
            self.create_task_update(task_id, agent_id, "progress_update", f"Researching: {query}")

            # Search the web
            search_results = self.search_web(query, num_results=5)  # Increased to 5 results per query

            # Update progress
            progress = 20 + (i + 1) * 5  # Adjusted progress calculation
            self.update_task_status(task_id, "build", min(progress, 60), f"Completed search {i+1}/{len(queries)}", agent_id)

            # Fetch content from top results
            query_data = []
            for result in search_results:
                try:
                    content = self.fetch_webpage_content(result['url'])
                    if content:
                        query_data.append({
                            'title': result['title'],
                            'url': result['url'],
                            'content': content[:8000]  # Increased content size limit
                        })
                    else:
                        # If content fetch fails, use the snippet as content
                        query_data.append({
                            'title': result['title'],
                            'url': result['url'],
                            'content': result['snippet']
                        })
                except Exception as e:
                    logger.error(f"Error fetching content from {result['url']}: {e}")
                    # Add the result with just the snippet
                    query_data.append({
                        'title': result['title'],
                        'url': result['url'],
                        'content': result['snippet']
                    })

            research_data[query] = query_data

        # Save research data
        research_json = json.dumps(research_data, indent=2)
        self.save_output_file(output_dir, "research_data.json", research_json)

        # Update progress
        self.update_task_status(task_id, "build", 70, "Completed web research", agent_id)

        # Summarize research findings for each query
        query_summaries = {}
        for query, results in research_data.items():
            # Skip if no results
            if not results:
                continue

            # Create a summary prompt for this query
            query_summary_prompt = f"""
            # Research Summary for Query: "{query}"

            ## Sources
            {json.dumps([{'title': r['title'], 'url': r['url']} for r in results], indent=2)}

            ## Content Excerpts
            {json.dumps([{'title': r['title'], 'content': r['content'][:1000] + '...' if len(r['content']) > 1000 else r['content']} for r in results], indent=2)}

            ## Instructions
            Synthesize the key information from these sources related to the query "{query}".

            Focus on:
            - Main facts and data points
            - Different perspectives or approaches
            - Consensus views and areas of disagreement
            - Recent developments or trends
            - Relevance to the overall task

            ## Output Format
            Provide a concise but comprehensive summary (300-500 words) in markdown format with:
            - Key findings as bullet points
            - Important quotes or statistics
            - Citations to sources using [Source Title](URL) format
            """

            # Query LLM for query summary
            system_prompt = "You are an expert researcher and information synthesizer. Your job is to extract, organize, and summarize the most relevant information from multiple sources."
            query_summary = self.query_llm(model, query_summary_prompt, system_prompt, max_tokens=2000)

            if query_summary:
                query_summaries[query] = query_summary
                # Save individual query summary
                self.save_output_file(output_dir, f"research_summary_{query.replace(' ', '_')[:30]}.md", query_summary)

        # Update progress
        self.update_task_status(task_id, "build", 80, "Generated query summaries", agent_id)

        # Create comprehensive research summary
        comprehensive_summary_prompt = f"""
        # Comprehensive Research Summary

        ## Task Details
        - Title: {task['title']}
        - Description: {task['description']}

        ## Research Plan
        {plan}

        ## Query Summaries
        {json.dumps(query_summaries, indent=2)}

        ## Instructions
        Create a comprehensive research summary that synthesizes all the information gathered across different queries.

        Your summary should:
        1. Begin with an executive summary of key findings (1-2 paragraphs)
        2. Organize information by major themes or topics, not by search queries
        3. Highlight connections, patterns, and contradictions across different sources
        4. Include relevant quotes, statistics, and examples with proper citations
        5. Identify any gaps in the research that may need further investigation
        6. Conclude with implications for the task at hand

        ## Output Format
        Provide your summary in markdown format with:
        - Clear headings and subheadings
        - Bullet points for key information
        - Citations to sources using [Source Title](URL) format
        - A bibliography section at the end listing all sources
        """

        # Query LLM for comprehensive summary
        system_prompt = "You are an expert researcher and academic writer. Your job is to synthesize complex information from multiple sources into a coherent, well-structured, and comprehensive summary."
        research_summary = self.query_llm(model, comprehensive_summary_prompt, system_prompt, max_tokens=4000)

        if research_summary:
            self.save_output_file(output_dir, "research_summary.md", research_summary)
            self.create_task_update(task_id, agent_id, "progress_update", f"Completed comprehensive research summary: {research_summary[:200]}...")

        # Update progress
        self.update_task_status(task_id, "build", 90, "Research phase nearly complete", agent_id)

        logger.info(f"Research phase completed for task {task_id}")
        return research_data

    def execution_phase(self, task, agent, plan, research_data, output_dir):
        """
        Execution phase of task execution.

        1. Generate the primary output based on plan and research
        2. Create any additional required files
        3. Format the output according to requirements
        """
        task_id = task['id']
        agent_id = agent['id']
        model = agent['model']

        logger.info(f"Starting execution phase for task {task_id}")

        # Load research summary if it exists
        research_summary_path = os.path.join(output_dir, "research_summary.md")
        research_summary = ""
        if os.path.exists(research_summary_path):
            with open(research_summary_path, 'r', encoding='utf-8') as f:
                research_summary = f.read()

        # Load plan
        plan_path = os.path.join(output_dir, "plan.md")
        plan_content = ""
        if os.path.exists(plan_path):
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan_content = f.read()

        # Determine output formats
        output_formats = []
        if task['output_formats']:
            try:
                if isinstance(task['output_formats'], str):
                    output_formats = json.loads(task['output_formats'])
                else:
                    output_formats = task['output_formats']
            except:
                output_formats = []

        # Default to markdown if no formats specified
        if not output_formats:
            output_formats = ["markdown"]

        # Create execution prompt
        execution_prompt = f"""
        # Task Execution

        ## Task Details
        - Title: {task['title']}
        - Description: {task['description']}

        ## Task Plan
        {plan_content}

        ## Research Summary
        {research_summary[:10000]}  # Limit size to avoid token limits

        ## Instructions
        Based on the task details, plan, and research above, create the complete output for this task.

        Follow these guidelines:
        1. Adhere strictly to the output structure defined in the plan
        2. Incorporate key findings from the research summary
        3. Ensure all content is accurate, well-organized, and comprehensive
        4. Use proper citations when referencing external sources
        5. Include all required elements (introduction, body, conclusion, etc.)
        6. Maintain a professional, authoritative tone throughout
        7. Format the content appropriately with headings, subheadings, lists, etc.

        ## Output Format
        The primary output should be in markdown format with:
        - Clear, hierarchical heading structure (# for main headings, ## for subheadings, etc.)
        - Proper formatting for emphasis, lists, tables, and code blocks if needed
        - Citations in a consistent format
        - Well-structured paragraphs with clear topic sentences
        - Logical flow between sections
        """

        # Query LLM for primary output
        system_prompt = "You are an expert content creator with extensive experience in producing high-quality, comprehensive outputs across various domains. Your writing is clear, well-structured, authoritative, and tailored to the specific requirements of each task."
        primary_output = self.query_llm(model, execution_prompt, system_prompt, max_tokens=8000)

        if not primary_output:
            logger.error(f"Failed to generate primary output for task {task_id}")
            self.create_task_update(task_id, agent_id, "note", "Failed to generate primary output")
            return []

        # Save primary output as markdown
        primary_file = self.save_output_file(output_dir, "output.md", primary_output)
        self.create_task_update(task_id, agent_id, "progress_update", f"Generated primary output: {primary_output[:200]}...")

        # Update progress
        self.update_task_status(task_id, "test", 50, "Generated primary output", agent_id)

        # Create additional output formats
        output_files = [primary_file]

        # Convert to HTML if needed
        if "html" in output_formats or "HTML" in output_formats:
            html_content = self.generate_html_from_markdown(primary_output)
            html_file = self.save_output_file(output_dir, "output.html", html_content)
            output_files.append(html_file)
            self.create_task_update(task_id, agent_id, "progress_update", "Generated HTML version of output")

        # Update progress
        self.update_task_status(task_id, "test", 80, "Generated all output formats", agent_id)

        logger.info(f"Execution phase completed for task {task_id}")
        return output_files

    def review_phase(self, task, agent, output_files, output_dir):
        """
        Review phase of task execution.

        1. Evaluate the output against quality criteria
        2. Make improvements if needed
        3. Finalize the output
        """
        task_id = task['id']
        agent_id = agent['id']
        model = agent['model']

        logger.info(f"Starting review phase for task {task_id}")

        # Load primary output
        primary_output_path = os.path.join(output_dir, "output.md")
        primary_output = ""
        if os.path.exists(primary_output_path):
            with open(primary_output_path, 'r', encoding='utf-8') as f:
                primary_output = f.read()

        # Load plan
        plan_path = os.path.join(output_dir, "plan.md")
        plan = ""
        if os.path.exists(plan_path):
            with open(plan_path, 'r', encoding='utf-8') as f:
                plan = f.read()

        # Load research summary
        research_summary_path = os.path.join(output_dir, "research_summary.md")
        research_summary = ""
        if os.path.exists(research_summary_path):
            with open(research_summary_path, 'r', encoding='utf-8') as f:
                research_summary = f.read()

        # Create review prompt
        review_prompt = f"""
        # Output Review

        ## Task Details
        - Title: {task['title']}
        - Description: {task['description']}

        ## Task Plan
        {plan[:5000]}  # Truncate if too large

        ## Output to Review
        {primary_output[:15000]}  # Truncate if too large

        ## Instructions
        Conduct a thorough, critical review of the output against the task requirements and plan. Your review should be detailed, specific, and actionable.

        Evaluate the output based on these criteria:

        1. Completeness: Does it address all aspects of the task requirements?
        2. Accuracy: Is all information correct and up-to-date?
        3. Structure: Is the content well-organized and logically structured?
        4. Clarity: Is the writing clear, concise, and easy to understand?
        5. Depth: Is the analysis sufficiently thorough and insightful?
        6. Citations: Are sources properly cited where needed?
        7. Formatting: Is the markdown formatting correct and effective?
        8. Overall Quality: Does it meet professional standards?

        For each criterion, provide specific examples from the output to support your assessment.

        ## Output Format
        Provide your review in the following format:

        1. Executive Summary: [Brief overall assessment]

        2. Detailed Evaluation:
           - Completeness: [Assessment with specific examples]
           - Accuracy: [Assessment with specific examples]
           - Structure: [Assessment with specific examples]
           - Clarity: [Assessment with specific examples]
           - Depth: [Assessment with specific examples]
           - Citations: [Assessment with specific examples]
           - Formatting: [Assessment with specific examples]

        3. Strengths: [List specific strengths with examples]

        4. Areas for Improvement: [List specific issues that need to be addressed, with clear recommendations]

        5. Final Verdict: [Clear statement on whether the output is acceptable as is, needs minor revisions, or needs major revisions]
        """

        # Query LLM for review
        system_prompt = "You are an expert quality reviewer with extensive experience evaluating academic and professional content. Your reviews are thorough, critical, fair, and actionable. You have high standards but provide constructive feedback that helps improve the work."
        review_response = self.query_llm(model, review_prompt, system_prompt, max_tokens=4000)

        if not review_response:
            logger.error(f"Failed to generate review for task {task_id}")
            self.create_task_update(task_id, agent_id, "note", "Failed to generate review")
            return primary_output

        # Save the review
        review_file = self.save_output_file(output_dir, "review.md", review_response)

        # Create task update
        self.create_task_update(
            task_id,
            agent_id,
            "progress_update",
            f"Completed review: {review_response[:200]}..."
        )

        # Check if revisions are needed
        needs_revision = any(phrase in review_response.lower() for phrase in [
            "needs revision", "not acceptable", "major revisions", "significant improvements",
            "substantial changes", "inadequate", "insufficient", "poor quality"
        ])

        # If revisions are needed, improve the output
        if needs_revision:
            logger.info(f"Output needs revision for task {task_id}")

            # Create revision prompt
            revision_prompt = f"""
            # Output Revision

            ## Task Details
            - Title: {task['title']}
            - Description: {task['description']}

            ## Task Plan
            {plan[:3000]}  # Truncate if too large

            ## Research Summary
            {research_summary[:5000]}  # Include part of the research summary

            ## Original Output
            {primary_output[:10000]}  # Truncate if too large

            ## Review Feedback
            {review_response}

            ## Instructions
            Revise the original output based on the review feedback. Address ALL issues and areas for improvement identified in the review.

            Your revision should:
            1. Fix all identified problems while maintaining the strengths of the original
            2. Ensure completeness, accuracy, clarity, and depth
            3. Improve structure and formatting where needed
            4. Add or enhance content in areas identified as lacking
            5. Maintain a consistent, professional tone throughout

            Create a complete, revised version of the output that fully addresses the review feedback.

            ## Output Format
            Provide the complete revised output in markdown format. Include all sections from the original output, with improvements as needed.
            """

            # Query LLM for revised output
            system_prompt = "You are an expert content creator and editor with extensive experience revising academic and professional content. You excel at addressing feedback while maintaining the core strengths of the original work. Your revisions are thorough, thoughtful, and significantly improve the quality of the content."
            revised_output = self.query_llm(model, revision_prompt, system_prompt, max_tokens=8000)

            if revised_output:
                # Save the revised output
                self.save_output_file(output_dir, "output_revised.md", revised_output)

                # Update the primary output file
                self.save_output_file(output_dir, "output.md", revised_output)

                # Convert to HTML if needed
                if os.path.exists(os.path.join(output_dir, "output.html")):
                    html_content = self.generate_html_from_markdown(revised_output)
                    self.save_output_file(output_dir, "output.html", html_content)

                # Create task update
                self.create_task_update(
                    task_id,
                    agent_id,
                    "progress_update",
                    "Revised output based on review feedback"
                )

                # Perform a final review of the revised output
                final_review_prompt = f"""
                # Final Review

                ## Task Details
                - Title: {task['title']}
                - Description: {task['description']}

                ## Original Review Issues
                {review_response[:2000]}  # Include key parts of the original review

                ## Revised Output
                {revised_output[:15000]}  # Truncate if too large

                ## Instructions
                Perform a final review of the revised output. Verify that all issues identified in the original review have been addressed.

                ## Output Format
                Provide your final review in the following format:

                1. Overall Assessment: [Brief assessment of the revised output]
                2. Issues Addressed: [List of issues from the original review that have been successfully addressed]
                3. Remaining Issues (if any): [List of issues that still need attention]
                4. Final Verdict: [Whether the revised output is now acceptable]
                """

                # Query LLM for final review
                final_review = self.query_llm(model, final_review_prompt, system_prompt, max_tokens=2000)

                if final_review:
                    self.save_output_file(output_dir, "final_review.md", final_review)
                    self.create_task_update(
                        task_id,
                        agent_id,
                        "progress_update",
                        f"Completed final review: {final_review[:200]}..."
                    )

                primary_output = revised_output
        else:
            # If no revisions needed, create a completion note
            self.create_task_update(
                task_id,
                agent_id,
                "progress_update",
                "Output passed review with no revisions needed"
            )

        # Update progress
        self.update_task_status(task_id, "review", 90, "Review phase nearly complete", agent_id)

        logger.info(f"Review phase completed for task {task_id}")
        return primary_output

    def process_task(self, task, agent):
        """Process a task using the specified agent."""
        task_id = task['id']
        agent_id = agent['id']
        model = agent['model']

        logger.info(f"Processing task {task_id} with agent {agent_id} using model {model}")

        # Create output directory
        output_dir = self.create_task_output_dir(task_id)

        # Update task status to design stage
        self.update_task_status(task_id, "design", 0, "Starting design phase", agent_id)

        # 1. Planning Phase
        plan = self.planning_phase(task, agent, output_dir)
        if not plan:
            self.update_task_status(task_id, "not_started", 0, "Planning phase failed", agent_id)
            return False

        # Update progress
        self.update_task_status(task_id, "design", 100, "Design phase completed", agent_id)

        # 2. Research Phase (Build)
        self.update_task_status(task_id, "build", 0, "Starting research and build phase", agent_id)
        research_data = self.research_phase(task, agent, plan, output_dir)

        # Update progress
        self.update_task_status(task_id, "build", 100, "Research and build phase completed", agent_id)

        # 3. Execution Phase (Test)
        self.update_task_status(task_id, "test", 0, "Starting execution phase", agent_id)
        output_files = self.execution_phase(task, agent, plan, research_data, output_dir)

        # Update progress
        self.update_task_status(task_id, "test", 100, "Execution phase completed", agent_id)

        # 4. Review Phase
        self.update_task_status(task_id, "review", 0, "Starting review phase", agent_id)
        final_output = self.review_phase(task, agent, output_files, output_dir)

        # Update task result path
        self.update_task_result_path(task_id, output_dir)

        # Mark task as complete
        self.update_task_status(task_id, "complete", 100, "Task completed successfully", agent_id)

        logger.info(f"Task {task_id} completed successfully")
        return True

    def run(self, interval=15):
        """
        Main loop to continuously process tasks.

        Args:
            interval: Time in seconds to wait between checking for new tasks
        """
        logger.info("Starting task processor")

        try:
            while True:
                try:
                    # Reconnect to the database if needed
                    if self.conn is None:
                        self.connect_db()

                    # Get next task
                    task = self.get_next_task()

                    if task:
                        logger.info(f"Found task: {task['id']} - {task['title']}")

                        # Get available agent
                        agent = self.get_available_agent(task['complexity'])

                        if agent:
                            logger.info(f"Found available agent: {agent['id']} - {agent['name']}")

                            # Assign task to agent
                            if self.assign_task_to_agent(task['id'], agent['id']):
                                # Process task with timeout
                                try:
                                    # Set a timeout for task processing
                                    max_processing_time = 1800  # 30 minutes
                                    start_time = time.time()

                                    # Process the task
                                    self.process_task(task, agent)

                                    # Check if processing took too long
                                    if time.time() - start_time > max_processing_time:
                                        logger.warning(f"Task {task['id']} processing took too long, may be stuck")
                                except Exception as e:
                                    logger.error(f"Error processing task {task['id']}: {e}")
                                    # Reset task and agent status
                                    self.update_task_status(task['id'], "not_started", 0, f"Task processing failed: {str(e)}", agent['id'])
                                    self.cursor.execute(
                                        'UPDATE agents SET status = "available", last_active = ? WHERE id = ?',
                                        (datetime.now().isoformat(), agent['id'])
                                    )
                                    self.conn.commit()
                        else:
                            logger.info(f"No available agent for task {task['id']} (complexity: {task['complexity']})")

                            # Check if there are any stuck agents
                            self.cursor.execute(
                                'SELECT * FROM agents WHERE status = "busy"'
                            )
                            busy_agents = self.cursor.fetchall()

                            for busy_agent in busy_agents:
                                # Check when the agent was last active
                                last_active = datetime.fromisoformat(busy_agent['last_active'])
                                now = datetime.now()

                                # If the agent has been busy for more than 30 minutes, reset it
                                if (now - last_active).total_seconds() > 1800:  # 30 minutes
                                    logger.warning(f"Agent {busy_agent['id']} has been busy for too long, resetting")

                                    # Get the task assigned to this agent
                                    self.cursor.execute(
                                        'SELECT * FROM tasks WHERE assigned_agent_id = ?',
                                        (busy_agent['id'],)
                                    )
                                    stuck_task = self.cursor.fetchone()

                                    if stuck_task:
                                        # Reset the task
                                        self.update_task_status(stuck_task['id'], "not_started", 0, "Task reset due to timeout", busy_agent['id'])

                                    # Reset the agent
                                    self.cursor.execute(
                                        'UPDATE agents SET status = "available", last_active = ? WHERE id = ?',
                                        (datetime.now().isoformat(), busy_agent['id'])
                                    )
                                    self.conn.commit()
                    else:
                        logger.info("No tasks in queue")

                    # Wait for next check
                    logger.info(f"Waiting {interval} seconds before next check")
                    time.sleep(interval)

                except sqlite3.Error as e:
                    logger.error(f"Database error: {e}")
                    # Try to reconnect to the database
                    self.close_db()
                    time.sleep(5)
                    self.connect_db()
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Task processor stopped by user")
        except Exception as e:
            logger.error(f"Task processor error: {e}")
        finally:
            self.close_db()
            logger.info("Task processor stopped")


if __name__ == "__main__":
    # Create and run task processor
    processor = TaskProcessor()
    processor.run()
