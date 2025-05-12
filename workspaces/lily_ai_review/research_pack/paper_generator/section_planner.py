"""
Section Planner Module
Generates detailed section outlines for academic papers based on membership tier.
"""
import logging
from typing import Dict, List, Optional, Any
import aiohttp
import re
import os
import json

# Define constants that were previously imported
API_ENDPOINTS = {
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "requesty": "https://api.requesty.ai/api/v1/chat/completions"
}

# Default AI model configuration
AI_MODEL = {
    "name": "google/gemini-2.5-flash-preview",
    "provider": "openrouter"
}

# Default word counts by section and tier
SECTION_WORD_COUNTS = {
    "premium": {
        "introduction": "750-1000",
        "topic_analysis": "7000-9000",
        "methodological_approaches": "4000-5000",
        "key_arguments": "7000-9000",
        "citations_resources": "2000-3000",
        "personalized_questions": "1000-1500",
        "appendices": "1000-1500"
    },
    "standard": {
        "introduction": "500-750",
        "topic_analysis": "5000-7000",
        "methodological_approaches": "3000-4000",
        "key_arguments": "5000-7000",
        "citations_resources": "1000-2000",
        "personalized_questions": "500-1000",
        "appendices": "500-1000"
    },
    "sample": {
        "introduction": "300-500",
        "topic_analysis": "2000-3000",
        "methodological_approaches": "1000-1500",
        "key_arguments": "2000-3000",
        "citations_resources": "500-1000",
        "personalized_questions": "300-500",
        "appendices": "300-500"
    }
}

# Default paper formats
PAPER_FORMATS = {
    "standard": ["Introduction", "Literature Review", "Methodology", "Results", "Discussion", "Conclusion"],
    "extended": ["Abstract", "Introduction", "Literature Review", "Methodology", "Results", "Discussion", "Conclusion", "References"]
}

DEFAULT_PAPER_FORMAT = "standard"

def get_section_word_count(section: str, tier_name: str = None) -> str:
    """
    Get the target word count for a section based on tier.

    Args:
        section: The section name
        tier_name: The subscription tier (premium, standard, or sample)

    Returns:
        Word count range as a string (e.g., "500-750")
    """
    # Default to standard tier
    tier = "standard"
    if tier_name:
        tier = tier_name.lower()
        if tier not in SECTION_WORD_COUNTS:
            tier = "standard"

    # Get word count for this section and tier
    section_key = section.lower().replace(" ", "_")
    return SECTION_WORD_COUNTS[tier].get(section_key, "1000-1500")

logger = logging.getLogger(__name__)

