"""
Diagram Orchestrator
Provides a unified interface for generating beautiful diagrams
"""

import logging
import asyncio
import os
import json
from .mind_map_generator import MindMapGenerator
from .journey_map_generator import JourneyMapGenerator
from .question_breakdown_generator import QuestionBreakdownGenerator
from .argument_mapping_generator import ArgumentMappingGenerator
from .comparative_analysis_generator import ComparativeAnalysisGenerator
from .content_generator import ContentGenerator

# Set up logging
logger = logging.getLogger(__name__)

# Initialize generators
_content_generator = None
_mind_map_generator = None
_journey_map_generator = None
_question_breakdown_generator = None
_argument_mapping_generator = None
_comparative_analysis_generator = None

# Create directory for job-specific diagrams
JOB_DIAGRAMS_DIR = "/home/admin/projects/kdd/app/static/job_diagrams"
os.makedirs(JOB_DIAGRAMS_DIR, exist_ok=True)

def _get_content_generator():
    """Get or create the content generator"""
    global _content_generator
    if _content_generator is None:
        logger.info("ORCHESTRATOR DEBUG: Creating new ContentGenerator instance")
        _content_generator = ContentGenerator()
        logger.info(f"ORCHESTRATOR DEBUG: ContentGenerator created, has OpenRouter key: {bool(_content_generator.openrouter_key)}")
    return _content_generator

def _get_mind_map_generator():
    """Get or create the mind map generator"""
    global _mind_map_generator
    if _mind_map_generator is None:
        logger.info("ORCHESTRATOR DEBUG: Creating new MindMapGenerator instance")
        _mind_map_generator = MindMapGenerator(content_generator=_get_content_generator())
    return _mind_map_generator

def _get_journey_map_generator():
    """Get or create the journey map generator"""
    global _journey_map_generator
    if _journey_map_generator is None:
        logger.info("ORCHESTRATOR DEBUG: Creating new JourneyMapGenerator instance")
        _journey_map_generator = JourneyMapGenerator(content_generator=_get_content_generator())
    return _journey_map_generator

def _get_question_breakdown_generator():
    """Get or create the question breakdown generator"""
    global _question_breakdown_generator
    if _question_breakdown_generator is None:
        logger.info("ORCHESTRATOR DEBUG: Creating new QuestionBreakdownGenerator instance")
        _question_breakdown_generator = QuestionBreakdownGenerator(content_generator=_get_content_generator())
    return _question_breakdown_generator

def _get_argument_mapping_generator():
    """Get or create the argument mapping generator"""
    global _argument_mapping_generator
    if _argument_mapping_generator is None:
        logger.info("ORCHESTRATOR DEBUG: Creating new ArgumentMappingGenerator instance")
        _argument_mapping_generator = ArgumentMappingGenerator(content_generator=_get_content_generator())
    return _argument_mapping_generator

def _get_comparative_analysis_generator():
    """Get or create the comparative analysis generator"""
    global _comparative_analysis_generator
    if _comparative_analysis_generator is None:
        logger.info("ORCHESTRATOR DEBUG: Creating new ComparativeAnalysisGenerator instance")
        _comparative_analysis_generator = ComparativeAnalysisGenerator(content_generator=_get_content_generator())
    return _comparative_analysis_generator

