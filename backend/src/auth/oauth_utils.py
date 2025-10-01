import secrets
import base64
from urllib.parse import urlencode
from typing import Dict, Any
import httpx
from src.config.settings import settings


class AtlassianOAuthHelper:
    """
    Helper class for Atlassian OAuth 2.0 flows.
    
    Handles OAuth authorization URL generation and token exchange
    for both Jira and Confluence.
    """
    
    # OAuth endpoints
    AUTHORIZATION_URL = "https://auth.atlassian.com/authorize"
    TOKEN_URL = "https://auth.atlassian.com/oauth/token"
    
    # OAuth scopes
    JIRA_SCOPES = ["read:jira-user", "read:jira-work"]
    CONFLUENCE_SCOPES = ["read:confluence-user", "read:confluence-space.summary"]
    
    @staticmethod
    def generate_authorization_url(provider: str) -> tuple[str, str]:
        """
        Generate OAuth authorization URL for the specified provider.
        
        Args:
            provider: Either 'jira' or 'confluence'
            
        Returns:
            Tuple of (authorization_url, state)
        """
        if provider == "jira":
            client_id = settings.jira_client_id
            scopes = AtlassianOAuthHelper.JIRA_SCOPES
        elif provider == "confluence":
            client_id = settings.confluence_client_id  
            scopes = AtlassianOAuthHelper.CONFLUENCE_SCOPES
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
        if not client_id:
            raise ValueError(f"Client ID not configured for {provider}")
            
        # Generate random state for security
        state = secrets.token_urlsafe(32)
        
        params = {
            "audience": "api.atlassian.com",
            "client_id": client_id,
            "scope": " ".join(scopes),
            "redirect_uri": settings.oauth_redirect_uri,
            "state": state,
            "response_type": "code",
            "prompt": "consent"
        }
        
        authorization_url = f"{AtlassianOAuthHelper.AUTHORIZATION_URL}?{urlencode(params)}"
        return authorization_url, state
    
    @staticmethod
    async def exchange_code_for_token(provider: str, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            provider: Either 'jira' or 'confluence'
            code: Authorization code from OAuth callback
            
        Returns:
            Token response dictionary
            
        Raises:
            httpx.HTTPError: If token exchange fails
            ValueError: If provider is invalid or not configured
        """
        if provider == "jira":
            client_id = settings.jira_client_id
            client_secret = settings.jira_client_secret
        elif provider == "confluence":
            client_id = settings.confluence_client_id
            client_secret = settings.confluence_client_secret
        else:
            raise ValueError(f"Unsupported provider: {provider}")
            
        if not client_id or not client_secret:
            raise ValueError(f"OAuth credentials not configured for {provider}")
        
        # Prepare basic auth header
        credentials = f"{client_id}:{client_secret}"
        credentials_b64 = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            "Authorization": f"Basic {credentials_b64}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "redirect_uri": settings.oauth_redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                AtlassianOAuthHelper.TOKEN_URL,
                headers=headers,
                data=data
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def get_user_info(access_token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            User information dictionary
        """
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/me",
                headers=headers
            )
            response.raise_for_status()
            return response.json()


class APITokenHelper:
    """
    Helper class for API token authentication with Atlassian services.
    """
    
    @staticmethod
    async def validate_jira_credentials(domain: str, email: str, api_token: str) -> Dict[str, Any]:
        """
        Validate Jira API token credentials.
        
        Args:
            domain: Jira domain (e.g., your-domain.atlassian.net)
            email: User email
            api_token: API token
            
        Returns:
            User information if valid
            
        Raises:
            httpx.HTTPError: If validation fails
        """
        if not domain.startswith("https://"):
            domain = f"https://{domain}"
            
        auth = (email, api_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{domain}/rest/api/3/myself",
                auth=auth
            )
            response.raise_for_status()
            return response.json()
    
    @staticmethod
    async def validate_confluence_credentials(domain: str, email: str, api_token: str) -> Dict[str, Any]:
        """
        Validate Confluence API token credentials.
        
        Args:
            domain: Confluence domain (e.g., your-domain.atlassian.net)
            email: User email
            api_token: API token
            
        Returns:
            User information if valid
            
        Raises:
            httpx.HTTPError: If validation fails
        """
        if not domain.startswith("https://"):
            domain = f"https://{domain}"
            
        auth = (email, api_token)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{domain}/wiki/rest/api/user/current",
                auth=auth
            )
            response.raise_for_status()
            return response.json()
