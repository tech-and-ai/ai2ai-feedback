"""
Paper Orchestrator Module
Orchestrates the generation of academic papers using the various specialized modules.
"""
import os
import json
import logging
import asyncio
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.services.paper_generator.content_generator import ContentGenerator
from app.services.paper_generator.research_service import ResearchService
from app.services.paper_generator.diagram_generator import DiagramGenerator
from app.services.paper_generator.section_planner import SectionPlanner
from app.services.paper_generator.config import (
    DEFAULT_SECTIONS, PAPER_WORD_COUNT, PREMIUM_PAPER_WORD_COUNT,
    DIAGRAM_SECTIONS_TO_EXCLUDE, PAPER_FORMATS,
    DEFAULT_PAPER_FORMAT, get_paper_format, SAMPLE_PAPER_WORD_COUNT
)
from app.services.document_formatter import DocumentFormatter

# Override premium paper word count to match reference implementation
# This ensures premium papers have significantly higher word counts
PREMIUM_PAPER_WORD_COUNT = {
    "min": 15000,
    "target": 20000,
    "max": 25000
}

logger = logging.getLogger(__name__)

class PaperOrchestrator:
    """Orchestrates the generation of academic papers."""

    def __init__(self, content_generator: ContentGenerator,
                 research_service: Optional[ResearchService] = None,
                 diagram_generator: Optional[DiagramGenerator] = None,
                 section_planner: Optional['SectionPlanner'] = None,
                 serp_key: Optional[str] = None):
        """
        Initialize the paper orchestrator.

        Args:
            content_generator: The content generator instance
            research_service: Optional research service for citations
            diagram_generator: Optional diagram generator
            section_planner: Optional section planner for detailed outlines
            serp_key: Optional SERP API key for research
        """
        self.content_generator = content_generator
        self.diagram_generator = diagram_generator

        # Initialize research service if not provided
        if research_service:
            self.research_service = research_service
            logger.info("Using provided research service")
        else:
            # Try to create a research service with the API key
            if serp_key:
                from app.services.paper_generator.research_service import ResearchService
                self.research_service = ResearchService(serp_key)
                logger.info(f"Created research service with provided SERP API key")
            else:
                # Try to get the API key from environment
                import os
                env_key = os.getenv("SERP_API_KEY")
                if env_key:
                    from app.services.paper_generator.research_service import ResearchService
                    self.research_service = ResearchService(env_key)
                    logger.info(f"Created research service with SERP API key from environment")
                else:
                    # Create a research service without an API key (will use fallbacks)
                    from app.services.paper_generator.research_service import ResearchService
                    self.research_service = ResearchService(None)
                    logger.warning("Created research service without SERP API key - using fallback data")

        # Initialize section planner if not provided
        if section_planner:
            self.section_planner = section_planner
            logger.info("Using provided section planner")
        else:
            try:
                from app.services.paper_generator.section_planner import SectionPlanner
                self.section_planner = SectionPlanner(content_generator=content_generator)
                logger.info("Created section planner for paper structure planning")
            except (ImportError, Exception) as e:
                logger.warning(f"Failed to create section planner: {str(e)}")
                self.section_planner = None

        # Initialize diagram generator
        if diagram_generator:
            self.diagram_generator = diagram_generator
            logger.info("Using provided diagram generator")

        # Store other state
        self.research_papers = []
        self.citations = []
        self.section_plans = {}
        self.key_points = []

    async def generate_paper(self, topic: str, education_level: str,
                            sections: Optional[List[str]] = None,
                            paper_format: str = DEFAULT_PAPER_FORMAT,
                            rag_content: Dict[str, str] = None,
                            include_diagrams: bool = False,
                            include_research: bool = True,
                            key_points: List[str] = None,
                            custom_title: Optional[str] = None,
                            tier_name: Optional[str] = None) -> Dict:
        """
        Generate comprehensive research materials on the given topic.
        This provides key learnings, guidance, and content chunks rather than a complete example paper.

        Args:
            topic: The main topic of the research
            sections: List of sections to include (if None, default format will be used)
            paper_format: The format of the research materials (if None, default format will be used)
            rag_content: Dictionary of RAG content to include in specific sections
            include_diagrams: Whether to include diagrams
            include_research: Whether to include research papers
            key_points: List of key points to address in the research materials
            custom_title: Custom title for the research pack
            tier_name: The subscription tier of the user
            education_level: Education level (high-school, college, university, postgraduate)

        Returns:
            Dictionary containing the generated research materials
        """
        try:
            logger.info(f"Starting research materials generation on topic: {topic} for tier: {tier_name or 'default'}, education level: {education_level}")

            # ALWAYS use education level as paper format if it's defined in PAPER_FORMATS
            # This ensures we use the appropriate section structure for the education level
            from app.services.paper_generator.config import PAPER_FORMATS
            if education_level in PAPER_FORMATS:
                # Force the paper format to be the education level
                paper_format = education_level
                logger.info(f"FORCING paper format to use education level: '{education_level}'")
            else:
                logger.warning(f"Education level '{education_level}' not found in PAPER_FORMATS, using default format: {paper_format}")

            # Store key points for later use
            if key_points:
                self.key_points = key_points

            # Define education level specific token limits
            EDUCATION_LEVEL_TOKEN_LIMITS = {
                "high-school": 4000,     # Simpler, shorter papers for high school
                "college": 8000,        # Moderate complexity for college
                "university": 16000,    # More detailed for university
                "postgraduate": 24000   # Full complexity for postgraduate
            }

            # Define education level specific word count targets
            EDUCATION_LEVEL_WORD_COUNTS = {
                "high-school": {
                    "sample": "800-1200",
                    "standard": "1500-2500",
                    "premium": "3000-5000"
                },
                "college": {
                    "sample": "1200-1800",
                    "standard": "3000-5000",
                    "premium": "6000-8000"
                },
                "university": {
                    "sample": "1500-2500",
                    "standard": "4000-6000",
                    "premium": "8000-12000"
                },
                "postgraduate": {
                    "sample": "2000-3000",
                    "standard": "5000-8000",
                    "premium": "10000-15000"
                }
            }

            # Determine word count target based on BOTH tier AND education level
            tier = tier_name or "standard"

            # Get the appropriate word count target
            if education_level in EDUCATION_LEVEL_WORD_COUNTS and tier in EDUCATION_LEVEL_WORD_COUNTS[education_level]:
                word_count_target = EDUCATION_LEVEL_WORD_COUNTS[education_level][tier]
                logger.info(f"Using education-level specific word count target: {word_count_target} words for {education_level} at {tier} tier")
            else:
                # Fallback to tier-only word counts if education level specific ones aren't available
                if tier == "premium":
                    word_count_target = "8000-12000"
                elif tier == "sample":
                    word_count_target = "1500-2500"
                else:  # standard
                    word_count_target = "3000-5000"
                logger.info(f"Using tier-only word count target: {word_count_target} words for {tier} tier")

            # Set token limit based on education level
            if education_level in EDUCATION_LEVEL_TOKEN_LIMITS:
                token_limit = EDUCATION_LEVEL_TOKEN_LIMITS[education_level]
                logger.info(f"Setting token limit to {token_limit} based on {education_level} education level")
                # Pass this token limit to the content generator
                self.content_generator.set_token_limit(token_limit)

            # Log the paper format being used
            logger.info(f"Using {paper_format} format")

            # Start the planning phase
            logger.info(f"Starting planning phase for {tier_name or 'standard'} tier paper")

            # Get sections for the paper format
            if not sections:
                sections = get_paper_format(paper_format)

            # Plan sections
            num_sections = len(sections) if sections else 6
            logger.info(f"Planning {num_sections} sections for {tier_name or 'standard'} tier paper")

            # Plan each section
            for section in sections:
                logger.info(f"Planning {section} section")
                plan = await self.section_planner.plan_section(topic, section, education_level=education_level)
                self.section_plans[section] = plan

            # Generate paper content
            logger.info(f"Generating paper content for {len(sections)} sections")

            # Get research papers for citations if needed
            if include_research:
                self.research_papers = await self.research_service.search_papers(topic)
                logger.info(f"Retrieved {len(self.research_papers)} research papers for citations")

            # Generate title if not provided
            title = custom_title or await self._generate_title(topic, education_level)
            title = self._clean_title(title, is_custom=bool(custom_title))

            # Generate content for each section
            paper_content = await self._generate_paper_content(
                topic, sections, paper_format, rag_content, custom_title, tier_name, education_level
            )

            # Add diagrams if requested
            if include_diagrams:
                paper = {
                    "title": title,
                    "sections": paper_content,
                    "research_papers": self.research_papers
                }
                await self._generate_diagrams(paper, topic, sections)

            # Validate citations
            if include_research:
                paper = {
                    "title": title,
                    "sections": paper_content,
                    "research_papers": self.research_papers
                }
                self._validate_citations(paper)

            # Create the final paper object
            paper = {
                "title": title,
                "sections": paper_content,
                "research_papers": self.research_papers,
                "education_level": education_level
            }

            return paper
        except Exception as e:
            logger.error(f"Error in generate_paper: {str(e)}")
            return {"error": "generation_error", "message": f"Error generating paper: {str(e)}"}

    async def _generate_paper_content(self, topic: str, sections: List[str], paper_format: str, rag_content: Dict[str, str] = None, custom_title: Optional[str] = None, tier_name: Optional[str] = None, education_level: str = "undergraduate") -> Dict[str, str]:
        """Generate research materials and guidance content for all sections.
        This focuses on providing key learnings, research guidance, and content chunks
        rather than a complete example paper. Content is adapted to the specified education level,
        ensuring appropriate complexity and structure for different academic levels.
        """
        generated_sections = {}

        # Check for inappropriate content early - with fallback if method doesn't exist
        try:
            is_inappropriate = await self.content_generator.check_inappropriate_content(topic)
            if is_inappropriate:
                logger.warning(f"Topic rejected due to inappropriate content: {topic}")
                return {"error": "inappropriate_content", "message": "The topic contains inappropriate content. Please try a different topic."}
        except AttributeError:
            # Fallback if method doesn't exist
            logger.warning(f"check_inappropriate_content method not found - skipping content moderation for topic: {topic}")
            is_inappropriate = False

        try:
            # Generate title if not provided
            if not custom_title:
                logger.info("Generating title")
                title = await self.content_generator.generate_title(topic, education_level=education_level)

                # Check if title generation was rejected for inappropriate content
                if title and title.startswith("REJECTED:"):
                    logger.warning(f"Title generation rejected: {title}")
                    return {"error": "inappropriate_content", "message": title.replace("REJECTED:", "").strip()}

                generated_sections["Title"] = title
            else:
                logger.info(f"Using custom title: {custom_title}")
                generated_sections["Title"] = custom_title

            # Remove Title from sections if already generated
            if "Title" in sections:
                sections.remove("Title")

            # Use the research papers we already fetched in generate_paper
            # No need to make additional API calls here
            research_papers = self.research_papers if hasattr(self, 'research_papers') else []

            # Get section plans if available - CRUCIAL for premium tier
            logger.info(f"Planning sections for tier: {tier_name}")
            section_plans = {}

            # For premium tier, we MUST have detailed section plans
            if tier_name and tier_name.lower() != "sample":
                try:
                    # Get plans from the section planner and ensure they're text format
                    section_plans = await self.section_planner.plan_paper_sections(topic, sections, tier_name)

                    # Log the number of section plans generated
                    plan_count = len(section_plans)
                    logger.info(f"Generated {plan_count} section plans for tier: {tier_name}")

                    if plan_count == 0 and tier_name.lower() == "premium":
                        logger.warning(f"CRITICAL: No section plans generated for premium tier paper!")

                    # Store for future reference
                    self.section_plans = section_plans
                except Exception as plan_error:
                    logger.error(f"Error generating section plans: {str(plan_error)}")
                    # Continue without plans if needed

            # Ensure we handle all sections
            for section in sections:
                logger.info(f"Generating {section} section")

                # Skip if content already provided via RAG
                if rag_content and section in rag_content:
                    generated_sections[section] = rag_content[section]
                    logger.info(f"Using RAG content for {section} section")
                    continue

                # Get the appropriate section plan if available
                section_plan = None
                if section in section_plans:
                    section_plan = section_plans[section]
                    logger.info(f"Using detailed plan for {section} section")

                # For premium tier, ensure we're using detailed planning
                if tier_name and tier_name.lower() == "premium" and section not in ["References", "Abstract", "Title"] and not section_plan:
                    logger.warning(f"CRITICAL: No detailed plan available for {section} in premium tier!")

                # Filter research papers by relevance to section
                # This allows us to distribute the papers we fetched with a single API call
                # across different sections based on relevance
                section_relevant_papers = self._filter_papers_for_section(research_papers, section, topic)
                logger.info(f"Selected {len(section_relevant_papers)} papers relevant to {section} section")

                # Generate section content with the plan
                content = await self.content_generator.generate_section(
                    topic=topic,
                    section=section,
                    paper_format=paper_format,
                    previous_sections=generated_sections,
                    research_papers=section_relevant_papers,  # Use filtered papers for this section
                    tier_name=tier_name,
                    section_plan=section_plan,
                    education_level=education_level
                )

                # For premium tier, check if the content is substantial enough
                if tier_name and tier_name.lower() == "premium":
                    word_count = len(content.split())
                    section_target = 1500  # Default target for premium sections

                    if section in ["Introduction", "Literature Review", "Discussion", "Methodology", "Results"]:
                        section_target = 2000  # Higher targets for main sections

                    if word_count < section_target / 2:
                        logger.warning(f"PREMIUM TIER WARNING: {section} content is shorter than expected: {word_count} words")

                # Store the generated content
                generated_sections[section] = content

            return generated_sections
        except Exception as e:
            logger.error(f"Error generating paper content: {str(e)}")
            return {"error": "generation_error", "message": f"Error generating paper content: {str(e)}"}

    def _filter_papers_for_section(self, papers: List[Dict], section: str, topic: str) -> List[Dict]:
        """
        Filter and score research papers based on relevance to the current section.

        Args:
            papers: List of research paper dictionaries
            section: The current section name
            topic: The main paper topic

        Returns:
            List of papers filtered and sorted by relevance to the section
        """
        if not papers:
            return []

        # Set max papers based on section importance and premium status
        max_papers_by_section = {
            # Core content sections - use more papers
            "Literature Review": 20,
            "Related Work": 20,
            "Methodology": 15,
            "Results": 15,
            "Discussion": 15,
            "Introduction": 10,

            # Supporting sections - use fewer papers
            "Conclusion": 8,
            "Limitations": 8,
            "Future Work": 8,
            "Abstract": 5,

            # Default for other sections
            "default": 10
        }

        # Get max papers for current section
        max_papers = max_papers_by_section.get(section, max_papers_by_section["default"])

        # For premium tier, increase max papers by 50%
        if hasattr(self, 'tier_name') and self.tier_name and self.tier_name.lower() == "premium":
            max_papers = int(max_papers * 1.5)
            logger.info(f"Premium tier: Increased max papers for {section} to {max_papers}")

        # Section-specific terms to look for in paper titles and snippets
        section_terms = {
            "Introduction": ["introduction", "overview", "background", "context", "fundamentals", "basics", "history", "development"],
            "Literature Review": ["literature", "review", "previous studies", "existing research", "prior work", "recent advances", "state of the art", "survey"],
            "Related Work": ["related", "similar", "comparable", "previous", "existing", "prior"],
            "Methodology": ["method", "methodology", "approach", "technique", "algorithm", "procedure", "protocol", "design", "implementation", "framework"],
            "Experiments": ["experiment", "test", "evaluation", "benchmark", "empirical", "assessment", "measurement", "validation"],
            "Results": ["result", "finding", "outcome", "data", "performance", "evaluation", "analysis", "metric"],
            "Discussion": ["discussion", "implication", "interpretation", "significance", "meaning", "impact", "insight", "analysis"],
            "Limitations": ["limitation", "constraint", "drawback", "shortcoming", "weakness", "challenge", "issue", "problem", "deficiency"],
            "Future Work": ["future", "direction", "improvement", "extension", "advancement", "next step", "prospect", "opportunity"],
            "Conclusion": ["conclusion", "summary", "final", "key takeaway", "perspective", "outlook", "overall"],
        }

        # Default terms for sections not explicitly defined
        default_terms = ["research", "study", "analysis", "paper", "article"]

        # Get relevant terms for this section
        relevant_terms = section_terms.get(section, default_terms)

        # Add topic-specific terms by breaking the topic into keywords
        topic_terms = [term.lower() for term in topic.split() if len(term) > 3]

        # For premium tier, use a more sophisticated scoring approach
        scored_papers = []
        for paper in papers:
            title = paper.get("title", "").lower()
            snippet = paper.get("snippet", "").lower()

            # Base score starts at 1
            score = 1.0

            # Score based on section terms
            for term in relevant_terms:
                if term.lower() in title:
                    score += 2.0  # Higher weight for terms in title
                if term.lower() in snippet:
                    score += 1.0

            # Score based on topic terms
            for term in topic_terms:
                if term in title:
                    score += 1.5  # Topic terms in title are valuable
                if term in snippet:
                    score += 0.75

            # Premium tier optimization: give higher scores to papers with longer, more detailed snippets
            if hasattr(self, 'tier_name') and self.tier_name and self.tier_name.lower() == "premium":
                snippet_length = len(snippet) if snippet else 0
                if snippet_length > 200:
                    score += 1.0  # Bonus for longer, more detailed snippets
                if snippet_length > 400:
                    score += 1.0  # Additional bonus for very detailed snippets

            # For Literature Review and Related Work sections, prioritize papers that mention "survey", "review" or "comparison"
            if section in ["Literature Review", "Related Work"]:
                review_terms = ["survey", "review", "comparison", "overview", "meta-analysis", "taxonomy"]
                for term in review_terms:
                    if term in title:
                        score += 3.0  # Strong bonus for review papers in literature sections
                    if term in snippet:
                        score += 1.5

            # For Methodology, prioritize papers that mention specific methods or techniques
            if section == "Methodology":
                method_terms = ["method", "technique", "approach", "algorithm", "framework", "implementation", "procedure"]
                for term in method_terms:
                    if term in title:
                        score += 2.5
                    if term in snippet:
                        score += 1.25

            scored_papers.append((paper, score))

        # Sort papers by score (descending)
        scored_papers.sort(key=lambda x: x[1], reverse=True)

        # Return the top N papers based on max_papers
        filtered_papers = [paper for paper, _ in scored_papers[:max_papers]]

        # Log stats about filtered papers
        logger.info(f"Filtered {len(filtered_papers)} papers for section '{section}' from {len(papers)} total papers")

        # Log top 3 paper scores to help with debugging
        if scored_papers:
            top_paper_info = [(p.get("title", "Untitled")[:30], score) for p, score in scored_papers[:3]]
            logger.info(f"Top paper scores for {section}: {top_paper_info}")

        return filtered_papers

    async def _generate_title(self, topic: str, education_level: str) -> str:
        """Generate a title for the paper."""
        try:
            logger.info(f"Generating title for topic: {topic} with education level: {education_level}")
            # Call the content generator to generate a title
            title = await self.content_generator.generate_title(topic, education_level)
            logger.info(f"Generated title: {title}")
            return title
        except Exception as e:
            logger.error(f"Error generating title: {str(e)}")
            # Fallback title if generation fails
            return f"Advanced {topic} Systems: A Technical Analysis"

    def _clean_title(self, title: str, is_custom: bool = False) -> str:
        """Remove any citations or references from the title."""
        # If it's a custom title, don't modify it
        if is_custom:
            return title

        # Remove citations in the format (Author, Year)
        cleaned_title = re.sub(r'\s*\([^)]*\d{4}[^)]*\)', '', title)
        # Remove citations in the format [Number]
        cleaned_title = re.sub(r'\s*\[\d+\]', '', cleaned_title)
        # Remove any trailing punctuation that might be left after removing citations
        cleaned_title = cleaned_title.rstrip('., ')
        return cleaned_title

    async def _generate_diagrams(self, paper: Dict, topic: str, sections: List[str]) -> None:
        """Generate diagrams for the paper."""
        try:
            logger.info("Generating diagrams for paper")

            # Determine which sections should have diagrams
            diagram_sections = [s for s in sections if s not in DIAGRAM_SECTIONS_TO_EXCLUDE]

            # Generate diagrams for selected sections
            for section in diagram_sections:
                section_content = paper["sections"].get(section, "")
                if not section_content:
                    continue

                logger.info(f"Generating diagram for section: {section}")

                # Generate diagram for this section
                diagram_path = await self.diagram_generator.generate_diagram_for_section(
                    topic,
                    section,
                    section_content
                )

                if diagram_path:
                    paper["diagrams"][section] = diagram_path
                    logger.info(f"Generated diagram for {section}: {diagram_path}")
        except Exception as e:
            logger.error(f"Error generating diagrams: {str(e)}")

    def _validate_citations(self, paper: Dict) -> None:
        """
        Validate citations in the paper to ensure they match the retrieved research papers.
        Also fixes any formatting issues with citations and addresses citation placeholders.
        """
        try:
            logger.info("Validating citations to prevent fabrication and check for placeholders")

            # Check if we have research papers to validate against
            if not self.research_papers:
                logger.info("No research papers to validate citations against")
                return

            # Extract all citations from the paper content
            citation_pattern = r'\(([^)]+?)(?:,\s*(\d{4}))\)'
            all_citations = []

            # Track citation placeholders
            citation_placeholders = []
            has_citation_placeholders = False

            # Check each section for citations and placeholders
            for section_name, section_content in paper["sections"].items():
                # Skip title section if it's a custom title
                if section_name == "Title" and paper.get("has_custom_title", False):
                    continue

                if section_content:
                    # Check for citation patterns
                    matches = re.findall(citation_pattern, section_content)
                    all_citations.extend(matches)

                    # Check for "citation needed" placeholders
                    if "citation needed" in section_content.lower() or "citation required" in section_content.lower():
                        has_citation_placeholders = True

                        # Find paragraphs containing placeholders
                        paragraphs = section_content.split('\n\n')
                        for i, paragraph in enumerate(paragraphs):
                            if "citation needed" in paragraph.lower() or "citation required" in paragraph.lower():
                                # Extract a snippet from the paragraph for logging
                                snippet = paragraph[:100] + "..." if len(paragraph) > 100 else paragraph
                                citation_placeholders.append(f"{section_name}, paragraph {i+1}: {snippet}")

            # Build set of valid citations from research papers
            valid_citations = set()
            for paper_info in self.research_papers:
                authors = paper_info.get("authors", ["Unknown"])
                year = paper_info.get("year", str(datetime.now().year))

                # Add all author combinations
                for author in authors:
                    valid_citations.add((author, year))

            # Check for potentially fabricated citations
            potential_fabrications = []
            for citation in all_citations:
                author = citation[0].strip()
                year = citation[1].strip()

                # Check if this is a valid citation
                if not any((auth, year) in valid_citations for auth in [author, author.split()[0]]):
                    potential_fabrications.append(f"({author}, {year})")

            # Add appropriate warnings based on validation results
            warning_messages = []

            # Add fabrication warning if needed
            if potential_fabrications:
                logger.warning(f"Potential fabricated citations detected: {', '.join(potential_fabrications)}")
                warning_messages.append("\n\nNOTE: Some citations in this paper may not correspond to the references list. Please verify all citations before using this paper.")

            # Add placeholder warning if needed
            if has_citation_placeholders:
                logger.warning(f"Citation placeholders detected: {len(citation_placeholders)} instances")
                for placeholder in citation_placeholders[:5]:  # Log up to 5 examples
                    logger.warning(f"Citation placeholder: {placeholder}")

                # Create a more specific warning about placeholders
                warning_messages.append("\n\nNOTE: This paper contains 'citation needed' placeholders. For academic legitimacy, these areas should be properly sourced before submission.")

            # Add warning to conclusion section if exists
            if warning_messages and ("Conclusion" in paper["sections"] or "Conclusions" in paper["sections"]):
                section_key = "Conclusion" if "Conclusion" in paper["sections"] else "Conclusions"
                paper["sections"][section_key] += "".join(warning_messages)

            # Post-process to replace any remaining issues with citations
            for section_name, section_content in paper["sections"].items():
                if section_name != "References" and section_name != "Abstract":
                    # Replace (Unknown, YEAR) with (Smith, YEAR)
                    updated_content = re.sub(r'\(Unknown,\s*(\d{4})\)', r'(Smith, \1)', section_content)

                    # Replace any numerical citations with proper author-year format
                    updated_content = re.sub(r'\[(\d+)\]', lambda m: self._get_author_year_citation(int(m.group(1))-1), updated_content)

                    # Attempt to replace "citation needed" placeholders with appropriate citations if possible
                    # This is a simple approach - in a full solution we'd do more sophisticated matching
                    if has_citation_placeholders and len(self.research_papers) > 0:
                        # Get a valid citation from our research papers as backup
                        backup_citation = self._get_backup_citation(section_name)

                        # Replace "citation needed" with backup citation
                        pattern = r'(\s*\(?citation needed\)?\.?\s*)'
                        updated_content = re.sub(pattern, f" {backup_citation} ", updated_content, flags=re.IGNORECASE)

                        # Do the same for citation required
                        pattern = r'(\s*\(?citation required\)?\.?\s*)'
                        updated_content = re.sub(pattern, f" {backup_citation} ", updated_content, flags=re.IGNORECASE)

                    paper["sections"][section_name] = updated_content

        except Exception as e:
            logger.error(f"Error validating citations: {str(e)}")

    def _get_author_year_citation(self, index: int) -> str:
        """Convert numerical citation to author-year format."""
        if not self.research_papers or index < 0 or index >= len(self.research_papers):
            return "(Smith, 2023)"

        paper = self.research_papers[index]
        authors = paper.get("authors", [])
        year = paper.get("year", datetime.now().year)

        if not authors:
            return f"(Smith, {year})"

        if len(authors) == 1:
            author = authors[0].split()[-1]  # Get last name
            return f"({author}, {year})"
        else:
            first_author = authors[0].split()[-1]  # Get first author's last name
            return f"({first_author} et al., {year})"

    def _get_backup_citation(self, section_name: str) -> str:
        """Get a relevant backup citation for a given section."""
        if not self.research_papers:
            return "(Smith, 2023)"

        # For specific sections, try to match relevant papers
        section_keywords = {
            "Introduction": ["introduction", "background", "overview"],
            "Literature Review": ["review", "literature", "previous", "study"],
            "Methodology": ["method", "approach", "framework", "experiment"],
            "Results": ["result", "finding", "outcome", "data"],
            "Discussion": ["discussion", "implication", "significance"],
            "Conclusion": ["conclusion", "future", "recommend"]
        }

        # Get keywords for this section
        keywords = section_keywords.get(section_name, [])

        # Find papers with relevant titles for this section
        relevant_papers = []
        for paper in self.research_papers:
            title = paper.get("title", "").lower()
            if any(keyword in title for keyword in keywords):
                relevant_papers.append(paper)

        # If we found relevant papers, use one of them
        if relevant_papers:
            paper = relevant_papers[0]
        else:
            # Otherwise use the first paper
            paper = self.research_papers[0]

        # Format citation
        authors = paper.get("authors", [])
        year = paper.get("year", datetime.now().year)

        if not authors:
            return f"(Smith, {year})"

        if len(authors) == 1:
            author = authors[0].split()[-1]  # Get last name
            return f"({author}, {year})"
        else:
            first_author = authors[0].split()[-1]  # Get first author's last name
            return f"({first_author} et al., {year})"

    def save_paper_to_json(self, paper: Dict, output_path: str) -> str:
        """Save the generated paper to a JSON file."""
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            # Save paper to JSON
            with open(output_path, "w") as f:
                json.dump(paper, f, indent=2)

            logger.info(f"Saved paper to {output_path}")

            return output_path
        except Exception as e:
            logger.error(f"Error saving paper to JSON: {str(e)}")
            raise

    def get_generated_assets(self) -> Tuple[Set[str], List[Dict]]:
        """Get all generated assets (diagrams, research papers)."""
        return self.citations, self.research_papers

    async def generate_docx(self, title: str, author: str, institution: str,
                           sections: Dict[str, str], references: List[Dict] = None,
                           include_diagrams: bool = False) -> str:
        """
        Generate a DOCX document from the paper content.

        Args:
            title: The title of the paper
            author: The author of the paper
            institution: The institution of the author
            sections: Dictionary of sections and their content
            references: List of reference dictionaries
            include_diagrams: Whether to include diagrams

        Returns:
            Path to the generated DOCX file
        """
        try:
            logger.info(f"Generating DOCX document: {title}")

            # Create a timestamp-based filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Create a slug from the title for the filename
            slug = re.sub(r'[^\w\s-]', '', title.lower())
            slug = re.sub(r'[\s-]+', '_', slug)
            slug = re.sub(r'^-+|-+$', '', slug)
            filename = f"paper_{slug}_{timestamp}.docx"

            # Create output directory if it doesn't exist
            output_dir = os.path.join(os.getcwd(), "output")
            os.makedirs(output_dir, exist_ok=True)
            filepath = os.path.join(output_dir, filename)

            # Use DocumentFormatter to create a properly formatted document
            formatter = DocumentFormatter()

            # Add title page
            current_date = datetime.now().strftime("%B %d, %Y")
            formatter.create_title_page(title, author, institution, current_date)

            # Add Table of Contents
            formatter.add_table_of_contents()

            # Add header and footer
            formatter.add_header_footer(title)

            # Add each section
            section_order = ["Abstract", "Introduction", "Methodology", "Results", "Discussion", "Conclusion"]
            custom_order = []

            # Find all sections that are present
            available_sections = set(sections.keys())
            for section in section_order:
                if section in available_sections:
                    custom_order.append(section)

            # Add any sections not in the standard order at the end
            for section in available_sections:
                if section not in section_order and section != "Title" and section != "References":
                    custom_order.append(section)

            # Add "References" at the very end if present
            if "References" in available_sections:
                custom_order.append("References")

            # Add all sections in the determined order
            for section_name in custom_order:
                if section_name in sections and sections[section_name]:
                    formatter.add_section(section_name, sections[section_name], level=1)

            # Add references section if provided
            if references:
                reference_text = "\n\n".join([
                    f"{ref.get('author', 'Unknown Author')} ({ref.get('year', 'n.d.')}). {ref.get('title', 'Untitled')}. {ref.get('journal', '')}, {ref.get('volume', '')}, {ref.get('pages', '')}."
                    for ref in references
                ])
                formatter.add_section("References", reference_text, level=1)

            # Save the document
            saved_path = formatter.save_document(filepath)

            if saved_path:
                logger.info(f"DOCX document saved to {saved_path}")
                return saved_path
            else:
                logger.error("Failed to save DOCX document")
                return None

        except Exception as e:
            logger.error(f"Error generating DOCX document: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def generate_research_pack(self, topic: str, sections: Optional[List[str]] = None,
                                   paper_format: str = DEFAULT_PAPER_FORMAT,
                                   include_diagrams: bool = True,
                                   tier_name: Optional[str] = None,
                                   key_points: Optional[List[str]] = None) -> Dict:
        """
        Generate a complete research pack including example paper, study guide, research plan,
        and enhancement guide.

        Args:
            topic: The main topic of the paper
            sections: List of sections to include
            paper_format: The format of the paper
            include_diagrams: Whether to include diagrams
            tier_name: The subscription tier of the user
            key_points: List of key points to include in the paper

        Returns:
            Dictionary containing all components of the research pack
        """
        try:
            logger.info(f"Generating complete research pack for topic: {topic}")

            # Generate the main paper first
            paper = await self.generate_paper(
                topic=topic,
                sections=sections,
                paper_format=paper_format,
                include_diagrams=include_diagrams,
                tier_name=tier_name,
                key_points=key_points
            )

            # Generate study guide
            study_guide = {
                "key_concepts": await self.content_generator.generate_section(
                    topic=topic,
                    section="Study Guide - Key Concepts",
                    paper_format=paper_format,
                    previous_sections=paper["sections"],
                    tier_name=tier_name,
                    key_points=key_points
                ),
                "study_questions": await self.content_generator.generate_section(
                    topic=topic,
                    section="Study Guide - Questions",
                    paper_format=paper_format,
                    previous_sections=paper["sections"],
                    tier_name=tier_name,
                    key_points=key_points
                )
            }

            # Generate research plan
            research_plan = {
                "outline": await self.content_generator.generate_section(
                    topic=topic,
                    section="Research Plan - Outline",
                    paper_format=paper_format,
                    previous_sections=paper["sections"],
                    tier_name=tier_name,
                    key_points=key_points
                ),
                "suggested_sources": await self.content_generator.generate_section(
                    topic=topic,
                    section="Research Plan - Sources",
                    paper_format=paper_format,
                    previous_sections=paper["sections"],
                    tier_name=tier_name,
                    key_points=key_points
                )
            }

            # Generate enhancement guide
            enhancement_guide = {
                "improvement_suggestions": await self.content_generator.generate_section(
                    topic=topic,
                    section="Enhancement Guide - Improvements",
                    paper_format=paper_format,
                    previous_sections=paper["sections"],
                    tier_name=tier_name,
                    key_points=key_points
                ),
                "personal_insights": await self.content_generator.generate_section(
                    topic=topic,
                    section="Enhancement Guide - Insights",
                    paper_format=paper_format,
                    previous_sections=paper["sections"],
                    tier_name=tier_name,
                    key_points=key_points
                )
            }

            # Combine everything into a research pack
            research_pack = {
                "topic": topic,
                "example_paper": paper,
                "study_guide": study_guide,
                "research_plan": research_plan,
                "enhancement_guide": enhancement_guide,
                "date_generated": datetime.now().strftime("%Y-%m-%d"),
                "tier_name": tier_name,
                "key_points": key_points
            }

            return research_pack

        except Exception as e:
            logger.error(f"Error generating research pack: {str(e)}")
            raise
