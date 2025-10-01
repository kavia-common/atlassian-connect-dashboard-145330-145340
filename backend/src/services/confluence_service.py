import httpx
import logging
from typing import List, Dict, Any, Optional
from src.models.auth import SessionInfo

logger = logging.getLogger(__name__)


class ConfluenceService:
    """
    Service class for interacting with Confluence REST API.
    
    Handles API calls to fetch Confluence spaces, pages, and other resources
    using authenticated session information.
    """

    @staticmethod
    def _get_confluence_base_url(session: SessionInfo) -> str:
        """
        Get the Confluence base URL for API calls.
        
        Args:
            session: Authenticated session information
            
        Returns:
            Base URL for Confluence API calls
            
        Raises:
            ValueError: If domain is not available for API token auth
        """
        if session.auth_method == "oauth":
            # For OAuth, we need to get the cloudId first, but for now use the accessible resource
            return "https://api.atlassian.com/ex/confluence"
        elif session.auth_method == "api_token":
            if not session.domain:
                raise ValueError("Domain is required for API token authentication")
            domain = session.domain
            if not domain.startswith("https://"):
                domain = f"https://{domain}"
            return f"{domain}/wiki/rest/api"
        else:
            raise ValueError(f"Unsupported auth method: {session.auth_method}")

    @staticmethod
    def _get_auth_headers(session: SessionInfo) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Args:
            session: Authenticated session information
            
        Returns:
            Dictionary of headers for authentication
        """
        if session.auth_method == "oauth":
            return {
                "Authorization": f"Bearer {session.access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        elif session.auth_method == "api_token":
            # For API token, we need email and token for basic auth
            import base64
            # The access_token field contains the API token
            credentials = f"{session.email}:{session.access_token}"
            credentials_b64 = base64.b64encode(credentials.encode()).decode()
            return {
                "Authorization": f"Basic {credentials_b64}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
        else:
            raise ValueError(f"Unsupported auth method: {session.auth_method}")

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_accessible_resources(session: SessionInfo) -> List[Dict[str, Any]]:
        """
        Get accessible Confluence resources for OAuth authenticated users.
        
        This is only applicable for OAuth authentication to discover
        available Confluence instances.
        
        Args:
            session: OAuth authenticated session information
            
        Returns:
            List of accessible Confluence resources
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If not OAuth authenticated
        """
        if session.auth_method != "oauth":
            raise ValueError("Accessible resources only available for OAuth authentication")
            
        headers = ConfluenceService._get_auth_headers(session)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_spaces(session: SessionInfo, cloud_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all Confluence spaces accessible to the authenticated user.
        
        Args:
            session: Authenticated session information
            cloud_id: Cloud ID for OAuth authentication (optional for API token)
            
        Returns:
            List of Confluence spaces with basic information
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If authentication method is not supported
        """
        headers = ConfluenceService._get_auth_headers(session)
        
        if session.auth_method == "oauth":
            if not cloud_id:
                # Try to get the first accessible resource
                resources = await ConfluenceService.get_accessible_resources(session)
                if not resources:
                    raise ValueError("No accessible Confluence resources found")
                cloud_id = resources[0]["id"]
                
            url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/rest/api/space"
        else:
            base_url = ConfluenceService._get_confluence_base_url(session)
            url = f"{base_url}/space"
        
        # Add query parameters for better data
        params = {
            "expand": "description.plain,homepage,metadata.labels",
            "limit": 50  # Increase limit to get more spaces
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract results from paginated response
            spaces = data.get("results", []) if isinstance(data, dict) else data
            
            logger.info(f"Fetched {len(spaces)} Confluence spaces for user {session.email}")
            return spaces

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_space_details(
        session: SessionInfo, 
        space_key: str, 
        cloud_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific Confluence space.
        
        Args:
            session: Authenticated session information
            space_key: Space key
            cloud_id: Cloud ID for OAuth authentication (optional for API token)
            
        Returns:
            Detailed space information
            
        Raises:
            httpx.HTTPError: If API request fails or space not found
        """
        headers = ConfluenceService._get_auth_headers(session)
        
        if session.auth_method == "oauth":
            if not cloud_id:
                # Try to get the first accessible resource
                resources = await ConfluenceService.get_accessible_resources(session)
                if not resources:
                    raise ValueError("No accessible Confluence resources found")
                cloud_id = resources[0]["id"]
                
            url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/rest/api/space/{space_key}"
        else:
            base_url = ConfluenceService._get_confluence_base_url(session)
            url = f"{base_url}/space/{space_key}"
        
        params = {
            "expand": "description.plain,homepage,metadata.labels,permissions"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            space = response.json()
            
            logger.info(f"Fetched space details for {space_key} for user {session.email}")
            return space

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_space_content(
        session: SessionInfo, 
        space_key: str, 
        cloud_id: Optional[str] = None,
        content_type: str = "page"
    ) -> List[Dict[str, Any]]:
        """
        Get content (pages, blog posts) from a specific Confluence space.
        
        Args:
            session: Authenticated session information
            space_key: Space key
            cloud_id: Cloud ID for OAuth authentication (optional for API token)
            content_type: Type of content to fetch ('page', 'blogpost')
            
        Returns:
            List of content items in the space
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        headers = ConfluenceService._get_auth_headers(session)
        
        if session.auth_method == "oauth":
            if not cloud_id:
                # Try to get the first accessible resource
                resources = await ConfluenceService.get_accessible_resources(session)
                if not resources:
                    raise ValueError("No accessible Confluence resources found")
                cloud_id = resources[0]["id"]
                
            url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/rest/api/content"
        else:
            base_url = ConfluenceService._get_confluence_base_url(session)
            url = f"{base_url}/content"
        
        params = {
            "spaceKey": space_key,
            "type": content_type,
            "expand": "space,history,version",
            "limit": 25
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract results from paginated response
            content = data.get("results", []) if isinstance(data, dict) else data
            
            logger.info(f"Fetched {len(content)} {content_type} items from space {space_key} for user {session.email}")
            return content

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_user_permissions(session: SessionInfo, cloud_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user information and permissions for the authenticated user.
        
        Args:
            session: Authenticated session information
            cloud_id: Cloud ID for OAuth authentication (optional for API token)
            
        Returns:
            User information and permissions
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        headers = ConfluenceService._get_auth_headers(session)
        
        if session.auth_method == "oauth":
            if not cloud_id:
                # Try to get the first accessible resource
                resources = await ConfluenceService.get_accessible_resources(session)
                if not resources:
                    raise ValueError("No accessible Confluence resources found")
                cloud_id = resources[0]["id"]
                
            url = f"https://api.atlassian.com/ex/confluence/{cloud_id}/wiki/rest/api/user/current"
        else:
            base_url = ConfluenceService._get_confluence_base_url(session)
            url = f"{base_url}/user/current"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            user_info = response.json()
            
            logger.info(f"Fetched user permissions for user {session.email}")
            return user_info