def _ensure_job_dir(job_id):
    """Ensure the job directory exists"""
    if not job_id:
        logger.warning("No job ID provided for diagram generation")
        return None

    job_dir = os.path.join(JOB_DIAGRAMS_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    logger.info(f"Ensured job directory exists: {job_dir}")
    return job_dir

def generate_mind_map(topic, job_id=None):
    """
    Generate a mind map for a topic

    Args:
        topic (str): The topic to generate a mind map for
        job_id (str): Optional job ID to associate the diagram with

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_mind_map called for topic: '{topic}', job_id: '{job_id}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for mind map: {output_dir}")

    try:
        generator = _get_mind_map_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using mind map generator: {generator.__class__.__name__}")

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the mind map
            result = generator.generate_mind_map(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            result = generator.generate_mind_map(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Mind map generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating mind map: {str(e)}", exc_info=True)
        return None

def generate_mind_map_with_content(topic, job_id=None, content_file=None):
    """
    Generate a mind map for a topic using pre-generated content

    Args:
        topic (str): The topic to generate a mind map for
        job_id (str): Optional job ID to associate the diagram with
        content_file (str): Path to a JSON file containing pre-generated content

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_mind_map_with_content called for topic: '{topic}', job_id: '{job_id}', content_file: '{content_file}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for mind map: {output_dir}")

    try:
        generator = _get_mind_map_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using mind map generator: {generator.__class__.__name__}")

        # Load pre-generated content if available
        mind_map_data = None
        if content_file and os.path.exists(content_file):
            try:
                with open(content_file, 'r') as f:
                    mind_map_data = json.load(f)
                logger.info(f"ORCHESTRATOR DEBUG: Loaded pre-generated mind map content from {content_file}")
            except Exception as e:
                logger.error(f"Error loading mind map content from {content_file}: {str(e)}")
                mind_map_data = None

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the mind map with pre-generated content if available
            if mind_map_data:
                # Prepare data for the template
                template_data = {
                    "TITLE": topic,
                    "json_data": mind_map_data
                }
                result = generator.generate_diagram("jsmind_mind_map", template_data, prefix="mind_map")
            else:
                # Fall back to regular generation
                result = generator.generate_mind_map(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            if mind_map_data:
                # Prepare data for the template
                template_data = {
                    "TITLE": topic,
                    "json_data": mind_map_data
                }
                result = generator.generate_diagram("jsmind_mind_map", template_data, prefix="mind_map")
            else:
                result = generator.generate_mind_map(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Mind map generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating mind map with content: {str(e)}", exc_info=True)
        return None

def generate_research_journey_map(topic, job_id=None):
    """
    Generate a research journey map for a topic

    Args:
        topic (str): The topic to generate a journey map for
        job_id (str): Optional job ID to associate the diagram with

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_research_journey_map called for topic: '{topic}', job_id: '{job_id}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for journey map: {output_dir}")

    try:
        generator = _get_journey_map_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using journey map generator: {generator.__class__.__name__}")

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the journey map
            result = generator.generate_journey_map(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            result = generator.generate_journey_map(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Journey map generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating journey map: {str(e)}", exc_info=True)
        return None

def generate_research_journey_map_with_content(topic, job_id=None, content_file=None):
    """
    Generate a research journey map for a topic using pre-generated content

    Args:
        topic (str): The topic to generate a journey map for
        job_id (str): Optional job ID to associate the diagram with
        content_file (str): Path to a JSON file containing pre-generated content

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_research_journey_map_with_content called for topic: '{topic}', job_id: '{job_id}', content_file: '{content_file}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for journey map: {output_dir}")

    try:
        generator = _get_journey_map_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using journey map generator: {generator.__class__.__name__}")

        # Load pre-generated content if available
        journey_map_data = None
        if content_file and os.path.exists(content_file):
            try:
                with open(content_file, 'r') as f:
                    journey_map_data = json.load(f)
                logger.info(f"ORCHESTRATOR DEBUG: Loaded pre-generated journey map content from {content_file}")
            except Exception as e:
                logger.error(f"Error loading journey map content from {content_file}: {str(e)}")
                journey_map_data = None

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the journey map with pre-generated content if available
            if journey_map_data:
                # Prepare data for the template
                template_data = {
                    "title": f"Research Journey Map: {topic}",
                    "description": journey_map_data.get("description", f"This journey map shows how different stakeholders experience the research process for '{topic}'"),
                    "json_data": journey_map_data
                }
                result = generator.generate_diagram("journey_map", template_data, prefix="journey_map")
            else:
                # Fall back to regular generation
                result = generator.generate_journey_map(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            if journey_map_data:
                # Prepare data for the template
                template_data = {
                    "title": f"Research Journey Map: {topic}",
                    "description": journey_map_data.get("description", f"This journey map shows how different stakeholders experience the research process for '{topic}'"),
                    "json_data": journey_map_data
                }
                result = generator.generate_diagram("journey_map", template_data, prefix="journey_map")
            else:
                result = generator.generate_journey_map(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Journey map generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating journey map with content: {str(e)}", exc_info=True)
        return None

def generate_research_process_diagram(topic, job_id=None):
    """
    Generate a research process diagram for a topic

    Args:
        topic (str): The research topic
        job_id (str): Optional job ID to associate the diagram with

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_research_process_diagram called for topic: '{topic}', job_id: '{job_id}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for process diagram: {output_dir}")

    try:
        # Use the question breakdown generator instead of the old process diagram
        generator = _get_question_breakdown_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using question breakdown generator: {generator.__class__.__name__}")

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the question breakdown
            result = generator.generate_question_breakdown(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            result = generator.generate_question_breakdown(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Question breakdown generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating research process diagram: {str(e)}", exc_info=True)
        return None

def generate_research_process_diagram_with_content(topic, job_id=None, content_file=None):
    """
    Generate a research process diagram for a topic using pre-generated content

    Args:
        topic (str): The research topic
        job_id (str): Optional job ID to associate the diagram with
        content_file (str): Path to a JSON file containing pre-generated content

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_research_process_diagram_with_content called for topic: '{topic}', job_id: '{job_id}', content_file: '{content_file}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for process diagram: {output_dir}")

    try:
        # Use the question breakdown generator instead of the old process diagram
        generator = _get_question_breakdown_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using question breakdown generator: {generator.__class__.__name__}")

        # Load pre-generated content if available
        process_diagram_data = None
        if content_file and os.path.exists(content_file):
            try:
                with open(content_file, 'r') as f:
                    process_diagram_data = json.load(f)
                logger.info(f"ORCHESTRATOR DEBUG: Loaded pre-generated process diagram content from {content_file}")
            except Exception as e:
                logger.error(f"Error loading process diagram content from {content_file}: {str(e)}")
                process_diagram_data = None

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the process diagram with pre-generated content if available
            if process_diagram_data:
                # Prepare data for the template
                template_data = {
                    "title": process_diagram_data.get("title", f"Research Process for {topic}"),
                    "steps": process_diagram_data.get("steps", []),
                    "connections": process_diagram_data.get("connections", [])
                }
                result = generator.generate_diagram("research_process", template_data, prefix="process_diagram")
            else:
                # Fall back to regular generation
                result = generator.generate_question_breakdown(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            if process_diagram_data:
                # Prepare data for the template
                template_data = {
                    "title": process_diagram_data.get("title", f"Research Process for {topic}"),
                    "steps": process_diagram_data.get("steps", []),
                    "connections": process_diagram_data.get("connections", [])
                }
                result = generator.generate_diagram("research_process", template_data, prefix="process_diagram")
            else:
                result = generator.generate_question_breakdown(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Process diagram generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating research process diagram with content: {str(e)}", exc_info=True)
        return None

def generate_argument_map(topic, job_id=None):
    """
    Generate an argument map for a topic

    Args:
        topic (str): The topic to generate an argument map for
        job_id (str): Optional job ID to associate the diagram with

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_argument_map called for topic: '{topic}', job_id: '{job_id}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for argument map: {output_dir}")

    try:
        generator = _get_argument_mapping_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using argument mapping generator: {generator.__class__.__name__}")

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the argument map
            result = generator.generate_argument_map(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            result = generator.generate_argument_map(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Argument map generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating argument map: {str(e)}", exc_info=True)
        return None

def generate_argument_map_with_content(topic, job_id=None, content_file=None):
    """
    Generate an argument map for a topic using pre-generated content

    Args:
        topic (str): The topic to generate an argument map for
        job_id (str): Optional job ID to associate the diagram with
        content_file (str): Path to a JSON file containing pre-generated content

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_argument_map_with_content called for topic: '{topic}', job_id: '{job_id}', content_file: '{content_file}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for argument map: {output_dir}")

    try:
        generator = _get_argument_mapping_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using argument mapping generator: {generator.__class__.__name__}")

        # Load pre-generated content if available
        argument_map_data = None
        if content_file and os.path.exists(content_file):
            try:
                with open(content_file, 'r') as f:
                    argument_map_data = json.load(f)
                logger.info(f"ORCHESTRATOR DEBUG: Loaded pre-generated argument map content from {content_file}")
            except Exception as e:
                logger.error(f"Error loading argument map content from {content_file}: {str(e)}")
                argument_map_data = None

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the argument map with pre-generated content if available
            if argument_map_data:
                # Prepare data for the template
                template_data = {
                    "title": f"Argument Mapping: {topic}",
                    "description": f"This argument map shows different perspectives on {topic}, presenting supporting and opposing arguments with evidence and rebuttals.",
                    "json_data": argument_map_data
                }
                result = generator.generate_diagram("argument_mapping", template_data, prefix="argument_map")
            else:
                # Fall back to regular generation
                result = generator.generate_argument_map(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            if argument_map_data:
                # Prepare data for the template
                template_data = {
                    "title": f"Argument Mapping: {topic}",
                    "description": f"This argument map shows different perspectives on {topic}, presenting supporting and opposing arguments with evidence and rebuttals.",
                    "json_data": argument_map_data
                }
                result = generator.generate_diagram("argument_mapping", template_data, prefix="argument_map")
            else:
                result = generator.generate_argument_map(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Argument map generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating argument map with content: {str(e)}", exc_info=True)
        return None

def generate_comparative_analysis(topic, job_id=None):
    """
    Generate a comparative analysis diagram for a topic

    Args:
        topic (str): The topic to generate a comparative analysis for
        job_id (str): Optional job ID to associate the diagram with

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_comparative_analysis called for topic: '{topic}', job_id: '{job_id}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for comparative analysis: {output_dir}")

    try:
        generator = _get_comparative_analysis_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using comparative analysis generator: {generator.__class__.__name__}")

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the comparative analysis
            result = generator.generate_comparative_analysis(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            result = generator.generate_comparative_analysis(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Comparative analysis generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating comparative analysis: {str(e)}", exc_info=True)
        return None

def generate_question_breakdown(topic, job_id=None):
    """
    Generate a question breakdown diagram for a topic

    Args:
        topic (str): The topic to generate a question breakdown for
        job_id (str): Optional job ID to associate the diagram with

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    logger.info(f"ORCHESTRATOR DEBUG: generate_question_breakdown called for topic: '{topic}', job_id: '{job_id}'")

    # Create job-specific directory if job_id is provided
    output_dir = None
    if job_id:
        output_dir = _ensure_job_dir(job_id)
        logger.info(f"Using job-specific directory for question breakdown: {output_dir}")

    try:
        generator = _get_question_breakdown_generator()
        logger.info(f"ORCHESTRATOR DEBUG: Using question breakdown generator: {generator.__class__.__name__}")

        if output_dir:
            # Set the output directory for this specific job
            original_output_dir = generator.output_dir
            generator.output_dir = output_dir

            # Generate the question breakdown
            result = generator.generate_question_breakdown(topic)

            # Restore the original output directory
            generator.output_dir = original_output_dir
        else:
            # Use the default output directory
            result = generator.generate_question_breakdown(topic)

        logger.info(f"ORCHESTRATOR DEBUG: Question breakdown generation result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error generating question breakdown: {str(e)}", exc_info=True)
        return None

def generate_custom_diagram(template_name, data, prefix="leo_diagram"):
    """
    Generate a custom diagram using a template and data

    Args:
        template_name (str): Name of the template to use
        data (dict): Data to populate the template with
        prefix (str): Prefix for the output filename

    Returns:
        str: Path to the generated PNG file or None if generation fails
    """
    try:
        generator = _get_mind_map_generator()  # Use the mind map generator as a base
        return generator.generate_diagram(template_name, data, prefix)
    except Exception as e:
        logger.error(f"Error in generate_custom_diagram: {str(e)}")
        return None
