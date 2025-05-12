"""
Test script for the document formatter.

This script creates a sample research pack and formats it into a document.
"""
import os
import sys
import logging
from datetime import datetime
from document_formatter import DocumentFormatter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_sample_research_pack():
    """Create a sample research pack for testing."""
    return {
        "title": "Artificial Intelligence Ethics",
        "author": "Test User",
        "date_generated": datetime.now().strftime("%B %d, %Y"),
        "sections": {
            "introduction": {
                "about_this_pack": "This research pack provides an overview of ethical considerations in artificial intelligence development.",
                "how_to_use": "Use this pack as a guide for your research on AI ethics.",
                "whats_included": "This pack includes an analysis of key ethical issues, methodological approaches, and resources for further research."
            },
            "topic_analysis": {
                "key_concepts": "Artificial Intelligence (AI) ethics encompasses a range of considerations including fairness, accountability, transparency, and privacy.\n\n[[LILY_CALLOUT type=\"tip\" title=\"Research Tip\"]]When exploring AI ethics, consider both theoretical frameworks and practical applications.[[/LILY_CALLOUT]]\n\nThese concepts are essential for developing responsible AI systems.",
                "current_debates": "Current debates in AI ethics include algorithmic bias, privacy concerns, and the impact of automation on employment."
            },
            "methodology": {
                "research_methods": "Research methods in AI ethics include case studies, surveys, and experimental approaches.",
                "data_collection": "Data collection methods include interviews with experts, literature reviews, and analysis of existing AI systems."
            },
            "questions": {
                "How can we ensure AI systems are fair?": "Ensuring fairness in AI systems requires careful consideration of training data, algorithm design, and ongoing monitoring.\n\n[[LILY_CALLOUT type=\"insight\" title=\"Key Insight\"]]Fairness is context-dependent and may require different approaches in different domains.[[/LILY_CALLOUT]]",
                "What are the privacy implications of AI?": "AI systems often collect and process large amounts of personal data, raising significant privacy concerns."
            },
            "experts": {
                "key_researchers": "Key researchers in AI ethics include Stuart Russell, Timnit Gebru, and Kate Crawford.",
                "organizations": "Organizations working on AI ethics include the AI Now Institute, the Future of Life Institute, and the Partnership on AI."
            },
            "citations": "This section includes citations and references to key resources on AI ethics.",
            "appendices": "This section includes additional resources and templates for AI ethics research."
        },
        "diagrams": []
    }

def main():
    """Main function to test the document formatter."""
    logger.info("Creating sample research pack")
    research_pack = create_sample_research_pack()
    
    logger.info("Creating document formatter")
    formatter = DocumentFormatter()
    
    logger.info("Formatting research pack")
    document = formatter.format_research_pack(research_pack)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save the document
    output_path = os.path.join(output_dir, "test_research_pack.docx")
    logger.info(f"Saving document to {output_path}")
    formatter.save_document(output_path)
    
    logger.info("Document formatting complete")

if __name__ == "__main__":
    main()
