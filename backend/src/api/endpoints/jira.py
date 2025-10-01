from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from src.auth.dependencies import get_jira_session
from src.models.auth import SessionInfo
from src.models.api_responses import (
    JiraProjectsResponse, 
    JiraProject, 
    AccessibleResourcesResponse,
    ResourceInfo
)
from src.services.jira_service import JiraService

logger = logging.getLogger(__name__)

# Create router with tags for API documentation
router = APIRouter(prefix="/jira", tags=["Jira"])


# PUBLIC_INTERFACE
@router.get("/resources", response_model=AccessibleResourcesResponse)
async def get_accessible_resources(
    session: SessionInfo = Depends(get_jira_session)
):
    """
    Get accessible Jira resources for OAuth authenticated users.
    
    This endpoint returns the list of Jira instances (cloud IDs) that the 
    authenticated user has access to. This is only applicable for OAuth authentication.
    
    Headers:
        X-Session-Id: Valid session ID from Jira authentication
        
    Returns:
        AccessibleResourcesResponse: List of accessible Jira resources
        
    Raises:
        HTTPException: If user is not OAuth authenticated or API call fails
    """
    try:
        if session.auth_method != "oauth":
            raise HTTPException(
                status_code=400,
                detail="Accessible resources only available for OAuth authentication"
            )
            
        resources_data = await JiraService.get_accessible_resources(session)
        
        resources = [
            ResourceInfo(
                id=resource["id"],
                url=resource["url"], 
                name=resource["name"],
                scopes=resource["scopes"],
                avatarUrl=resource["avatarUrl"]
            )
            for resource in resources_data
        ]
        
        logger.info(f"Retrieved {len(resources)} accessible resources for user {session.email}")
        
        return AccessibleResourcesResponse(
            success=True,
            resources=resources
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accessible resources for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get accessible resources: {str(e)}"
        )


# PUBLIC_INTERFACE
@router.get("/projects", response_model=JiraProjectsResponse)
async def get_jira_projects(
    cloud_id: Optional[str] = Query(None, description="Cloud ID for OAuth authentication"),
    session: SessionInfo = Depends(get_jira_session)
):
    """
    Fetch all Jira projects accessible to the authenticated user.
    
    For OAuth authentication, if cloud_id is not provided, the first accessible
    resource will be used. For API token authentication, cloud_id is not required.
    
    Headers:
        X-Session-Id: Valid session ID from Jira authentication
        
    Query Parameters:
        cloud_id: Optional cloud ID for OAuth authentication
        
    Returns:
        JiraProjectsResponse: List of Jira projects with metadata
        
    Raises:
        HTTPException: If authentication fails or no projects are accessible
    """
    try:
        projects_data = await JiraService.get_projects(session, cloud_id)
        
        # Convert to Pydantic models for validation and consistent response
        projects = []
        for project_data in projects_data:
            try:
                project = JiraProject(**project_data)
                projects.append(project)
            except Exception as e:
                # Log validation errors but continue with other projects
                logger.warning(f"Failed to parse project {project_data.get('key', 'unknown')}: {str(e)}")
                continue
        
        # For OAuth, try to get the cloud_id that was used
        used_cloud_id = cloud_id
        if session.auth_method == "oauth" and not cloud_id:
            try:
                resources = await JiraService.get_accessible_resources(session)
                if resources:
                    used_cloud_id = resources[0]["id"]
            except Exception:
                # Don't fail if we can't get cloud_id, just log it
                logger.warning("Could not determine cloud_id for response")
        
        logger.info(f"Retrieved {len(projects)} Jira projects for user {session.email}")
        
        return JiraProjectsResponse(
            success=True,
            projects=projects,
            cloud_id=used_cloud_id,
            total_count=len(projects)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Jira projects for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Jira projects: {str(e)}"
        )


# PUBLIC_INTERFACE  
@router.get("/projects/{project_key}")
async def get_jira_project_details(
    project_key: str,
    cloud_id: Optional[str] = Query(None, description="Cloud ID for OAuth authentication"),
    session: SessionInfo = Depends(get_jira_session)
):
    """
    Get detailed information about a specific Jira project.
    
    Headers:
        X-Session-Id: Valid session ID from Jira authentication
        
    Path Parameters:
        project_key: Jira project key or ID
        
    Query Parameters:
        cloud_id: Optional cloud ID for OAuth authentication
        
    Returns:
        Detailed project information from Jira API
        
    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project_details = await JiraService.get_project_details(session, project_key, cloud_id)
        
        logger.info(f"Retrieved project details for {project_key} for user {session.email}")
        
        return {
            "success": True,
            "project": project_details,
            "cloud_id": cloud_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project details for {project_key} for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch project details: {str(e)}"
        )


# PUBLIC_INTERFACE
@router.get("/permissions")
async def get_user_permissions(
    cloud_id: Optional[str] = Query(None, description="Cloud ID for OAuth authentication"),
    session: SessionInfo = Depends(get_jira_session)
):
    """
    Get user permissions for the authenticated user in Jira.
    
    Headers:
        X-Session-Id: Valid session ID from Jira authentication
        
    Query Parameters:
        cloud_id: Optional cloud ID for OAuth authentication
        
    Returns:
        User permissions information from Jira API
        
    Raises:
        HTTPException: If permissions cannot be retrieved
    """
    try:
        permissions = await JiraService.get_user_permissions(session, cloud_id)
        
        logger.info(f"Retrieved user permissions for user {session.email}")
        
        return {
            "success": True,
            "permissions": permissions,
            "cloud_id": cloud_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user permissions for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch user permissions: {str(e)}"
        )
