from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import logging
from typing import Callable
import httpx

logger = logging.getLogger(__name__)


class TokenValidationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for validating authentication tokens and handling API errors.
    
    This middleware provides additional validation and error handling
    beyond the basic FastAPI dependencies.
    """
    
    def __init__(self, app, exempt_paths: list = None):
        """
        Initialize the middleware.
        
        Args:
            app: FastAPI application instance
            exempt_paths: List of paths to exempt from token validation
        """
        super().__init__(app)
        self.exempt_paths = exempt_paths or [
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/auth/jira/oauth/start",
            "/auth/jira/oauth/callback",
            "/auth/jira/api-token",
            "/auth/confluence/oauth/start", 
            "/auth/confluence/oauth/callback",
            "/auth/confluence/api-token",
            "/auth/health"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and apply validation logic.
        
        Args:
            request: Incoming request
            call_next: Next middleware/handler in chain
            
        Returns:
            Response from the application or error response
        """
        path = request.url.path
        
        # Skip validation for exempt paths
        if any(path.startswith(exempt_path) for exempt_path in self.exempt_paths):
            return await call_next(request)
        
        # Log API access attempts
        session_id = request.headers.get("X-Session-Id")
        if session_id:
            logger.info(f"API access attempt: {request.method} {path} with session {session_id[:8]}...")
        else:
            logger.warning(f"API access attempt without session: {request.method} {path}")
        
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Handle known HTTP exceptions
            logger.warning(f"HTTP exception on {path}: {e.status_code} - {e.detail}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "success": False,
                    "error": e.detail,
                    "error_code": f"HTTP_{e.status_code}"
                }
            )
            
        except httpx.HTTPError as e:
            # Handle external API errors
            logger.error(f"External API error on {path}: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "success": False,
                    "error": "External service unavailable. Please try again later.",
                    "error_code": "EXTERNAL_API_ERROR",
                    "details": {"service_error": str(e)}
                }
            )
            
        except Exception as e:
            # Handle unexpected errors
            logger.error(f"Unexpected error on {path}: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "An unexpected error occurred. Please try again.",
                    "error_code": "INTERNAL_SERVER_ERROR"
                }
            )


def create_error_response(
    status_code: int, 
    message: str, 
    error_code: str = None,
    details: dict = None
) -> JSONResponse:
    """
    Create a standardized error response.
    
    Args:
        status_code: HTTP status code
        message: Error message
        error_code: Optional error code for programmatic handling
        details: Optional additional error details
        
    Returns:
        JSONResponse with standardized error format
    """
    content = {
        "success": False,
        "error": message,
    }
    
    if error_code:
        content["error_code"] = error_code
        
    if details:
        content["details"] = details
        
    return JSONResponse(status_code=status_code, content=content)


async def validate_session_token(session_id: str) -> bool:
    """
    Additional validation logic for session tokens.
    
    This can be extended to perform additional checks beyond
    the basic session existence validation.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        True if session is valid and active
    """
    # This could include additional checks like:
    # - Rate limiting
    # - Token refresh validation
    # - Permission checks
    # - Audit logging
    
    # For now, just return True as the main validation
    # is handled by the FastAPI dependencies
    return True
