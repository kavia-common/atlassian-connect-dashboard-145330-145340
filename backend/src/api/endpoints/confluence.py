from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import logging

from src.auth.dependencies import get_confluence_session
from src.models.auth import SessionInfo
from src.models.api_responses import (
    ConfluenceSpacesResponse,
    ConfluenceSpace,
    AccessibleResourcesResponse,
    ResourceInfo
)
from src.services.confluence_service import ConfluenceService

logger = logging.getLogger(__name__)

# Create router with tags for API documentation
router = APIRouter(prefix="/confluence", tags=["Confluence"])


# PUBLIC_INTERFACE
@router.get("/resources", response_model=AccessibleResourcesResponse)
async def get_accessible_resources(
    session: SessionInfo = Depends(get_confluence_session)
):
    """
    Get accessible Confluence resources for OAuth authenticated users.
    
    This endpoint returns the list of Confluence instances (cloud IDs) that the 
    authenticated user has access to. This is only applicable for OAuth authentication.
    
    Headers:
        X-Session-Id: Valid session ID from Confluence authentication
        
    Returns:
        AccessibleResourcesResponse: List of accessible Confluence resources
        
    Raises:
        HTTPException: If user is not OAuth authenticated or API call fails
    """
    try:
        if session.auth_method != "oauth":
            raise HTTPException(
                status_code=400,
                detail="Accessible resources only available for OAuth authentication"
            )
            
        resources_data = await ConfluenceService.get_accessible_resources(session)
        
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
@router.get("/spaces", response_model=ConfluenceSpacesResponse)
async def get_confluence_spaces(
    cloud_id: Optional[str] = Query(None, description="Cloud ID for OAuth authentication"),
    session: SessionInfo = Depends(get_confluence_session)
):
    """
    Fetch all Confluence spaces accessible to the authenticated user.
    
    For OAuth authentication, if cloud_id is not provided, the first accessible
    resource will be used. For API token authentication, cloud_id is not required.
    
    Headers:
        X-Session-Id: Valid session ID from Confluence authentication
        
    Query Parameters:
        cloud_id: Optional cloud ID for OAuth authentication
        
    Returns:
        ConfluenceSpacesResponse: List of Confluence spaces with metadata
        
    Raises:
        HTTPException: If authentication fails or no spaces are accessible
    """
    try:
        spaces_data = await ConfluenceService.get_spaces(session, cloud_id)
        
        # Convert to Pydantic models for validation and consistent response
        spaces = []
        for space_data in spaces_data:
            try:
                space = ConfluenceSpace(**space_data)
                spaces.append(space)
            except Exception as e:
                # Log validation errors but continue with other spaces
                logger.warning(f"Failed to parse space {space_data.get('key', 'unknown')}: {str(e)}")
                continue
        
        # For OAuth, try to get the cloud_id that was used
        used_cloud_id = cloud_id
        if session.auth_method == "oauth" and not cloud_id:
            try:
                resources = await ConfluenceService.get_accessible_resources(session)
                if resources:
                    used_cloud_id = resources[0]["id"]
            except Exception:
                # Don't fail if we can't get cloud_id, just log it
                logger.warning("Could not determine cloud_id for response")
        
        logger.info(f"Retrieved {len(spaces)} Confluence spaces for user {session.email}")
        
        return ConfluenceSpacesResponse(
            success=True,
            spaces=spaces,
            cloud_id=used_cloud_id,
            total_count=len(spaces)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting Confluence spaces for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch Confluence spaces: {str(e)}"
        )


# PUBLIC_INTERFACE
@router.get("/spaces/{space_key}")
async def get_confluence_space_details(
    space_key: str,
    cloud_id: Optional[str] = Query(None, description="Cloud ID for OAuth authentication"),
    session: SessionInfo = Depends(get_confluence_session)
):
    """
    Get detailed information about a specific Confluence space.
    
    Headers:
        X-Session-Id: Valid session ID from Confluence authentication
        
    Path Parameters:
        space_key: Confluence space key
        
    Query Parameters:
        cloud_id: Optional cloud ID for OAuth authentication
        
    Returns:
        Detailed space information from Confluence API
        
    Raises:
        HTTPException: If space not found or access denied
    """
    try:
        space_details = await ConfluenceService.get_space_details(session, space_key, cloud_id)
        
        logger.info(f"Retrieved space details for {space_key} for user {session.email}")
        
        return {
            "success": True,
            "space": space_details,
            "cloud_id": cloud_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting space details for {space_key} for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch space details: {str(e)}"
        )


# PUBLIC_INTERFACE
@router.get("/spaces/{space_key}/content")
async def get_space_content(
    space_key: str,
    content_type: str = Query("page", description="Content type (page, blogpost)"),
    cloud_id: Optional[str] = Query(None, description="Cloud ID for OAuth authentication"), 
    session: SessionInfo = Depends(get_confluence_session)
):
    """
    Get content (pages, blog posts) from a specific Confluence space.
    
    Headers:
        X-Session-Id: Valid session ID from Confluence authentication
        
    Path Parameters:
        space_key: Confluence space key
        
    Query Parameters:
        content_type: Type of content to fetch ('page' or 'blogpost')
        cloud_id: Optional cloud ID for OAuth authentication
        
    Returns:
        List of content items in the space
        
    Raises:
        HTTPException: If space not found or access denied
    """
    try:
        if content_type not in ["page", "blogpost"]:
            raise HTTPException(
                status_code=400,
                detail="content_type must be 'page' or 'blogpost'"
            )
            
        content = await ConfluenceService.get_space_content(session, space_key, cloud_id, content_type)
        
        logger.info(f"Retrieved {len(content)} {content_type} items from space {space_key} for user {session.email}")
        
        return {
            "success": True,
            "content": content,
            "space_key": space_key,
            "content_type": content_type,
            "cloud_id": cloud_id,
            "total_count": len(content)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting space content for {space_key} for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch space content: {str(e)}"
        )


# PUBLIC_INTERFACE
@router.get("/user")
async def get_user_info(
    cloud_id: Optional[str] = Query(None, description="Cloud ID for OAuth authentication"),
    session: SessionInfo = Depends(get_confluence_session)
):
    """
    Get user information and permissions for the authenticated user in Confluence.
    
    Headers:
        X-Session-Id: Valid session ID from Confluence authentication
        
    Query Parameters:
        cloud_id: Optional cloud ID for OAuth authentication
        
    Returns:
        User information from Confluence API
        
    Raises:
        HTTPException: If user information cannot be retrieved
    """
    try:
        user_info = await ConfluenceService.get_user_permissions(session, cloud_id)
        
        logger.info(f"Retrieved user information for user {session.email}")
        
        return {
            "success": True,
            "user": user_info,
            "cloud_id": cloud_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user information for user {session.email}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch user information: {str(e)}"
        )
