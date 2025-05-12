"""
Content Generator Module
Handles the generation of paper content using LLMs.
"""
import os
import re
import logging
import aiohttp
from typing import Dict, List, Union
from datetime import datetime

from app.services.paper_generator.config import (
    AI_MODEL, API_ENDPOINTS, SECTION_WORD_COUNTS,
    CONCLUSION_PHRASES, STOP_WORDS, SUMMARY_MAX_WORDS,
    DEFAULT_AUTHOR, TITLE_GUIDELINES, PAPER_FORMATS,
    DEFAULT_SECTIONS
)

logger = logging.getLogger(__name__)

class ContentGenerator:
    """Handles generation of paper content using LLMs."""

    def __init__(self, openrouter_key: str, research_service=None):
        """Initialize the content generator."""
        self.openrouter_key = openrouter_key
        self.research_service = research_service
        self.current_section = None
        self.section_collections = {}
        self.custom_token_limit = None  # Initialize custom token limit as None
        self.citations = {}  # Initialize citations dictionary

    def set_token_limit(self, token_limit: int):
        """Set a custom token limit for content generation.

        Args:
            token_limit: The maximum number of tokens to use for generation
        """
        self.custom_token_limit = token_limit
        logger.info(f"Set custom token limit to {token_limit} tokens")

    async def check_inappropriate_content(self, topic: str) -> bool:
        """
        Check if the topic contains inappropriate content.
        Returns True if content is inappropriate, False otherwise.
        """
        try:
            logger.info(f"Checking if topic is appropriate: {topic}")
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            moderation_prompt = f"""Evaluate if the following academic paper topic is appropriate for research in an ACADEMIC CONTEXT:

            Topic: {topic}

            IMPORTANT: This is for ACADEMIC RESEARCH. Many sensitive topics are valid for academic study.

            SPECIFICALLY ALLOWED academic topics include:
            - Analysis of combat sports (UFC, boxing, martial arts) including safety and health impacts
            - Academic studies of sexuality, gender, and reproductive health
            - Medical and psychological research on topics like suicide, self-harm, or mental health conditions
            - Sociological or criminological studies of violence, crime, or illegal activities
            - Political, historical, or cultural analysis of controversial subjects

            Only flag topics that:
            1. Explicitly request INSTRUCTIONS for illegal activities
            2. Directly promote or glorify harmful actions
            3. Specifically target individuals or groups with derogatory language
            4. Ask for help with academic dishonesty (e.g., "write my essay for me")
            5. Have NO legitimate academic or research purpose

            If the topic violates these guidelines, respond with "INAPPROPRIATE: [specific reason]"
            If the topic is appropriate for academic study, respond with "APPROPRIATE"

            Provide only one of these responses with no additional text.
            """

            moderation_payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": moderation_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 50,
                "provider": {
                    "allow_fallbacks": False
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=moderation_payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from OpenRouter API during moderation check: Status {response.status}, Response: {error_text}")
                        return False  # Default to allowing content if API check fails

                    data = await response.json()
                    if "choices" in data and data["choices"]:
                        moderation_result = data["choices"][0]["message"]["content"].strip()
                        logger.info(f"Moderation result: {moderation_result}")

                        if moderation_result.startswith("INAPPROPRIATE"):
                            reason = moderation_result.split(":", 1)[1].strip() if ":" in moderation_result else "Content violates our guidelines"
                            logger.warning(f"Topic rejected: {reason}")
                            return True  # Inappropriate content found

            return False  # Content is appropriate
        except Exception as e:
            logger.error(f"Error checking inappropriate content: {str(e)}")
            return False  # Default to allowing content if check fails

    async def generate_content(self, prompt: str, max_tokens: int = 2000) -> str:
        """Generate content based on a specific prompt.

        Args:
            prompt: The detailed prompt for content generation
            max_tokens: Maximum number of tokens to generate

        Returns:
            The generated content
        """
        try:
            logger.info(f"Generating content with max_tokens={max_tokens}")

            # Prepare the API request
            payload = {
                "model": AI_MODEL["model"],  # Use the model name directly
                "messages": [
                    {"role": "system", "content": "You are an academic research assistant helping students with their papers."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7,   # Balanced between creativity and accuracy
                "provider": {
                    "allow_fallbacks": True
                }
            }

            # Apply custom token limit if set
            if self.custom_token_limit is not None:
                payload["max_tokens"] = min(self.custom_token_limit, max_tokens)  # Use the smaller of the two

            # Make the API request
            response = await self._make_api_request(payload)

            # Extract and return the content
            if response and "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0]["message"]["content"]
                logger.info(f"Successfully generated content ({len(content.split())} words)")
                return content
            else:
                logger.error("Failed to generate content: Invalid API response")
                return "I'm sorry, I couldn't generate the requested content. Please try again."

        except Exception as e:
            logger.error(f"Error generating content: {str(e)}")
            return "I'm sorry, I couldn't generate the requested content due to an error. Please try again."

    async def generate_custom_content(self, prompt: str) -> str:
        """Generate custom content based on a specific prompt.

        Args:
            prompt: The detailed prompt for content generation

        Returns:
            The generated content
        """
        return await self.generate_content(prompt, max_tokens=2000)

    async def generate_title(self, topic: str, education_level: str) -> str:
        """Generate a title for the paper."""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            # Get education level specific guidelines
            education_level_guidelines = self._get_education_level_guidelines(education_level)

            # First, check if the topic is appropriate
            moderation_prompt = f"""Evaluate if the following academic paper topic is appropriate for research in an ACADEMIC CONTEXT:

            Topic: {topic}

            IMPORTANT: This is for ACADEMIC RESEARCH. Many sensitive topics are valid for academic study.

            SPECIFICALLY ALLOWED academic topics include:
            - Analysis of combat sports (UFC, boxing, martial arts) including safety and health impacts
            - Academic studies of sexuality, gender, and reproductive health
            - Medical and psychological research on topics like suicide, self-harm, or mental health conditions
            - Sociological or criminological studies of violence, crime, or illegal activities
            - Political, historical, or cultural analysis of controversial subjects

            Only flag topics that:
            1. Explicitly request INSTRUCTIONS for illegal activities
            2. Directly promote or glorify harmful actions
            3. Specifically target individuals or groups with derogatory language
            4. Ask for help with academic dishonesty (e.g., "write my essay for me")
            5. Have NO legitimate academic or research purpose

            If the topic violates these guidelines, respond with "INAPPROPRIATE: [specific reason]"
            If the topic is appropriate for academic study, respond with "APPROPRIATE"

            Provide only one of these responses with no additional text.
            """

            moderation_payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": moderation_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 50,
                "provider": {
                    "allow_fallbacks": False
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=moderation_payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from OpenRouter API during moderation check: Status {response.status}, Response: {error_text}")
                    else:
                        data = await response.json()
                        if "choices" in data and data["choices"]:
                            moderation_result = data["choices"][0]["message"]["content"].strip()
                            logger.info(f"Moderation result: {moderation_result}")

                            if moderation_result.startswith("INAPPROPRIATE"):
                                reason = moderation_result.split(":", 1)[1].strip() if ":" in moderation_result else "Content violates our guidelines"
                                return f"REJECTED: {reason}"

            # If moderation passes or fails to run, proceed with title generation
            prompt = f"""Generate an academic paper title about {topic}.

# EDUCATION LEVEL: {education_level.replace('-', ' ').title()}
{education_level_guidelines}

You MUST strictly adhere to the education level guidelines above. This is CRITICAL.

⚠️ CRITICAL REQUIREMENT: DO NOT INCLUDE ANY CITATIONS, REFERENCES, OR AUTHOR NAMES IN THE TITLE.
⚠️ DO NOT include any text in parentheses like (Author, Year) or [Author, Year].
⚠️ The title MUST be completely free of citations and references.
⚠️ Violation of this requirement will result in rejection of the title.

The title should be:
            """

            # Add title guidelines from config
            for i, guideline in enumerate(TITLE_GUIDELINES, 1):
                prompt += f"{i}. {guideline}\n"

            prompt += "\nReturn only the title text with no quotes or formatting."

            payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": AI_MODEL["temperature"],
                "max_tokens": AI_MODEL["title_max_tokens"],
                "provider": {
                    "allow_fallbacks": False
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from OpenRouter API: Status {response.status}, Response: {error_text}")
                        return f"Advanced {topic} Systems: A Technical Analysis"

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return f"Advanced {topic} Systems: A Technical Analysis"

                    title = data["choices"][0]["message"]["content"].strip()

                    # Remove quotes if present
                    title = title.strip('"\'')

                    logger.info(f"Generated title: {title}")

                    return title
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            return f"Advanced {topic} Systems: A Technical Analysis"

    async def generate_abstract(self, topic: str, education_level: str, key_points: List[str] = None) -> str:
        """Generate an abstract for the paper."""
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            # Get education level specific guidelines
            education_level_guidelines = self._get_education_level_guidelines(education_level)

            prompt = f"""Write an abstract for an academic paper about {topic}.

            # EDUCATION LEVEL: {education_level.replace('-', ' ').title()}
            {education_level_guidelines}

            You MUST strictly adhere to the education level guidelines above. This is CRITICAL.

            The abstract should:
            1. Be 150-250 words
            2. Summarize the paper's purpose, methods, and findings
            3. Be specific to {topic}
            4. Use language appropriate for the specified education level
            5. Avoid first-person pronouns
            6. Clearly state the research problem and significance
            7. Briefly mention methodology and key approaches
            8. Highlight the most important findings
            9. Indicate the implications of the research
            10. Be concise and clear
            """

            if key_points:
                prompt += "\n\nInclude these key points in the abstract:\n"
                for point in key_points:
                    prompt += f"- {point}\n"

            payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": AI_MODEL["temperature"],
                "max_tokens": 500,
                "provider": {
                    "allow_fallbacks": False
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from OpenRouter API: Status {response.status}, Response: {error_text}")
                        return f"This paper presents a comprehensive analysis of {topic}."

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return f"This paper presents a comprehensive analysis of {topic}."

                    abstract = data["choices"][0]["message"]["content"].strip()

                    # Clean up the abstract
                    abstract = self._clean_section_content(abstract)

                    logger.info(f"Generated abstract: {abstract[:100]}...")

                    return abstract
        except Exception as e:
            logger.error(f"Error generating abstract: {str(e)}")
            return f"This paper presents a comprehensive analysis of {topic}."

    async def generate_section(self, topic: str, section: str, education_level: str,
                            paper_format: str = "",
                            previous_sections: Dict[str, str] = None,
                            research_papers: List[Dict] = None,
                            tier_name: str = None,
                            section_plan: str = None) -> str:
        """Generate a section of the paper.

        Args:
            topic: The main topic of the paper
            section: The section to generate
            paper_format: The format of the paper
            previous_sections: Previously generated sections
            research_papers: Research papers to reference
            tier_name: The subscription tier of the user
            section_plan: Optional detailed plan for the section
            education_level: Education level (high-school, college, university, postgraduate)

        Returns:
            The generated section content
        """
        try:
            logger.info(f"Generating {section} for {topic}")

            # Determine token limit based on tier and education level
            if tier_name and tier_name.lower() == "premium":
                max_tokens = 32000  # Increased for premium
            elif tier_name and tier_name.lower() == "standard":
                max_tokens = 16000
            else:
                max_tokens = 8000

            # Adjust token limit based on education level
            if education_level == "high-school":
                # Reduce token limit for high school level to ensure simpler content
                max_tokens = min(max_tokens, 4000)
                logger.info(f"Adjusting token limit for high-school level: {max_tokens}")
            elif education_level == "college":
                max_tokens = min(max_tokens, 8000)
                logger.info(f"Adjusting token limit for college level: {max_tokens}")
            elif education_level == "university":
                max_tokens = min(max_tokens, 16000)
                logger.info(f"Adjusting token limit for university level: {max_tokens}")

            # Process previous sections to create context
            context = ""
            if previous_sections:
                context_parts = []
                for prev_section, content in previous_sections.items():
                    if prev_section != section:
                        # Summarize long previous sections to avoid context overflow
                        if len(content.split()) > 500:
                            summary = self._summarize_content(content)
                            context_parts.append(f"{prev_section}:\n{summary}")
                        else:
                            context_parts.append(f"{prev_section}:\n{content}")

                context = "\n\n".join(context_parts)

            # Get section-specific instructions
            section_instructions = self._get_section_instructions(section, paper_format)

            # Get word count guide based on section and tier
            word_count = self._get_section_word_count(section)
            target_count = int(word_count.split('-')[1]) if '-' in word_count else int(word_count)

            # Log education level being used
            logger.info(f"Using education level: {education_level} for section: {section}")

            # Tier-specific word count instructions
            if tier_name:
                if tier_name.lower() == "premium":
                    if section in ["Introduction", "Literature Review", "Methodology", "Results", "Discussion"]:
                        # Enhanced instruction for premium tier core sections
                        word_count_instruction = (
                            f"This is a PREMIUM tier paper requiring extremely detailed and comprehensive content. "
                            f"Target word count for this section: {word_count} words. "
                            f"You MUST aim for at least {target_count} words with detailed analysis and thorough exploration of the topic. "
                            f"Include detailed examples, comprehensive analysis, and thorough citations of research."
                        )
                    else:
                        word_count_instruction = f"Target word count for this section: {word_count} words. This is a PREMIUM tier paper requiring extremely detailed content."
                else:
                    word_count_instruction = f"Target word count for this section: {word_count} words. This is a PREMIUM tier paper requiring detailed content."
            else:
                word_count_instruction = f"Target word count for this section: {word_count} words."

            # Build the full instruction prompt
            prompt = self._build_section_prompt(section, topic, section_instructions,
                                               word_count_instruction, education_level, tier_name)

            # Add context from previous sections
            if context:
                prompt += f"\n\nContext from previous sections:\n{context}"

            # Include research papers if provided
            if research_papers and section not in ["Title", "Abstract", "References"]:
                cited_papers = []
                num_papers_to_include = min(len(research_papers), 15 if tier_name and tier_name.lower() == "premium" else 5)

                # For premium tier, include more research papers
                if tier_name and tier_name.lower() == "premium":
                    num_papers_to_include = min(len(research_papers), 20)  # Use up to 20 papers for premium

                prompt += f"\n\nIncorporate insights from these {num_papers_to_include} research papers:\n"

                for i, paper in enumerate(research_papers[:num_papers_to_include]):
                    title = paper.get("title", "Untitled Research")
                    authors = paper.get("authors", "Unknown Authors")
                    year = paper.get("year", "N/A")
                    snippet = paper.get("snippet", "No summary available.")
                    link = paper.get("link", "")

                    paper_info = f"{i+1}. \"{title}\" by {authors} ({year})\n"
                    paper_info += f"   Summary: {snippet}\n"
                    if link:
                        paper_info += f"   Link: {link}\n"
                    prompt += paper_info + "\n"

                    cited_papers.append({
                        "title": title,
                        "authors": authors,
                        "year": year,
                        "link": link
                    })

                # Save citations for this section
                if self.citations.get(section) is None:
                    self.citations[section] = []
                self.citations[section].extend(cited_papers)

                # Add specific instructions for research integration based on section
                if section == "Literature Review" or section == "Related Work":
                    prompt += "\nFor this Literature Review section, critically analyze ALL the papers provided above. Compare and contrast their findings, methodologies, and conclusions. Identify themes, gaps, and contradictions in the literature.\n"
                elif section == "Methodology":
                    prompt += "\nReference relevant methodologies from the research papers to support your approach. Explain how these relate to your methodology design.\n"
                elif section == "Results" or section == "Discussion":
                    prompt += "\nCompare your findings with those in the research papers. Discuss similarities and differences, and explain the implications.\n"

                # Add enhanced citation instructions to avoid placeholders
                prompt += """

CRITICAL CITATION INSTRUCTIONS:
1. NEVER use 'Citation needed' placeholders in the text
2. Every substantial claim must be properly supported with a specific citation from the provided research papers
3. When citing, use the full author name and year format (Smith, 2023) - not just [1] or numerical references
4. For critical areas requiring evidence, ALWAYS cite the most relevant research paper instead of leaving gaps
5. If you absolutely cannot find a relevant citation for an important claim, rephrase to make it a general observation rather than a specific claim requiring citation
6. Distribute citations throughout the text - don't cluster them only at the beginning or end
7. For sections with research findings, aim for at least 1-2 citations per paragraph
8. Ensure every major claim has a proper citation - this is essential for academic legitimacy
"""

            # Debug logging for section plan
            if section_plan:
                plan_length = len(section_plan.split('\n')) if isinstance(section_plan, str) else 0
                plan_subsections = section_plan.count('##') if isinstance(section_plan, str) else 0
                plan_points = section_plan.count('•') if isinstance(section_plan, str) else 0

                logger.info(f"Section plan for {section}: {plan_length} lines, {plan_subsections} subsections, {plan_points} talking points")

                # Log a preview of the section plan
                if isinstance(section_plan, str) and len(section_plan) > 0:
                    plan_preview = section_plan.split('\n')[:5]
                    logger.info(f"Section plan preview: {' | '.join(plan_preview)}")
            else:
                logger.warning(f"No section plan provided for {section}")

            # Add section plan if provided (for standard and premium tiers)
            if section_plan and tier_name and tier_name.lower() != "sample":
                prompt += f"\n\nFollow this detailed section plan:\n{section_plan}"

                # For premium tier, add extra instruction to expand each subsection extensively
                if tier_name and tier_name.lower() == "premium":
                    prompt += "\n\nAs this is a PREMIUM tier paper, develop EACH subsection in the plan EXTENSIVELY with multiple paragraphs, examples, and detailed analysis. For each bullet point, provide comprehensive explanations and examples."

            # Special handling for premium tier
            if tier_name and tier_name.lower() == "premium":
                # For premium papers, ensure we're using all available context
                prompt += """

This is a PREMIUM academic paper requiring exceptional depth, comprehensive coverage, and nuanced analysis:

1. Write with advanced academic vocabulary and complex sentence structures
2. Develop EACH key point with extensive supporting evidence, examples, and analysis
3. Include multiple perspectives and theoretical frameworks for each major concept
4. Critically analyze the limitations and implications of ALL key arguments
5. Ensure comprehensive coverage of the topic with no important aspects overlooked
6. Use precise, discipline-specific terminology throughout
7. Create a sophisticated rhetorical structure with clear transitions between complex ideas
8. Analyze relationships between concepts rather than just describing them
9. Cite research papers thoroughly and meaningfully, not just as references
10. Meet or exceed the specified premium-tier word count target

The paper should demonstrate mastery of the subject matter through its exceptional depth and scholarly rigor.
"""

            # Cache the prompt for debugging
            self.last_prompt = prompt

            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            # Configure payload with appropriate token limit based on tier
            payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": AI_MODEL["temperature"],
                "max_tokens": max_tokens,
                "provider": {
                    "allow_fallbacks": False
                }
            }

            # Apply custom token limit if set (based on education level)
            if self.custom_token_limit is not None:
                # Override max_tokens with the education level specific limit
                payload["max_tokens"] = self.custom_token_limit
                logger.info(f"Using education level specific token limit: {self.custom_token_limit}")

                # Add education level specific instructions
                if "messages" in payload and payload["messages"]:
                    education_flag = f"\n\nIMPORTANT: THIS IS {education_level.upper()} LEVEL CONTENT. ADJUST COMPLEXITY AND LENGTH ACCORDINGLY."
                    payload["messages"][0]["content"] += education_flag
            # For premium tier without custom token limit, use maximum possible token limit
            # This is crucial to match the reference implementation which generates 20k+ word papers
            elif tier_name and tier_name.lower() == "premium":
                # Set maximum allowed tokens for premium tier content generation
                payload["max_tokens"] = 32000  # Higher token limit to ensure complete generation
                logger.info(f"Using maximum token limit for premium tier content generation: 32000")

                # Additionally, let the model know this is premium content requiring length
                if "messages" in payload and payload["messages"]:
                    premium_flag = "\n\nIMPORTANT: THIS IS PREMIUM TIER CONTENT. GENERATE MUCH LONGER, MORE DETAILED CONTENT THAN STANDARD PAPERS."
                    payload["messages"][0]["content"] += premium_flag

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from OpenRouter API: Status {response.status}, Response: {error_text}")
                        return f"Error generating {section}. Please try again later."

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return f"Error generating {section}. Please try again later."

                    section_content = data["choices"][0]["message"]["content"].strip()

                    # Store in collections for retrieval and analysis
                    if section not in self.section_collections:
                        self.section_collections[section] = []
                    self.section_collections[section].append(section_content)

                    # Process the content
                    section_content = self._clean_section_content(section_content)

                    # Log the actual word count of generated content
                    word_count = len(section_content.split())
                    logger.info(f"Generated {section} with {word_count} actual words")

                    # For premium tier, check if content is substantive enough
                    if tier_name and tier_name.lower() == "premium" and section not in ["Abstract", "Title", "References"]:
                        if word_count < 1000:
                            logger.warning(f"Premium tier {section} section has only {word_count} words - below target")

                    # For sample tier, ensure content doesn't exceed word limits
                    if tier_name and tier_name.lower() == "sample":
                        max_words = 150  # Conservative limit for sample tier sections

                        if word_count > max_words:
                            logger.info(f"Truncating {section} content for sample tier: {word_count} -> {max_words} words")
                            # Simple truncation to first n words + ellipsis
                            section_content = " ".join(section_content.split()[:max_words]) + "..."

                    # Check for any remaining "Citation needed" placeholders and log a warning
                    if "citation needed" in section_content.lower() or "citation required" in section_content.lower():
                        logger.warning(f"Section {section} still contains 'citation needed' placeholders despite instructions")

                    return section_content
        except Exception as e:
            logger.error(f"Error generating {section}: {str(e)}")
            return f"Error generating {section}. Please try again later."

    def _clean_section_content(self, content: str) -> str:
        """Remove markdown formatting, redundant conclusions, and extra whitespace."""
        # Split into paragraphs
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if not paragraphs:
            return content

        # Process each paragraph - clean up markdown formatting
        cleaned_paragraphs = []
        for para in paragraphs:
            # Clean up section headers first
            lines = para.split('\n')
            cleaned_lines = []

            for line in lines:
                # Remove markdown header formatting (###, ##, #)
                if re.match(r'^#+\s+', line):
                    line = re.sub(r'^#+\s+', '', line)

                # Remove asterisk formatting (***Bold***, **Bold**, *Italic*)
                if re.match(r'^\*+\s+', line):
                    line = re.sub(r'^\*+\s+', '', line)

                # Remove underscore formatting (___Bold___, __Bold__, _Italic_)
                if re.match(r'^_+\s+', line):
                    line = re.sub(r'^_+\s+', '', line)

                cleaned_lines.append(line)

            # Rejoin the lines
            cleaned_para = '\n'.join(cleaned_lines)
            cleaned_paragraphs.append(cleaned_para)

        # Filter redundant content and conclusions
        unique_paragraphs = []
        seen_content = set()

        for para in cleaned_paragraphs:
            # Normalize paragraph
            normalized = ' '.join(self._normalize_text(para))
            if normalized not in seen_content:
                seen_content.add(normalized)
                unique_paragraphs.append(para)

        # Remove redundant conclusions
        conclusion_phrases = CONCLUSION_PHRASES

        final_paragraphs = []

        for para in unique_paragraphs:
            # Remove markdown formatting from headers
            if para.startswith('###') or para.startswith('##') or para.startswith('#'):
                para = re.sub(r'^#+\s*', '', para)

            # Remove asterisk formatting
            if para.startswith('***') or para.startswith('**') or para.startswith('*'):
                para = re.sub(r'^\*+\s*', '', para)

            # Check if this is a conclusion paragraph
            is_conclusion = any(phrase in para.lower() for phrase in conclusion_phrases)

            # Only include conclusion paragraphs in the actual Conclusion section
            # But allow them in the Abstract section since abstracts often contain summary language
            if is_conclusion and hasattr(self, 'current_section') and self.current_section != "Conclusion" and self.current_section != "Abstract":
                # Skip conclusion paragraphs in non-conclusion sections (except Abstract)
                continue
            else:
                final_paragraphs.append(para)

        # Remove extra whitespace
        cleaned_content = '\n\n'.join(final_paragraphs)
        cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)

        return cleaned_content

    def _get_education_level_guidelines(self, education_level: str) -> str:
        """Get guidelines specific to the education level."""
        guidelines = {
            "high-school": """
            For HIGH SCHOOL level content:
            - Use simpler vocabulary and shorter sentences
            - Explain concepts in basic terms without complex jargon
            - Focus on fundamental concepts and clear explanations
            - Use more examples and concrete illustrations
            - Keep paragraphs shorter (3-4 sentences)
            - Aim for a reading level appropriate for ages 14-18
            - Use a more informal, engaging tone
            - Include more step-by-step explanations
            - Avoid complex theoretical frameworks
            - Limit the depth of analysis
            """,

            "college": """
            For COLLEGE level content:
            - Use moderate vocabulary with some field-specific terminology
            - Include more detailed explanations and examples
            - Introduce some theoretical concepts with explanations
            - Balance theory and practical applications
            - Maintain a semi-formal academic tone
            - Include some critical analysis but keep it accessible
            - Provide context for more complex ideas
            - Use a mix of simple and complex sentence structures
            - Include some references to academic sources
            - Aim for a reading level appropriate for undergraduate students
            """,

            "university": """
            For UNIVERSITY level content:
            - Use proper academic vocabulary and field-specific terminology
            - Develop complex arguments with supporting evidence
            - Include theoretical frameworks and models
            - Provide in-depth analysis of concepts and ideas
            - Maintain a formal academic tone throughout
            - Include critical evaluation of different perspectives
            - Make connections between different theories and concepts
            - Use proper academic citations and references
            - Include methodological considerations where appropriate
            - Aim for a reading level appropriate for advanced undergraduate or early graduate students
            """,

            "postgraduate": """
            For POSTGRADUATE level content:
            - Use sophisticated academic vocabulary and specialized terminology
            - Develop complex theoretical arguments in depth
            - Include detailed critical analysis of competing theories
            - Discuss methodological implications and limitations
            - Maintain a highly formal academic tone
            - Include nuanced discussion of epistemological considerations
            - Make connections to broader theoretical frameworks
            - Include detailed discussion of research implications
            - Address gaps in current research and theory
            - Aim for a reading level appropriate for advanced graduate students and academics
            """,

            # Default to undergraduate level if not specified
            "default": """
            For UNDERGRADUATE level content:
            - Use proper academic vocabulary and field-specific terminology
            - Develop arguments with supporting evidence
            - Include some theoretical frameworks with explanations
            - Provide analysis of concepts and ideas
            - Maintain a formal academic tone
            - Include evaluation of different perspectives
            - Make connections between related concepts
            - Use proper academic citations
            - Aim for a reading level appropriate for university students
            """
        }

        # Return the guidelines for the specified education level, or default if not found
        return guidelines.get(education_level.lower(), guidelines["default"])

    def _normalize_text(self, text: str) -> List[str]:
        """Normalize text for comparison."""
        # Convert to lowercase
        text = text.lower()
        # Remove punctuation
        text = re.sub(r'[^\w\s]', '', text)
        # Split into words
        words = text.split()
        # Remove common words
        stop_words = STOP_WORDS
        words = [word for word in words if word not in stop_words]
        return words

    def _summarize_content(self, content: str, max_words: int = SUMMARY_MAX_WORDS) -> str:
        """Extract key points from content."""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', content)

        # Take first 2 sentences and last sentence
        if len(sentences) <= 3:
            return content

        summary = ' '.join(sentences[:2])

        # Check if we're under the word limit
        if len(summary.split()) < max_words:
            summary += ' ... ' + sentences[-1]

        return summary

    def _format_citation(self, paper: Dict) -> str:
        """Format a paper as a citation string."""
        try:
            # Extract author names
            authors = paper.get('authors', [DEFAULT_AUTHOR])
            if not authors:
                authors = [DEFAULT_AUTHOR]

            # Format author list
            if len(authors) == 1:
                author_text = authors[0]
            elif len(authors) == 2:
                author_text = f"{authors[0]} and {authors[1]}"
            else:
                author_text = f"{authors[0]} et al."

            # Get year
            year = paper.get('year', '')

            # Get title
            title = paper.get('title', 'Untitled')

            # Get publication
            publication = paper.get('publication', '')

            # Format citation
            citation = f"{author_text} ({year}). {title}"

            # Add publication info if available
            if publication:
                citation += f". {publication}"

                # Add volume and pages if available
                volume = paper.get('volume', '')
                pages = paper.get('pages', '')

                if volume:
                    citation += f", {volume}"

                if pages:
                    citation += f", {pages}"

            # Add link if available
            link = paper.get('link', '')
            if link:
                citation += f". Available at: {link}"

            return citation
        except Exception as e:
            logger.error(f"Error formatting citation: {str(e)}")
            return f"{DEFAULT_AUTHOR} (Unknown). {paper.get('title', 'Untitled')}"

    def _format_citations_for_context(self, papers: List[Dict]) -> str:
        """Format paper information as context for the LLM."""
        if not papers:
            return "No research papers available for citation."

        formatted_papers = []
        for paper in papers:
            # Get author information
            authors = paper.get('authors', [DEFAULT_AUTHOR])
            if not authors:
                authors = [DEFAULT_AUTHOR]

            # Format author for citation
            if len(authors) == 1:
                author_text = authors[0]
            elif len(authors) == 2:
                author_text = f"{authors[0]} and {authors[1]}"
            else:
                author_text = f"{authors[0]} et al."

            # Get year
            year = paper.get('year', '')

            # Format citation
            citation = self._format_citation(paper)

            # Add snippet if available
            snippet = paper.get('snippet', "")
            if snippet:
                # Truncate snippet if too long
                if len(snippet) > 200:
                    snippet = snippet[:200] + "..."
                formatted_paper = f"[{author_text}, {year}] {citation}\nSummary: {snippet}"
            else:
                formatted_paper = f"[{author_text}, {year}] {citation}"

            formatted_papers.append(formatted_paper)

        return "Available research papers for citation:\n\n" + "\n\n".join(formatted_papers)

    def _get_section_word_count(self, section: str) -> str:
        """
        Return the appropriate word count range for each section to achieve
        a total paper length of 4,000-8,000 words.
        """
        return SECTION_WORD_COUNTS.get(section, SECTION_WORD_COUNTS["default"])

    def _get_section_instructions(self, section: str, paper_format: str) -> str:
        """Get specific instructions for a section based on paper format."""

        # Add research pack section instructions
        research_pack_instructions = {
            "Study Guide - Key Concepts": """Create a comprehensive breakdown of key concepts from the paper. Include:
1. Clear definitions of important terms and theories
2. Explanation of core methodologies
3. Key relationships and dependencies between concepts
4. Visual representations or diagrams where helpful
5. Examples that illustrate complex ideas""",

            "Study Guide - Questions": """Generate thought-provoking study questions that help understand the material deeply. Include:
1. Comprehension questions about main concepts
2. Analysis questions that require critical thinking
3. Application questions that connect to real-world scenarios
4. Discussion questions that encourage deeper exploration
5. Self-assessment questions to check understanding""",

            "Research Plan - Outline": """Create a detailed research plan that guides through the paper development process. Include:
1. Step-by-step research methodology
2. Timeline suggestions for each phase
3. Data collection and analysis strategies
4. Key areas to focus investigation
5. Potential challenges and mitigation strategies""",

            "Research Plan - Sources": """Provide a curated list of suggested sources and research directions. Include:
1. Key academic databases to search
2. Specific journals relevant to the topic
3. Search terms and keywords to use
4. Types of sources to look for (primary, secondary, etc.)
5. Tips for evaluating source credibility""",

            "Enhancement Guide - Improvements": """Suggest specific ways to enhance and strengthen the paper. Include:
1. Areas that could benefit from more detail
2. Suggestions for additional research angles
3. Methods to strengthen arguments
4. Ways to improve methodology
5. Tips for better data presentation""",

            "Enhancement Guide - Insights": """Provide guidance for developing personal insights and original contributions. Include:
1. Questions to spark critical thinking
2. Areas for potential innovation
3. Gaps in current research to explore
4. Ways to connect different concepts
5. Prompts for developing unique perspectives"""
        }

        # First check if it's a research pack section
        if section in research_pack_instructions:
            return research_pack_instructions[section]

        # If not, use the standard section instructions
        standard_instructions = {
            "Abstract": "Provide a concise summary of the entire paper including purpose, methodology, results, and conclusions. Do not cite references in the abstract. If the research involves statistical analysis, briefly mention key findings with significance levels.",

            "Introduction": "Introduce the topic, provide background information, state the research problem, and outline the paper's objectives. Establish the significance of the research. Include a clear research question or hypothesis where applicable.",

            "Literature Review": "Critically analyze and summarize existing research relevant to the topic. Identify gaps in current knowledge that your paper addresses. Only cite credible, peer-reviewed sources.",

            "Related Work": "Discuss and compare previous approaches, models, or systems related to your topic. Focus on technical aspects and contributions of prior work. Highlight how your work builds upon or differs from existing research.",

            "Research Questions/Hypothesis": "Clearly state the research questions or hypotheses being investigated. Explain the rationale behind each question or hypothesis.",

            "Methodology": "Describe the research methods, experimental design, data collection procedures, and analytical techniques used. Provide enough detail for replication. When describing patient demographics or study characteristics in tables, use realistic data values with appropriate sample sizes, means, and standard deviations. Do not use placeholders. Explicitly define data selection criteria, sample size calculation rationale, and potential sources of bias. Include a brief paragraph on ethical considerations relevant to the research.",

            "Proposed Method": "Detail the technical approach, algorithms, models, or frameworks proposed. Include mathematical formulations, pseudocode, or system architecture as appropriate.",

            "Experiments": "Describe the experimental setup, datasets, evaluation metrics, and implementation details. Explain how experiments test the proposed method.",

            "Ethical Considerations": "Discuss ethical implications of the research, including privacy concerns, potential biases, societal impacts, and mitigation strategies. Address compliance with applicable guidelines for research integrity and data handling.",

            "Results": "Present the findings objectively without interpretation. Include tables, figures, and statistics as appropriate. When creating tables, use realistic data values with appropriate means, standard deviations, and sample sizes that reflect the described population. Do not use placeholders like '[insert number here]' or '[insert mean and SD]'. For statistical results, include p-values, confidence intervals, and appropriate hypothesis tests where applicable. Use well-labeled tables and appropriate visualizations (charts, plots) to represent key findings.",

            "Discussion": "Interpret the results, explain their significance, and relate them to existing literature. Address whether the findings support the hypothesis. Clearly state the limitations of the study, acknowledging any methodological constraints, potential biases, or uncertainties in the data.",

            "Limitations": "Honestly acknowledge the limitations, constraints, and potential weaknesses of the study or approach. Discuss how these limitations might affect the interpretation of results and suggest how they might be addressed in future work.",

            "Future Work": "Suggest directions for future research, improvements, or extensions based on the current findings.",

            "Conclusion": "Summarize the key findings and their implications. Emphasize the contribution to the field without introducing new information.",

            "References": "List all sources cited in the paper using APA 7th Edition format. Include ONLY the papers you actually cited in the text. For each reference, include all required elements (authors, year, title, journal, volume, pages)."
        }

        # Format-specific modifications to instructions
        format_specific_instructions = {
            "computer_science": {
                "Related Work": "Compare your approach with existing methods in terms of technical innovation, performance metrics, and limitations. Focus on recent and directly relevant work.",
                "Proposed Method": "Provide detailed technical description of your approach including algorithms, architectures, and implementation details. Use mathematical notation where appropriate.",
                "Experiments": "Describe benchmarks, datasets, evaluation metrics, and experimental setup in detail. Compare results with state-of-the-art methods."
            },

            "ethical_research": {
                "Ethical Considerations": "Thoroughly analyze ethical implications including: 1) Privacy and data protection, 2) Potential biases and fairness, 3) Societal impacts, 4) Compliance with regulations, and 5) Mitigation strategies implemented."
            },

            "literature_review": {
                "Literature Review": "Provide a comprehensive analysis of existing literature organized by themes or chronologically. Critically evaluate methodologies, findings, and limitations of previous studies. Identify research gaps this paper addresses."
            },

            "hypothesis_driven": {
                "Research Questions/Hypothesis": "Clearly state each hypothesis in testable form. Explain the theoretical basis for each hypothesis and how it relates to existing knowledge. Describe how each hypothesis will be tested."
            },

            "extended_discussion": {
                "Limitations": "Discuss methodological limitations, theoretical constraints, and practical challenges encountered. Address potential threats to validity and generalizability.",
                "Future Work": "Propose specific research directions, methodological improvements, and potential applications. Explain how future work could address the limitations identified."
            },

            "academic_research": {
                "Abstract": "Provide a concise summary of the paper including purpose, methodology, key results with statistical significance (p-values), and main conclusions. Do not include citations. Limit to 250 words.",

                "Introduction": "Introduce the topic with relevant background, clearly state the research problem, and outline the paper's objectives. Establish significance of the research and include explicit research questions or hypotheses. Use citations to support key claims and establish the context of your work within the existing literature.",

                "Methodology": "Describe research methods in detail sufficient for replication. Include: 1) Selection criteria and sample size justification, 2) Data collection methods, 3) Statistical tests used (chi-squared, ANOVA, regression, etc.), 4) Potential sources of bias and how they were addressed, 5) Ethical considerations including research approval, data privacy, consent procedures, and compliance with relevant guidelines (IRB, GDPR, HIPAA, etc.). Use subsections to organize this information clearly.",

                "Results": "Present findings objectively without interpretation. Include: 1) Statistical analyses with p-values, confidence intervals, and effect sizes, 2) Well-labeled tables with clear titles (e.g., 'Table 1. Performance Comparison Across Models'), 3) Relevant data visualizations (bar charts, scatter plots, survival curves, histograms) with proper labeling, 4) Explicit statement of which statistical tests were used for each analysis. Use realistic data values instead of placeholders.",

                "Discussion": "Interpret results and relate them to existing literature. Discuss whether findings support the hypothesis and their broader implications. Maintain an academic tone with evidence-based claims. Avoid vague or generalized statements.",

                "Limitations": "Clearly define the study's limitations, including constraints in methodology, potential biases, and areas for future research. Be specific about how limitations might affect interpretation of results.",

                "Conclusion": "Summarize key findings and their implications. Tie conclusions directly to research objectives and avoid speculative claims. Conclusions must be evidence-based and supported by the presented results.",

                "References": "List only peer-reviewed, verifiable academic literature. Format citations according to APA 7th Edition style. Include ONLY sources actually cited in the text. Each reference should include all required elements (authors, year, title, journal, volume, pages)."
            }
        }

        # Get base instructions
        instructions = standard_instructions.get(section, "Write this section in a formal academic style appropriate for the topic.")

        # Apply format-specific modifications if available
        if paper_format in format_specific_instructions and section in format_specific_instructions[paper_format]:
            instructions = format_specific_instructions[paper_format][section]

        return instructions

    async def _make_api_request(self, payload: dict) -> dict:
        """Make an API request to the OpenRouter API.

        Args:
            payload: The request payload

        Returns:
            The API response as a dictionary
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error from OpenRouter API: Status {response.status}, Response: {error_text}")
                        return None

                    return await response.json()

        except Exception as e:
            logger.error(f"Error making API request: {str(e)}")
            return None

    def _get_education_level_guidelines(self, education_level: str) -> str:
        """Get detailed guidelines for the specified education level."""
        guidelines = {
            "undergraduate": """
This research guidance MUST be tailored for UNDERGRADUATE level students (UK university, US college):

1. VOCABULARY: Use clear academic language with appropriate field-specific terminology. Define specialized terms when first introduced. Explain to students when and how to use discipline-specific vocabulary in their own research.

2. RESEARCH APPROACH: Guide students on intermediate research methodologies appropriate for undergraduate work. Explain how to develop research questions, conduct literature reviews, and analyze findings at this academic level.

3. CONCEPTS: Introduce and explain intermediate academic concepts and theoretical frameworks. Show students how to identify and apply these frameworks to their own research topics.

4. ORGANIZATION: Provide clear guidance on academic structure with examples of well-developed paragraphs and sections. Include templates and outlines students can adapt for their own work.

5. CRITICAL THINKING: Offer strategies for developing critical thinking and analytical skills. Show students how to evaluate evidence and arguments from different perspectives.

6. RESEARCH DEPTH: Guide students on appropriate depth for undergraduate research. Explain how to go beyond surface-level understanding while maintaining realistic scope for this academic level.

7. SOURCE EVALUATION: Teach students how to identify, evaluate, and incorporate credible academic sources. Provide examples of effective citation practices and explain their importance.

The final content should provide practical, actionable research guidance that helps undergraduate students develop competence in academic research and writing.
""",
            "high-school": """
This paper MUST be written at a HIGH SCHOOL level (UK Key Stage 4, GCSE, or US grades 9-12):

1. VOCABULARY: Use straightforward language with limited academic terminology. When technical terms are necessary, define them clearly.

2. SENTENCE STRUCTURE: Use mostly simple and compound sentences. Limit complex sentences with multiple clauses.

3. CONCEPTS: Explain basic concepts thoroughly. Avoid advanced theoretical frameworks. Focus on fundamental principles.

4. EXAMPLES: Use concrete, relatable examples that high school students would understand from their everyday experience or general knowledge.

5. ANALYSIS: Keep analysis straightforward. Focus on obvious connections and clear cause-effect relationships.

6. DEPTH: Maintain moderate depth - cover key points without extensive elaboration on nuances or exceptions.

7. CITATIONS: Use minimal citations. Focus on widely recognized sources or basic textbook knowledge.

The final content should be easily understood by a 15-17 year old student with no specialized knowledge of the subject.
""",

            "college": """
This paper MUST be written at a COLLEGE level (UK A-Levels, US undergraduate years 1-2, or equivalent to UK Level 4-5):

1. VOCABULARY: Use a mix of everyday and academic language. Introduce field-specific terminology with brief explanations.

2. SENTENCE STRUCTURE: Use a balanced mix of simple and complex sentences. Paragraphs should have clear topic sentences and supporting details.

3. CONCEPTS: Introduce some specialized concepts but explain them clearly. Begin to connect concepts to broader theoretical frameworks.

4. EXAMPLES: Use examples that demonstrate application of concepts, including some field-specific examples that require modest background knowledge.

5. ANALYSIS: Develop moderate analytical depth. Examine relationships between concepts and begin to evaluate different perspectives.

6. DEPTH: Provide more detailed explanations than high school level, but avoid highly specialized debates or advanced theoretical nuances.

7. CITATIONS: Include regular citations from textbooks, introductory academic articles, and reliable online sources.

The final content should be appropriate for a first or second-year undergraduate student with basic familiarity with the subject area.
""",

            "university": """
This paper MUST be written at a UNIVERSITY level (UK undergraduate degree, US years 3-4, or equivalent to UK Level 6):

1. VOCABULARY: Use appropriate academic language and discipline-specific terminology. Technical terms can be used with minimal explanation if they're standard in the field.

2. SENTENCE STRUCTURE: Use varied sentence structures including complex sentences. Paragraphs should develop complete arguments with evidence and analysis.

3. CONCEPTS: Engage with specialized concepts and theoretical frameworks. Make connections between different theories and approaches.

4. EXAMPLES: Use discipline-specific examples that demonstrate nuanced understanding. Examples should illustrate complex points or theoretical applications.

5. ANALYSIS: Develop substantial analytical depth. Evaluate competing perspectives and identify strengths and limitations of different approaches.

6. DEPTH: Provide detailed explanations that acknowledge complexity and nuance. Address potential counterarguments.

7. CITATIONS: Include regular citations from peer-reviewed academic sources, emphasizing recent scholarship in the field.

The final content should be appropriate for a final-year undergraduate student with substantial background in the subject area.
""",

            "postgraduate": """
This paper MUST be written at a POSTGRADUATE level (UK Masters/PhD, US graduate school, or equivalent to UK Level 7-8):

1. VOCABULARY: Use sophisticated academic language and specialized terminology appropriate to advanced discourse in the field. Technical vocabulary should be used precisely and accurately.

2. SENTENCE STRUCTURE: Use complex sentence structures that convey nuanced arguments. Paragraphs should develop sophisticated arguments with multiple layers of analysis.

3. CONCEPTS: Engage deeply with advanced theoretical frameworks and specialized concepts. Critically evaluate theoretical positions and their epistemological foundations.

4. EXAMPLES: Use sophisticated examples that demonstrate expert understanding. Examples should illustrate complex theoretical points or methodological applications.

5. ANALYSIS: Develop sophisticated analysis that identifies subtle distinctions and implications. Evaluate methodological approaches and theoretical frameworks critically.

6. DEPTH: Provide comprehensive explanations that engage with current scholarly debates. Address complexities, contradictions, and limitations in current research.

7. CITATIONS: Include extensive citations from recent peer-reviewed academic sources, demonstrating familiarity with current research and seminal works in the field.

The final content should demonstrate expertise comparable to published academic work in scholarly journals.
"""
        }

        # Default to undergraduate if the specified level is not found
        return guidelines.get(education_level, guidelines["undergraduate"])

    def _build_section_prompt(self, section: str, topic: str, section_instructions: str,
                             word_count_instruction: str, education_level: str,
                             tier_name: str = None) -> str:
        """Build the prompt for generating a section."""

        # Get education level specific guidelines
        education_level_guidelines = self._get_education_level_guidelines(education_level)

        prompt = f"""As Lily, an AI research assistant, generate the {section} section for a research pack on {topic}.

# EDUCATION LEVEL: {education_level.replace('-', ' ').title()}
{education_level_guidelines}

You MUST strictly adhere to the education level guidelines above. This is CRITICAL.

{section_instructions}

{word_count_instruction}

IMPORTANT: This is NOT an example paper but a research guidance pack. For this {section} section, include:

1. SKILL DEVELOPMENT: Provide practical research and writing skills specific to this section
2. MINI-EXAMPLES: Include short, targeted examples of well-written content (not complete sections)
3. ACTIVITIES: Create interactive exercises, brainstorming prompts, or planning templates
4. GUIDANCE: Offer step-by-step instructions on how to approach this part of the research
5. COMMON PITFALLS: Highlight mistakes students often make and how to avoid them

If this is a Topic Builder section:
- Help students narrow and refine their topic
- Provide question frameworks to develop research questions
- Include examples of strong vs. weak research questions

If this is a Mind Map Activity section:
- Create a textual description of a mind map structure
- Show how key concepts connect to subtopics
- Provide instructions for students to expand the map

If this is a Research Skills section:
- Offer practical search strategies for finding sources
- Explain how to evaluate source credibility
- Provide templates for organizing research findings

If this is a Writing Toolkit section:
- Include paragraph templates for different purposes
- Provide transition phrases and academic vocabulary lists
- Show examples of effective argumentation structures

IMPORTANT: Throughout your content, include Lily's voice and personality. Write in first person as Lily, addressing the student directly with a friendly, mentoring tone. For example:

"I've found that students often struggle with narrowing their topic. Let me help you with that! Start by asking yourself these three questions..."

"Here's a mini-example of how you might structure your introduction paragraph. Notice how I've included a hook, context, and a clear thesis statement."

"Let's work through this brainstorming activity together. I'll guide you step by step to organize your thoughts on this topic."

Write in a clear, instructional style that guides students through the research process while maintaining academic rigor appropriate for their education level."""

        # Add tier-specific instructions
        if tier_name and tier_name.lower() == "premium":
            prompt += """

For Premium Tier Research Pack:
- Provide more extensive skill development activities and exercises
- Include additional mini-examples showing different approaches to the same content
- Create more detailed planning templates and organizational tools
- Offer advanced research strategies with step-by-step guidance
- Include more comprehensive brainstorming frameworks and critical thinking prompts
- Provide more extensive vocabulary lists and academic phrase banks
- Develop more detailed mind mapping structures with multiple branching options
- Include weekend planning templates and time management strategies"""

        return prompt

    async def generate_dynamic_sections(self, topic: str) -> List[str]:
        """
        Generate dynamic sections for a paper based on the topic.
        Returns a list of section names.
        """
        try:
            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            prompt = f"""Given the topic "{topic}", suggest 5-8 appropriate sections for an academic research paper.

Your suggestions should:
1. Follow a logical structure for scholarly work
2. Include standard sections like Introduction and Conclusion
3. Be specific to the topic's domain and requirements
4. Use formal academic naming conventions
5. Provide a complete structure for a substantial scholarly paper

Return ONLY the section names, numbered, one per line, with no additional text.
"""

            payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 200
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Error from OpenRouter API: Status {response.status}")
                        return DEFAULT_SECTIONS

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return DEFAULT_SECTIONS

                    sections_text = data["choices"][0]["message"]["content"].strip()

                    # Parse the returned text into a list of sections
                    sections = []
                    for line in sections_text.split("\n"):
                        # Remove numbering, whitespace, and other characters
                        clean_line = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
                        clean_line = clean_line.strip()
                        if clean_line:
                            sections.append(clean_line)

                    if not sections:
                        logger.warning("No valid sections found in API response")
                        return DEFAULT_SECTIONS

                    # Ensure critical sections are included
                    if "Title" not in sections:
                        sections.insert(0, "Title")
                    if "Abstract" not in sections:
                        sections.insert(1, "Abstract")
                    if "References" not in sections:
                        sections.append("References")

                    logger.info(f"Generated dynamic sections: {sections}")
                    return sections

        except Exception as e:
            logger.error(f"Error generating dynamic sections: {str(e)}")
            return DEFAULT_SECTIONS

    async def generate_section_plan(self, topic: str, section_name: str, paper_title: str, complexity: str = "moderate") -> str:
        """
        Generate a detailed plan for a specific section of a research paper.

        Args:
            topic: The main topic of the paper
            section_name: The name of the section to plan
            paper_title: The title of the paper
            complexity: Desired complexity level (low, moderate, high)

        Returns:
            A detailed section plan as text
        """
        try:
            logger.info(f"Generating plan for section: {section_name} (complexity: {complexity})")

            headers = {
                "Authorization": f"Bearer {self.openrouter_key}",
                "Content-Type": "application/json"
            }

            # Adjust token length based on complexity
            max_tokens = 1000
            if complexity == "high":
                max_tokens = 2000
            elif complexity == "low":
                max_tokens = 500

            prompt = f"""Create a detailed plan for the "{section_name}" section of a research paper titled:
"{paper_title}"

Main topic: {topic}

The plan should include:
1. The main arguments or points to cover
2. Key concepts to explain
3. Data or evidence to include
4. Logical flow of ideas
5. How this section connects to the overall paper

This is for a {complexity}-complexity academic paper. Make the plan appropriately detailed for this level.
The section plan should be well-structured, comprehensive, and follow academic standards.

Format the plan with clear subheadings, bullet points, and a logical progression of ideas.
"""

            payload = {
                "model": AI_MODEL["name"],
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": max_tokens
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(API_ENDPOINTS["openrouter"], headers=headers, json=payload) as response:
                    if response.status != 200:
                        logger.error(f"Error from OpenRouter API: Status {response.status}")
                        return f"# {section_name} Plan\n\n- Cover key aspects of {topic}\n- Analyze main concepts\n- Provide evidence and data\n- Conclude with insights"

                    data = await response.json()

                    if "choices" not in data or not data["choices"]:
                        logger.error("No choices in OpenRouter API response")
                        return f"# {section_name} Plan\n\n- Cover key aspects of {topic}\n- Analyze main concepts\n- Provide evidence and data\n- Conclude with insights"

                    section_plan = data["choices"][0]["message"]["content"].strip()

                    # Validate the plan has sufficient content
                    if len(section_plan.split()) < 50:
                        logger.warning(f"Section plan for {section_name} is too short, using fallback")
                        return f"# {section_name} Plan\n\n- Cover key aspects of {topic}\n- Analyze main concepts\n- Provide evidence and data\n- Conclude with insights"

                    logger.info(f"Successfully generated plan for {section_name} section")
                    return section_plan

        except Exception as e:
            logger.error(f"Error generating section plan: {str(e)}")
            return f"# {section_name} Plan\n\n- Cover key aspects of {topic}\n- Analyze main concepts\n- Provide evidence and data\n- Conclude with insights"

    def _clean_content(self, content: str) -> str:
        # ... existing code ...
        pass
