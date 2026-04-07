"""Application Configuration"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # App settings
    APP_NAME: str = "AML Knowledge Copilot"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # OpenAI settings
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION_NAME: str = "aml_knowledge"
    QDRANT_VECTOR_SIZE: int = 1536
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    
    # Document processing settings
    MAX_CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    MAX_FILE_SIZE_MB: int = 50
    
    # RAG settings
    TOP_K_RESULTS: int = 5
    MIN_SIMILARITY_SCORE: float = 0.7
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


settings = Settings()