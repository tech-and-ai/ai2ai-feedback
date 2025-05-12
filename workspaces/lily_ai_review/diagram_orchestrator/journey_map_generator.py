"""
Journey Map Generator

Generates research journey maps showing different stakeholder perspectives
across phases of a research process.
"""

import os
import uuid
import logging
import json
from typing import Dict, List, Any, Optional
import asyncio
import re

from .base_generator import BaseDiagramGenerator

# Set up logging
logger = logging.getLogger(__name__)

class JourneyMapGenerator(BaseDiagramGenerator):
    """
    Generates journey maps showing stakeholder experiences across research phases.

    The journey map visualizes how different stakeholders experience the research
    process across 5 distinct phases, with emotional indicators for each touchpoint.
    """

    def __init__(self, content_generator=None):
        """Initialize the journey map generator"""
        super().__init__()
        self.content_generator = content_generator
        self.template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates",
            "journey_map_template.html"
        )

        # Ensure the template exists
        if not os.path.exists(self.template_path):
            logger.warning(f"Journey map template not found at {self.template_path}")
            # Create the templates directory if it doesn't exist
            os.makedirs(os.path.dirname(self.template_path), exist_ok=True)

            # Create the template file with the content from the implementation
            with open(self.template_path, "w") as f:
                f.write(self._get_default_template())
            logger.info(f"Created default journey map template at {self.template_path}")

    def generate_journey_map(self, topic: str) -> Optional[str]:
        """
        Generate a journey map for the given research topic.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        logger.info(f"JOURNEY MAP DEBUG: generate_journey_map called for topic: {topic}")
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                logger.info(f"JOURNEY MAP DEBUG: Getting event loop")

                # Check if the loop is running
                if loop.is_running():
                    logger.info(f"JOURNEY MAP DEBUG: Event loop is already running")

                    # Create a new event loop for this operation
                    import nest_asyncio
                    nest_asyncio.apply()
                    logger.info(f"JOURNEY MAP DEBUG: Applied nest_asyncio")

                    # Now we can use the loop safely
                    result = loop.run_until_complete(self.generate_journey_map_async(topic))
                else:
                    logger.info(f"JOURNEY MAP DEBUG: Event loop is not running")
                    # Run the async function in the existing loop
                    result = loop.run_until_complete(self.generate_journey_map_async(topic))
            except RuntimeError as e:
                logger.info(f"JOURNEY MAP DEBUG: RuntimeError: {str(e)}, creating new loop")
                # If we can't get the current loop, create a new one
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(self.generate_journey_map_async(topic))
                new_loop.close()

            logger.info(f"JOURNEY MAP DEBUG: Journey map generation result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in generate_journey_map: {str(e)}", exc_info=True)
            return None

    async def generate_journey_map_async(self, topic: str) -> Optional[str]:
        """
        Generate a journey map asynchronously.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        try:
            # Generate journey map content using LLM
            journey_map_data = await self._generate_journey_map_content(topic)

            # Generate the diagram using the template
            template_data = {
                "title": f"Research Journey Map: {topic}",
                "description": journey_map_data.get("description", f"This journey map shows how different stakeholders experience the research process for '{topic}'"),
                "json_data": journey_map_data
            }

            # Generate the diagram
            return self.generate_diagram("journey_map", template_data, prefix="journey_map")
        except Exception as e:
            logger.error(f"Error in generate_journey_map_async: {str(e)}", exc_info=True)
            return None

    async def _generate_journey_map_content(self, topic: str) -> Dict[str, Any]:
        """
        Generate journey map content using the LLM.

        Args:
            topic: The research topic

        Returns:
            Dictionary with journey map content
        """
        if not self.content_generator:
            logger.warning("No content generator available, using default journey map content")
            return self._get_default_journey_map_content(topic)

        try:
            # Create the prompt for the LLM
            prompt = f"""
            Create a research journey map for the topic: "{topic}"

            The journey map should show how 3 different stakeholders experience 5 phases of the research process.

            STRICT REQUIREMENTS:
            1. Exactly 3 stakeholders (rows)
            2. Exactly 5 phases (columns)
            3. Each touchpoint must have a short title (3-5 words) and brief description (8-12 words)
            4. Each touchpoint must have an emotional state: "positive", "neutral", or "negative"
            5. The journey map should tell a coherent story across all phases

            Return your response as a JSON object with this exact structure:
            {{
                "title": "Research Journey Map: {topic}",
                "description": "A brief description of what this journey map shows",
                "phases": [
                    {{
                        "name": "Phase 1 Name",
                        "description": "Brief description of phase 1"
                    }},
                    ... (5 phases total)
                ],
                "stakeholders": [
                    "Stakeholder 1 Name",
                    "Stakeholder 2 Name",
                    "Stakeholder 3 Name"
                ],
                "touchpoints": [
                    [
                        {{
                            "title": "Touchpoint 1-1 Title",
                            "description": "Description of touchpoint 1-1",
                            "emotion": "positive"
                        }},
                        ... (5 touchpoints for stakeholder 1)
                    ],
                    [
                        {{
                            "title": "Touchpoint 2-1 Title",
                            "description": "Description of touchpoint 2-1",
                            "emotion": "neutral"
                        }},
                        ... (5 touchpoints for stakeholder 2)
                    ],
                    [
                        {{
                            "title": "Touchpoint 3-1 Title",
                            "description": "Description of touchpoint 3-1",
                            "emotion": "negative"
                        }},
                        ... (5 touchpoints for stakeholder 3)
                    ]
                ]
            }}

            IMPORTANT: Ensure all text is concise and fits within the specified word limits.
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
                journey_map_data = json.loads(json_str)

                # Validate the structure
                self._validate_journey_map_data(journey_map_data)

                logger.info(f"Successfully generated journey map content for topic: {topic}")
                return journey_map_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON from LLM response: {response[:100]}... Error: {str(e)}")
                # Try a more aggressive approach to extract JSON
                try:
                    # Try to extract JSON object using regex
                    json_match = re.search(r'\{[^\{\}]*(\{[^\{\}]*\}[^\{\}]*)*\}', response)
                    if json_match:
                        json_str = json_match.group(0)
                        journey_map_data = json.loads(json_str)
                        logger.info(f"Successfully extracted JSON using regex for topic: {topic}")
                        
                        # Validate the structure
                        self._validate_journey_map_data(journey_map_data)
                        return journey_map_data
                except Exception as e2:
                    logger.error(f"Failed to extract JSON using regex: {str(e2)}")
                
                # If all attempts fail, use default content
                return self._get_default_journey_map_content(topic)
            except Exception as e:
                logger.error(f"Error validating journey map data: {str(e)}")
                return self._get_default_journey_map_content(topic)
        except Exception as e:
            logger.error(f"Error generating journey map content: {str(e)}")
            return self._get_default_journey_map_content(topic)

    def _validate_journey_map_data(self, data: Dict[str, Any]) -> None:
        """
        Validate the journey map data structure.

        Args:
            data: The journey map data to validate

        Raises:
            ValueError: If the data structure is invalid
        """
        # Check required fields
        required_fields = ["title", "description", "phases", "stakeholders", "touchpoints"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Check phases
        if len(data["phases"]) != 5:
            raise ValueError(f"Expected 5 phases, got {len(data['phases'])}")

        for phase in data["phases"]:
            if "name" not in phase or "description" not in phase:
                raise ValueError("Each phase must have a name and description")

        # Check stakeholders
        if len(data["stakeholders"]) != 3:
            raise ValueError(f"Expected 3 stakeholders, got {len(data['stakeholders'])}")

        # Check touchpoints
        if len(data["touchpoints"]) != 3:
            raise ValueError(f"Expected 3 rows of touchpoints, got {len(data['touchpoints'])}")

        for i, row in enumerate(data["touchpoints"]):
            if len(row) != 5:
                raise ValueError(f"Expected 5 touchpoints in row {i+1}, got {len(row)}")

            for j, touchpoint in enumerate(row):
                required_touchpoint_fields = ["title", "description", "emotion"]
                for field in required_touchpoint_fields:
                    if field not in touchpoint:
                        raise ValueError(f"Missing required field '{field}' in touchpoint {i+1}-{j+1}")

                # Validate emotion
                if touchpoint["emotion"] not in ["positive", "neutral", "negative"]:
                    raise ValueError(f"Invalid emotion '{touchpoint['emotion']}' in touchpoint {i+1}-{j+1}")

    def _get_default_journey_map_content(self, topic: str) -> Dict[str, Any]:
        """
        Get default journey map content for a topic.

        Args:
            topic: The research topic

        Returns:
            Dictionary with default journey map content
        """
        return {
            "title": f"Research Journey Map: {topic}",
            "description": f"This journey map shows how different stakeholders experience the research process for '{topic}'",
            "phases": [
                {
                    "name": "Exploration",
                    "description": "Initial discovery and question formation"
                },
                {
                    "name": "Planning",
                    "description": "Developing methodology and approach"
                },
                {
                    "name": "Data Collection",
                    "description": "Gathering information and evidence"
                },
                {
                    "name": "Analysis",
                    "description": "Interpreting findings and patterns"
                },
                {
                    "name": "Synthesis",
                    "description": "Drawing conclusions and implications"
                }
            ],
            "stakeholders": [
                "Student Researcher",
                "Academic Advisor",
                "Research Participant"
            ],
            "touchpoints": [
                [
                    {
                        "title": "Initial Curiosity",
                        "description": "Excitement about discovering new knowledge and insights",
                        "emotion": "positive"
                    },
                    {
                        "title": "Method Selection",
                        "description": "Choosing appropriate research methods and tools",
                        "emotion": "neutral"
                    },
                    {
                        "title": "Field Challenges",
                        "description": "Encountering unexpected obstacles during data collection",
                        "emotion": "negative"
                    },
                    {
                        "title": "Pattern Recognition",
                        "description": "Identifying meaningful patterns in collected data",
                        "emotion": "positive"
                    },
                    {
                        "title": "Knowledge Creation",
                        "description": "Developing new understanding and theoretical insights",
                        "emotion": "positive"
                    }
                ],
                [
                    {
                        "title": "Guiding Questions",
                        "description": "Helping refine research questions and scope",
                        "emotion": "positive"
                    },
                    {
                        "title": "Methodology Review",
                        "description": "Providing feedback on research design choices",
                        "emotion": "neutral"
                    },
                    {
                        "title": "Progress Monitoring",
                        "description": "Checking in on data collection progress",
                        "emotion": "neutral"
                    },
                    {
                        "title": "Critical Feedback",
                        "description": "Challenging assumptions in preliminary analysis",
                        "emotion": "negative"
                    },
                    {
                        "title": "Validation",
                        "description": "Confirming the validity of research findings",
                        "emotion": "positive"
                    }
                ],
                [
                    {
                        "title": "Initial Contact",
                        "description": "Being approached to participate in research",
                        "emotion": "neutral"
                    },
                    {
                        "title": "Consent Process",
                        "description": "Understanding research purpose and providing consent",
                        "emotion": "neutral"
                    },
                    {
                        "title": "Active Participation",
                        "description": "Sharing experiences and providing requested information",
                        "emotion": "positive"
                    },
                    {
                        "title": "Follow-up Questions",
                        "description": "Responding to additional inquiries during analysis",
                        "emotion": "neutral"
                    },
                    {
                        "title": "Results Sharing",
                        "description": "Receiving findings and seeing contribution valued",
                        "emotion": "positive"
                    }
                ]
            ]
        }

    def _get_default_template(self) -> str:
        """
        Get the default HTML template for journey maps.

        Returns:
            String containing the HTML template
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Journey Map Template</title>
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
            max-width: 1200px;
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
        .journey-map {
            width: 100%;
            overflow-x: auto;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .journey-grid {
            display: grid;
            grid-template-columns: 150px repeat(5, 1fr);
            grid-gap: 10px;
            min-width: 900px;
        }
        .phase-header {
            text-align: center;
            font-weight: bold;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 5px;
        }
        .phase-description {
            text-align: center;
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
        .stakeholder-label {
            font-weight: bold;
            display: flex;
            align-items: center;
            padding: 10px;
        }
        .touchpoint {
            border-radius: 10px;
            padding: 15px;
            height: 100px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            box-shadow: 2px 2px 3px rgba(0,0,0,0.2);
            background-color: white;
        }
        .touchpoint-title {
            font-weight: bold;
            margin-bottom: 8px;
        }
        .touchpoint-description {
            font-size: 12px;
            color: #555;
        }
        .positive {
            border: 2px solid #8BC34A;
        }
        .neutral {
            border: 2px solid #FFC107;
        }
        .negative {
            border: 2px solid #E57373;
        }
        .milestone {
            position: relative;
        }
        .milestone::after {
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            right: -5px;
            width: 1px;
            background-color: #aaa;
            border-right: 1px dashed #666;
        }
        .legend {
            display: flex;
            justify-content: center;
            margin-top: 20px;
        }
        .legend-item {
            display: flex;
            align-items: center;
            margin: 0 10px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            margin-right: 8px;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{title}}</h1>
        <p class="description">
            {{description}}
        </p>

        <div class="journey-map">
            <div class="journey-grid">
                <!-- Phase Headers -->
                <div></div>
                {% for phase in json_data.phases %}
                <div class="phase-header {% if loop.index == 3 or loop.index == 4 %}milestone{% endif %}">
                    {{phase.name}}
                    <div class="phase-description">{{phase.description}}</div>
                </div>
                {% endfor %}

                <!-- Stakeholder Rows -->
                {% for stakeholder_idx in range(json_data.stakeholders|length) %}
                <div class="stakeholder-label">{{json_data.stakeholders[stakeholder_idx]}}</div>

                {% for touchpoint_idx in range(json_data.touchpoints[stakeholder_idx]|length) %}
                <div class="touchpoint {{json_data.touchpoints[stakeholder_idx][touchpoint_idx].emotion}}">
                    <div class="touchpoint-title">{{json_data.touchpoints[stakeholder_idx][touchpoint_idx].title}}</div>
                    <div class="touchpoint-description">{{json_data.touchpoints[stakeholder_idx][touchpoint_idx].description}}</div>
                </div>
                {% endfor %}

                {% endfor %}
            </div>
        </div>

        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: white; border: 2px solid #8BC34A;"></div>
                <span>Positive Experience</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: white; border: 2px solid #FFC107;"></div>
                <span>Neutral Experience</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: white; border: 2px solid #E57373;"></div>
                <span>Challenging Experience</span>
            </div>
        </div>
    </div>
</body>
</html>"""