class SectionPlanner:
    """Planner for creating detailed section outlines for academic papers."""

    def __init__(self, content_generator=None, openrouter_key=None):
        """Initialize the section planner."""
        self.content_generator = content_generator
        self.openrouter_key = openrouter_key

        # If content generator provided, use its key
        if content_generator and hasattr(content_generator, 'openrouter_key'):
            self.openrouter_key = content_generator.openrouter_key
            logger.info("Using OpenRouter key from content generator")

        # Ensure we have an OpenRouter key
        if not self.openrouter_key:
            try:
                # Try to get from environment
                env_key = os.getenv("OPENROUTER_API_KEY")
                if env_key:
                    self.openrouter_key = env_key
                    logger.info("Using OpenRouter key from environment variables")
            except Exception as e:
                logger.warning(f"Error getting OpenRouter key from environment: {str(e)}")

        if not self.openrouter_key:
            logger.warning("No OpenRouter key available for section planning. Some features may be limited.")

    async def plan_paper_sections(self, topic: str, sections: List[str], tier_name: str = None) -> Dict[str, str]:
        """
        Plan detailed outlines for each section of an academic paper.

        Args:
            topic: The paper topic
            sections: List of section names to plan
            tier_name: The subscription tier

        Returns:
            Dictionary mapping section names to detailed outlines
        """
        try:
            logger.info(f"Planning sections for paper on topic: {topic}")

            # Determine depth of planning based on tier
            plan_depth = "standard"
            if tier_name:
                if tier_name.lower() == "premium":
                    plan_depth = "comprehensive"
                elif tier_name.lower() == "sample":
                    plan_depth = "basic"

            logger.info(f"Using {plan_depth} plan depth for tier: {tier_name}")

            # Generate detailed plans for each section
            plans = {}

            # For sample tier, skip detailed planning
            if tier_name and tier_name.lower() == "sample":
                logger.info("Skipping detailed planning for sample tier")
                return plans

            # For other tiers, plan each section
            paper_title = f"Research on {topic}"

            # Track previously planned sections to avoid repetition
            previous_sections = {}

            for section in sections:
                # Skip planning for basic sections
                if section in ["Title", "References"]:
                    continue

                logger.info(f"Planning outline for {section} section")

                # If we have a content generator, use that for planning
                if self.content_generator:
                    try:
                        plan = await self._plan_section_with_content_generator(
                            topic, section, paper_title, plan_depth, previous_sections)
                        plans[section] = plan

                        # Add this section to previous_sections for context in future sections
                        previous_sections[section] = plan

                        logger.info(f"Successfully planned {section} with content generator")
                    except Exception as e:
                        logger.error(f"Error planning {section} with content generator: {str(e)}")
                        # Try to use direct API as fallback
                        try:
                            plan = await self._plan_section_with_api(
                                topic, section, paper_title, plan_depth, previous_sections)
                            plans[section] = plan

                            # Add this section to previous_sections for context in future sections
                            previous_sections[section] = plan

                            logger.info(f"Successfully planned {section} with direct API fallback")
                        except Exception as api_error:
                            logger.error(f"Fallback planning failed for {section}: {str(api_error)}")
                # Otherwise use the API directly
                else:
                    try:
                        plan = await self._plan_section_with_api(
                            topic, section, paper_title, plan_depth, previous_sections)
                        plans[section] = plan

                        # Add this section to previous_sections for context in future sections
                        previous_sections[section] = plan

                        logger.info(f"Successfully planned {section} with direct API")
                    except Exception as e:
                        logger.error(f"Error planning {section} with direct API: {str(e)}")

            logger.info(f"Successfully planned {len(plans)} sections")
            return plans

        except Exception as e:
            logger.error(f"Error planning paper sections: {str(e)}")
            # Return empty plans dictionary as fallback
            return {}

    async def plan_section(self, topic: str, section: str, tier_name: str = None) -> Dict[str, Any]:
        """
        Generate a detailed outline for a specific section.

        Args:
            topic: The main topic of the paper
            section: The section to plan (e.g., Introduction, Methodology)
            tier_name: The subscription tier (premium, standard, or sample)

        Returns:
            Dictionary containing the section plan with subsections and talking points
        """
        try:
            # Determine tier-specific planning requirements
            subsection_count, points_per_subsection = self._get_tier_requirements(section, tier_name)
            word_count = get_section_word_count(section, tier_name)

            # Build prompt for section planning
            prompt = self._build_planning_prompt(topic, section, subsection_count,
                                                points_per_subsection, word_count)

            # Get token limit based on tier (premium tier needs higher token limits)
            # Simplified to match reference implementation - using 2000 tokens for all tiers
            max_tokens = 2000  # Standard token limit for planning

            # Check if prompt is too long and trim if needed
            estimated_prompt_tokens = len(prompt.split()) * 1.3  # Rough estimation
            if estimated_prompt_tokens > 3000:
                logger.warning(f"Planning prompt for {section} is very long ({estimated_prompt_tokens:.0f} est. tokens). Trimming...")
                # Keep the key parts but trim some details
                prompt = self._trim_planning_prompt(prompt)

            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,  # Lower temperature for more consistent planning
                "max_tokens": max_tokens
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Error from OpenRouter API: Status {response.status}")
                        return self._create_fallback_plan(section, tier_name)

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return self._create_fallback_plan(section, tier_name)

                    raw_plan = data["choices"][0]["message"]["content"].strip()

                    # Parse the raw plan into a structured format
                    return self._parse_section_plan(raw_plan, section)

        except Exception as e:
            logger.error(f"Error planning {section} section: {str(e)}")
            return self._create_fallback_plan(section, tier_name)

    def _get_tier_requirements(self, section: str, tier_name: str = None) -> tuple:
        """
        Determine tier-specific requirements for section planning.

        Returns:
            Tuple of (subsection_count, points_per_subsection)
        """
        # Default values for standard tier
        subsection_count = 3
        points_per_subsection = 3

        if tier_name:
            if tier_name.lower() == "premium":
                # For premium papers, use more subsections and points for longer papers
                # Simplified to match reference implementation
                subsection_count = 5
                points_per_subsection = 5

                # Core sections in premium papers get even more detailed
                if section in ["Methodology", "Results", "Discussion", "Literature Review"]:
                    subsection_count = 7
                    points_per_subsection = 5

                # Introduction and Conclusion also get more detailed in premium papers
                elif section in ["Introduction", "Conclusion"]:
                    subsection_count = 6
                    points_per_subsection = 5
            elif tier_name.lower() == "standard":
                # Standard tier requirements
                subsection_count = 3
                points_per_subsection = 3

                # Core sections in standard papers
                if section in ["Methodology", "Results", "Discussion"]:
                    subsection_count = 4
                    points_per_subsection = 4

        return subsection_count, points_per_subsection

    def _build_planning_prompt(self, topic: str, section: str, subsection_count: int,
                              points_per_subsection: int, word_count: str) -> str:
        """Build the prompt for section planning."""
        # Split the word count range and get the maximum value
        try:
            word_count_parts = word_count.split('-')
            max_word_count = int(word_count_parts[1]) if len(word_count_parts) > 1 else int(word_count_parts[0])
        except (ValueError, IndexError):
            max_word_count = 1000  # Default fallback

        # Calculate words per subsection and per talking point
        words_per_subsection = int(max_word_count / subsection_count)
        words_per_point = int(words_per_subsection / points_per_subsection)

        # Premium tier gets a more detailed prompt
        premium_tier = subsection_count >= 8

        prompt = f"""As an expert academic paper planner, create a detailed outline for the {section} section of a research paper on {topic}.

Target word count: {word_count} words.

Create an outline with {subsection_count} subsections, each with {points_per_subsection} specific talking points that incorporate:

1. In-Depth Analysis:
   - Expand each point with detailed reasoning and evidence
   - Include specific examples, data, or case studies
   - Connect to broader theoretical frameworks
   - Provide thorough explanation of complex concepts
"""

        if premium_tier:
            prompt += """
   - Explore historical development of key concepts
   - Connect micro-level analysis with macro-level implications
   - Incorporate statistical evidence and detailed data analysis
   - Develop extended case studies to illustrate points
"""

        prompt += """
2. Alternative Viewpoints:
   - Present multiple perspectives on key issues
   - Explore counterarguments and opposing theories
   - Address potential objections to main arguments
   - Ensure balanced discussion of different viewpoints
"""

        if premium_tier:
            prompt += """
   - Analyze competing theoretical frameworks
   - Examine disciplinary divides on the topic
   - Consider cultural, geographical, and temporal variations in viewpoints
   - Construct detailed critiques of dominant perspectives
"""

        prompt += """
3. Critical Evaluation:
   - Discuss limitations and constraints
   - Examine underlying assumptions
   - Identify areas of uncertainty
   - Evaluate strength of evidence
   - Consider practical implications
"""

        if premium_tier:
            prompt += """
   - Analyze methodological soundness of existing research
   - Evaluate theoretical coherence of competing frameworks
   - Assess real-world applicability of proposed solutions
   - Identify gaps in current literature that need addressing
   - Develop criteria for evaluating quality of evidence
"""

        prompt += """
4. Interdisciplinary Insights:
   - Integrate perspectives from related fields
   - Draw parallels with similar phenomena
   - Consider cross-disciplinary implications
   - Connect to broader academic discourse
"""

        if premium_tier:
            prompt += """
   - Synthesize insights from at least 3-4 distinct academic disciplines
   - Examine methodological approaches from different fields
   - Identify potential for interdisciplinary collaboration
   - Discuss emerging hybrid approaches to the topic
   - Consider how disciplinary boundaries affect knowledge production
"""

        prompt += f"""
Guidelines for Structure:
1. Number each subsection (e.g., 2.1, 2.2) with clear, descriptive titles
2. Make each talking point specific enough to generate {3 if premium_tier else 2}-{5 if premium_tier else 3} detailed paragraphs
3. Ensure logical flow and progression of ideas
4. Include guidance on evidence and examples to use
5. Maintain balance between depth and breadth
"""

        if premium_tier:
            prompt += """
6. Structure larger sections with sub-subsections where appropriate
7. Include specific areas where original research or data should be incorporated
8. Note areas where visual elements (charts, diagrams, tables) would enhance understanding
9. Identify key connections between this section and other sections of the paper
10. Suggest specific types of sources for each major point
"""

        prompt += """
Output format:
```
# SECTION: {section}
## SUBSECTION 1: [Descriptive Title]
- Talking point 1:
  * Main argument/analysis
  * Supporting evidence/examples
  * Alternative perspectives
  * Critical considerations
- Talking point 2: [Similar structure]
...

## SUBSECTION 2: [Descriptive Title]
[Similar structure...]
```
"""

        prompt += f"""
Target approximately {words_per_subsection} words per subsection and {words_per_point} words per talking point to meet the overall word count of {word_count} words. {
"For a premium tier research paper, focus on creating comprehensive, publication-quality content with substantial depth and breadth." if premium_tier else ""
}"""

        return prompt

    def _parse_section_plan(self, raw_plan, section):
        """
        Parse the raw plan output into a structured format.
        Returns a structured text format that can be easily used by content generation.
        """
        if not raw_plan:
            return f"No plan available for {section} section"

        try:
            # Clean up the raw plan
            clean_plan = raw_plan.strip()

            # Make sure the section name is at the top
            formatted_plan = f"# {section.upper()} SECTION OUTLINE\n\n"

            # Split by clear subsection markers (1., 2., etc.)
            subsections = re.findall(r'\n\s*\d+\.\s+([^\n]+)', clean_plan)

            if subsections:
                # Found numbered subsections - now extract the text for each
                section_content = re.split(r'\n\s*\d+\.\s+', clean_plan)

                # First element might be introduction or empty
                intro = section_content[0].strip()
                if intro:
                    formatted_plan += f"## Introduction to {section}\n{intro}\n\n"

                # Process each subsection
                for i, (subsection_title, content) in enumerate(zip(subsections, section_content[1:])):
                    formatted_plan += f"## {i+1}. {subsection_title}\n"

                    # Look for bullet points or numbered items within this subsection
                    talking_points = re.findall(r'\n\s*[-•*]\s+([^\n]+)', content)
                    if not talking_points:
                        # Try alternative bullet formats
                        talking_points = re.findall(r'\n\s*[a-z]\)\s+([^\n]+)', content)

                    if talking_points:
                        for j, point in enumerate(talking_points):
                            formatted_plan += f"• {point}\n"
                    else:
                        # If no bullet points found, use the content as is
                        formatted_plan += f"{content.strip()}\n"

                    formatted_plan += "\n"
            else:
                # Fallback - simply add sections with • to be clear
                lines = clean_plan.split("\n")
                current_section = None

                for line in lines:
                    line = line.strip()
                    if not line:
                        continue

                    # Try to detect subsection headers (may be capitalized or end with colon)
                    if line.isupper() or line.endswith(":") or (len(line) < 80 and ":" in line):
                        current_section = line
                        formatted_plan += f"## {current_section}\n"
                    else:
                        # Add bullet points for content that's not a section header
                        if line.startswith("-") or line.startswith("•"):
                            formatted_plan += f"{line}\n"
                        else:
                            formatted_plan += f"• {line}\n"

            # Add implementation guidelines at the end
            formatted_plan += "\n## Implementation Guidelines\n"
            formatted_plan += "• Each subsection should be thoroughly developed\n"
            formatted_plan += "• Connect ideas between subsections for narrative flow\n"
            formatted_plan += "• Support points with evidence, examples and academic references\n"
            formatted_plan += "• Maintain appropriate academic tone and depth throughout\n"

            return formatted_plan

        except Exception as e:
            logger.error(f"Error parsing section plan: {str(e)}")
            return raw_plan  # Return the raw plan if parsing fails

    def _create_fallback_plan(self, section: str, tier_name: str = None) -> Dict[str, Any]:
        """Create a basic fallback plan if the API request fails."""
        subsection_count, points_per_subsection = self._get_tier_requirements(section, tier_name)

        # Create a simple fallback plan
        fallback_plan = {
            "section": section,
            "subsections": []
        }

        # Generate generic subsections
        for i in range(1, subsection_count + 1):
            subsection = {
                "title": f"Key Aspect {i} of {section}",
                "talking_points": [
                    f"Discuss important element {j} with supporting evidence"
                    for j in range(1, points_per_subsection + 1)
                ]
            }
            fallback_plan["subsections"].append(subsection)

        return fallback_plan

    def get_section_plan_as_text(self, section: str) -> str:
        """Convert a section plan to formatted text for inclusion in prompts."""
        if section not in self.section_plans:
            return ""

        plan = self.section_plans[section]
        text = f"Detailed outline for {section} section:\n\n"

        for i, subsection in enumerate(plan["subsections"], 1):
            text += f"Subsection {i}: {subsection['title']}\n"
            for j, point in enumerate(subsection["talking_points"], 1):
                text += f"  {j}. {point}\n"
            text += "\n"

        return text

    def _trim_planning_prompt(self, prompt: str) -> str:
        """Trim a planning prompt to a more reasonable size while keeping essential instructions."""
        lines = prompt.split('\n')

        # Keep the first 10 lines (introduction and main instructions)
        start_lines = lines[:15]

        # Skip some of the detailed guidelines
        # Find output format section to keep
        output_format_index = -1
        for i, line in enumerate(lines):
            if "Output format:" in line:
                output_format_index = i
                break

        if output_format_index > 0:
            end_lines = lines[output_format_index:]
        else:
            # If output format not found, keep last 15 lines
            end_lines = lines[-15:]

        # Combine and return
        trimmed_lines = start_lines + ["...", "Key points summarized for brevity", "..."] + end_lines
        return '\n'.join(trimmed_lines)

    async def _plan_section_with_content_generator(self, topic: str, section: str,
                                               paper_title: str, plan_depth: str,
                                               previous_sections: Dict[str, str] = None) -> str:
        """
        Plan a section using the provided content generator.

        Args:
            topic: The paper topic
            section: The section name
            paper_title: The title of the paper
            plan_depth: The depth of planning (basic, standard, comprehensive)
            previous_sections: Dictionary of previously planned sections to avoid repetition

        Returns:
            Detailed section plan as text
        """
        try:
            if not self.content_generator:
                raise ValueError("Content generator not available")

            logger.info(f"Planning section {section} with content generator")

            # Determine complexity based on plan depth
            complexity = "moderate"
            if plan_depth == "comprehensive":
                complexity = "high"
            elif plan_depth == "basic":
                complexity = "low"

            # Initialize previous_sections if not provided
            if previous_sections is None:
                previous_sections = {}

            # Create a summary of previous sections to avoid repetition
            previous_sections_summary = ""
            if previous_sections:
                previous_sections_summary = "Previously planned sections:\n\n"
                for prev_section, prev_plan in previous_sections.items():
                    # Add a brief summary of each previous section
                    prev_summary = prev_plan[:500] + "..." if len(prev_plan) > 500 else prev_plan
                    previous_sections_summary += f"--- {prev_section} ---\n{prev_summary}\n\n"

            # Use the content generator to plan the section with awareness of previous sections
            section_plan = await self.content_generator.generate_section_plan(
                topic=topic,
                section_name=section,
                paper_title=paper_title,
                complexity=complexity,
                previous_sections_summary=previous_sections_summary
            )

            if not section_plan or len(section_plan) < 50:
                logger.warning(f"Section plan for {section} is too short or empty")
                raise ValueError(f"Invalid section plan generated for {section}")

            return section_plan

        except Exception as e:
            logger.error(f"Error in _plan_section_with_content_generator: {str(e)}")
            raise

    async def _plan_section_with_api(self, topic: str, section: str,
                                 paper_title: str, plan_depth: str,
                                 previous_sections: Dict[str, str] = None) -> str:
        """
        Plan a section using the provided API.

        Args:
            topic: The paper topic
            section: The section name
            paper_title: The title of the paper
            plan_depth: The depth of planning (basic, standard, comprehensive)
            previous_sections: Dictionary of previously planned sections to avoid repetition

        Returns:
            Detailed section plan as text
        """
        try:
            logger.info(f"Planning section {section} with API")

            # Determine complexity based on plan depth
            complexity = "moderate"
            if plan_depth == "comprehensive":
                complexity = "high"
            elif plan_depth == "basic":
                complexity = "low"

            # Initialize previous_sections if not provided
            if previous_sections is None:
                previous_sections = {}

            # Create a summary of previous sections to avoid repetition
            previous_sections_summary = ""
            if previous_sections:
                previous_sections_summary = "Previously planned sections:\n\n"
                for prev_section, prev_plan in previous_sections.items():
                    # Add a brief summary of each previous section
                    prev_summary = prev_plan[:500] + "..." if len(prev_plan) > 500 else prev_plan
                    previous_sections_summary += f"--- {prev_section} ---\n{prev_summary}\n\n"

            # Build prompt for section planning
            prompt = self._build_planning_prompt(topic, section, 3, 3, complexity)

            # Add previous sections summary to the prompt
            if previous_sections_summary:
                prompt += f"\n\nIMPORTANT: Avoid repeating content from these previously planned sections:\n{previous_sections_summary}\n\nEnsure your plan for this section complements but does not duplicate the content in previous sections."

            # Get token limit based on tier (premium tier needs higher token limits)
            # Simplified to match reference implementation - using 2000 tokens for all tiers
            max_tokens = 2000  # Standard token limit for planning

            # Check if prompt is too long and trim if needed
            estimated_prompt_tokens = len(prompt.split()) * 1.3  # Rough estimation
            if estimated_prompt_tokens > 3000:
                logger.warning(f"Planning prompt for {section} is very long ({estimated_prompt_tokens:.0f} est. tokens). Trimming...")
                # Keep the key parts but trim some details
                prompt = self._trim_planning_prompt(prompt)

            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,  # Lower temperature for more consistent planning
                "max_tokens": max_tokens
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Error from OpenRouter API: Status {response.status}")
                        return self._create_fallback_plan(section, None)

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return self._create_fallback_plan(section, None)

                    raw_plan = data["choices"][0]["message"]["content"].strip()

                    # Parse the raw plan into a structured format
                    return self._parse_section_plan(raw_plan, section)

        except Exception as e:
            logger.error(f"Error in _plan_section_with_api: {str(e)}")
            return self._create_fallback_plan(section, None)