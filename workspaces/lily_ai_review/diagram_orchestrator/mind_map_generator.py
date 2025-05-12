"""
Mind Map Generator
Creates beautiful D3.js mind maps
"""

import os
import json
import logging
import asyncio
import re
from .base_generator import BaseDiagramGenerator
from .content_generator import ContentGenerator

# Set up logging
logger = logging.getLogger(__name__)

class MindMapGenerator(BaseDiagramGenerator):
    """Mind Map Generator using D3.js and Cloudmersive"""

    def __init__(self, content_generator=None):
        """Initialize the mind map generator"""
        super().__init__()
        self.content_generator = content_generator

    async def generate_mind_map_async(self, topic):
        """
        Generate a mind map for a topic (async version)

        Args:
            topic (str): The research topic

        Returns:
            str: Path to the generated PNG file

        Raises:
            ValueError: If content generation fails with both OpenRouter and Requesty
        """
        # Generate mind map content
        mind_map_data = await self._generate_mind_map_content(topic)

        # Prepare data for the template
        template_data = {
            "TITLE": topic,
            "json_data": mind_map_data
        }

        # Generate the diagram using the JSMind template
        result = self.generate_diagram("jsmind_mind_map", template_data, prefix="mind_map")

        if not result:
            raise ValueError("Failed to generate mind map diagram")

        return result

    def _generate_mind_map_sync(self, topic):
        """
        Synchronously generate a mind map for the given topic.
        This is a fallback method when the event loop is already running.

        Args:
            topic (str): The topic to generate a mind map for

        Returns:
            The path to the generated mind map image

        Raises:
            ValueError: If content generation fails
        """
        try:
            logger.info(f"MIND MAP DEBUG: Generating mind map content synchronously for topic: {topic}")

            # We can't use async methods in a sync context, so we need to raise an error
            # This will be caught by the caller and should result in the job being requeued
            raise ValueError("Cannot generate mind map content synchronously. Please requeue the job.")

        except Exception as e:
            logger.error(f"Error in _generate_mind_map_sync: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise ValueError(f"Failed to generate mind map content: {str(e)}")

    def generate_mind_map(self, topic):
        """
        Generate a mind map for a topic (sync wrapper)

        Args:
            topic (str): The research topic

        Returns:
            str: Path to the generated PNG file

        Raises:
            ValueError: If content generation fails with both OpenRouter and Requesty
        """
        logger.info(f"MIND MAP DEBUG: generate_mind_map called for topic: {topic}")
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_event_loop()
                logger.info(f"MIND MAP DEBUG: Getting event loop")

                # Check if the loop is running
                if loop.is_running():
                    logger.info(f"MIND MAP DEBUG: Event loop is already running")

                    # Create a new event loop for this operation
                    try:
                        import nest_asyncio
                        nest_asyncio.apply()
                        logger.info(f"MIND MAP DEBUG: Applied nest_asyncio")

                        # Now we can use the loop safely
                        result = loop.run_until_complete(self.generate_mind_map_async(topic))
                    except ValueError as e:
                        # If we can't patch the loop, propagate the error to requeue the job
                        logger.warning(f"MIND MAP DEBUG: Could not patch loop: {str(e)}")
                        raise ValueError(f"Cannot generate mind map: {str(e)}")
                else:
                    logger.info(f"MIND MAP DEBUG: Event loop is not running")
                    # Run the async function in the existing loop
                    result = loop.run_until_complete(self.generate_mind_map_async(topic))
            except RuntimeError as e:
                logger.info(f"MIND MAP DEBUG: RuntimeError: {str(e)}, creating new loop")
                # If we can't get the current loop, create a new one
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                result = new_loop.run_until_complete(self.generate_mind_map_async(topic))
                new_loop.close()

            logger.info(f"MIND MAP DEBUG: Mind map generation result: {result}")
            if not result:
                raise ValueError("Failed to generate mind map")
            return result
        except ValueError as e:
            # Propagate ValueError to requeue the job
            logger.error(f"Error in generate_mind_map: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            # For other exceptions, also propagate to requeue
            logger.error(f"Unexpected error in generate_mind_map: {str(e)}", exc_info=True)
            raise ValueError(f"Unexpected error generating mind map: {str(e)}")

    async def _generate_mind_map_content(self, topic):
        """
        Generate mind map content using LLM

        Args:
            topic (str): The research topic

        Returns:
            dict: Mind map structure with center and branches

        Raises:
            ValueError: If content generation fails with both OpenRouter and Requesty
        """
        # Create content generator if not provided
        if self.content_generator:
            content_gen = self.content_generator
            logger.info("Using provided ContentGenerator")
        else:
            # Get API keys from environment
            openrouter_key = os.environ.get("OPENROUTER_API_KEY")
            requesty_key = os.environ.get("REQUESTY_API_KEY")

            # Create content generator with both API keys
            content_gen = ContentGenerator(openrouter_key=openrouter_key, requesty_key=requesty_key)
            logger.info(f"Created new ContentGenerator with OpenRouter key: {bool(openrouter_key)}, Requesty key: {bool(requesty_key)}")

        # Create prompt for the LLM
        prompt = f"""
        Create a mind map for the topic: "{topic}"

        The mind map should help visualize the key aspects and relationships within this topic.

        Follow these guidelines STRICTLY:
        1. Create a mind map with a central topic and a MAXIMUM of 10 main branches
        2. Each branch should have a MAXIMUM of 2 children (no more than 2 per branch)
        3. Keep all text concise (2-4 words per item)
        4. Make sure all content is directly relevant to the specific topic
        5. Focus on the most important aspects of the topic

        Return your response as a JSON object with this structure:
        {{
            "center": "Central Topic",
            "branches": [
                {{
                    "title": "Branch 1 Title",
                    "children": [
                        "Child 1",
                        "Child 2"
                    ]
                }},
                // more branches (maximum 10 total)...
            ]
        }}

        Only return the JSON object, nothing else.
        """

        # Generate content
        try:
            # Use JSON output format to get properly formatted JSON
            response = await content_gen.generate_content(prompt, max_tokens=1000, output_format="json")

            try:
                # Parse the JSON response
                mind_map_data = json.loads(response)

                # Enforce constraints on the data
                if "branches" in mind_map_data:
                    # Limit to 10 branches maximum
                    if len(mind_map_data["branches"]) > 10:
                        mind_map_data["branches"] = mind_map_data["branches"][:10]
                        logger.info(f"Trimmed branches to 10 for topic: {topic}")

                    # Limit each branch to 2 children maximum
                    for branch in mind_map_data["branches"]:
                        if "children" in branch and len(branch["children"]) > 2:
                            branch["children"] = branch["children"][:2]
                            logger.info(f"Trimmed children to 2 for branch: {branch['title']}")

                logger.info(f"Successfully generated mind map content for topic: {topic}")
                return mind_map_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {response}. Error: {str(e)}")
                # Try a more aggressive approach to extract JSON
                try:
                    # Try to extract JSON object using regex
                    json_match = re.search(r'\{[^\{\}]*(\{[^\{\}]*\}[^\{\}]*)*\}', response)
                    if json_match:
                        json_str = json_match.group(0)
                        mind_map_data = json.loads(json_str)
                        logger.info(f"Successfully extracted JSON using regex for topic: {topic}")
                        return mind_map_data
                except Exception as e2:
                    logger.error(f"Failed to extract JSON using regex: {str(e2)}")
                    # Propagate the error to requeue the job
                    raise ValueError(f"Failed to generate valid mind map content: {str(e)}")
        except ValueError as e:
            # Propagate ValueError to requeue the job
            logger.error(f"Error generating mind map content: {str(e)}")
            raise
        except Exception as e:
            # For other exceptions, also propagate to requeue
            logger.error(f"Unexpected error generating mind map content: {str(e)}")
            raise ValueError(f"Unexpected error generating mind map content: {str(e)}")


