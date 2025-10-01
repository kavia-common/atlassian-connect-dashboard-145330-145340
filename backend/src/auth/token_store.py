import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional
from src.models.auth import SessionInfo


class InMemoryTokenStore:
    """
    In-memory token store for managing user sessions and authentication tokens.
    
    This implementation stores all session data in memory, which means:
    - Sessions are lost when the application restarts
    - Not suitable for production with multiple instances
    - Good for development and single-instance deployments
    """
    
    def __init__(self):
        self._sessions: Dict[str, SessionInfo] = {}
        
    def create_session(
        self, 
        user_id: str, 
        email: str, 
        access_token: str,
        provider: str,
        auth_method: str,
        refresh_token: Optional[str] = None,
        domain: Optional[str] = None,
        expires_in_seconds: int = 3600
    ) -> str:
        """
        Create a new session and return session ID.
        
        Args:
            user_id: Unique user identifier from provider
            email: User email address
            access_token: OAuth access token or API token
            provider: 'jira' or 'confluence'
            auth_method: 'oauth' or 'api_token'
            refresh_token: OAuth refresh token (if available)
            domain: Atlassian domain (for API token auth)
            expires_in_seconds: Token expiration time in seconds
            
        Returns:
            Session ID string
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session_info = SessionInfo(
            session_id=session_id,
            user_id=user_id,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=now + timedelta(seconds=expires_in_seconds),
            provider=provider,
            auth_method=auth_method,
            domain=domain,
            created_at=now,
            last_accessed=now
        )
        
        self._sessions[session_id] = session_info
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionInfo]:
        """
        Retrieve session information by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            SessionInfo if session exists and is valid, None otherwise
        """
        if session_id not in self._sessions:
            return None
            
        session = self._sessions[session_id]
        
        # Check if session has expired
        if datetime.utcnow() > session.expires_at:
            self.delete_session(session_id)
            return None
            
        # Update last accessed time
        session.last_accessed = datetime.utcnow()
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        now = datetime.utcnow()
        expired_sessions = [
            session_id for session_id, session in self._sessions.items()
            if now > session.expires_at
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
            
        return len(expired_sessions)
    
    def get_session_count(self) -> int:
        """Get the total number of active sessions."""
        return len(self._sessions)


# Global token store instance
token_store = InMemoryTokenStore()
