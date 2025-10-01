from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class JiraProject(BaseModel):
    """Model for Jira project information"""
    id: str = Field(..., description="Project ID")
    key: str = Field(..., description="Project key")
    name: str = Field(..., description="Project name")
    projectTypeKey: str = Field(..., description="Project type key")
    simplified: Optional[bool] = Field(None, description="Whether project uses simplified workflow")
    style: Optional[str] = Field(None, description="Project style")
    isPrivate: Optional[bool] = Field(None, description="Whether project is private")
    description: Optional[str] = Field(None, description="Project description")
    url: Optional[str] = Field(None, description="Project URL")
    email: Optional[str] = Field(None, description="Project email")
    assigneeType: Optional[str] = Field(None, description="Default assignee type")
    avatarUrls: Optional[Dict[str, str]] = Field(None, description="Avatar URLs")
    projectCategory: Optional[Dict[str, Any]] = Field(None, description="Project category")


class JiraProjectsResponse(BaseModel):
    """Response model for Jira projects endpoint"""
    success: bool = Field(True, description="Whether the request was successful")
    projects: List[JiraProject] = Field(..., description="List of Jira projects")
    cloud_id: Optional[str] = Field(None, description="Cloud ID used for OAuth requests")
    total_count: int = Field(..., description="Total number of projects")


class ConfluenceSpace(BaseModel):
    """Model for Confluence space information"""
    id: str = Field(..., description="Space ID") 
    key: str = Field(..., description="Space key")
    name: str = Field(..., description="Space name")
    type: str = Field(..., description="Space type (global, personal)")
    status: Optional[str] = Field(None, description="Space status")
    description: Optional[Dict[str, Any]] = Field(None, description="Space description")
    homepage: Optional[Dict[str, Any]] = Field(None, description="Homepage information")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Space metadata")
    links: Optional[Dict[str, str]] = Field(None, description="Related links", alias="_links")


class ConfluenceSpacesResponse(BaseModel):
    """Response model for Confluence spaces endpoint"""
    success: bool = Field(True, description="Whether the request was successful")
    spaces: List[ConfluenceSpace] = Field(..., description="List of Confluence spaces")
    cloud_id: Optional[str] = Field(None, description="Cloud ID used for OAuth requests")
    total_count: int = Field(..., description="Total number of spaces")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    success: bool = Field(False, description="Request was not successful")
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for programmatic handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class ResourceInfo(BaseModel):
    """Model for accessible resource information"""
    id: str = Field(..., description="Resource ID (cloud ID)")
    url: str = Field(..., description="Resource URL")
    name: str = Field(..., description="Resource name")
    scopes: List[str] = Field(..., description="Available scopes")
    avatarUrl: str = Field(..., description="Resource avatar URL")


class AccessibleResourcesResponse(BaseModel):
    """Response model for accessible resources endpoint"""
    success: bool = Field(True, description="Whether the request was successful")
    resources: List[ResourceInfo] = Field(..., description="List of accessible resources")
