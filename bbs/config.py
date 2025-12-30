"""Configuration management for the BBS."""
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://bbs_user:bbs_password@postgres:5432/bbs_db"
    )
    
    # Telnet Server
    TELNET_HOST: str = os.getenv("TELNET_HOST", "0.0.0.0")
    TELNET_PORT: int = int(os.getenv("TELNET_PORT", "2323"))  # Default 2323 (23 requires root)
    
    # Web Server
    WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
    WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))
    
    # Application
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


config = Config()

