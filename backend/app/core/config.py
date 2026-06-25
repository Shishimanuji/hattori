"""Configuration module for FastAPI application"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database Configuration
    database_url: str
    database_echo: bool = False

    # Application Configuration
    app_name: str = "Project Resource Management System"
    app_version: str = "0.1.0"
    debug: bool = False

    # Security Configuration
    secret_key: str
    password_salt: str = "default-salt-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 24
    refresh_token_expire_days: int = 7

    # Session Timeout Configuration (in minutes)
    idle_timeout_minutes: int = 30  # Reset on each request
    absolute_timeout_minutes: int = 35  # Hard limit regardless of activity
    session_warning_minutes: int = 30  # Warn user 5 minutes before idle timeout (at 30 min mark)

    # CORS Configuration
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]

    # API Configuration
    api_v1_prefix: str = "/api"
    api_title: str = "PRMS API"
    api_description: str = "REST API for Project Resource Management System"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()  # type: ignore
