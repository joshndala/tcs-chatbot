"""
Centralized configuration management for the TCS Multi-Agent Chatbot.
"""
import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Google AI Configuration
    google_api_key: str
    
    # Hardcoded defaults (not configurable via .env)
    model_name: str = "gemini-3-flash-preview"
    embedding_model: str = "models/gemini-embedding-001"
    sqlite_db_path: str = "data/customers.db"
    chroma_persist_dir: str = "data/embeddings"
    pdf_upload_dir: str = "data/pdfs"
    chunk_size: int = 1800
    chunk_overlap: int = 200

    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent
    
    @property
    def db_path(self) -> Path:
        """Get the absolute path to the SQLite database."""
        return self.project_root / self.sqlite_db_path
    
    @property
    def chroma_path(self) -> Path:
        """Get the absolute path to the ChromaDB persistence directory."""
        return self.project_root / self.chroma_persist_dir
    
    @property
    def pdf_dir(self) -> Path:
        """Get the absolute path to the PDF upload directory."""
        return self.project_root / self.pdf_upload_dir
    
    def ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.db_path.parent,
            self.chroma_path,
            self.pdf_dir,
            self.project_root / "logs"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()

# Ensure all required directories exist
settings.ensure_directories()
