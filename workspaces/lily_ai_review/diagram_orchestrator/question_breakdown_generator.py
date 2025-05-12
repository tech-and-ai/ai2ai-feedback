"""
Question Breakdown Generator

Generates research question breakdown diagrams that help students
understand how to approach complex research topics by breaking them down
into manageable sub-questions of different types.
"""

import os
import uuid
import logging
import json
from typing import Dict, Any, Optional
import asyncio
import re

from .base_generator import BaseDiagramGenerator

# Set up logging
logger = logging.getLogger(__name__)

class QuestionBreakdownGenerator(BaseDiagramGenerator):
    """
    Generates question breakdown diagrams showing how to approach complex research topics.

    The question breakdown visualizes a main research question broken down into 6 sub-questions
    of different types (factual, analytical, evaluative, and ethical).
    """

    def __init__(self, content_generator=None):
        """Initialize the question breakdown generator"""
        super().__init__()
        self.content_generator = content_generator
        self.template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates",
            "question_breakdown_template.html"
        )

        # Ensure the template exists
        if not os.path.exists(self.template_path):
            logger.warning(f"Question breakdown template not found at {self.template_path}")
            # Create the templates directory if it doesn't exist
            os.makedirs(os.path.dirname(self.template_path), exist_ok=True)

            # Create the template file with the content from the implementation
            with open(self.template_path, "w") as f:
                f.write(self._get_default_template())
            logger.info(f"Created default question breakdown template at {self.template_path}")

    def generate_question_breakdown(self, topic: str) -> Optional[str]:
        """
        Generate a question breakdown diagram for the given research topic.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        logger.info(f"QUESTION BREAKDOWN DEBUG: generate_question_breakdown called for topic: {topic}")
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                logger.info(f"QUESTION BREAKDOWN DEBUG: Getting event loop")

                # Check if the loop is running
                if loop.is_running():
                    logger.info(f"QUESTION BREAKDOWN DEBUG: Event loop is already running")

                    # Create a new event loop for this operation
                    import nest_asyncio
                    nest_asyncio.apply()
                    logger.info(f"QUESTION BREAKDOWN DEBUG: Applied nest_asyncio")

                    # Now we can use the loop safely
                    result = loop.run_until_complete(self.generate_question_breakdown_async(topic))
                else:
                    logger.info(f"QUESTION BREAKDOWN DEBUG: Event loop is not running")
                    # Run the async function in the existing loop
                    result = loop.run_until_complete(self.generate_question_breakdown_async(topic))
            except RuntimeError as e:
                logger.info(f"QUESTION BREAKDOWN DEBUG: RuntimeError: {str(e)}, creating new loop")
                # If we can't get the current loop, create a new one
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(self.generate_question_breakdown_async(topic))
                new_loop.close()

            logger.info(f"QUESTION BREAKDOWN DEBUG: Question breakdown generation result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in generate_question_breakdown: {str(e)}", exc_info=True)
            return None

    async def generate_question_breakdown_async(self, topic: str) -> Optional[str]:
        """
        Generate a question breakdown diagram asynchronously.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        try:
            # Generate question breakdown content using LLM
            question_breakdown_data = await self._generate_question_breakdown_content(topic)

            # Generate the diagram using the template
            template_data = {
                "title": f"Research Question Breakdown: {topic}",
                "description": f"Breaking down the main research question into focused sub-questions helps organize your research on '{topic}' and ensures you cover all important aspects of the topic.",
                "json_data": question_breakdown_data
            }

            # Generate the diagram
            return self.generate_diagram("question_breakdown", template_data, prefix="question_breakdown")
        except Exception as e:
            logger.error(f"Error in generate_question_breakdown_async: {str(e)}", exc_info=True)
            return None

    async def _generate_question_breakdown_content(self, topic: str) -> Dict[str, Any]:
        """
        Generate question breakdown content using the LLM.

        Args:
            topic: The research topic

        Returns:
            Dictionary with question breakdown content
        """
        if not self.content_generator:
            logger.warning("No content generator available, using default question breakdown content")
            return self._get_default_question_breakdown_content(topic)

        try:
            # Create the prompt for the LLM
            prompt = f"""
            Create a research question breakdown for the topic: "{topic}"

            The breakdown should include a main research question and 4 sub-questions that help students approach the topic systematically.

            GUIDANCE AND RULES:
            1. The main question should be clear, specific, and focused on the topic
            2. Sub-questions should be diverse and cover different aspects of the topic
            3. Include exactly one question of each type for balanced research:
               - Factual questions (blue): Focus on identifying existing information, technologies, or challenges
                 Example: "What AI technologies are currently being used in education?"

               - Analytical questions (purple): Focus on examining relationships, comparisons, or patterns
                 Example: "How do different learning approaches compare when using AI tools?"

               - Evaluative questions (orange): Focus on assessing effectiveness, quality, or impact
                 Example: "What evidence exists for the effectiveness of AI in improving learning outcomes?"

               - Ethical questions (green): Focus on moral implications, privacy, equity, or social concerns
                 Example: "What privacy concerns arise when implementing AI in educational settings?"

            4. Sub-questions should progress from basic factual information to more complex analysis
            5. Keep question titles very concise (under 10 words)
            6. Keep descriptions extremely brief (10-15 words maximum)
            7. Questions should be specific enough to guide research but open enough to require investigation
            8. Avoid questions that can be answered with a simple yes/no
            9. Focus on questions that encourage critical thinking and deeper research

            Return your response as a JSON object with this exact structure:
            {{
                "main_question": "What is the main research question?",
                "sub_questions": [
                    {{
                        "question": "Sub-question 1",
                        "description": "Brief description of what this sub-question explores",
                        "type": "factual"
                    }},
                    ... (4 sub-questions total, one of each type)
                ]
            }}

            IMPORTANT:
            - Ensure you include exactly 4 sub-questions (one of each type)
            - Each sub-question must have a type that is one of: "factual", "analytical", "evaluative", or "ethical"
            - Make sure the questions are diverse and cover different aspects of the topic
            - Keep all text extremely concise to ensure the diagram fits on a single A4 page
            """

            # Generate content
            response = await self.content_generator.generate_content(prompt, max_tokens=2000)

            # Parse the JSON response
            try:
                # Extract JSON from the response (handle potential text before/after the JSON)
                json_str = response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()

                # Try to fix common JSON formatting issues
                # Remove any non-JSON text before or after the JSON object
                json_str = re.sub(r'^[^{]*', '', json_str)
                json_str = re.sub(r'[^}]*$', '', json_str)
                # Fix any trailing commas before closing brackets
                json_str = re.sub(r',\s*}', '}', json_str)
                json_str = re.sub(r',\s*]', ']', json_str)

                # Parse the JSON
                question_breakdown_data = json.loads(json_str)

                # Validate the structure
                self._validate_question_breakdown_data(question_breakdown_data)

                logger.info(f"Successfully generated question breakdown content for topic: {topic}")
                return question_breakdown_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {response[:100]}... Error: {str(e)}")
                # Try a more aggressive approach to extract JSON
                try:
                    # Try to extract JSON object using regex
                    json_match = re.search(r'\{[^\{\}]*(\{[^\{\}]*\}[^\{\}]*)*\}', response)
                    if json_match:
                        json_str = json_match.group(0)
                        question_breakdown_data = json.loads(json_str)
                        logger.info(f"Successfully extracted JSON using regex for topic: {topic}")

                        # Validate the structure
                        self._validate_question_breakdown_data(question_breakdown_data)
                        return question_breakdown_data
                except Exception as e2:
                    logger.error(f"Failed to extract JSON using regex: {str(e2)}")

                # If all attempts fail, use default content
                return self._get_default_question_breakdown_content(topic)
            except Exception as e:
                logger.error(f"Error validating question breakdown data: {str(e)}")
                return self._get_default_question_breakdown_content(topic)
        except Exception as e:
            logger.error(f"Error generating question breakdown content: {str(e)}")
            return self._get_default_question_breakdown_content(topic)

    def _validate_question_breakdown_data(self, data: Dict[str, Any]) -> None:
        """
        Validate the question breakdown data structure.

        Args:
            data: The question breakdown data to validate

        Raises:
            ValueError: If the data structure is invalid
        """
        # Check required fields
        if "main_question" not in data:
            raise ValueError("Missing required field: main_question")

        if "sub_questions" not in data:
            raise ValueError("Missing required field: sub_questions")

        # Check sub-questions
        if len(data["sub_questions"]) != 4:
            raise ValueError(f"Expected 4 sub-questions, got {len(data['sub_questions'])}")

        # Check that we have at least one of each question type
        question_types = set()
        for sub_question in data["sub_questions"]:
            if "question" not in sub_question:
                raise ValueError("Each sub-question must have a 'question' field")

            if "description" not in sub_question:
                raise ValueError("Each sub-question must have a 'description' field")

            if "type" not in sub_question:
                raise ValueError("Each sub-question must have a 'type' field")

            if sub_question["type"] not in ["factual", "analytical", "evaluative", "ethical"]:
                raise ValueError(f"Invalid question type: {sub_question['type']}")

            question_types.add(sub_question["type"])

        # Check that we have at least one of each question type
        required_types = {"factual", "analytical", "evaluative", "ethical"}
        missing_types = required_types - question_types
        if missing_types:
            raise ValueError(f"Missing question types: {missing_types}")

    def _get_default_question_breakdown_content(self, topic: str) -> Dict[str, Any]:
        """
        Get default question breakdown content for a topic.

        Args:
            topic: The research topic

        Returns:
            Dictionary with default question breakdown content
        """
        main_question = f"How does {topic} impact society and what are its implications?"

        return {
            "main_question": main_question,
            "sub_questions": [
                {
                    "question": f"What are the key applications of {topic}?",
                    "description": "Identify current implementations and use cases.",
                    "type": "factual"
                },
                {
                    "question": f"How does {topic} compare to alternatives?",
                    "description": "Analyze advantages and disadvantages versus traditional methods.",
                    "type": "analytical"
                },
                {
                    "question": f"How effective is {topic}?",
                    "description": "Assess evidence of success and impact.",
                    "type": "evaluative"
                },
                {
                    "question": f"What ethical issues arise from {topic}?",
                    "description": "Examine privacy concerns and potential consequences.",
                    "type": "ethical"
                }
            ]
        }

    def _get_default_template(self) -> str:
        """
        Get the default HTML template for question breakdowns.

        Returns:
            String containing the HTML template
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Research Question Breakdown</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f9f9f9;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #444;
            margin-bottom: 10px;
        }
        .description {
            text-align: center;
            margin-bottom: 30px;
            color: #666;
        }
        .question-breakdown {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .main-question {
            text-align: center;
            margin-bottom: 40px;
        }
        .main-question-box {
            background-color: #f0f7ff;
            border: 2px solid #3498db;
            border-radius: 10px;
            padding: 20px;
            display: inline-block;
            min-width: 60%;
            box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        }
        .main-question-text {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
        }
        .sub-questions {
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
        }
        .sub-question {
            background-color: white;
            border: 2px solid #95a5a6;
            border-radius: 8px;
            padding: 15px;
            width: calc(50% - 40px);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            position: relative;
        }
        .sub-question::before {
            content: "";
            position: absolute;
            top: -20px;
            left: 50%;
            width: 2px;
            height: 20px;
            background-color: #95a5a6;
        }
        .sub-question h3 {
            margin-top: 0;
            color: #34495e;
            font-size: 16px;
        }
        .sub-question p {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 0;
        }
        .connector {
            width: 2px;
            height: 30px;
            background-color: #95a5a6;
            margin: 0 auto;
        }
        .connector-horizontal {
            width: 80%;
            height: 2px;
            background-color: #95a5a6;
            margin: 0 auto 20px auto;
        }

        /* Color-coding for different types of sub-questions */
        .factual {
            border-color: #3498db;
        }
        .factual h3 {
            color: #3498db;
        }
        .factual::before {
            background-color: #3498db;
        }

        .analytical {
            border-color: #9b59b6;
        }
        .analytical h3 {
            color: #9b59b6;
        }
        .analytical::before {
            background-color: #9b59b6;
        }

        .evaluative {
            border-color: #e67e22;
        }
        .evaluative h3 {
            color: #e67e22;
        }
        .evaluative::before {
            background-color: #e67e22;
        }

        .ethical {
            border-color: #27ae60;
        }
        .ethical h3 {
            color: #27ae60;
        }
        .ethical::before {
            background-color: #27ae60;
        }

        .legend {
            display: flex;
            justify-content: center;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 0 15px 10px 15px;
        }
        .legend-color {
            width: 15px;
            height: 15px;
            margin-right: 8px;
            border-radius: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{title}}</h1>
        <p class="description">
            {{description}}
        </p>

        <div class="question-breakdown">
            <div class="main-question">
                <div class="main-question-box">
                    <p class="main-question-text">{{json_data.main_question}}</p>
                </div>
            </div>

            <div class="connector"></div>
            <div class="connector-horizontal"></div>

            <div class="sub-questions">
                {% for sub_question in json_data.sub_questions %}
                <div class="sub-question {{sub_question.type}}">
                    <h3>{{sub_question.question}}</h3>
                    <p>{{sub_question.description}}</p>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: #3498db;"></div>
                <span>Factual Questions</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #9b59b6;"></div>
                <span>Analytical Questions</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #e67e22;"></div>
                <span>Evaluative Questions</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #27ae60;"></div>
                <span>Ethical Questions</span>
            </div>
        </div>
    </div>
</body>
</html>"""
