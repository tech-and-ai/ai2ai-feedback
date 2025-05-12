"""
Database Context Provider for Lily AI

This module provides a service for retrieving context from the database.
"""
import json
import logging
from typing import Dict, List, Any, Optional
from supabase import create_client, Client

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseContextProvider:
    """
    Service for retrieving context from the database.
    """
    def __init__(self, supabase_url: str, supabase_key: str):
        """
        Initialize the database context provider.

        Args:
            supabase_url: URL for the Supabase API
            supabase_key: API key for Supabase
        """
        self.supabase = create_client(supabase_url, supabase_key)
        logger.info("Database context provider initialized")

    def get_context_entries(self,
                           entry_type: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get context entries from the database.

        Args:
            entry_type: Type of entries to retrieve (optional)
            limit: Maximum number of entries to retrieve

        Returns:
            List of context entries
        """
        try:
            query = self.supabase.table("tool_context_entries").select("*").limit(limit)

            if entry_type:
                query = query.eq("entry_type", entry_type)

            response = query.execute()
            entries = response.data

            logger.info(f"Retrieved {len(entries)} context entries")
            return entries

        except Exception as e:
            logger.error(f"Error retrieving context entries: {str(e)}")
            return []

    def get_context_entry_by_id(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a context entry by ID.

        Args:
            entry_id: ID of the entry to retrieve

        Returns:
            Context entry or None if not found
        """
        try:
            response = self.supabase.table("tool_context_entries").select("*").eq("id", entry_id).execute()
            entries = response.data

            if entries:
                logger.info(f"Retrieved context entry with ID {entry_id}")
                return entries[0]
            else:
                logger.warning(f"Context entry with ID {entry_id} not found")
                return None

        except Exception as e:
            logger.error(f"Error retrieving context entry by ID: {str(e)}")
            return None

    def get_context_entry_by_title(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Get a context entry by title.

        Args:
            title: Title of the entry to retrieve

        Returns:
            Context entry or None if not found
        """
        try:
            response = self.supabase.table("tool_context_entries").select("*").eq("title", title).execute()
            entries = response.data

            if entries:
                logger.info(f"Retrieved context entry with title '{title}'")
                return entries[0]
            else:
                logger.warning(f"Context entry with title '{title}' not found")
                return None

        except Exception as e:
            logger.error(f"Error retrieving context entry by title: {str(e)}")
            return None

    def get_relationships(self,
                         source_id: Optional[int] = None,
                         target_id: Optional[int] = None,
                         relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relationships from the database.

        Args:
            source_id: ID of the source entry (optional)
            target_id: ID of the target entry (optional)
            relationship_type: Type of relationship (optional)

        Returns:
            List of relationships
        """
        try:
            query = self.supabase.table("tool_context_relationships").select("*")

            if source_id:
                query = query.eq("source_id", source_id)

            if target_id:
                query = query.eq("target_id", target_id)

            if relationship_type:
                query = query.eq("relationship_type", relationship_type)

            response = query.execute()
            relationships = response.data

            logger.info(f"Retrieved {len(relationships)} relationships")
            return relationships

        except Exception as e:
            logger.error(f"Error retrieving relationships: {str(e)}")
            return []

    def get_related_entries(self, entry_id: int, relationship_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get entries related to a specific entry.

        Args:
            entry_id: ID of the entry to find relationships for
            relationship_type: Type of relationship (optional)

        Returns:
            List of related entries
        """
        try:
            # Get relationships where the entry is the source
            source_query = self.supabase.table("tool_context_relationships").select("target_id, relationship_type").eq("source_id", entry_id)

            if relationship_type:
                source_query = source_query.eq("relationship_type", relationship_type)

            source_response = source_query.execute()
            source_relationships = source_response.data

            # Get relationships where the entry is the target
            target_query = self.supabase.table("tool_context_relationships").select("source_id, relationship_type").eq("target_id", entry_id)

            if relationship_type:
                target_query = target_query.eq("relationship_type", relationship_type)

            target_response = target_query.execute()
            target_relationships = target_response.data

            # Get the related entries
            related_entries = []

            for rel in source_relationships:
                entry = self.get_context_entry_by_id(rel["target_id"])
                if entry:
                    entry["relationship"] = rel["relationship_type"]
                    entry["relationship_direction"] = "outgoing"
                    related_entries.append(entry)

            for rel in target_relationships:
                entry = self.get_context_entry_by_id(rel["source_id"])
                if entry:
                    entry["relationship"] = rel["relationship_type"]
                    entry["relationship_direction"] = "incoming"
                    related_entries.append(entry)

            logger.info(f"Retrieved {len(related_entries)} related entries for entry {entry_id}")
            return related_entries

        except Exception as e:
            logger.error(f"Error retrieving related entries: {str(e)}")
            return []

    def search_context_entries(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search for context entries.

        Args:
            query: Search query
            limit: Maximum number of entries to retrieve

        Returns:
            List of matching context entries
        """
        try:
            # Search in title and content
            search_query = f"title.ilike.%{query}%,content.ilike.%{query}%"
            response = self.supabase.table("tool_context_entries").select("*").or_(search_query).limit(limit).execute()
            entries = response.data

            logger.info(f"Found {len(entries)} entries matching query '{query}'")
            return entries

        except Exception as e:
            logger.error(f"Error searching context entries: {str(e)}")
            return []

    def create_context_entry(self,
                            entry_type: str,
                            title: str,
                            content: str,
                            metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Create a new context entry.

        Args:
            entry_type: Type of the entry
            title: Title of the entry
            content: Content of the entry
            metadata: Additional metadata (optional)

        Returns:
            Created entry or None if creation failed
        """
        try:
            entry = {
                "entry_type": entry_type,
                "title": title,
                "content": content,
                "metadata": json.dumps(metadata) if metadata else None
            }

            response = self.supabase.table("tool_context_entries").insert(entry).execute()

            if response.data:
                logger.info(f"Created context entry with title '{title}'")
                return response.data[0]
            else:
                logger.warning(f"Failed to create context entry with title '{title}'")
                return None

        except Exception as e:
            logger.error(f"Error creating context entry: {str(e)}")
            return None

    def create_relationship(self,
                           source_id: int,
                           target_id: int,
                           relationship_type: str) -> Optional[Dict[str, Any]]:
        """
        Create a new relationship.

        Args:
            source_id: ID of the source entry
            target_id: ID of the target entry
            relationship_type: Type of relationship

        Returns:
            Created relationship or None if creation failed
        """
        try:
            relationship = {
                "source_id": source_id,
                "target_id": target_id,
                "relationship_type": relationship_type
            }

            response = self.supabase.table("tool_context_relationships").insert(relationship).execute()

            if response.data:
                logger.info(f"Created relationship of type '{relationship_type}' from {source_id} to {target_id}")
                return response.data[0]
            else:
                logger.warning(f"Failed to create relationship of type '{relationship_type}' from {source_id} to {target_id}")
                return None

        except Exception as e:
            logger.error(f"Error creating relationship: {str(e)}")
            return None

    def get_context_for_code(self, code: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant context entries for a code snippet.

        Args:
            code: Code snippet to find context for
            limit: Maximum number of entries to retrieve

        Returns:
            List of relevant context entries
        """
        try:
            # Extract keywords from the code (simplified implementation)
            keywords = self._extract_keywords_from_code(code)

            # Search for entries matching the keywords
            entries = []
            for keyword in keywords:
                keyword_entries = self.search_context_entries(keyword, limit=3)
                entries.extend(keyword_entries)

            # Remove duplicates and limit the number of entries
            unique_entries = []
            entry_ids = set()

            for entry in entries:
                if entry["id"] not in entry_ids:
                    entry_ids.add(entry["id"])
                    unique_entries.append(entry)

                    if len(unique_entries) >= limit:
                        break

            logger.info(f"Found {len(unique_entries)} relevant context entries for code snippet")
            return unique_entries

        except Exception as e:
            logger.error(f"Error getting context for code: {str(e)}")
            return []

    def _extract_keywords_from_code(self, code: str) -> List[str]:
        """
        Extract keywords from a code snippet.

        Args:
            code: Code snippet to extract keywords from

        Returns:
            List of keywords
        """
        # Simplified implementation - in a real system, this would be more sophisticated
        keywords = []

        # Split the code into lines
        lines = code.split("\n")

        for line in lines:
            # Skip empty lines and comments
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("//"):
                continue

            # Extract class names
            if "class " in line:
                class_name = line.split("class ")[1].split("(")[0].split(":")[0].strip()
                if class_name:
                    keywords.append(class_name)

            # Extract function names
            if "def " in line:
                function_name = line.split("def ")[1].split("(")[0].strip()
                if function_name:
                    keywords.append(function_name)

            # Extract import statements
            if "import " in line:
                if "from " in line:
                    module = line.split("from ")[1].split("import")[0].strip()
                    if module:
                        keywords.append(module)
                else:
                    module = line.split("import ")[1].strip()
                    if module:
                        keywords.append(module)

        return keywords
