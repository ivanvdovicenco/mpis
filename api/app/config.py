"""
MPIS Genesis API Configuration

This module handles all configuration through environment variables
with sensible defaults for development and production.
"""
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    APP_NAME: str = "MPIS Genesis API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DRY_RUN: bool = False  # Mock LLM for testing
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://mpis:mpis@mpis-postgres:5432/mpis"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Qdrant
    QDRANT_URL: str = "http://mpis-qdrant:6333"
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_SOURCES: str = "persona_sources_embeddings"
    QDRANT_COLLECTION_CORE: str = "persona_core_embeddings"
    EMBEDDING_DIMENSION: int = 1536  # OpenAI text-embedding-3-small
    
    # LLM Configuration
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openai"  # or "anthropic"
    LLM_MODEL: str = "gpt-4-turbo-preview"
    LLM_MAX_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0.7
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Paths
    YOUTUBE_LINKS_DIR: str = "/opt/mpis/input"
    YOUTUBE_LINKS_FILENAME: str = "youtube_links.txt"
    PERSONAS_BASE_DIR: str = "/opt/mpis/personas"
    SOURCES_BASE_DIR: str = "/opt/mpis/sources"
    SECRETS_DIR: str = "/opt/mpis/secrets"
    
    # Google Drive
    GDRIVE_SERVICE_ACCOUNT_JSON_PATH: str = "/opt/mpis/secrets/gdrive_sa.json"
    
    # Public Persona Web Enrichment
    PUBLIC_WEB_MAX_SOURCES: int = 20
    PUBLIC_WEB_ALLOWED_DOMAINS: Optional[str] = None  # comma-separated
    PUBLIC_WEB_DENIED_DOMAINS: Optional[str] = None  # comma-separated
    SERPAPI_API_KEY: Optional[str] = None
    WEB_REQUEST_TIMEOUT: int = 30
    WEB_REQUEST_DELAY: float = 1.0  # Rate limiting delay between requests
    
    # Chunking
    CHUNK_MIN_TOKENS: int = 500
    CHUNK_MAX_TOKENS: int = 1200
    CHUNK_OVERLAP_TOKENS: int = 100
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8080
    
    # Web content summary length limit
    WEB_SUMMARY_MAX_CHARS: int = 500
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def youtube_links_path(self) -> str:
        """Full path to youtube_links.txt"""
        import os
        return os.path.join(self.YOUTUBE_LINKS_DIR, self.YOUTUBE_LINKS_FILENAME)
    
    @property
    def allowed_domains_list(self) -> List[str]:
        """Parse allowed domains into list"""
        if not self.PUBLIC_WEB_ALLOWED_DOMAINS:
            return []
        return [d.strip() for d in self.PUBLIC_WEB_ALLOWED_DOMAINS.split(",") if d.strip()]
    
    @property
    def denied_domains_list(self) -> List[str]:
        """Parse denied domains into list"""
        if not self.PUBLIC_WEB_DENIED_DOMAINS:
            return []
        return [d.strip() for d in self.PUBLIC_WEB_DENIED_DOMAINS.split(",") if d.strip()]


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
