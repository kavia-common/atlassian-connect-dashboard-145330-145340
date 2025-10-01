from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class OAuthStartResponse(BaseModel):
    """Response model for OAuth start endpoints"""
    authorization_url: str = Field(..., description="URL to redirect user for OAuth authorization")
    state: str = Field(..., description="State parameter for OAuth flow security")


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback endpoints"""
    code: str = Field(..., description="Authorization code from OAuth provider")
    state: str = Field(..., description="State parameter from OAuth flow")


class APITokenRequest(BaseModel):
    """Request model for API token authentication"""
    domain: str = Field(..., description="Atlassian domain (e.g., your-domain.atlassian.net)")
    email: str = Field(..., description="User email address")
    api_token: str = Field(..., description="API token or personal access token")


class AuthenticationResponse(BaseModel):
    """Response model for successful authentication"""
    success: bool = Field(..., description="Whether authentication was successful")
    message: str = Field(..., description="Success or error message")
    session_id: Optional[str] = Field(None, description="Session ID for authenticated user")
    user_info: Optional[Dict[str, Any]] = Field(None, description="User information from provider")


class SessionInfo(BaseModel):
    """Model for session information stored in token store"""
    session_id: str
    user_id: str
    email: str
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    expires_at: datetime
    provider: str  # 'jira' or 'confluence'
    auth_method: str  # 'oauth' or 'api_token'
    domain: Optional[str] = None  # For API token auth
    created_at: datetime
    last_accessed: datetime


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = False
    message: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
