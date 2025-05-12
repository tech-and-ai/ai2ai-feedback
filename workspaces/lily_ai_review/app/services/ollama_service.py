"""
Ollama Service for Lily AI

This module provides a service for interacting with Ollama models.
"""
import json
import logging
import requests
from typing import Dict, List, Any, Optional, Union

# Configure logging
logger = logging.getLogger(__name__)

class OllamaService:
    """
    Service for interacting with Ollama models.
    """
    def __init__(self, base_url: str = "http://localhost:11434"):
        """
        Initialize the Ollama service.

        Args:
            base_url: Base URL for the Ollama API
        """
        self.base_url = base_url
        logger.info(f"Ollama service initialized with base URL: {base_url}")

    def generate(self,
                 model: str,
                 prompt: str,
                 system: Optional[str] = None,
                 temperature: float = 0.7,
                 max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Generate text using an Ollama model.

        Args:
            model: Name of the model to use
            prompt: Prompt to send to the model
            system: System message to send to the model
            temperature: Temperature for generation
            max_tokens: Maximum number of tokens to generate

        Returns:
            Response from the model
        """
        try:
            url = f"{self.base_url}/api/generate"

            payload = {
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False  # Important: Request non-streaming response
            }

            if system:
                payload["system"] = system

            logger.debug(f"Sending request to Ollama: {payload}")

            # Detailed request logging
            shortened_prompt = prompt[:100] + "..." if len(prompt) > 100 else prompt
            logger.info(f"Sending prompt to Ollama model {model}, prompt starts with: {shortened_prompt}")

            response = requests.post(url, json=payload, timeout=60)  # Add timeout
            response.raise_for_status()

            # Log the raw response for debugging
            logger.debug(f"Received raw response from Ollama: {response.text[:500]}...")

            # Handle response
            result = None
            try:
                result = response.json()
                logger.debug(f"Parsed JSON response successfully")
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Problematic JSON: {response.text[:200]}...")
                
                # Return a simplified response with the raw text
                return {
                    "response": f"Error parsing JSON response. Raw text: {response.text[:500]}...",
                    "error": f"JSON parse error: {str(e)}"
                }
            
            # Check if we got any result
            if not result:
                logger.error(f"Failed to parse any JSON from Ollama response")
                return {"response": response.text, "error": "Failed to parse JSON response"}
            
            # Log a summary of the response
            if "response" in result:
                response_preview = result["response"][:100] + "..." if len(result["response"]) > 100 else result["response"]
                logger.info(f"Received response from Ollama: {response_preview}")
            else:
                logger.warning(f"No 'response' field in Ollama result: {list(result.keys())}")
            
            return result

        except requests.exceptions.RequestException as e:
            logger.error(f"Request error with Ollama: {str(e)}")
            return {"error": f"Request error: {str(e)}", "response": "Error connecting to Ollama API"}
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e), "response": "Error occurred during generation"}

    def chat(self,
             model: str,
             messages: List[Dict[str, str]],
             temperature: float = 0.7,
             max_tokens: int = 2000) -> Dict[str, Any]:
        """
        Chat with an Ollama model.

        Args:
            model: Name of the model to use
            messages: List of messages to send to the model
            temperature: Temperature for generation
            max_tokens: Maximum number of tokens to generate

        Returns:
            Response from the model
        """
        try:
            url = f"{self.base_url}/api/chat"

            payload = {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }

            logger.debug(f"Sending chat request to Ollama: {payload}")

            response = requests.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            logger.debug(f"Received chat response from Ollama: {result}")

            return result

        except Exception as e:
            logger.error(f"Error chatting with Ollama: {str(e)}")
            return {"error": str(e)}

    def list_models(self) -> List[Dict[str, Any]]:
        """
        List available Ollama models.

        Returns:
            List of available models
        """
        try:
            url = f"{self.base_url}/api/tags"

            response = requests.get(url)
            response.raise_for_status()

            result = response.json()
            models = result.get("models", [])

            logger.info(f"Listed {len(models)} Ollama models")
            return models

        except Exception as e:
            logger.error(f"Error listing Ollama models: {str(e)}")
            return []

    def get_embeddings(self, model: str, text: str) -> List[float]:
        """
        Get embeddings for text using an Ollama model.

        Args:
            model: Name of the model to use
            text: Text to get embeddings for

        Returns:
            List of embedding values
        """
        try:
            url = f"{self.base_url}/api/embeddings"

            payload = {
                "model": model,
                "prompt": text
            }

            response = requests.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            embeddings = result.get("embedding", [])

            logger.debug(f"Got embeddings for text (length: {len(embeddings)})")
            return embeddings

        except Exception as e:
            logger.error(f"Error getting embeddings from Ollama: {str(e)}")
            return []

    def analyze_code(self,
                     model: str,
                     code: str,
                     language: Optional[str] = None,
                     task: str = "document") -> Dict[str, Any]:
        """
        Analyze code using an Ollama model.

        Args:
            model: Name of the model to use
            code: Code to analyze
            language: Programming language of the code
            task: Task to perform (document, explain, optimize, etc.)

        Returns:
            Analysis results
        """
        try:
            # Create a prompt for code analysis with detailed instructions
            prompt = f"""Task: Provide detailed documentation for the following {language} code.

```{language}
{code}
```

Generate comprehensive documentation that includes:

1. PURPOSE OVERVIEW:
   - What is the main purpose of this code?
   - What problem does it solve?
   - How does it fit into the larger system?

2. COMPONENTS:
   - List all classes, functions, methods
   - For each component:
     - Name and type
     - Purpose
     - Parameters with types
     - Return values with types
     - Important behavior details
   
3. DEPENDENCIES:
   - External libraries/modules used
   - Internal dependencies
   - Important relationships between components
   
4. USAGE EXAMPLES:
   - Show practical examples of how to use the main functions/classes
   - Include input/output examples
   
5. EDGE CASES & CONSIDERATIONS:
   - Security implications
   - Performance considerations
   - Error handling approach
   - Potential improvements

Format your response as a well-structured markdown document with clear headings and code examples.
"""

            # Generate response
            logger.info(f"Sending code analysis request to Ollama for {language} code of length {len(code)}")
            result = self.generate(model, prompt, temperature=0.1, max_tokens=4000)

            # Log the raw response for debugging
            logger.info(f"Raw Ollama response keys: {list(result.keys() if result else [])}")
            
            # Extract the response text
            response_text = result.get("response", "")
            
            # Log a sample of the response text
            response_sample = response_text[:100] + "..." if len(response_text) > 100 else response_text
            logger.info(f"Received response from Ollama (sample): {response_sample}")

            if not response_text:
                logger.error(f"Empty response from Ollama: {result}")
                return {"error": "Empty response from Ollama", "result": "No analysis available."}

            # Parse the response into a structured format
            analysis = {
                "task": task,
                "language": language,
                "result": response_text
            }

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing code with Ollama: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e), "result": "Error occurred during analysis."}

    def generate_documentation(self,
                              model: str,
                              files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate documentation for multiple files.

        Args:
            model: Name of the model to use
            files: List of file information dictionaries

        Returns:
            Generated documentation
        """
        try:
            # Create a system prompt for documentation generation
            system = "You are a code documentation expert. Your task is to analyze code files and generate comprehensive documentation."

            # Create a prompt with information about all files
            prompt = "# Code Documentation Task\n\n"
            prompt += f"I need to document {len(files)} files. Here's a summary of the files:\n\n"

            for i, file in enumerate(files):
                prompt += f"{i+1}. {file['filename']} - {file.get('language', 'Unknown language')}\n"

            prompt += "\nPlease generate documentation for these files, including:\n"
            prompt += "1. Overall structure and purpose of the codebase\n"
            prompt += "2. Key components and their functions\n"
            prompt += "3. Relationships between components\n"
            prompt += "4. Usage examples\n\n"

            # Add the content of each file
            for i, file in enumerate(files):
                prompt += f"## File {i+1}: {file['filename']}\n\n"
                prompt += f"```{file.get('language', '')}\n{file['content']}\n```\n\n"

            # Generate response
            result = self.generate(model, prompt, system=system, temperature=0.2, max_tokens=4000)

            # Extract the response text
            response_text = result.get("response", "")

            # Return the documentation
            return {
                "documentation": response_text,
                "files": [file['filename'] for file in files]
            }

        except Exception as e:
            logger.error(f"Error generating documentation with Ollama: {str(e)}")
            return {"error": str(e)}
