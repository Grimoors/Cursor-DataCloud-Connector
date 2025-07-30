"""
Configuration settings for the Salesforce Data Cloud Middleware.

This module defines all configuration settings using Pydantic BaseSettings,
which automatically loads values from environment variables and provides
type validation and default values.
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be configured via environment variables or .env files.
    Pydantic automatically handles type conversion and validation.
    """
    
    # Application Configuration
    app_name: str = "Salesforce Data Cloud Middleware"
    version: str = "1.0.0"
    environment: str = Field(default="development", env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Server Configuration
    host: str = Field(default="localhost", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # API Configuration
    enable_docs: bool = Field(default=True, env="ENABLE_DOCS")
    enable_mcp: bool = Field(default=True, env="ENABLE_MCP")
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    
    # CORS Configuration
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    
    # Salesforce Configuration
    salesforce_username: str = Field(..., env="SALESFORCE_USERNAME")
    salesforce_consumer_key: str = Field(..., env="SALESFORCE_CONSUMER_KEY")
    salesforce_private_key_path: str = Field(..., env="SALESFORCE_PRIVATE_KEY_PATH")
    salesforce_instance_url: str = Field(
        default="https://login.salesforce.com",
        env="SALESFORCE_INSTANCE_URL"
    )
    salesforce_api_version: str = Field(default="58.0", env="SALESFORCE_API_VERSION")
    
    # Data Cloud Configuration
    data_cloud_dataspace: str = Field(..., env="DATA_CLOUD_DATASPACE")
    data_cloud_api_version: str = Field(default="1", env="DATA_CLOUD_API_VERSION")
    
    # Authentication Configuration
    jwt_algorithm: str = Field(default="RS256", env="JWT_ALGORITHM")
    jwt_expiration_minutes: int = Field(default=5, env="JWT_EXPIRATION_MINUTES")
    token_refresh_threshold_minutes: int = Field(
        default=10, 
        env="TOKEN_REFRESH_THRESHOLD_MINUTES"
    )
    
    # Caching Configuration
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")
    
    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    rate_limit_requests_per_minute: int = Field(
        default=60, 
        env="RATE_LIMIT_REQUESTS_PER_MINUTE"
    )
    
    # Security Configuration
    allowed_api_keys: List[str] = Field(default=[], env="ALLOWED_API_KEYS")
    enable_api_key_validation: bool = Field(
        default=True, 
        env="ENABLE_API_KEY_VALIDATION"
    )
    
    # MCP Configuration
    mcp_server_name: str = Field(
        default="salesforce-data-tools",
        env="MCP_SERVER_NAME"
    )
    mcp_server_description: str = Field(
        default="Salesforce Data Cloud integration tools",
        env="MCP_SERVER_DESCRIPTION"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_api_keys", pre=True)
    def parse_api_keys(cls, v):
        """Parse API keys from comma-separated string."""
        if isinstance(v, str):
            return [key.strip() for key in v.split(",")]
        return v
    
    @validator("salesforce_private_key_path")
    def validate_private_key_path(cls, v):
        """Validate that the private key file exists."""
        key_path = Path(v)
        if not key_path.exists():
            raise ValueError(f"Private key file not found: {v}")
        if not key_path.is_file():
            raise ValueError(f"Private key path is not a file: {v}")
        return str(key_path.absolute())
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level is one of the allowed values."""
        allowed_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed_levels:
            raise ValueError(f"Log level must be one of: {allowed_levels}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment is one of the allowed values."""
        allowed_environments = ["development", "staging", "production"]
        if v.lower() not in allowed_environments:
            raise ValueError(f"Environment must be one of: {allowed_environments}")
        return v.lower()
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings: The application settings instance
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.
    
    This is useful for testing or when settings need to be updated
    during runtime.
    
    Returns:
        Settings: The reloaded settings instance
    """
    global _settings
    _settings = Settings()
    return _settings 