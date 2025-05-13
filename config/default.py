"""
Default Configuration

This module defines the default configuration for the AI2AI Feedback System.
"""

CONFIG = {
    # Server configuration
    'host': '0.0.0.0',
    'port': 8000,

    # Database configuration
    'database_url': 'ai2ai_feedback.db',

    # Logging configuration
    'log_level': 'info',

    # Model providers configuration
    'model_providers': {
        'ollama': {
            'type': 'ollama',
            'base_url': 'http://192.168.0.77:11434',
            'timeout': 120,  # Increased timeout for larger model
            'supported_models': [
                'deepseek-coder-v2:16b'
            ]
        }
    },

    # Prompt templates configuration
    'prompt_templates': {
        # System prompts
        'system_default': {
            'content': 'You are a helpful AI assistant.'
        },
        'system_gemma3:4b': {
            'content': 'You are a helpful AI assistant powered by the Gemma 3 4B model. You excel at understanding and generating human-like text across a wide range of topics.'
        },
        'system_gemma3:1b': {
            'content': 'You are a helpful AI assistant powered by the Gemma 3 1B model. You are designed to be efficient and responsive while providing helpful information.'
        },
        'system_deepseek-coder-v2:16b': {
            'content': 'You are a helpful AI assistant powered by the DeepSeek Coder model. You excel at understanding and generating code across various programming languages. You provide clear, efficient, and well-documented code solutions.'
        },

        # Task stage prompts
        'planning_default': {
            'content': '''
            # Task Planning

            ## Task Details
            - Title: ${task_title}
            - Description: ${task_description}

            ## Instructions
            Please create a detailed plan for completing this task. Your plan should include:

            1. A breakdown of the task into smaller, manageable steps
            2. The resources and information needed for each step
            3. Any potential challenges or obstacles
            4. A timeline for completion
            5. Success criteria for the task

            Be specific, thorough, and organized in your planning.
            '''
        },
        'research_default': {
            'content': '''
            # Task Research

            ## Task Details
            - Title: ${task_title}
            - Description: ${task_description}

            ## Task Plan
            ${task_metadata_plan}

            ## Instructions
            Based on the task details and plan above, conduct research to gather the necessary information. Your research should:

            1. Focus on the key areas identified in the plan
            2. Gather information from reliable and up-to-date sources
            3. Organize the information in a clear and structured way
            4. Identify any gaps or contradictions in the information
            5. Provide citations for all information

            Be thorough, accurate, and comprehensive in your research.
            '''
        },
        'execution_default': {
            'content': '''
            # Task Execution

            ## Task Details
            - Title: ${task_title}
            - Description: ${task_description}

            ## Task Plan
            ${task_metadata_plan}

            ## Research Summary
            ${task_metadata_research}

            ## Instructions
            Based on the task details, plan, and research above, create the complete output for this task. Your output should:

            1. Adhere strictly to the output structure defined in the plan
            2. Incorporate key findings from the research
            3. Be accurate, well-organized, and comprehensive
            4. Use proper citations when referencing external sources
            5. Include all required elements (introduction, body, conclusion, etc.)
            6. Maintain a professional, authoritative tone throughout
            7. Be formatted appropriately with headings, subheadings, lists, etc.

            Be creative, thorough, and focused on delivering high-quality output.
            '''
        },
        'review_default': {
            'content': '''
            # Task Review

            ## Task Details
            - Title: ${task_title}
            - Description: ${task_description}

            ## Task Output
            ${task_metadata_output}

            ## Instructions
            Please review the task output above and provide a comprehensive assessment. Your review should:

            1. Evaluate how well the output meets the task requirements
            2. Identify any errors, omissions, or areas for improvement
            3. Assess the quality, clarity, and organization of the output
            4. Suggest specific improvements or corrections
            5. Provide an overall rating (1-10) with justification

            Be thorough, constructive, and specific in your feedback.
            '''
        }
    },

    # Research service configuration
    'research': {
        'search': {
            'provider': 'duckduckgo',
            'timeout': 30
        },
        'extractor': {
            'timeout': 30
        }
    },

    # Execution environment configuration
    'execution': {
        'timeout': 30,
        'max_memory': '256m',
        'base_dir': 'sandbox'
    }
}
