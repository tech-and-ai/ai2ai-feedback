"""
Comparative Analysis Generator

Generates comparative analysis diagrams that help students understand
the strengths, weaknesses, and trade-offs between different approaches
by evaluating them across multiple criteria.
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

class ComparativeAnalysisGenerator(BaseDiagramGenerator):
    """
    Generates comparative analysis diagrams showing different approaches evaluated across criteria.

    The comparative analysis visualizes three different approaches or perspectives on a topic,
    evaluating them across multiple criteria with ratings and notes.
    """

    def __init__(self, content_generator=None):
        """Initialize the comparative analysis generator"""
        super().__init__()
        self.content_generator = content_generator
        self.template_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "templates",
            "comparative_analysis_template.html"
        )

        # Ensure the template exists
        if not os.path.exists(self.template_path):
            logger.warning(f"Comparative analysis template not found at {self.template_path}")
            # Create the templates directory if it doesn't exist
            os.makedirs(os.path.dirname(self.template_path), exist_ok=True)

            # Create the template file with the content from the implementation
            with open(self.template_path, "w") as f:
                f.write(self._get_default_template())
            logger.info(f"Created default comparative analysis template at {self.template_path}")

    def generate_comparative_analysis(self, topic: str) -> Optional[str]:
        """
        Generate a comparative analysis for the given research topic.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        logger.info(f"COMPARATIVE ANALYSIS DEBUG: generate_comparative_analysis called for topic: {topic}")
        try:
            # Create a new event loop for async operations if needed
            try:
                logger.info(f"COMPARATIVE ANALYSIS DEBUG: Getting event loop")
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    logger.info(f"COMPARATIVE ANALYSIS DEBUG: Event loop closed, creating new one")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(self.generate_comparative_analysis_async(topic))
                else:
                    logger.info(f"COMPARATIVE ANALYSIS DEBUG: Using existing event loop")
                    result = loop.run_until_complete(self.generate_comparative_analysis_async(topic))
            except RuntimeError as re:
                # If we're already in an event loop
                logger.info(f"COMPARATIVE ANALYSIS DEBUG: RuntimeError: {str(re)}, creating new loop")
                new_loop = asyncio.new_event_loop()
                result = new_loop.run_until_complete(self.generate_comparative_analysis_async(topic))
                new_loop.close()

            logger.info(f"COMPARATIVE ANALYSIS DEBUG: Comparative analysis generation result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error in generate_comparative_analysis: {str(e)}", exc_info=True)
            return None

    async def generate_comparative_analysis_async(self, topic: str) -> Optional[str]:
        """
        Generate a comparative analysis asynchronously.

        Args:
            topic: The research topic

        Returns:
            Path to the generated PNG file or None if generation fails
        """
        try:
            # Generate comparative analysis content using LLM
            comparative_analysis_data = await self._generate_comparative_analysis_content(topic)

            # Generate the diagram using the template
            template_data = {
                "title": f"Comparative Analysis: {topic}",
                "description": f"This comparative analysis evaluates three different approaches to {topic} across multiple criteria.",
                "json_data": comparative_analysis_data
            }

            # Generate the diagram
            return self.generate_diagram("comparative_analysis", template_data, prefix="comparative_analysis")
        except Exception as e:
            logger.error(f"Error in generate_comparative_analysis_async: {str(e)}", exc_info=True)
            return None

    async def _generate_comparative_analysis_content(self, topic: str) -> Dict[str, Any]:
        """
        Generate comparative analysis content using the LLM.

        Args:
            topic: The research topic

        Returns:
            Dictionary with comparative analysis content
        """
        if not self.content_generator:
            logger.warning("No content generator available, using default comparative analysis content")
            return self._get_default_comparative_analysis_content(topic)

        try:
            # Create the prompt for the LLM
            prompt = f"""
            Create a comparative analysis for the topic: "{topic}"

            The comparative analysis should compare three different approaches or perspectives on the topic across exactly 6 criteria.

            GUIDANCE AND RULES:
            1. Choose three distinct approaches that represent different perspectives or methods
            2. Select exactly 6 criteria that highlight meaningful differences between approaches
            3. Use a mix of objective and evaluative criteria
            4. For rated criteria (2, 3, 5), be fair and consistent in applying ratings (high, medium, low)
            5. Keep cell content extremely concise (3-8 words for most cells)
            6. Notes should provide important context but remain very brief (3-5 words)
            7. Ensure the comparison is balanced and doesn't obviously favor one approach

            IMPORTANT: You MUST return ONLY a JSON object with no additional text, explanations, or markdown formatting.
            The JSON object must have this exact structure:
            {{
                "approaches": [
                    "First Approach Name",
                    "Second Approach Name",
                    "Third Approach Name"
                ],
                "criteria": [
                    "First Criteria Name",
                    "Second Criteria Name",
                    "Third Criteria Name",
                    "Fourth Criteria Name",
                    "Fifth Criteria Name",
                    "Sixth Criteria Name"
                ],
                "cells": [
                    [
                        {{
                            "content": "Content for Approach 1, Criteria 1"
                        }},
                        {{
                            "content": "Content for Approach 2, Criteria 1"
                        }},
                        {{
                            "content": "Content for Approach 3, Criteria 1"
                        }}
                    ],
                    [
                        {{
                            "content": "Content for Approach 1, Criteria 2",
                            "rating": "high"
                        }},
                        {{
                            "content": "Content for Approach 2, Criteria 2",
                            "rating": "medium"
                        }},
                        {{
                            "content": "Content for Approach 3, Criteria 2",
                            "rating": "low"
                        }}
                    ],
                    [
                        {{
                            "content": "Content for Approach 1, Criteria 3",
                            "rating": "medium"
                        }},
                        {{
                            "content": "Content for Approach 2, Criteria 3",
                            "rating": "high"
                        }},
                        {{
                            "content": "Content for Approach 3, Criteria 3",
                            "rating": "low"
                        }}
                    ],
                    [
                        {{
                            "content": "Content for Approach 1, Criteria 4"
                        }},
                        {{
                            "content": "Content for Approach 2, Criteria 4"
                        }},
                        {{
                            "content": "Content for Approach 3, Criteria 4"
                        }}
                    ],
                    [
                        {{
                            "content": "Content for Approach 1, Criteria 5",
                            "rating": "low",
                            "notes": "Brief note"
                        }},
                        {{
                            "content": "Content for Approach 2, Criteria 5",
                            "rating": "medium",
                            "notes": "Brief note"
                        }},
                        {{
                            "content": "Content for Approach 3, Criteria 5",
                            "rating": "high",
                            "notes": "Brief note"
                        }}
                    ],
                    [
                        {{
                            "content": "Content for Approach 1, Criteria 6"
                        }},
                        {{
                            "content": "Content for Approach 2, Criteria 6"
                        }},
                        {{
                            "content": "Content for Approach 3, Criteria 6"
                        }}
                    ]
                ]
            }}

            DO NOT include any explanatory text, markdown formatting, or code blocks. Return ONLY the JSON object.

            IMPORTANT:
            - Choose approaches that represent genuinely different perspectives
            - Ensure fair representation of all approaches
            - Use criteria that matter for the specific topic
            - Be consistent in how you evaluate each approach
            - Highlight trade-offs rather than suggesting one approach is universally superior
            """

            # Generate content
            response = await self.content_generator.generate_content(prompt, max_tokens=2500)

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
                comparative_analysis_data = json.loads(json_str)

                # Validate the structure
                self._validate_comparative_analysis_data(comparative_analysis_data)

                logger.info(f"Successfully generated comparative analysis content for topic: {topic}")
                return comparative_analysis_data
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
                        comparative_analysis_data = json.loads(json_str)
                        self._validate_comparative_analysis_data(comparative_analysis_data)
                        logger.info(f"Successfully parsed JSON with aggressive approach")
                        return comparative_analysis_data
                except Exception as e2:
                    logger.error(f"Aggressive JSON parsing also failed: {str(e2)}")
                    return self._get_default_comparative_analysis_content(topic)

                return self._get_default_comparative_analysis_content(topic)
            except Exception as e:
                logger.error(f"Error validating comparative analysis data: {str(e)}")
                return self._get_default_comparative_analysis_content(topic)
        except Exception as e:
            logger.error(f"Error generating comparative analysis content: {str(e)}")
            return self._get_default_comparative_analysis_content(topic)

    def _validate_comparative_analysis_data(self, data: Dict[str, Any]) -> None:
        """
        Validate the comparative analysis data structure.

        Args:
            data: The comparative analysis data to validate

        Raises:
            ValueError: If the data structure is invalid
        """
        # Check required fields
        required_fields = ["approaches", "criteria", "cells"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Missing required field: {field}")

        # Check approaches
        if len(data["approaches"]) != 3:
            raise ValueError(f"Expected 3 approaches, got {len(data['approaches'])}")

        # Check criteria
        if len(data["criteria"]) != 6:
            raise ValueError(f"Expected 6 criteria, got {len(data['criteria'])}")

        # Check cells
        if len(data["cells"]) != 6:
            raise ValueError(f"Expected 6 rows of cells, got {len(data['cells'])}")

        for i, row in enumerate(data["cells"]):
            if len(row) != 3:
                raise ValueError(f"Expected 3 cells in row {i+1}, got {len(row)}")

            for j, cell in enumerate(row):
                if "content" not in cell:
                    raise ValueError(f"Missing required field 'content' in cell {i+1},{j+1}")

                # Check ratings for specific rows
                if i in [1, 2, 4]:  # Rows 2, 3, 5 (0-indexed)
                    if "rating" not in cell:
                        raise ValueError(f"Missing required field 'rating' in cell {i+1},{j+1}")

                    if cell["rating"] not in ["high", "medium", "low"]:
                        raise ValueError(f"Invalid rating '{cell['rating']}' in cell {i+1},{j+1}")

                # Check notes for specific rows
                if i in [4]:  # Row 5 (0-indexed)
                    if "notes" not in cell:
                        raise ValueError(f"Missing required field 'notes' in cell {i+1},{j+1}")

    def _get_default_comparative_analysis_content(self, topic: str) -> Dict[str, Any]:
        """
        Get default comparative analysis content for a topic.

        Args:
            topic: The research topic

        Returns:
            Dictionary with default comparative analysis content
        """
        # Create default approaches based on the topic
        approaches = [
            f"Traditional {topic} Approach",
            f"Modern {topic} Framework",
            f"Emerging {topic} Paradigm"
        ]

        criteria = [
            "Primary Goal",
            "Effectiveness",
            "Equity Impact",
            "Key Stakeholders",
            "Implementation Complexity",
            "Future Potential"
        ]

        cells = [
            [
                {"content": "Optimize existing processes"},
                {"content": "Balance tradition with innovation"},
                {"content": "Transform fundamental approaches"}
            ],
            [
                {"content": "Reliable in familiar contexts", "rating": "medium"},
                {"content": "Strong across diverse applications", "rating": "high"},
                {"content": "Promising but limited validation", "rating": "low"}
            ],
            [
                {"content": "May reinforce existing inequities", "rating": "low"},
                {"content": "Addresses some equity concerns", "rating": "medium"},
                {"content": "Designed for inclusive outcomes", "rating": "high"}
            ],
            [
                {"content": "Established institutions"},
                {"content": "Forward-thinking organizations"},
                {"content": "Early adopters and innovators"}
            ],
            [
                {"content": "Simple implementation", "rating": "high", "notes": "Minimal training"},
                {"content": "Moderate adaptation needed", "rating": "medium", "notes": "Some retraining"},
                {"content": "Significant restructuring required", "rating": "low", "notes": "Major changes"}
            ],
            [
                {"content": "Gradual, incremental improvement"},
                {"content": "Steady evolution and integration"},
                {"content": "Potential for transformative change"}
            ]
        ]

        return {
            "approaches": approaches,
            "criteria": criteria,
            "cells": cells
        }

    def _get_default_template(self) -> str:
        """
        Get the default HTML template for comparative analyses.

        Returns:
            String containing the HTML template
        """
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Comparative Analysis</title>
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
        .comparison-table {
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            margin-bottom: 20px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px 15px;
            border: 1px solid #ddd;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #333;
        }
        th:first-child {
            width: 20%;
            background-color: #f8f9fa;
        }
        th:not(:first-child) {
            width: 26.66%;
            text-align: center;
        }
        td:not(:first-child) {
            text-align: center;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        .approach-header {
            font-weight: bold;
            color: white;
            padding: 10px;
        }
        .approach-1 {
            background-color: #3498db;
        }
        .approach-2 {
            background-color: #e74c3c;
        }
        .approach-3 {
            background-color: #9b59b6;
        }
        .rating {
            font-weight: bold;
        }
        .high {
            color: #27ae60;
        }
        .medium {
            color: #f39c12;
        }
        .low {
            color: #c0392b;
        }
        .notes {
            font-size: 12px;
            color: #666;
            font-style: italic;
        }
        .legend {
            margin-top: 20px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>{{title}}</h1>
        <p class="description">
            {{description}}
        </p>

        <div class="comparison-table">
            <table>
                <thead>
                    <tr>
                        <th>Criteria</th>
                        {% for approach in json_data.approaches %}
                        <th class="approach-header approach-{{loop.index}}">{{approach}}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for criteria_idx in range(json_data.criteria|length) %}
                    <tr>
                        <td><strong>{{json_data.criteria[criteria_idx]}}</strong></td>
                        {% for cell_idx in range(json_data.cells[criteria_idx]|length) %}
                        <td
                            {% if json_data.cells[criteria_idx][cell_idx].rating is defined %}
                            class="rating {{json_data.cells[criteria_idx][cell_idx].rating}}"
                            {% endif %}
                        >
                            {{json_data.cells[criteria_idx][cell_idx].content}}
                            {% if json_data.cells[criteria_idx][cell_idx].notes is defined %}
                            <br><span class="notes">{{json_data.cells[criteria_idx][cell_idx].notes}}</span>
                            {% endif %}
                        </td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>

            <div class="legend">
                <p><strong>Rating Key:</strong> <span class="high">High</span> = Strong performance/capability | <span class="medium">Medium</span> = Moderate performance/capability | <span class="low">Low</span> = Limited performance/capability</p>
            </div>
        </div>
    </div>
</body>
</html>"""
