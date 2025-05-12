import requests
import json
from typing import Dict, Any, Optional, List, Tuple

class AIDebugClient:
    """
    Client for AI Debugging Assistant API that other LLMs can use to interact with the API.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize the client with the API base URL.
        
        Args:
            base_url: The base URL of the AI Debugging Assistant API
        """
        self.base_url = base_url.rstrip("/")
    
    def ask(self, 
            question: str, 
            conversation_id: Optional[str] = None,
            model: str = "google/gemini-2.5-flash-preview",
            system_message: Optional[str] = None) -> Tuple[str, str]:
        """
        Ask a question to the AI debugging assistant.
        
        Args:
            question: The question to ask
            conversation_id: Optional ID of an existing conversation to continue
            model: The AI model to use
            system_message: Optional system message to set for a new conversation
            
        Returns:
            Tuple of (answer, conversation_id)
        """
        url = f"{self.base_url}/api/ask"
        
        payload = {
            "question": question,
            "model": model
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
            
        if system_message:
            payload["system_message"] = system_message
        
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            return result["answer"], result["conversation_id"]
        except requests.exceptions.RequestException as e:
            error_msg = f"Error calling AI Debugging Assistant API: {str(e)}"
            if hasattr(e, 'response') and e.response:
                error_msg += f"\nResponse: {e.response.text}"
            return error_msg, conversation_id or ""
    
    def list_conversations(self) -> List[Dict[str, Any]]:
        """
        List all conversations.
        
        Returns:
            List of conversation summaries
        """
        url = f"{self.base_url}/api/conversations"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error listing conversations: {str(e)}")
            return []
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get details of a specific conversation.
        
        Args:
            conversation_id: ID of the conversation to retrieve
            
        Returns:
            Conversation details including messages
        """
        url = f"{self.base_url}/api/conversations/{conversation_id}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting conversation: {str(e)}")
            return {}
    
    def export_conversation(self, conversation_id: str, format: str = "markdown") -> Tuple[str, str]:
        """
        Export a conversation in the specified format.
        
        Args:
            conversation_id: ID of the conversation to export
            format: Export format ("markdown", "json", or "html")
            
        Returns:
            Tuple of (content, filename)
        """
        url = f"{self.base_url}/api/conversations/{conversation_id}/export"
        
        try:
            response = requests.post(url, json={"format": format})
            response.raise_for_status()
            result = response.json()
            return result["content"], result["filename"]
        except requests.exceptions.RequestException as e:
            print(f"Error exporting conversation: {str(e)}")
            return "", ""
    
    def get_token_usage(self) -> Dict[str, Any]:
        """
        Get token usage statistics.
        
        Returns:
            Token usage statistics
        """
        url = f"{self.base_url}/api/token-usage"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting token usage: {str(e)}")
            return {}


# Example usage
if __name__ == "__main__":
    client = AIDebugClient()
    
    # Ask a question about Stripe
    system_message = "You are a Stripe API expert. Provide detailed, technical answers about Stripe API integration, webhooks, payment processing, subscriptions, and error handling. Include code examples in relevant programming languages when appropriate."
    
    answer, conversation_id = client.ask(
        question="How do I implement webhook handling for Stripe events in Node.js to ensure idempotency?",
        system_message=system_message,
        model="google/gemini-2.5-flash-preview"
    )
    
    print(f"Answer: {answer}")
    print(f"Conversation ID: {conversation_id}")
    
    # Ask a follow-up question
    follow_up_answer, _ = client.ask(
        question="Can you provide a complete code example with error handling?",
        conversation_id=conversation_id
    )
    
    print(f"\nFollow-up answer: {follow_up_answer}")
    
    # Export the conversation
    content, filename = client.export_conversation(conversation_id, format="markdown")
    
    print(f"\nExported to {filename}")
    print(f"Content preview: {content[:200]}...")
