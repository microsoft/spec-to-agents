"""
Application configuration management using Pydantic Settings.

This module handles all environment variables and configuration settings
for the Microsoft Agent Framework Reference implementation.
"""

from functools import lru_cache
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application settings
    APP_NAME: str = Field(default="Microsoft Agent Framework Reference API")
    DEBUG: bool = Field(default=False)
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    ALLOWED_HOSTS: List[str] = Field(default=["*"])
    
    # Azure OpenAI Configuration
    AZURE_OPENAI_ENDPOINT: str = Field(default="", description="Azure OpenAI service endpoint")
    AZURE_OPENAI_API_KEY: str = Field(default="", description="Azure OpenAI API key")
    AZURE_OPENAI_API_VERSION: str = Field(default="2024-02-15-preview")
    AZURE_OPENAI_CHAT_MODEL: str = Field(default="gpt-4")
    AZURE_OPENAI_EMBEDDING_MODEL: str = Field(default="text-embedding-ada-002")
    
    # Azure AI Foundry Configuration
    AZURE_AI_FOUNDRY_ENDPOINT: str = Field(default="", description="Azure AI Foundry endpoint")
    AZURE_AI_FOUNDRY_API_KEY: str = Field(default="", description="Azure AI Foundry API key")
    AZURE_AI_FOUNDRY_PROJECT_ID: str = Field(default="", description="Azure AI Foundry project ID")
    
    # CosmosDB Configuration
    COSMOS_ENDPOINT: str = Field(default="", description="CosmosDB endpoint URL")
    COSMOS_KEY: str = Field(default="", description="CosmosDB primary key")
    COSMOS_DATABASE_NAME: str = Field(default="agent_framework_reference")
    

    # Azure Key Vault Configuration
    KEY_VAULT_ENDPOINT: str = Field(default="", description="Azure Key Vault endpoint")
    
    # Azure Service Bus Configuration
    SERVICE_BUS_CONNECTION_STRING: str = Field(default="", description="Azure Service Bus connection string")
    SERVICE_BUS_QUEUE_NAME: str = Field(default="agent-events")
    
    # Application Insights Configuration
    APPLICATION_INSIGHTS_CONNECTION_STRING: str = Field(default="", description="Application Insights connection string")
    
    # Authentication and Security
    SECRET_KEY: str = Field(default="development-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    
    # Learning Configuration
    DEFAULT_DIFFICULTY_LEVEL: str = Field(default="beginner", description="Default learning difficulty")
    MAX_WORKFLOW_DURATION: int = Field(default=300, description="Maximum workflow duration in seconds")
    ENABLE_LEARNING_ANALYTICS: bool = Field(default=True)
    
    # Agent Configuration
    DEFAULT_AGENT_TIMEOUT: int = Field(default=60, description="Default agent timeout in seconds")
    MAX_CONCURRENT_AGENTS: int = Field(default=10)
    ENABLE_AGENT_CACHING: bool = Field(default=True)
    
    # Tool Configuration
    ENABLE_MCP_TOOLS: bool = Field(default=True)
    ENABLE_HOSTED_TOOLS: bool = Field(default=True)
    TOOL_EXECUTION_TIMEOUT: int = Field(default=30)
    
    # Workflow Configuration
    MAX_WORKFLOW_STEPS: int = Field(default=50)
    ENABLE_WORKFLOW_PERSISTENCE: bool = Field(default=True)
    WORKFLOW_STATE_TTL: int = Field(default=86400, description="Workflow state TTL in seconds")
    
    # Monitoring and Logging
    LOG_LEVEL: str = Field(default="INFO")
    ENABLE_METRICS: bool = Field(default=True)
    ENABLE_TRACING: bool = Field(default=True)
    METRICS_PORT: int = Field(default=8001)
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = Field(default=60)
    RATE_LIMIT_BURST: int = Field(default=10)
    
    # WebSocket Configuration
    WEBSOCKET_MAX_CONNECTIONS: int = Field(default=100)
    WEBSOCKET_HEARTBEAT_INTERVAL: int = Field(default=30)
    
    def get_azure_openai_config(self) -> dict:
        """Get Azure OpenAI configuration dictionary."""
        return {
            "endpoint": self.AZURE_OPENAI_ENDPOINT,
            "api_key": self.AZURE_OPENAI_API_KEY,
            "api_version": self.AZURE_OPENAI_API_VERSION,
            "chat_model": self.AZURE_OPENAI_CHAT_MODEL,
            "embedding_model": self.AZURE_OPENAI_EMBEDDING_MODEL,
        }
    
    def get_cosmos_config(self) -> dict:
        """Get CosmosDB configuration dictionary."""
        return {
            "endpoint": self.COSMOS_ENDPOINT,
            "key": self.COSMOS_KEY,
            "database_name": self.COSMOS_DATABASE_NAME,
        }
    
    def get_redis_config(self) -> dict:
        """Get Redis configuration dictionary."""
        return {
            "connection_string": self.REDIS_CONNECTION_STRING,
            "key_prefix": self.REDIS_KEY_PREFIX,
            "default_ttl": self.REDIS_DEFAULT_TTL,
        }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Using lru_cache ensures settings are loaded only once and cached.
    This is important for performance and consistency across the application.
    """
    return Settings()