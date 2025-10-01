import httpx
import logging
from typing import List, Dict, Any, Optional
from src.models.auth import SessionInfo

logger = logging.getLogger(__name__)


class JiraService:
    """
    Service class for interacting with Jira REST API.
    
    Handles API calls to fetch Jira projects, issues, and other resources
    using authenticated session information.
    """

    @staticmethod
    def _get_jira_base_url(session: SessionInfo) -> str:
        """
        Get the Jira base URL for API calls.
        
        Args:
            session: Authenticated session information
            
        Returns:
            Base URL for Jira API calls
            
        Raises:
            ValueError: If domain is not available for API token auth
        """
        if session.auth_method == "oauth":
            # For OAuth, we need to get the cloudId first, but for now use the accessible resource
            return "https://api.atlassian.com/ex/jira"
        elif session.auth_method == "api_token":
            if not session.domain:
                raise ValueError("Domain is required for API token authentication")
            domain = session.domain
            if not domain.startswith("https://"):
                domain = f"https://{domain}"
            return f"{domain}/rest/api/3"
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
        Get accessible Jira resources for OAuth authenticated users.
        
        This is only applicable for OAuth authentication to discover
        available Jira instances.
        
        Args:
            session: OAuth authenticated session information
            
        Returns:
            List of accessible Jira resources
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If not OAuth authenticated
        """
        if session.auth_method != "oauth":
            raise ValueError("Accessible resources only available for OAuth authentication")
            
        headers = JiraService._get_auth_headers(session)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.atlassian.com/oauth/token/accessible-resources",
                headers=headers
            )
            response.raise_for_status()
            return response.json()

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_projects(session: SessionInfo, cloud_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Fetch all Jira projects accessible to the authenticated user.
        
        Args:
            session: Authenticated session information
            cloud_id: Cloud ID for OAuth authentication (optional for API token)
            
        Returns:
            List of Jira projects with basic information
            
        Raises:
            httpx.HTTPError: If API request fails
            ValueError: If authentication method is not supported
        """
        headers = JiraService._get_auth_headers(session)
        
        if session.auth_method == "oauth":
            if not cloud_id:
                # Try to get the first accessible resource
                resources = await JiraService.get_accessible_resources(session)
                if not resources:
                    raise ValueError("No accessible Jira resources found")
                cloud_id = resources[0]["id"]
                
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project"
        else:
            base_url = JiraService._get_jira_base_url(session)
            url = f"{base_url}/project"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            projects = response.json()
            
            logger.info(f"Fetched {len(projects)} Jira projects for user {session.email}")
            return projects

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_project_details(
        session: SessionInfo, 
        project_key: str, 
        cloud_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific Jira project.
        
        Args:
            session: Authenticated session information
            project_key: Project key or ID
            cloud_id: Cloud ID for OAuth authentication (optional for API token)
            
        Returns:
            Detailed project information
            
        Raises:
            httpx.HTTPError: If API request fails or project not found
        """
        headers = JiraService._get_auth_headers(session)
        
        if session.auth_method == "oauth":
            if not cloud_id:
                # Try to get the first accessible resource
                resources = await JiraService.get_accessible_resources(session)
                if not resources:
                    raise ValueError("No accessible Jira resources found")
                cloud_id = resources[0]["id"]
                
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/project/{project_key}"
        else:
            base_url = JiraService._get_jira_base_url(session)
            url = f"{base_url}/project/{project_key}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            project = response.json()
            
            logger.info(f"Fetched project details for {project_key} for user {session.email}")
            return project

    # PUBLIC_INTERFACE
    @staticmethod
    async def get_user_permissions(session: SessionInfo, cloud_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user permissions for the authenticated user.
        
        Args:
            session: Authenticated session information
            cloud_id: Cloud ID for OAuth authentication (optional for API token)
            
        Returns:
            User permissions information
            
        Raises:
            httpx.HTTPError: If API request fails
        """
        headers = JiraService._get_auth_headers(session)
        
        if session.auth_method == "oauth":
            if not cloud_id:
                # Try to get the first accessible resource
                resources = await JiraService.get_accessible_resources(session)
                if not resources:
                    raise ValueError("No accessible Jira resources found")
                cloud_id = resources[0]["id"]
                
            url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3/mypermissions"
        else:
            base_url = JiraService._get_jira_base_url(session)
            url = f"{base_url}/mypermissions"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            permissions = response.json()
            
            logger.info(f"Fetched user permissions for user {session.email}")
            return permissions
