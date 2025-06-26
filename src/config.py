from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:devpassword@localhost:5432/work_management_dev"
    
    # API Keys
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
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
    
    class Config:
        env_file = ".env.dev"
        case_sensitive = False

settings = Settings()