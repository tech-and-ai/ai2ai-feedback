"""
Feedback parser utility for AI-to-AI Feedback API
"""

from typing import Dict, Optional, Tuple

def extract_structured_feedback(feedback: str) -> Dict[str, str]:
    """
    Extract structured feedback from the consultation model's response

    Args:
        feedback: Feedback text from the consultation model

    Returns:
        Dict[str, str]: Structured feedback components
    """
    sections = {
        'FEEDBACK_SUMMARY': '',
        'REASONING_ASSESSMENT': '',
        'KNOWLEDGE_GAPS': '',
        'SUGGESTED_APPROACH': '',
        'ADDITIONAL_CONSIDERATIONS': ''
    }

    try:
        current_section = None
        lines = feedback.split('\n')

        for line in lines:
            # Check if this line starts a new section
            for section in sections.keys():
                if section in line:
                    current_section = section
                    break

            # Add content to current section if we're in one
            if current_section and line and current_section not in line:
                sections[current_section] += line + '\n'

        # Trim whitespace
        for section in sections:
            sections[section] = sections[section].strip()

        return sections
    except Exception as e:
        print(f"Error extracting structured feedback: {e}")
        return sections

class StreamingFeedbackParser:
    """Parser for streaming feedback that progressively builds structured feedback"""

    def __init__(self):
        """Initialize the streaming feedback parser"""
        self.sections = {
            'FEEDBACK_SUMMARY': '',
            'REASONING_ASSESSMENT': '',
            'KNOWLEDGE_GAPS': '',
            'SUGGESTED_APPROACH': '',
            'ADDITIONAL_CONSIDERATIONS': ''
        }
        self.current_section = None
        self.buffer = ""
        self.complete_feedback = ""

    def process_chunk(self, chunk: str) -> Tuple[Dict[str, str], Optional[str], Optional[str]]:
        """
        Process a chunk of streaming feedback

        Args:
            chunk: Text chunk from the streaming response

        Returns:
            Tuple containing:
            - Dict[str, str]: Current state of structured feedback
            - Optional[str]: Section that was updated (if any)
            - Optional[str]: Content that was added to the section (if any)
        """
        self.complete_feedback += chunk
        self.buffer += chunk

        # Check if we have complete lines in the buffer
        lines = self.buffer.split('\n')

        # Keep the last (potentially incomplete) line in the buffer
        if not self.buffer.endswith('\n') and len(lines) > 0:
            self.buffer = lines[-1]
            lines = lines[:-1]
        else:
            self.buffer = ""

        updated_section = None
        added_content = None

        # Process complete lines
        for line in lines:
            # Check if this line starts a new section
            for section in self.sections.keys():
                if section in line:
                    self.current_section = section
                    updated_section = section
                    added_content = ""
                    break

            # Add content to current section if we're in one
            if self.current_section and line and self.current_section not in line:
                self.sections[self.current_section] += line + '\n'
                if updated_section == self.current_section:
                    added_content = (added_content or "") + line + '\n'
                else:
                    updated_section = self.current_section
                    added_content = line + '\n'

        # Return the current state of structured feedback and what was updated
        return self.sections.copy(), updated_section, added_content

    def get_result(self) -> Dict[str, str]:
        """
        Get the final structured feedback result

        Returns:
            Dict[str, str]: Structured feedback components
        """
        # Process any remaining content in the buffer
        if self.buffer:
            self.process_chunk("\n")

        # Trim whitespace in all sections
        for section in self.sections:
            self.sections[section] = self.sections[section].strip()

        return self.sections.copy()
