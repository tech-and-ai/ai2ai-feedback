"""
Lily Callout Engine

This module processes content and adds Lily callouts before it's formatted into a document.
It sits between the content generation and document formatting stages.
"""

import os
import re
import json
import logging
import requests
import random
from typing import Dict, List, Any, Optional, Tuple, Union

# Import the document formatter
from app.services.document_formatter.document_formatter import DocumentFormatter

# Configure logging
logger = logging.getLogger(__name__)

class LilyCalloutEngine:
    """
    Engine for processing content and adding Lily callouts before document formatting.

    This class sits between content generation and document formatting, enhancing
    the content with contextually relevant Lily callouts.
    """

    def __init__(self, openrouter_api_key: Optional[str] = None):
        """
        Initialize the Lily callout engine.

        Args:
            openrouter_api_key: API key for OpenRouter (optional, will try to get from env if not provided)
        """
        logger.info("LILY ENGINE: Initializing Lily callout engine")

        # Get API key from environment if not provided
        self.api_key = openrouter_api_key

        # If no API key provided, try to get it from the environment
        if not self.api_key:
            self.api_key = os.environ.get("OPENROUTER_API_KEY")
            if self.api_key:
                logger.info("LILY ENGINE: OpenRouter API key loaded from environment")
            else:
                # Try to load from .env file
                try:
                    from dotenv import load_dotenv
                    # Try absolute path to app/.env
                    env_path = '/home/admin/projects/kdd/app/.env'
                    if os.path.exists(env_path):
                        logger.info(f"LILY ENGINE: Loading .env file from {env_path}")
                        load_dotenv(env_path)
                        self.api_key = os.environ.get("OPENROUTER_API_KEY")
                        if self.api_key:
                            logger.info(f"LILY ENGINE: OpenRouter API key loaded from {env_path}")
                        else:
                            logger.warning(f"LILY ENGINE: OpenRouter API key not found in {env_path}")
                    else:
                        logger.warning(f"LILY ENGINE: .env file not found at {env_path}")
                except Exception as e:
                    logger.error(f"LILY ENGINE: Error loading .env file: {str(e)}")

        if self.api_key:
            logger.info("LILY ENGINE: Initialized with OpenRouter API key")
        else:
            logger.warning("LILY ENGINE: No OpenRouter API key provided. Callout generation will not work.")

        # Define callout types with descriptions for the LLM
        self.callout_types = {
            "tip": "practical advice for research or writing",
            "insight": "deeper understanding of concepts",
            "question": "thought-provoking questions to consider",
            "warning": "important cautions or potential pitfalls",
            "confidence": "encouragement and motivation",
            "brainstorm": "ideas for further exploration",
            "research": "suggestions for additional research directions",
            "guidance": "step-by-step instructions or methodological advice",
            "reflection": "prompts for personal reflection on the topic",
            "connection": "links between different concepts or ideas",
            "example": "illustrative examples or case studies",
            "definition": "clarification of key terms or concepts",
            "caution": "similar to warning, but more gentle"
        }

        # Get API endpoints from the database
        try:
            from app.services.config.config_service import config_service
            self.api_url = config_service.get_config('openrouter_endpoint', 'https://openrouter.ai/api/v1/chat/completions')
            self.requesty_url = config_service.get_config('requesty_endpoint', 'https://router.requesty.ai/v1/chat/completions')
            logger.info(f"LILY ENGINE: Using OpenRouter endpoint from config: {self.api_url}")
            logger.info(f"LILY ENGINE: Using Requesty endpoint from config: {self.requesty_url}")
        except Exception as e:
            logger.warning(f"LILY ENGINE: Error getting API endpoints from config: {str(e)}")
            # Fallback to default endpoints
            self.api_url = "https://openrouter.ai/api/v1/chat/completions"
            self.requesty_url = "https://router.requesty.ai/v1/chat/completions"
            logger.info(f"LILY ENGINE: Using default OpenRouter endpoint: {self.api_url}")
            logger.info(f"LILY ENGINE: Using default Requesty endpoint: {self.requesty_url}")

        # Get model from configuration service
        try:
            from app.services.config.config_service import config_service
            self.model = config_service.get_config('default_llm_model', 'google/gemini-2.5-flash-preview')
            logger.info(f"LILY ENGINE: Using model from config: {self.model}")
        except Exception as e:
            logger.warning(f"LILY ENGINE: Could not load model from config service: {str(e)}")
            self.model = "google/gemini-2.5-flash-preview"  # Fallback model
            logger.info(f"LILY ENGINE: Using fallback model: {self.model}")

    def process_and_format(self, content: Dict[str, Any], topic: str, education_level: str) -> Any:
        """
        Process content to add Lily callouts and then format it into a document.

        Args:
            content: The content structure (JSON/dictionary)
            topic: The research topic
            education_level: The education level (university, postgraduate, etc.)

        Returns:
            The formatted document

        Raises:
            ValueError: If both OpenRouter and Requesty APIs fail
        """
        logger.info(f"Processing content for Lily callouts (topic: {topic}, education level: {education_level})")

        # Process the content to add Lily callouts
        # This will raise an exception if both OpenRouter and Requesty fail
        enhanced_content = self._enhance_with_callouts(content, topic, education_level)

        # Create a document formatter
        formatter = DocumentFormatter()

        # Format the enhanced content into a document
        formatted_doc = formatter.format_research_pack(enhanced_content)

        logger.info("Content processed and formatted successfully")
        return formatted_doc

    def _enhance_with_callouts(self, content: Dict[str, Any], topic: str, education_level: str) -> Dict[str, Any]:
        """
        Enhance content with Lily callouts.

        Args:
            content: The content structure (JSON/dictionary)
            topic: The research topic
            education_level: The education level (university, postgraduate, etc.)

        Returns:
            The enhanced content structure

        Raises:
            ValueError: If both OpenRouter and Requesty APIs fail
        """
        logger.info(f"LILY ENGINE: Enhancing content with callouts for topic: {topic}")
        logger.info(f"LILY ENGINE: Content type: {type(content)}")
        logger.info(f"LILY ENGINE: Content keys: {list(content.keys()) if isinstance(content, dict) else 'Not a dictionary'}")

        # Create a deep copy of the content to avoid modifying the original
        try:
            enhanced_content = content.copy()
            logger.info("LILY ENGINE: Successfully created a copy of the content")
        except Exception as e:
            logger.error(f"LILY ENGINE: Error creating copy of content: {str(e)}")
            raise ValueError(f"Error enhancing content with callouts: {str(e)}")

        # Get the sections from the content
        sections = None
        if "sections" in enhanced_content:
            sections = enhanced_content.get("sections", {})
            logger.info("LILY ENGINE: Found sections directly in content")
        elif "content_chunks" in enhanced_content and "sections" in enhanced_content["content_chunks"]:
            sections = enhanced_content["content_chunks"]["sections"]
            logger.info("LILY ENGINE: Found sections in content_chunks")
        else:
            logger.warning("LILY ENGINE: No sections found in content or content_chunks")
            logger.info(f"LILY ENGINE: Content structure: {list(enhanced_content.keys())}")
            if "content_chunks" in enhanced_content:
                logger.info(f"LILY ENGINE: Content chunks structure: {list(enhanced_content['content_chunks'].keys())}")
            return enhanced_content

        if not sections:
            logger.warning("LILY ENGINE: Sections dictionary is empty")
            return enhanced_content

        logger.info(f"LILY ENGINE: Found {len(sections)} sections in content: {list(sections.keys())}")

        # Get all section keys
        section_keys = list(sections.keys())
        logger.info(f"LILY ENGINE: All section keys: {section_keys}")

        # Skip static content sections and identify content sections
        static_sections = ['about_lily', 'how_to_use', 'appendices']
        content_sections = []

        # Check if sections is a dictionary with string keys
        if isinstance(sections, dict):
            for i, key in enumerate(section_keys):
                # Skip static sections
                if key in static_sections:
                    logger.info(f"LILY ENGINE: Skipping static section '{key}'")
                    continue

                # Skip personalized questions section
                if key == 'personalized_questions':
                    logger.info(f"LILY ENGINE: Skipping personalized questions section")
                    continue

                # Add to content sections
                content_sections.append((i, key))
                logger.info(f"LILY ENGINE: Added content section '{key}' at index {i}")
        else:
            # Handle case where sections is not a dictionary with string keys
            logger.warning(f"LILY ENGINE: Sections is not a dictionary with string keys: {type(sections)}")

            # Try to extract content from the structure
            if isinstance(enhanced_content, dict):
                # Look for content in common section names
                for potential_key in ['introduction', 'background', 'literature_review', 'methodology',
                                     'findings', 'discussion', 'conclusion', 'references']:
                    if potential_key in enhanced_content:
                        content_sections.append((0, potential_key))
                        logger.info(f"LILY ENGINE: Added content section '{potential_key}' from top level")

                # If we still don't have content sections, look for any string values
                if not content_sections:
                    for key, value in enhanced_content.items():
                        if isinstance(value, str) and len(value) > 100:  # Only consider substantial text
                            content_sections.append((0, key))
                            logger.info(f"LILY ENGINE: Added content section '{key}' from top level (string value)")

        # If no content sections found
        if not content_sections:
            logger.warning("LILY ENGINE: No content sections found")
            return enhanced_content

        # Process each content section
        callouts_added_count = 0

        for section_index, section_key in content_sections:
            section_content = sections.get(section_key, {})

            # Skip empty sections
            if not section_content:
                logger.info(f"LILY ENGINE: Skipping empty section {section_key}")
                continue

            logger.info(f"LILY ENGINE: Processing section {section_key} for callouts")
            logger.info(f"LILY ENGINE: Section content type: {type(section_content)}")
            logger.info(f"LILY ENGINE: Section content keys: {list(section_content.keys()) if isinstance(section_content, dict) else 'Not a dictionary'}")

            try:
                # Process the section content
                # This will raise an exception if both OpenRouter and Requesty fail
                enhanced_section = self._process_section(section_content, topic, education_level)
            except ValueError as e:
                # Propagate the error upward to indicate that the job should be requeued
                logger.error(f"LILY ENGINE: API failure while processing section {section_key}: {str(e)}")
                raise

            # Update the section in the enhanced content
            if "sections" in enhanced_content:
                enhanced_content["sections"][section_key] = enhanced_section
                logger.info(f"LILY ENGINE: Updated section {section_key} in content.sections")
            elif "content_chunks" in enhanced_content and "sections" in enhanced_content["content_chunks"]:
                enhanced_content["content_chunks"]["sections"][section_key] = enhanced_section
                logger.info(f"LILY ENGINE: Updated section {section_key} in content.content_chunks.sections")

            # Count callouts for logging
            section_callouts_count = str(enhanced_section).count("LILY_CALLOUT")
            callouts_added_count += section_callouts_count
            logger.info(f"LILY ENGINE: Added {section_callouts_count} callouts to section {section_key}")

        logger.info(f"LILY ENGINE: Added {callouts_added_count} callouts in total")

        # Check if any callouts were added
        if callouts_added_count > 0:
            logger.info("LILY ENGINE: Successfully added callouts to content")

            # Find and log a sample callout
            enhanced_content_str = str(enhanced_content)
            callout_index = enhanced_content_str.find("LILY_CALLOUT")
            if callout_index >= 0:
                start_index = max(0, callout_index - 20)
                end_index = min(len(enhanced_content_str), callout_index + 100)
                sample = enhanced_content_str[start_index:end_index]
                logger.info(f"LILY ENGINE: Sample callout: '{sample}'")
        else:
            logger.warning("LILY ENGINE: No callouts were added to content")

        return enhanced_content

    def _process_section(self, section_content: Dict[str, Any], topic: str, education_level: str) -> Dict[str, Any]:
        """
        Process a section to add Lily callouts.

        This method combines all subsection content into a single text, sends it to the LLM
        for callout generation, and then splits the enhanced content back into subsections.
        This allows the LLM to see the entire section context and place callouts at the most
        appropriate points without breaking the flow of the content.

        Args:
            section_content: The section content
            topic: The research topic
            education_level: The education level

        Returns:
            The enhanced section content

        Raises:
            ValueError: If both OpenRouter and Requesty APIs fail
        """
        logger.info(f"LILY ENGINE: Processing section with {len(section_content)} keys")
        logger.info(f"LILY ENGINE: Section keys: {list(section_content.keys())}")

        # Create a deep copy of the section content to avoid modifying the original
        try:
            enhanced_section = section_content.copy()
            logger.info("LILY ENGINE: Successfully created a copy of the section content")
        except Exception as e:
            logger.error(f"LILY ENGINE: Error creating copy of section content: {str(e)}")
            raise ValueError(f"Error processing section: {str(e)}")

        # Collect all text content from the section
        text_content = {}
        for key, value in section_content.items():
            # Skip non-string values (might be nested dictionaries or metadata)
            if not isinstance(value, str):
                logger.info(f"LILY ENGINE: Skipping non-string subsection '{key}' (type: {type(value)})")
                continue

            # Skip empty content
            if not value.strip():
                logger.info(f"LILY ENGINE: Skipping empty subsection '{key}'")
                continue

            # Add to text content dictionary
            text_content[key] = value

        # If no text content found, return the original section
        if not text_content:
            logger.info("LILY ENGINE: No text content found in section")
            return enhanced_section

        # Combine all text content into a single string with markers to identify subsections
        combined_content = ""
        subsection_markers = {}
        marker_index = 0

        for key, value in text_content.items():
            # Add a unique marker at the start of each subsection
            marker = f"[[SUBSECTION_START_{marker_index}]]"
            subsection_markers[marker] = key
            combined_content += f"\n\n{marker}\n{value}"
            marker_index += 1

        logger.info(f"LILY ENGINE: Combined {len(text_content)} subsections into a single text ({len(combined_content)} chars)")

        try:
            # Process the combined content to add Lily callouts
            # This will raise an exception if both OpenRouter and Requesty fail
            enhanced_combined_content = self._add_callouts_to_content(combined_content, topic, education_level)

            # Check if callouts were added
            callout_count = enhanced_combined_content.count("LILY_CALLOUT")
            if callout_count > 0:
                logger.info(f"LILY ENGINE: Added {callout_count} callouts to combined content")

                # Find and log a sample callout
                callout_index = enhanced_combined_content.find("LILY_CALLOUT")
                if callout_index >= 0:
                    start_index = max(0, callout_index - 20)
                    end_index = min(len(enhanced_combined_content), callout_index + 100)
                    sample = enhanced_combined_content[start_index:end_index]
                    logger.info(f"LILY ENGINE: Sample callout: '{sample}'")
            else:
                logger.info("LILY ENGINE: No callouts added to combined content")

            # Split the enhanced content back into subsections using the markers
            for marker, key in subsection_markers.items():
                # Find the start of this subsection
                start_index = enhanced_combined_content.find(marker)
                if start_index == -1:
                    logger.warning(f"LILY ENGINE: Could not find marker '{marker}' for subsection '{key}'")
                    continue

                # Find the start of the next subsection or the end of the content
                next_marker_index = float('inf')
                for next_marker in subsection_markers.keys():
                    if next_marker != marker:
                        next_index = enhanced_combined_content.find(next_marker, start_index + len(marker))
                        if next_index != -1 and next_index < next_marker_index:
                            next_marker_index = next_index

                # Extract the subsection content
                if next_marker_index == float('inf'):
                    # This is the last subsection
                    subsection_content = enhanced_combined_content[start_index + len(marker):].strip()
                else:
                    subsection_content = enhanced_combined_content[start_index + len(marker):next_marker_index].strip()

                # Remove the marker from the content
                subsection_content = subsection_content.replace(marker, "").strip()

                # Update the enhanced section
                enhanced_section[key] = subsection_content
                logger.info(f"LILY ENGINE: Updated subsection '{key}' with enhanced content")

        except ValueError as e:
            # Propagate the error upward to indicate that the job should be requeued
            logger.error(f"LILY ENGINE: API failure while processing section: {str(e)}")
            raise

        logger.info(f"LILY ENGINE: Processed section with {len(text_content)} subsections")
        return enhanced_section

    def _add_callouts_to_content(self, content: str, topic: str, education_level: str) -> str:
        """
        Add Lily callouts to content.

        This method sends the content to the LLM to add callout markers at appropriate
        points in the content. The LLM has a 1 million token context window, so we can
        send entire sections at once for better context and more appropriate callout placement.

        Args:
            content: The content to enhance
            topic: The research topic
            education_level: The education level

        Returns:
            The enhanced content with Lily callouts

        Raises:
            ValueError: If both OpenRouter and Requesty APIs fail
        """
        # No minimum content length check - we're sending entire sections
        # Log the content length for debugging
        logger.info(f"LILY ENGINE: Processing content for callouts ({len(content)} chars)")

        # Skip empty content
        if not content.strip():
            logger.info("LILY ENGINE: Content is empty, skipping callout generation")
            return content

        # Send the content to the LLM to add callout markers
        # This will raise an exception if both OpenRouter and Requesty fail
        marked_content = self._send_to_llm(content, topic, education_level)

        # Replace the simple markers with the proper callout format
        enhanced_content = self._replace_markers(marked_content)

        # Check if any callouts were added
        if "LILY_CALLOUT" in enhanced_content:
            callout_count = enhanced_content.count("LILY_CALLOUT")
            logger.info(f"LILY ENGINE: Added {callout_count} callouts to content")
        else:
            logger.info("LILY ENGINE: No callouts were added to content")

        return enhanced_content

    def _send_to_llm(self, content: str, topic: str, education_level: str) -> str:
        """
        Send content to the LLM to add callout markers.

        Args:
            content: The content to enhance
            topic: The research topic
            education_level: The education level

        Returns:
            The content with simple callout markers added or raises an exception if both APIs fail
        """
        # If no API key is available, raise an exception
        if not self.api_key:
            logger.error("LILY ENGINE: No OpenRouter API key provided.")
            raise ValueError("OpenRouter API key is required for Lily callout generation")

        logger.info("LILY ENGINE: Sending content to OpenRouter API for callout generation")

        # Create a prompt for the LLM
        prompt = self._create_prompt(content, topic, education_level)

        # Try OpenRouter first
        try:
            # Call the OpenRouter API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are Lily, an AI research assistant that helps students with their research."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }

            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()

            # Extract the response content
            result = response.json()

            # Check if the response contains the expected fields
            if "choices" in result and len(result["choices"]) > 0 and "message" in result["choices"][0] and "content" in result["choices"][0]["message"]:
                marked_content = result["choices"][0]["message"]["content"]
                logger.info("LILY ENGINE: Successfully received response from OpenRouter API")
                return marked_content
            else:
                logger.error("LILY ENGINE: Unexpected response format from OpenRouter API")
                # Fall through to try Requesty
        except Exception as e:
            logger.error(f"LILY ENGINE: Error calling OpenRouter API: {str(e)}")
            # Fall through to try Requesty

        # If OpenRouter failed, try Requesty as fallback
        logger.info("LILY ENGINE: OpenRouter failed, trying Requesty as fallback")
        try:
            # Get Requesty API key from environment
            requesty_api_key = os.getenv("REQUESTY_API_KEY")
            if not requesty_api_key:
                logger.error("LILY ENGINE: No Requesty API key available as fallback")
                raise ValueError("Both OpenRouter and Requesty APIs failed")

            # Call the Requesty API
            requesty_headers = {
                "Authorization": f"Bearer {requesty_api_key}",
                "Content-Type": "application/json"
            }

            requesty_data = {
                "model": self.model,  # Use the model from config
                "messages": [
                    {"role": "system", "content": "You are Lily, an AI research assistant that helps students with their research."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 4000
            }

            requesty_response = requests.post(self.requesty_url, headers=requesty_headers, json=requesty_data)
            requesty_response.raise_for_status()

            # Extract the response content
            requesty_result = requesty_response.json()

            # Check if the response contains the expected fields
            if "choices" in requesty_result and len(requesty_result["choices"]) > 0 and "message" in requesty_result["choices"][0] and "content" in requesty_result["choices"][0]["message"]:
                marked_content = requesty_result["choices"][0]["message"]["content"]
                logger.info("LILY ENGINE: Successfully received response from Requesty API")
                return marked_content
            else:
                logger.error("LILY ENGINE: Unexpected response format from Requesty API")
                raise ValueError("Both OpenRouter and Requesty APIs failed with unexpected response format")
        except Exception as e:
            logger.error(f"LILY ENGINE: Error calling Requesty API: {str(e)}")
            raise ValueError("Both OpenRouter and Requesty APIs failed, job should be requeued")

    def _create_prompt(self, content: str, topic: str, education_level: str) -> str:
        """
        Create a prompt for the LLM to add callout markers.

        Args:
            content: The content to enhance
            topic: The research topic
            education_level: The education level

        Returns:
            The prompt for the LLM
        """
        # Create a description of callout types
        callout_types_desc = "\n".join([f"- {ctype}: {desc}" for ctype, desc in self.callout_types.items()])

        prompt = f"""You are Lily, an AI research assistant helping students with their research on {topic}.

I'll provide you with a complete section of content from a research pack (education level: {education_level}). Your task is to identify 2-4 places where a helpful callout would benefit the reader. For each callout, insert a marker in this format:

$$L$$ [callout_type] [callout_title] [callout_content] $$LEND$$

For example:
$$L$$ tip "Research Method Tip" "When evaluating sources, always check the publication date to ensure you're using current information." $$LEND$$

Available callout types:
{callout_types_desc}

Guidelines for callout placement:
1. Place Lily's callouts ONLY at natural breaks in the content - after a complete thought or section
2. Always leave a clear separation (such as an extra line break) before and after each Lily callout
3. Make sure Lily's callouts feel like natural pauses where a student might realistically stop and reflect
4. Prefer callout placement after a major insight, a shift in topic, or at natural "breathing points" in the discussion
5. NEVER place Lily's callouts inside lists, mid-paragraph, or where it interrupts detailed arguments
6. Preserve the flow of the content - don't break up connected ideas
7. Place callouts at points where they enhance understanding without disrupting reading flow

Guidelines for callout content:
1. Add callouts only where they provide genuine value - don't force them if not needed
2. Make callouts specific to the surrounding content, not generic advice
3. Keep callout content concise but insightful (1-3 sentences)
4. Choose the most appropriate callout type based on the content
5. Ensure callouts enhance understanding of complex concepts or provide practical application tips
6. Vary the callout types to provide a diverse learning experience
7. DO NOT change the original content - only add the callout markers

Here's the content:

{content}

Return the content with your callout markers inserted at appropriate points. DO NOT summarize or modify the original content. Remember that you're seeing the entire section at once, so place callouts at natural breaks where they won't disrupt the flow of ideas.
"""
        return prompt

    def _add_mock_callouts(self, content: str) -> str:
        """
        Add mock callouts to content when the API is not available.

        Args:
            content: The content to enhance

        Returns:
            The content with mock callout markers added
        """
        logger.info("LILY ENGINE: Adding mock callouts to content")

        # Split the content into paragraphs
        paragraphs = content.split("\n\n")

        # Skip if there are too few paragraphs
        if len(paragraphs) < 3:
            return content

        # Sample callouts
        mock_callouts = [
            ('tip', 'Research Method Tip', 'When evaluating sources, always check the publication date to ensure you\'re using current information.'),
            ('insight', 'Critical Thinking', 'Consider how different perspectives might interpret this information differently.'),
            ('question', 'Reflection Question', 'How does this connect to your own experiences or other topics you\'ve studied?'),
            ('warning', 'Common Pitfall', 'Be careful not to overgeneralize from limited evidence.'),
            ('confidence', 'Progress Check', 'You\'re making great progress! Understanding these concepts builds a strong foundation for your research.'),
            ('brainstorm', 'Idea Generator', 'Try mapping out how these concepts connect to each other visually.'),
            ('research', 'Research Direction', 'Consider exploring primary sources that address this topic directly.'),
            ('guidance', 'Next Steps', 'After understanding these concepts, try applying them to a specific case study.'),
            ('connection', 'Interdisciplinary Link', 'This concept has interesting parallels in other fields like psychology and sociology.')
        ]

        # Add 1-3 callouts at random positions (but not too close to each other)
        num_callouts = min(3, max(1, len(paragraphs) // 3))

        try:
            # Generate random positions for callouts
            positions = sorted(random.sample(range(1, len(paragraphs) - 1), num_callouts))

            # Add callouts
            for pos in positions:
                callout = random.choice(mock_callouts)
                callout_marker = f"\n\n$$L$$ {callout[0]} \"{callout[1]}\" \"{callout[2]}\" $$LEND$$\n\n"
                paragraphs[pos] = paragraphs[pos] + callout_marker

            # Join the paragraphs back together
            marked_content = "\n\n".join(paragraphs)

            logger.info(f"LILY ENGINE: Added {num_callouts} mock callouts")
            return marked_content

        except ValueError:
            # If there are not enough paragraphs, return the original content
            return content

    def _replace_markers(self, marked_content: str) -> str:
        """
        Replace simple callout markers with the proper callout format.

        Args:
            marked_content: The content with simple callout markers

        Returns:
            The content with proper callout format
        """
        # Define the pattern for the simple markers
        pattern = r'\$\$L\$\$ ([a-z]+) "([^"]+)" "([^"]+)" \$\$LEND\$\$'

        # Find all matches
        matches = re.findall(pattern, marked_content)

        # Replace each match with the proper callout format
        enhanced_content = marked_content
        replaced_count = 0

        for callout_type, title, content in matches:
            # Create the proper callout format
            marker = f'$$L$$ {callout_type} "{title}" "{content}" $$LEND$$'

            # Use the original format that the document formatter expects
            callout = f'[[LILY_CALLOUT type="{callout_type}" title="{title}"]]'
            callout += content
            callout += '[[/LILY_CALLOUT]]'

            # Replace the marker with the callout
            if marker in enhanced_content:
                enhanced_content = enhanced_content.replace(marker, callout)
                replaced_count += 1

        if replaced_count > 0:
            logger.info(f"LILY ENGINE: Replaced {replaced_count} callout markers with proper format")

        return enhanced_content


# For testing
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Create a Lily callout engine
    engine = LilyCalloutEngine()

    # Test content
    test_content = """
    Academic research is a systematic process of inquiry that contributes to the body of knowledge in a particular field. It involves formulating research questions, collecting and analyzing data, and drawing conclusions based on evidence. This document provides an overview of academic research techniques and best practices.

    Effective research requires critical thinking, attention to detail, and a methodical approach. By following established research methodologies, scholars can ensure the validity and reliability of their findings. This guide will help you navigate the research process from start to finish.

    A literature review is a comprehensive summary of previous research on a topic. It helps researchers understand the current state of knowledge, identify gaps, and position their work within the existing literature. A good literature review is not merely a summary of sources but a synthesis that provides a critical analysis of the literature.

    When conducting a literature review, it's important to use a variety of sources, including peer-reviewed journals, books, and conference proceedings. Primary sources provide firsthand evidence, while secondary sources offer analysis and interpretation. Both are valuable for different reasons and should be included in a comprehensive literature review.

    Research methodology refers to the systematic approach used to collect and analyze data. The choice of methodology depends on the research questions, the nature of the data, and the disciplinary conventions. Common methodologies include qualitative, quantitative, and mixed methods approaches.

    Qualitative research focuses on understanding phenomena through detailed descriptions and interpretations. It often involves interviews, observations, and document analysis. Quantitative research, on the other hand, involves numerical data and statistical analysis. Mixed methods research combines both approaches to provide a more comprehensive understanding of the research problem.
    """

    # Test the engine
    enhanced_content = engine._add_callouts_to_content(test_content, "Academic Research", "university")

    print("Original content:")
    print(test_content)
    print("\nEnhanced content:")
    print(enhanced_content)
