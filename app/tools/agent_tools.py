"""
Agent tools for the AI2AI feedback system.
This module contains implementations of various tools that agents can use.
"""

import os
import json
import uuid
import aiohttp
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

class FalImageGenerationTool:
    """Tool for generating images using Fal.ai's API."""
    
    def __init__(self):
        self.api_key = os.getenv("FAL_API_KEY")
        self.default_model = os.getenv("FAL_DEFAULT_MODEL", "fal-ai/flux/dev")
        self.default_width = int(os.getenv("FAL_IMAGE_WIDTH", 512))
        self.default_height = int(os.getenv("FAL_IMAGE_HEIGHT", 512))
    
    async def generate_image(self, prompt: str, negative_prompt: str = "", 
                            width: Optional[int] = None, 
                            height: Optional[int] = None,
                            model: Optional[str] = None) -> Dict[str, Any]:
        """Generate an image using Fal.ai's API."""
        try:
            width = width or self.default_width
            height = height or self.default_height
            model = model or self.default_model
            
            headers = {
                "Authorization": f"Key {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "model_name": model
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post("https://api.fal.ai/v1/image/generation", 
                                       headers=headers, json=payload) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "image_url": result.get("image", {}).get("url"),
                            "model": model
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Fal.ai API error: {error}")
                        return {
                            "success": False,
                            "error": error
                        }
        except Exception as e:
            logger.exception(f"Error generating image: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class DuckDuckGoSearchTool:
    """Tool for searching the web using DuckDuckGo."""
    
    def __init__(self):
        self.max_results = int(os.getenv("DUCKDUCKGO_MAX_RESULTS", 5))
    
    async def search(self, query: str, num_results: Optional[int] = None) -> Dict[str, Any]:
        """Search the web using DuckDuckGo."""
        try:
            from duckduckgo_search import DDGS
            
            num_results = num_results or self.max_results
            results = []
            
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=num_results):
                    results.append({
                        "title": r.get("title"),
                        "body": r.get("body"),
                        "href": r.get("href"),
                        "source": "DuckDuckGo"
                    })
            
            return {
                "success": True,
                "results": results,
                "query": query
            }
        except Exception as e:
            logger.exception(f"Error searching DuckDuckGo: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class AI2AIDiscussionTool:
    """Tool for communicating with other AI agents using the discussion API."""
    
    def __init__(self):
        self.base_url = os.getenv("AI2AI_API_URL", "http://localhost:8001")
        self.api_url = f"{self.base_url}/api/v1/discussions"
    
    async def create_session(self, title: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Create a new discussion session."""
        try:
            payload = {
                "title": title,
                "system_prompt": system_prompt
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/sessions", json=payload) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            "success": True,
                            "session_id": result.get("id"),
                            "title": result.get("title")
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Error creating discussion session: {error}")
                        return {
                            "success": False,
                            "error": error
                        }
        except Exception as e:
            logger.exception(f"Error creating discussion session: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def send_message(self, session_id: str, role: str, content: str, 
                          metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a message to a discussion session."""
        try:
            payload = {
                "role": role,
                "content": content,
                "metadata": metadata or {}
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/sessions/{session_id}/messages", 
                                      json=payload) as response:
                    if response.status == 201:
                        result = await response.json()
                        return {
                            "success": True,
                            "message_id": result.get("id")
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Error sending message: {error}")
                        return {
                            "success": False,
                            "error": error
                        }
        except Exception as e:
            logger.exception(f"Error sending message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_messages(self, session_id: str, limit: int = 50) -> Dict[str, Any]:
        """Get messages from a discussion session."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/sessions/{session_id}/messages?limit={limit}") as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            "success": True,
                            "messages": result.get("items", [])
                        }
                    else:
                        error = await response.text()
                        logger.error(f"Error getting messages: {error}")
                        return {
                            "success": False,
                            "error": error
                        }
        except Exception as e:
            logger.exception(f"Error getting messages: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class EmailTool:
    """Tool for sending emails."""
    
    def __init__(self):
        self.smtp_server = os.getenv("EMAIL_SMTP_SERVER")
        self.smtp_port = int(os.getenv("EMAIL_SMTP_PORT", 587))
        self.username = os.getenv("EMAIL_USERNAME")
        self.password = os.getenv("EMAIL_PASSWORD")
        self.from_email = os.getenv("EMAIL_FROM")
        self.use_tls = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    
    async def send_email(self, to_email: str, subject: str, body: str, 
                        is_html: bool = False) -> Dict[str, Any]:
        """Send an email."""
        try:
            msg = MIMEMultipart()
            msg["From"] = self.from_email
            msg["To"] = to_email
            msg["Subject"] = subject
            
            if is_html:
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            return {
                "success": True,
                "to": to_email,
                "subject": subject
            }
        except Exception as e:
            logger.exception(f"Error sending email: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
