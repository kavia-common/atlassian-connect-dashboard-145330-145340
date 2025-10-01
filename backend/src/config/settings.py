from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application configuration settings loaded from environment variables.
    
    OAuth2 Configuration:
    - JIRA_CLIENT_ID: OAuth2 client ID for Jira
    - JIRA_CLIENT_SECRET: OAuth2 client secret for Jira  
    - CONFLUENCE_CLIENT_ID: OAuth2 client ID for Confluence
    - CONFLUENCE_CLIENT_SECRET: OAuth2 client secret for Confluence
    - OAUTH_REDIRECT_URI: Redirect URI for OAuth callbacks
    
    Application Configuration:
    - SECRET_KEY: Secret key for session management
    - ATLASSIAN_BASE_URL: Base URL for Atlassian APIs (default: https://api.atlassian.com)
    """
    
    # OAuth2 Configuration for Jira
    jira_client_id: Optional[str] = None
    jira_client_secret: Optional[str] = None
    
    # OAuth2 Configuration for Confluence  
    confluence_client_id: Optional[str] = None
    confluence_client_secret: Optional[str] = None
    
    # Common OAuth settings
    oauth_redirect_uri: Optional[str] = None
    
    # Application settings
    secret_key: str = "default-secret-key-change-in-production"
    atlassian_base_url: str = "https://api.atlassian.com"
    
    # Session configuration
    session_timeout_minutes: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
