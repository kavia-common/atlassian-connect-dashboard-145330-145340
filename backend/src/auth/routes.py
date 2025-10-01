from fastapi import APIRouter, HTTPException, Query, BackgroundTasks, Depends
from typing import Dict
import logging

from src.models.auth import (
    OAuthStartResponse, 
    APITokenRequest, 
    AuthenticationResponse,
    SessionInfo
)
from src.auth.oauth_utils import AtlassianOAuthHelper, APITokenHelper
from src.auth.token_store import token_store
from src.auth.dependencies import get_current_session
from src.config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router with tags for API documentation
router = APIRouter(prefix="/auth", tags=["Authentication"])


# OAuth state storage (in production, use Redis or database)
oauth_states: Dict[str, str] = {}


def cleanup_expired_sessions(background_tasks: BackgroundTasks):
    """Background task to cleanup expired sessions"""
    def cleanup():
        count = token_store.cleanup_expired_sessions()
        if count > 0:
            logger.info(f"Cleaned up {count} expired sessions")
    
    background_tasks.add_task(cleanup)


# PUBLIC_INTERFACE
@router.get("/jira/oauth/start", response_model=OAuthStartResponse)
async def start_jira_oauth():
    """
    Start OAuth2 flow for Jira authentication.
    
    Generates an authorization URL that the client should redirect the user to.
    The user will grant permissions and be redirected back to the callback endpoint.
    
    Returns:
        OAuthStartResponse: Contains authorization URL and state parameter
        
    Raises:
        HTTPException: If OAuth is not properly configured
    """
    try:
        authorization_url, state = AtlassianOAuthHelper.generate_authorization_url("jira")
        oauth_states[state] = "jira"  # Store state-provider mapping
        
        return OAuthStartResponse(
            authorization_url=authorization_url,
            state=state
        )
    except ValueError as e:
        logger.error(f"Jira OAuth configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# PUBLIC_INTERFACE
@router.get("/jira/oauth/callback")
async def jira_oauth_callback(
    code: str = Query(..., description="Authorization code from Atlassian"),
    state: str = Query(..., description="State parameter for security"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Handle OAuth2 callback for Jira authentication.
    
    Exchanges the authorization code for an access token and creates a user session.
    
    Args:
        code: Authorization code from Atlassian OAuth
        state: State parameter for CSRF protection
        background_tasks: Background tasks handler
        
    Returns:
        AuthenticationResponse: Success response with session information
        
    Raises:
        HTTPException: If authentication fails or state is invalid
    """
    # Validate state parameter
    if state not in oauth_states or oauth_states[state] != "jira":
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        # Exchange code for token
        token_response = await AtlassianOAuthHelper.exchange_code_for_token("jira", code)
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)
        
        # Get user information
        user_info = await AtlassianOAuthHelper.get_user_info(access_token)
        
        # Create session
        session_id = token_store.create_session(
            user_id=user_info["account_id"],
            email=user_info["email"],
            access_token=access_token,
            provider="jira",
            auth_method="oauth",
            refresh_token=refresh_token,
            expires_in_seconds=expires_in
        )
        
        # Clean up state
        del oauth_states[state]
        
        # Schedule background cleanup
        cleanup_expired_sessions(background_tasks)
        
        logger.info(f"Jira OAuth authentication successful for user: {user_info['email']}")
        
        return AuthenticationResponse(
            success=True,
            message="Jira authentication successful",
            session_id=session_id,
            user_info=user_info
        )
        
    except Exception as e:
        logger.error(f"Jira OAuth callback error: {e}")
        # Clean up state on error
        oauth_states.pop(state, None)
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


# PUBLIC_INTERFACE
@router.post("/jira/api-token", response_model=AuthenticationResponse)
async def authenticate_jira_api_token(
    request: APITokenRequest,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Authenticate with Jira using API token.
    
    Validates the provided API token credentials and creates a user session.
    
    Args:
        request: API token authentication request
        background_tasks: Background tasks handler
        
    Returns:
        AuthenticationResponse: Success response with session information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Validate credentials
        user_info = await APITokenHelper.validate_jira_credentials(
            request.domain, request.email, request.api_token
        )
        
        # Create session
        session_id = token_store.create_session(
            user_id=user_info["accountId"],
            email=user_info["emailAddress"],
            access_token=request.api_token,  # Store API token as access token
            provider="jira",
            auth_method="api_token",
            domain=request.domain,
            expires_in_seconds=settings.session_timeout_minutes * 60
        )
        
        # Schedule background cleanup
        cleanup_expired_sessions(background_tasks)
        
        logger.info(f"Jira API token authentication successful for user: {user_info['emailAddress']}")
        
        return AuthenticationResponse(
            success=True,
            message="Jira API token authentication successful",
            session_id=session_id,
            user_info=user_info
        )
        
    except Exception as e:
        logger.error(f"Jira API token authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# PUBLIC_INTERFACE
@router.get("/confluence/oauth/start", response_model=OAuthStartResponse)
async def start_confluence_oauth():
    """
    Start OAuth2 flow for Confluence authentication.
    
    Generates an authorization URL that the client should redirect the user to.
    The user will grant permissions and be redirected back to the callback endpoint.
    
    Returns:
        OAuthStartResponse: Contains authorization URL and state parameter
        
    Raises:
        HTTPException: If OAuth is not properly configured
    """
    try:
        authorization_url, state = AtlassianOAuthHelper.generate_authorization_url("confluence")
        oauth_states[state] = "confluence"  # Store state-provider mapping
        
        return OAuthStartResponse(
            authorization_url=authorization_url,
            state=state
        )
    except ValueError as e:
        logger.error(f"Confluence OAuth configuration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# PUBLIC_INTERFACE
@router.get("/confluence/oauth/callback")
async def confluence_oauth_callback(
    code: str = Query(..., description="Authorization code from Atlassian"),
    state: str = Query(..., description="State parameter for security"),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Handle OAuth2 callback for Confluence authentication.
    
    Exchanges the authorization code for an access token and creates a user session.
    
    Args:
        code: Authorization code from Atlassian OAuth
        state: State parameter for CSRF protection
        background_tasks: Background tasks handler
        
    Returns:
        AuthenticationResponse: Success response with session information
        
    Raises:
        HTTPException: If authentication fails or state is invalid
    """
    # Validate state parameter
    if state not in oauth_states or oauth_states[state] != "confluence":
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    try:
        # Exchange code for token
        token_response = await AtlassianOAuthHelper.exchange_code_for_token("confluence", code)
        access_token = token_response["access_token"]
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)
        
        # Get user information
        user_info = await AtlassianOAuthHelper.get_user_info(access_token)
        
        # Create session
        session_id = token_store.create_session(
            user_id=user_info["account_id"],
            email=user_info["email"],
            access_token=access_token,
            provider="confluence",
            auth_method="oauth",
            refresh_token=refresh_token,
            expires_in_seconds=expires_in
        )
        
        # Clean up state
        del oauth_states[state]
        
        # Schedule background cleanup
        cleanup_expired_sessions(background_tasks)
        
        logger.info(f"Confluence OAuth authentication successful for user: {user_info['email']}")
        
        return AuthenticationResponse(
            success=True,
            message="Confluence authentication successful",
            session_id=session_id,
            user_info=user_info
        )
        
    except Exception as e:
        logger.error(f"Confluence OAuth callback error: {e}")
        # Clean up state on error
        oauth_states.pop(state, None)
        raise HTTPException(status_code=400, detail=f"Authentication failed: {str(e)}")


# PUBLIC_INTERFACE
@router.post("/confluence/api-token", response_model=AuthenticationResponse)
async def authenticate_confluence_api_token(
    request: APITokenRequest,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Authenticate with Confluence using API token.
    
    Validates the provided API token credentials and creates a user session.
    
    Args:
        request: API token authentication request
        background_tasks: Background tasks handler
        
    Returns:
        AuthenticationResponse: Success response with session information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Validate credentials
        user_info = await APITokenHelper.validate_confluence_credentials(
            request.domain, request.email, request.api_token
        )
        
        # Create session
        session_id = token_store.create_session(
            user_id=user_info["userKey"],
            email=user_info["email"],
            access_token=request.api_token,  # Store API token as access token
            provider="confluence",
            auth_method="api_token",
            domain=request.domain,
            expires_in_seconds=settings.session_timeout_minutes * 60
        )
        
        # Schedule background cleanup
        cleanup_expired_sessions(background_tasks)
        
        logger.info(f"Confluence API token authentication successful for user: {user_info['email']}")
        
        return AuthenticationResponse(
            success=True,
            message="Confluence API token authentication successful",
            session_id=session_id,
            user_info=user_info
        )
        
    except Exception as e:
        logger.error(f"Confluence API token authentication error: {e}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")


# PUBLIC_INTERFACE
@router.get("/session", response_model=SessionInfo)
async def get_session_info(
    current_session: SessionInfo = Depends(get_current_session)
):
    """
    Get current session information.
    
    Requires X-Session-Id header with valid session ID.
    
    Args:
        current_session: Current authenticated session
        
    Returns:
        SessionInfo: Current session details
    """
    return current_session


# PUBLIC_INTERFACE
@router.delete("/session")
async def logout(
    current_session: SessionInfo = Depends(get_current_session)
):
    """
    Logout and invalidate current session.
    
    Requires X-Session-Id header with valid session ID.
    
    Args:
        current_session: Current authenticated session
        
    Returns:
        dict: Logout success message
    """
    token_store.delete_session(current_session.session_id)
    logger.info(f"User {current_session.email} logged out successfully")
    
    return {"message": "Logged out successfully"}


# PUBLIC_INTERFACE
@router.get("/health")
async def auth_health():
    """
    Authentication service health check.
    
    Returns:
        dict: Health status and session statistics
    """
    return {
        "status": "healthy",
        "active_sessions": token_store.get_session_count(),
        "service": "authentication"
    }
