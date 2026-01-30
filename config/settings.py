"""
Centralized configuration management for the TCS Multi-Agent Chatbot.
"""
import os
from pathlib import Path
from typing import Optional
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
    model_name: str = "gemini-3-flash-preview"
    embedding_model: str = "models/gemini-embedding-001"
    temperature: float = 0.1
    max_tokens: int = 8192
    
    # Database Configuration
    sqlite_db_path: str = "data/customers.db"
    chroma_persist_dir: str = "data/embeddings"
    
    # MCP Server Configuration
    mcp_server_host: str = "localhost"
    mcp_server_port: int = 8000
    mcp_server_url: Optional[str] = None
    
    # Streamlit Configuration
    streamlit_server_port: int = 8501
    streamlit_server_address: str = "localhost"
    
    # PDF Processing
    pdf_upload_dir: str = "data/pdfs"
    max_pdf_size_mb: int = 10
    chunk_size: int = 1800
    chunk_overlap: int = 200
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    
    @property
    def mcp_url(self) -> str:
        """Get the full MCP server URL."""
        if self.mcp_server_url:
            return self.mcp_server_url
        return f"http://{self.mcp_server_host}:{self.mcp_server_port}"
    
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
