"""
Argument Mapping Generator

Generates argument mapping diagrams that help students understand
different perspectives on a complex topic by showing supporting
and opposing arguments, evidence, and rebuttals.
"""

import os
import uuid
import logging
import json
from typing import Dict, Any, Optional
import asyncio

from .base_generator import BaseDiagramGenerator

# Set up logging
logger = logging.getLogger(__name__)

class ArgumentMappingGenerator(BaseDiagramGenerator):
    """
    Generates argument mapping diagrams showing supporting and opposing arguments.

    The argument map visualizes a central claim with supporting arguments on the left
    and opposing arguments on the right, including evidence and rebuttals.
    """

    def __init__(self, content_generator=None):
        """Initialize the argument mapping generator"""
        super().__init__()
        self.content_generator = content_generator
        logger.info(f"ARGUMENT MAP DEBUG: Initializing ArgumentMappingGenerator with content_generator: {content_generator.__class__.__name__ if content_generator else None}")
        self.template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates",
            "argument_mapping_template.html"
        )

        # Ensure the template exists
        if not os.path.exists(self.template_path):
            logger.warning(f"Argument mapping template not found at {self.template_path}")
            # Create the templates directory if it doesn't exist
            os.makedirs(os.path.dirname(self.template_path), exist_ok=True)

            # Create the template file with the content from the implementation
            with open(self.template_path, "w") as f:
                f.write(self._get_default_template())
            logger.info(f"Created default argument mapping template at {self.template_path}")

    def _generate_argument_map_sync(self, topic: str) -> Optional[str]:
        """
        Generate an argument map synchronously.
        This is a fallback method when the event loop is already running.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        try:
            logger.info(f"ARGUMENT MAP DEBUG: Generating argument map content synchronously for topic: {topic}")

            # Use the default argument map content
            argument_map_data = self._get_default_argument_map_content(topic)

            # Generate the diagram using the template
            template_data = {
                "title": f"Argument Mapping: {topic}",
                "description": f"This argument map shows different perspectives on {topic}, presenting supporting and opposing arguments with evidence and rebuttals.",
                "json_data": argument_map_data
            }

            # Generate the diagram
            return self.generate_diagram("argument_mapping", template_data, prefix="argument_map")
        except Exception as e:
            logger.error(f"Error in _generate_argument_map_sync: {str(e)}", exc_info=True)
            return None

    def generate_argument_map(self, topic: str) -> Optional[str]:
        """
        Generate an argument map for the given research topic.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        logger.info(f"ARGUMENT MAP DEBUG: generate_argument_map called for topic: {topic}")
        try:
            # Create a new event loop for async operations if needed
            try:
                logger.info(f"ARGUMENT MAP DEBUG: Getting event loop")
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    logger.info(f"ARGUMENT MAP DEBUG: Event loop closed, creating new one")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self.generate_argument_map_async(topic))
                else:
                    logger.info(f"ARGUMENT MAP DEBUG: Using existing event loop")
                    try:
                        result = loop.run_until_complete(self.generate_argument_map_async(topic))
                    except RuntimeError as e:
                        logger.warning(f"ARGUMENT MAP DEBUG: RuntimeError in run_until_complete: {str(e)}, using synchronous fallback")
                        result = self._generate_argument_map_sync(topic)
            except RuntimeError as re:
                # If we're already in an event loop
                logger.info(f"ARGUMENT MAP DEBUG: RuntimeError: {str(re)}, creating new loop")
                try:
                    new_loop = asyncio.new_event_loop()
                    result = new_loop.run_until_complete(self.generate_argument_map_async(topic))
                    new_loop.close()
                except RuntimeError as e:
                    logger.warning(f"ARGUMENT MAP DEBUG: RuntimeError in new loop: {str(e)}, using synchronous fallback")
                    result = self._generate_argument_map_sync(topic)

            logger.info(f"ARGUMENT MAP DEBUG: Argument map generation result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in generate_argument_map: {str(e)}", exc_info=True)
            return None

    async def generate_argument_map_async(self, topic: str) -> Optional[str]:
        """
        Generate an argument map asynchronously.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        try:
            # Generate argument map content using LLM
            argument_map_data = await self._generate_argument_map_content(topic)

            # Generate the diagram using the template
            template_data = {
                "title": f"Argument Mapping: {topic}",
                "description": f"This argument map shows different perspectives on {topic}, presenting supporting and opposing arguments with evidence and rebuttals.",
                "json_data": argument_map_data
            }

            # Generate the diagram
            return self.generate_diagram("argument_mapping", template_data, prefix="argument_map")
        except Exception as e:
            logger.error(f"Error in generate_argument_map_async: {str(e)}", exc_info=True)
            return None

    async def _generate_argument_map_content(self, topic: str) -> Dict[str, Any]:
        """
        Generate argument map content using the LLM.

        Args:
            topic: The research topic

        Returns:
            Dictionary with argument map content
        """
        if not self.content_generator:
            logger.warning("No content generator available, using default argument map content")
            return self._get_default_argument_map_content(topic)

        logger.info(f"ARGUMENT MAP DEBUG: Content generator available: {self.content_generator.__class__.__name__}")

        try:
            # Create the prompt for the LLM
            prompt = f"""
            Create an argument map for the topic: "{topic}"

            The argument map should show a central claim with supporting arguments on the left and opposing arguments on the right.

            GUIDANCE AND RULES:
            1. The central claim should be clear, specific, and genuinely debatable
            2. Include 3 supporting arguments and 3 opposing arguments
            3. Each argument should include a title, description, and evidence
            4. The first two arguments on each side should also include rebuttals
            5. Arguments should be strong representations of each side (not straw men)
            6. Evidence should include specific facts, statistics, or research findings when possible
            7. Rebuttals should address the strongest points of the opposing arguments
            8. Keep titles concise (3-6 words)
            9. Keep argument descriptions brief (15-25 words)
            10. Evidence should be specific and credible (20-30 words)
            11. Rebuttals should be concise but substantive (15-25 words)

            IMPORTANT: You MUST return ONLY a JSON object with no additional text, explanations, or markdown formatting.
            The JSON object must have this exact structure:
            {{
                "central_claim": "The main proposition being debated",
                "supporting_arguments": [
                    {{
                        "title": "First Supporting Argument",
                        "text": "Brief description of the argument",
                        "evidence": "Evidence supporting this argument",
                        "rebuttal": "Response to opposing arguments"
                    }},
                    {{
                        "title": "Second Supporting Argument",
                        "text": "Brief description of the argument",
                        "evidence": "Evidence supporting this argument",
                        "rebuttal": "Response to opposing arguments"
                    }},
                    {{
                        "title": "Third Supporting Argument",
                        "text": "Brief description of the argument",
                        "evidence": "Evidence supporting this argument"
                    }}
                ],
                "opposing_arguments": [
                    {{
                        "title": "First Opposing Argument",
                        "text": "Brief description of the argument",
                        "evidence": "Evidence supporting this argument",
                        "rebuttal": "Response to supporting arguments"
                    }},
                    {{
                        "title": "Second Opposing Argument",
                        "text": "Brief description of the argument",
                        "evidence": "Evidence supporting this argument",
                        "rebuttal": "Response to supporting arguments"
                    }},
                    {{
                        "title": "Third Opposing Argument",
                        "text": "Brief description of the argument",
                        "evidence": "Evidence supporting this argument"
                    }}
                ]
            }}

            DO NOT include any explanatory text, markdown formatting, or code blocks. Return ONLY the JSON object.

            IMPORTANT:
            - Ensure the central claim is genuinely debatable
            - Include a mix of logical, ethical, and practical arguments
            - Use real evidence rather than hypothetical examples when possible
            - Ensure rebuttals address the specific points made in opposing arguments
            - Avoid logical fallacies in both supporting and opposing arguments
            """

            # Generate content
            response = await self.content_generator.generate_content(prompt, max_tokens=2000)

            # Parse the JSON response
            try:
                # Extract JSON from the response (handle potential text before/after the JSON)
                json_str = response

                # Try to find JSON in the response
                if "```json" in response:
                    json_str = response.split("```json")[1].split("```")[0].strip()
                elif "```" in response:
                    json_str = response.split("```")[1].split("```")[0].strip()

                # Remove any leading/trailing non-JSON text
                json_str = json_str.strip()
                if json_str.startswith("{") and "}" in json_str:
                    # Find the last closing brace
                    end_idx = json_str.rindex("}")
                    json_str = json_str[:end_idx+1]

                logger.info(f"Attempting to parse JSON: {json_str[:100]}...")

                # Parse the JSON
                argument_map_data = json.loads(json_str)

                # Validate the structure
                self._validate_argument_map_data(argument_map_data)

                logger.info(f"Successfully generated argument map content for topic: {topic}")
                return argument_map_data
            except json.JSONDecodeError as jde:
                logger.error(f"Failed to parse JSON from LLM response: {response[:100]}...")
                logger.error(f"JSON decode error: {str(jde)}")

                # Try a more aggressive approach to extract JSON
                try:
                    # Find the first opening brace and last closing brace
                    if "{" in response and "}" in response:
                        start_idx = response.find("{")
                        end_idx = response.rindex("}")
                        json_str = response[start_idx:end_idx+1]
                        logger.info(f"Attempting aggressive JSON parsing: {json_str[:100]}...")
                        argument_map_data = json.loads(json_str)
                        self._validate_argument_map_data(argument_map_data)
                        logger.info(f"Successfully parsed JSON with aggressive approach")
                        return argument_map_data
                except Exception as e2:
                    logger.error(f"Aggressive JSON parsing also failed: {str(e2)}")
                    return self._get_default_argument_map_content(topic)

                return self._get_default_argument_map_content(topic)
            except Exception as e:
                logger.error(f"Error validating argument map data: {str(e)}")
                return self._get_default_argument_map_content(topic)
        except Exception as e:
            logger.error(f"Error generating argument map content: {str(e)}")
            return self._get_default_argument_map_content(topic)

    def _validate_argument_map_data(self, data: Dict[str, Any]) -> None:
        """
        Validate the argument map data structure.

        Args:
            data: The argument map data to validate

        Raises:
            ValueError: If the data structure is invalid
        """
        # Check required fields
        required_fields = ["central_claim", "supporting_arguments", "opposing_arguments"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Check supporting arguments
        if len(data["supporting_arguments"]) != 3:
            raise ValueError(f"Expected 3 supporting arguments, got {len(data['supporting_arguments'])}")

        for i, arg in enumerate(data["supporting_arguments"]):
            required_arg_fields = ["title", "text", "evidence"]
            for field in required_arg_fields:
                if field not in arg:
                    raise ValueError(f"Missing required field '{field}' in supporting argument {i+1}")

            # First two arguments should have rebuttals
            if i < 2 and "rebuttal" not in arg:
                raise ValueError(f"Missing required field 'rebuttal' in supporting argument {i+1}")

        # Check opposing arguments
        if len(data["opposing_arguments"]) != 3:
            raise ValueError(f"Expected 3 opposing arguments, got {len(data['opposing_arguments'])}")

        for i, arg in enumerate(data["opposing_arguments"]):
            required_arg_fields = ["title", "text", "evidence"]
            for field in required_arg_fields:
                if field not in arg:
                    raise ValueError(f"Missing required field '{field}' in opposing argument {i+1}")

            # First two arguments should have rebuttals
            if i < 2 and "rebuttal" not in arg:
                raise ValueError(f"Missing required field 'rebuttal' in opposing argument {i+1}")

    def _get_default_argument_map_content(self, topic: str) -> Dict[str, Any]:
        """
        Get default argument map content for a topic.

        Args:
            topic: The research topic

        Returns:
            Dictionary with default argument map content
        """
        # Create a default central claim based on the topic
        central_claim = f"The implementation of {topic} will have a net positive impact on society."

        return {
            "central_claim": central_claim,
            "supporting_arguments": [
                {
                    "title": "Increased Efficiency",
                    "text": "Implementation leads to significant improvements in efficiency and productivity.",
                    "evidence": "Studies show a 30-40% reduction in processing time and resource usage across multiple industries.",
                    "rebuttal": "While initial costs exist, long-term efficiency gains outweigh these investments within 2-3 years."
                },
                {
                    "title": "Economic Benefits",
                    "text": "Creates new job opportunities and economic growth in related sectors.",
                    "evidence": "Market analysis predicts creation of 500,000+ new specialized jobs globally by 2030.",
                    "rebuttal": "Job displacement is temporary and offset by growth in new roles requiring human creativity and oversight."
                },
                {
                    "title": "Quality Improvements",
                    "text": "Leads to higher quality outcomes and reduced error rates.",
                    "evidence": "Research demonstrates 60% reduction in critical errors when properly implemented in healthcare settings."
                }
            ],
            "opposing_arguments": [
                {
                    "title": "Implementation Costs",
                    "text": "High initial costs create barriers to adoption, especially for smaller organizations.",
                    "evidence": "Average implementation costs range from $500,000 to $2 million for mid-sized organizations.",
                    "rebuttal": "Phased implementation approaches and government incentives can mitigate initial cost barriers."
                },
                {
                    "title": "Job Displacement",
                    "text": "Will eliminate traditional jobs faster than new ones can be created.",
                    "evidence": "Automation potential threatens 15-20% of current workforce positions within 5 years.",
                    "rebuttal": "Historical technological shifts show net job creation when coupled with appropriate education and training programs."
                },
                {
                    "title": "Ethical Concerns",
                    "text": "Raises significant ethical questions about privacy, autonomy, and accountability.",
                    "evidence": "Survey data shows 68% of consumers express serious concerns about data privacy and algorithmic decision-making."
                }
            ]
        }

    def _get_default_template(self) -> str:
        """
        Get the default HTML template for argument mappings.

        Returns:
            String containing the HTML template
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Argument Mapping</title>
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
        .argument-map {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        .central-claim {
            text-align: center;
            margin-bottom: 40px;
        }
        .claim-box {
            background-color: #f0f7ff;
            border: 2px solid #3498db;
            border-radius: 10px;
            padding: 20px;
            display: inline-block;
            min-width: 60%;
            box-shadow: 0 3px 6px rgba(0,0,0,0.1);
        }
        .claim-text {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin: 0;
        }
        .arguments {
            display: flex;
            justify-content: space-between;
            margin-top: 30px;
        }
        .argument-column {
            width: 48%;
        }
        .argument-title {
            text-align: center;
            font-weight: bold;
            margin-bottom: 20px;
            padding: 10px;
            border-radius: 5px;
        }
        .supporting {
            background-color: #e8f5e9;
            color: #2e7d32;
        }
        .opposing {
            background-color: #ffebee;
            color: #c62828;
        }
        .argument {
            background-color: white;
            border: 2px solid #95a5a6;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .argument h3 {
            margin-top: 0;
            font-size: 16px;
        }
        .argument p {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 10px;
        }
        .evidence {
            background-color: #f8f9fa;
            border-left: 3px solid #95a5a6;
            padding: 8px 12px;
            margin-top: 10px;
            font-size: 13px;
        }
        .rebuttal {
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px dashed #ddd;
        }
        .rebuttal-title {
            font-weight: bold;
            font-size: 13px;
            color: #7b7b7b;
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
    </style>
</head>
<body>
    <div class="container">
        <h1>{{title}}</h1>
        <p class="description">
            {{description}}
        </p>

        <div class="argument-map">
            <div class="central-claim">
                <div class="claim-box">
                    <p class="claim-text">{{json_data.central_claim}}</p>
                </div>
            </div>

            <div class="connector"></div>
            <div class="connector-horizontal"></div>

            <div class="arguments">
                <div class="argument-column">
                    <div class="argument-title supporting">Supporting Arguments</div>

                    {% for arg in json_data.supporting_arguments %}
                    <div class="argument">
                        <h3>{{arg.title}}</h3>
                        <p>{{arg.text}}</p>
                        <div class="evidence">
                            Evidence: {{arg.evidence}}
                        </div>
                        {% if arg.rebuttal is defined %}
                        <div class="rebuttal">
                            <div class="rebuttal-title">Response to opposition:</div>
                            {{arg.rebuttal}}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>

                <div class="argument-column">
                    <div class="argument-title opposing">Opposing Arguments</div>

                    {% for arg in json_data.opposing_arguments %}
                    <div class="argument">
                        <h3>{{arg.title}}</h3>
                        <p>{{arg.text}}</p>
                        <div class="evidence">
                            Evidence: {{arg.evidence}}
                        </div>
                        {% if arg.rebuttal is defined %}
                        <div class="rebuttal">
                            <div class="rebuttal-title">Response to support:</div>
                            {{arg.rebuttal}}
                        </div>
                        {% endif %}
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""
