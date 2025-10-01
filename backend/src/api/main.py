from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.auth.routes import router as auth_router

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
            "name": "Health",
            "description": "Health check and status endpoints"
        }
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include authentication routes
app.include_router(auth_router)

@app.get("/", tags=["Health"])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        dict: Simple health status message
    """
    return {"message": "Healthy"}
