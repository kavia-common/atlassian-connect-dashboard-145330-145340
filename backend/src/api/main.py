from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.routes import router as auth_router
from src.api.endpoints.jira import router as jira_router
from src.api.endpoints.confluence import router as confluence_router
from src.middleware.validation import TokenValidationMiddleware

# Create FastAPI app with metadata for OpenAPI documentation
app = FastAPI(
    title="Atlassian Connect Dashboard API",
    description="Backend API for connecting to Jira and Confluence via OAuth2 and API tokens",
    version="1.0.0",
    openapi_tags=[
        {
            "name": "Authentication",
            "description": "OAuth2 and API token authentication endpoints for Jira and Confluence"
        },
        {
            "name": "Jira",
            "description": "Jira API endpoints for fetching projects, issues, and other resources"
        },
        {
            "name": "Confluence", 
            "description": "Confluence API endpoints for fetching spaces, pages, and other content"
        },
        {
            "name": "Health",
            "description": "Health check and status endpoints"
        }
    ]
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add token validation middleware
app.add_middleware(TokenValidationMiddleware)

# Include routers
app.include_router(auth_router)
app.include_router(jira_router)
app.include_router(confluence_router)

@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Simple health status message
    """
    return {"message": "Healthy"}
