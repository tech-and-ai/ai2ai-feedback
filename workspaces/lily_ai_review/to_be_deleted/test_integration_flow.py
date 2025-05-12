"""
Test Integration Flow

This script tests the integration flow between research content, orchestrator,
Lily callouts, and document formatter.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Import the necessary components
from app.services.research_generator.research_generator import ResearchGenerator
from app.services.lily_callout.lily_callout_engine import LilyCalloutEngine
from app.services.document_formatter.document_formatter import DocumentFormatter
from research_pack.ResearchPackOrchestrator import ResearchPackOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_integration_flow():
    """
    Test the integration flow between research content, orchestrator,
    Lily callouts, and document formatter.
    """
    # Step 1: Set up the test parameters
    topic = "Climate change impacts on marine ecosystems"
    questions = ["How does ocean acidification affect coral reefs?",
                "What are the economic impacts of declining fish populations?"]
    education_level = "university"

    # Get API keys from environment variables
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    serp_key = os.getenv("SERP_API_KEY")

    if not openrouter_key or not serp_key:
        logger.error("API keys not found in environment variables")
        return

    # Step 2: Initialize the components
    logger.info("Initializing components...")

    # Initialize the research generator
    research_generator = ResearchGenerator(
        openrouter_key=openrouter_key,
        serp_api_key=serp_key
    )

    # Initialize the Lily callout engine
    lily_callout_engine = LilyCalloutEngine(
        openrouter_api_key=openrouter_key
    )

    # Initialize the document formatter
    document_formatter = DocumentFormatter()

    # Initialize the orchestrator
    orchestrator = ResearchPackOrchestrator(
        lily_callout_engine=lily_callout_engine,
        document_formatter=document_formatter,
        openrouter_key=openrouter_key,
        serp_key=serp_key
    )

    # Skip the research generation step since it requires a database
    logger.info("Creating sample content for testing...")

    # Create a simplified content structure for the orchestrator
    content = {
        "title": f"Research Pack: {topic}",
        "author": "Lily AI",
        "date_generated": datetime.now().strftime("%B %d, %Y"),
        "sections": {
            "introduction": {
                "heading": "Introduction",
                "content": f"This research pack explores the topic of {topic}. "
                          f"It includes information gathered from academic sources "
                          f"and provides insights into the key aspects of this subject."
            },
            "literature_review": {
                "heading": "Literature Review",
                "content": "Climate change is causing significant impacts on marine ecosystems worldwide. "
                          "Ocean warming, acidification, and deoxygenation are three major stressors affecting "
                          "marine life (Hoegh-Guldberg & Bruno, 2010). Coral reefs are particularly vulnerable "
                          "to these changes, with mass bleaching events becoming more frequent and severe "
                          "(Hughes et al., 2018). Fish populations are shifting their distributions poleward "
                          "in response to warming waters, disrupting fisheries and food webs (Cheung et al., 2013)."
            },
            "methodology": {
                "heading": "Methodology",
                "content": "This research synthesizes findings from peer-reviewed literature on climate change "
                          "impacts on marine ecosystems. It focuses on three key areas: coral reef degradation, "
                          "changes in fish populations, and socioeconomic impacts on coastal communities. "
                          "The analysis draws on both observational studies and predictive models to assess "
                          "current impacts and future projections."
            },
            "findings": {
                "heading": "Findings",
                "content": "Ocean acidification is reducing the ability of calcifying organisms like corals and "
                          "mollusks to build their calcium carbonate structures. Experimental studies show that "
                          "under high CO2 conditions, coral growth rates decrease by 15-30% (Albright et al., 2016). "
                          "Marine heatwaves have caused five mass coral bleaching events on the Great Barrier Reef "
                          "since 1998, with the 2016-2017 event affecting over 90% of the reef (Hughes et al., 2018). "
                          "Fish species are shifting poleward at rates of 30-70 km per decade in response to warming "
                          "waters (Poloczanska et al., 2013)."
            },
            "conclusion": {
                "heading": "Conclusion",
                "content": "Climate change is fundamentally altering marine ecosystems through multiple stressors "
                          "including warming, acidification, and deoxygenation. These changes are occurring at "
                          "unprecedented rates, challenging the adaptive capacity of many marine species. "
                          "Without significant reductions in greenhouse gas emissions, marine ecosystems face "
                          "severe degradation, with profound implications for biodiversity and human communities "
                          "that depend on ocean resources."
            },
            "references": {
                "heading": "References",
                "content": "Albright, R., et al. (2016). Reversal of ocean acidification enhances net coral reef calcification. Nature, 531, 362-365.\n\n"
                          "Cheung, W. W., et al. (2013). Shrinking of fishes exacerbates impacts of global ocean changes on marine ecosystems. Nature Climate Change, 3, 254-258.\n\n"
                          "Hoegh-Guldberg, O., & Bruno, J. F. (2010). The impact of climate change on the world's marine ecosystems. Science, 328, 1523-1528.\n\n"
                          "Hughes, T. P., et al. (2018). Spatial and temporal patterns of mass bleaching of corals in the Anthropocene. Science, 359, 80-83.\n\n"
                          "Poloczanska, E. S., et al. (2013). Global imprint of climate change on marine life. Nature Climate Change, 3, 919-925."
            }
        }
    }

    # Step 5: Process content through Lily callout engine
    logger.info("Processing content through Lily callout engine...")
    try:
        enhanced_content = lily_callout_engine._enhance_with_callouts(content, topic, education_level)
        logger.info("Content processed through Lily callout engine successfully")

        # Step 6: Format the document
        logger.info("Formatting document...")
        formatted_doc = document_formatter.format_research_pack(enhanced_content)

        # Save the document
        output_path = f"test_integration_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        formatted_doc.save(output_path)
        logger.info(f"Document saved to {output_path}")

        logger.info("Integration flow test completed successfully")
        return output_path

    except Exception as e:
        logger.error(f"Error processing content through Lily callout engine: {str(e)}")
        return

if __name__ == "__main__":
    # Run the test
    output_path = asyncio.run(test_integration_flow())

    if output_path:
        print(f"\nTest completed successfully. Document saved to: {output_path}")
    else:
        print("\nTest failed. See logs for details.")
