"""
Configuration settings for the application.
"""
import os
from pydantic import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    """
    Application settings.
    """
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Autonomous Agent System"

    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Database settings
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///ai2ai_feedback.db")

    # Security settings
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "supersecretkey")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 8)))

    # Agent settings
    AGENT_WORKSPACE_ROOT: str = os.environ.get("AGENT_WORKSPACE_ROOT", "/home/admin/projects/ai2ai-feedback/agent_workspaces")

    # Tool settings
    ALLOWED_COMMANDS: List[str] = [
        "ls", "cat", "grep", "python", "pip", "git", "mkdir",
        "rm", "cp", "mv", "find", "curl", "wget"
    ]

    # Search settings
    DUCKDUCKGO_API_URL: str = "https://api.duckduckgo.com"

    # Email settings
    SMTP_SERVER: Optional[str] = os.environ.get("SMTP_SERVER")
    SMTP_PORT: int = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.environ.get("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = os.environ.get("SMTP_PASSWORD")

    # GitHub settings
    GITHUB_API_URL: str = "https://api.github.com"

    # OpenRouter settings
    OPENROUTER_API_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY: Optional[str] = os.environ.get("OPENROUTER_API_KEY")

    # Ollama settings
    OLLAMA_API_URL: str = os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api")

    class Config:
        case_sensitive = True
        env_file = ".env"


# Create settings instance
settings = Settings()
