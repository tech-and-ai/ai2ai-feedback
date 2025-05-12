"""
Service for handling paper-related operations.
"""
import logging
from app.database.database import get_db_connection

# Configure logging
logger = logging.getLogger(__name__)

class PaperService:
    """Service for handling paper-related operations."""

    def __init__(self):
        """Initialize the paper service."""
        self.db = get_db_connection()

    def get_user_papers(self, user_id):
        """
        Get all papers for a user.

        Args:
            user_id: The ID of the user

        Returns:
            List of paper objects
        """
        try:
            # Query the database for papers
            result = self.db.table("papers").select("*").eq("user_id", user_id).execute()

            # Return the papers
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting user papers: {str(e)}")
            return []

    def get_paper(self, paper_id):
        """
        Get a paper by ID.

        Args:
            paper_id: The ID of the paper

        Returns:
            Paper object or None if not found
        """
        try:
            # Query the database for the paper
            result = self.db.table("papers").select("*").eq("id", paper_id).execute()

            # Return the paper
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting paper: {str(e)}")
            return None

    def create_paper(self, user_id, title, topic, prompt):
        """
        Create a new paper.

        Args:
            user_id: The ID of the user
            title: The title of the paper
            topic: The topic of the paper
            prompt: The prompt for the paper

        Returns:
            The created paper object or None if creation failed
        """
        try:
            # Create the paper in the database
            paper_data = {
                "user_id": user_id,
                "title": title,
                "topic": topic,
                "prompt": prompt,
                "status": "pending",
                "word_count": 0
            }

            result = self.db.table("papers").insert(paper_data).execute()

            # Return the created paper
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error creating paper: {str(e)}")
            return None

    def update_paper_status(self, paper_id, status, content=None, word_count=None, error_message=None, storage_urls=None):
        """
        Update the status of a paper.

        Args:
            paper_id: The ID of the paper
            status: The new status of the paper
            content: The content of the paper (optional)
            word_count: The word count of the paper (optional)
            error_message: Error message if status is 'failed' (optional)
            storage_urls: URLs to the stored paper files (optional)

        Returns:
            True if the update was successful, False otherwise
        """
        try:
            # Use the Supabase Edge Function to update the paper status
            # This will also trigger the notification
            payload = {
                "paper_id": paper_id,
                "status": status
            }

            # Add optional fields if provided
            if content is not None:
                payload["content"] = content
            if word_count is not None:
                payload["word_count"] = word_count
            if error_message is not None:
                payload["error_message"] = error_message
            if storage_urls is not None:
                payload["storage_urls"] = storage_urls

            # Call the Edge Function
            result = self.db.functions.invoke(
                "update-paper-status",
                invoke_options={"body": payload}
            )

            # Check if the function call was successful
            if result and result.get("success") is True:
                logger.info(f"Paper {paper_id} status updated to {status} via Edge Function")
                return True
            else:
                error_details = result.get("error", "Unknown error")
                logger.error(f"Error updating paper status via Edge Function: {error_details}")

                # Fallback to direct database update if Edge Function fails
                logger.info(f"Falling back to direct database update for paper {paper_id}")
                update_data = {"status": status}
                if content is not None:
                    update_data["content"] = content
                if word_count is not None:
                    update_data["word_count"] = word_count
                if error_message is not None:
                    update_data["error_message"] = error_message
                if storage_urls is not None:
                    update_data["storage_urls"] = storage_urls

                # Update the paper in the database
                db_result = self.db.table("papers").update(update_data).eq("id", paper_id).execute()
                return True if db_result.data else False
        except Exception as e:
            logger.error(f"Error updating paper status: {str(e)}")

            # Fallback to direct database update if an exception occurs
            try:
                logger.info(f"Falling back to direct database update for paper {paper_id} after exception")
                update_data = {"status": status}
                if content is not None:
                    update_data["content"] = content
                if word_count is not None:
                    update_data["word_count"] = word_count
                if error_message is not None:
                    update_data["error_message"] = error_message
                if storage_urls is not None:
                    update_data["storage_urls"] = storage_urls

                # Update the paper in the database
                db_result = self.db.table("papers").update(update_data).eq("id", paper_id).execute()
                return True if db_result.data else False
            except Exception as inner_e:
                logger.error(f"Error in fallback update: {str(inner_e)}")
                return False

    def delete_paper(self, paper_id):
        """
        Delete a paper.

        Args:
            paper_id: The ID of the paper

        Returns:
            True if the deletion was successful, False otherwise
        """
        try:
            # Delete the paper from the database
            result = self.db.table("papers").delete().eq("id", paper_id).execute()

            # Return success status
            return True if result.data else False
        except Exception as e:
            logger.error(f"Error deleting paper: {str(e)}")
            return False
