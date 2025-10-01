from fastapi import Depends, HTTPException, Header
from typing import Optional
from src.auth.token_store import token_store
from src.models.auth import SessionInfo


async def get_current_session(
    x_session_id: Optional[str] = Header(None, description="Session ID from authentication")
) -> SessionInfo:
    """
    FastAPI dependency to get current authenticated session.
    
    Args:
        x_session_id: Session ID from X-Session-Id header
        
    Returns:
        SessionInfo: Current session information
        
    Raises:
        HTTPException: If session is invalid or expired
    """
    if not x_session_id:
        raise HTTPException(
            status_code=401,
            detail="Session ID required. Please authenticate first.",
            headers={"WWW-Authenticate": "Session"}
        )
    
    session = token_store.get_session(x_session_id)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired session. Please authenticate again.",
            headers={"WWW-Authenticate": "Session"}
        )
    
    return session


async def get_jira_session(
    session: SessionInfo = Depends(get_current_session)
) -> SessionInfo:
    """
    FastAPI dependency to get current Jira session.
    
    Args:
        session: Current session from get_current_session
        
    Returns:
        SessionInfo: Current Jira session
        
    Raises:
        HTTPException: If session is not for Jira
    """
    if session.provider != "jira":
        raise HTTPException(
            status_code=403,
            detail="Jira authentication required for this endpoint"
        )
    
    return session


async def get_confluence_session(
    session: SessionInfo = Depends(get_current_session)
) -> SessionInfo:
    """
    FastAPI dependency to get current Confluence session.
    
    Args:
        session: Current session from get_current_session
        
    Returns:
        SessionInfo: Current Confluence session
        
    Raises:
        HTTPException: If session is not for Confluence
    """
    if session.provider != "confluence":
        raise HTTPException(
            status_code=403,
            detail="Confluence authentication required for this endpoint"
        )
    
    return session
