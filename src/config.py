from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra='ignore'  # This will ignore extra environment variables
    )
    
    # Database
    database_url: str = "postgresql://postgres:devpassword@localhost:5432/work_management_dev"
    
    # Add these environment variables to your settings class
    openai_api_key: str = os.getenv("OPENAI_API_KEY")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY")
    
    # Application
    environment: str = "development"
    log_level: str = "DEBUG"
    max_note_length: int = 10000
    
    # Embedding settings
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    allowed_hosts: List[str] = ["*"]
    cors_origins: List[str] = ["*"]
    
    # Settings for Claude:
    claude_model: str = "claude-4-sonnet-20250514"
    claude_max_tokens: int = 5000
    claude_temperature: float = 0.1
    
    @property
    def claude_config(self):
        return {
            "model": self.claude_model,
            "max_tokens": self.claude_max_tokens,
            "temperature": self.claude_temperature
        }

settings = Settings()