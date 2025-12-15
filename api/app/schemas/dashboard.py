"""
MPIS Dashboard API - Dashboard Module Schemas

Pydantic schemas for Dashboard module API endpoints.
"""
from typing import List, Optional, Any, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- Dashboard Project Schemas ---

class DashboardProjectCreate(BaseModel):
    """Request to create a dashboard project."""
    name: str = Field(..., min_length=1, max_length=200, description="Project name")
    persona_id: UUID = Field(..., description="Persona ID")
    channels: List[str] = Field(..., description="Target channels")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Tech Blog Project",
            "persona_id": "550e8400-e29b-41d4-a716-446655440000",
            "channels": ["telegram", "instagram"]
        }
    })


class DashboardProjectResponse(BaseModel):
    """Response for a dashboard project."""
    id: UUID = Field(description="Project ID")
    name: str = Field(description="Project name")
    persona_id: UUID = Field(description="Persona ID")
    channels: List[str] = Field(description="Target channels")
    created_at: datetime = Field(description="Creation timestamp")


# --- Dashboard Run Schemas ---

class DashboardRunCreate(BaseModel):
    """Request to create a dashboard run."""
    project_id: UUID = Field(..., description="Dashboard project ID")
    persona_id: UUID = Field(..., description="Persona ID")
    channels: List[str] = Field(..., description="Target channels")
    date_from: str = Field(..., description="Content search start date (YYYY-MM-DD)")
    date_to: str = Field(..., description="Content search end date (YYYY-MM-DD)")
    templates: Optional[dict] = Field(None, description="Template IDs")
    options: Optional[dict] = Field(None, description="Run options")


class DashboardRunResponse(BaseModel):
    """Response for a dashboard run."""
    id: UUID = Field(description="Dashboard run ID")
    run_id: UUID = Field(description="MPIS run ID")
    project_id: UUID = Field(description="Dashboard project ID")
    persona_id: UUID = Field(description="Persona ID")
    status: str = Field(description="Run status (pending/running/success/failed/partial)")
    started_at: datetime = Field(description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
    n8n_execution_id: Optional[UUID] = Field(None, description="n8n execution ID")
    error_message: Optional[str] = Field(None, description="Error message if failed")


class DashboardRunCompleteRequest(BaseModel):
    """Request to complete a dashboard run (from n8n)."""
    run_id: UUID = Field(..., description="Run ID")
    status: Literal["success", "failed"] = Field(..., description="MPIS status")
    persona_id: UUID = Field(..., description="Persona ID")
    project_id: UUID = Field(..., description="Dashboard project ID")
    n8n_execution_id: UUID = Field(..., description="n8n execution ID")
    error: Optional[str] = Field(None, description="Error message")
    published_items: List[dict] = Field(default_factory=list, description="Published items")


# --- Publish Record Proxy Schemas ---

class PublishRecordProxyRequest(BaseModel):
    """Dashboard proxy request for publish record (transforms before forwarding to MPIS)."""
    draft_id: UUID = Field(..., description="Draft ID")
    channel: str = Field(..., description="Channel name")
    channel_item_id: str = Field(..., description="Channel item ID")
    channel_url: Optional[str] = Field(None, description="Channel URL")
    # Dashboard stores run_id, project_id, published_at locally
    # These are NOT sent to MPIS


class PublishRecordProxyResponse(BaseModel):
    """Response from dashboard publish record proxy."""
    published_item_id: UUID = Field(description="Published item ID from MPIS")
    status: str = Field(description="Record status")


# --- Dashboard Layout Schemas ---

class DashboardLayoutCreate(BaseModel):
    """Request to create a dashboard layout."""
    name: str = Field(..., min_length=1, max_length=200, description="Layout name")
    user_id: Optional[UUID] = Field(None, description="User ID (nullable for default)")
    is_default: bool = Field(default=False, description="Is default layout")
    layout_config: dict = Field(..., description="Layout configuration")


class DashboardLayoutResponse(BaseModel):
    """Response for a dashboard layout."""
    id: UUID = Field(description="Layout ID")
    user_id: Optional[UUID] = Field(description="User ID")
    name: str = Field(description="Layout name")
    is_default: bool = Field(description="Is default layout")
    layout_config: dict = Field(description="Layout configuration")
    created_at: datetime = Field(description="Creation timestamp")


# --- Widget Schemas ---

class WidgetRegisterRequest(BaseModel):
    """Request to register a widget."""
    widget_id: str = Field(..., description="Unique widget ID")
    name: str = Field(..., description="Widget name")
    description: Optional[str] = Field(None, description="Widget description")
    widget_type: Literal["builtin", "custom"] = Field(..., description="Widget type")
    schema: dict = Field(..., description="Widget schema")
    renderer_url: Optional[str] = Field(None, description="Renderer URL for custom widgets")


class WidgetResponse(BaseModel):
    """Response for a widget."""
    id: UUID = Field(description="Widget ID")
    widget_id: str = Field(description="Unique widget ID")
    name: str = Field(description="Widget name")
    description: Optional[str] = Field(description="Widget description")
    widget_type: str = Field(description="Widget type")
    schema: dict = Field(description="Widget schema")
    renderer_url: Optional[str] = Field(description="Renderer URL")


# --- Red Flags Schemas ---

class RedFlagResponse(BaseModel):
    """Response for a red flag."""
    id: UUID = Field(description="Red flag ID")
    flag_type: str = Field(description="Flag type")
    severity: str = Field(description="Severity level")
    description: Optional[str] = Field(description="Description")
    metadata: dict = Field(description="Additional metadata")
    created_at: datetime = Field(description="Creation timestamp")
    resolved_at: Optional[datetime] = Field(description="Resolution timestamp")


class RedFlagsSummaryResponse(BaseModel):
    """Response for red flags summary."""
    failed_runs: dict = Field(description="Failed runs statistics")
    missing_metrics: dict = Field(description="Missing metrics statistics")
    missing_publish_records: dict = Field(description="Missing publish records statistics")


# --- Metrics Ingestion Schemas ---

class MetricsIngestionJobCreate(BaseModel):
    """Request to create a metrics ingestion job."""
    job_name: str = Field(..., description="Job name")
    channel: str = Field(..., description="Channel name")
    persona_id: Optional[UUID] = Field(None, description="Persona ID")
    schedule_cron: str = Field(..., description="Cron schedule")
    config: dict = Field(default_factory=dict, description="Job configuration")


class MetricsIngestionJobResponse(BaseModel):
    """Response for a metrics ingestion job."""
    id: UUID = Field(description="Job ID")
    job_name: str = Field(description="Job name")
    channel: str = Field(description="Channel name")
    persona_id: Optional[UUID] = Field(description="Persona ID")
    schedule_cron: str = Field(description="Cron schedule")
    last_run_at: Optional[datetime] = Field(description="Last run timestamp")
    next_run_at: Optional[datetime] = Field(description="Next run timestamp")
    enabled: bool = Field(description="Is enabled")


class NormalizedMetricsResponse(BaseModel):
    """Response for normalized metrics."""
    id: UUID = Field(description="Metric ID")
    published_item_id: UUID = Field(description="Published item ID")
    channel: str = Field(description="Channel name")
    views: Optional[int] = Field(description="Views")
    impressions: Optional[int] = Field(description="Impressions")
    reach: Optional[int] = Field(description="Reach")
    reactions: Optional[int] = Field(description="Reactions")
    comments: Optional[int] = Field(description="Comments")
    shares: Optional[int] = Field(description="Shares")
    saves: Optional[int] = Field(description="Saves")
    clicks: Optional[int] = Field(description="Clicks")
    engagement_rate: Optional[float] = Field(description="Engagement rate")
    measured_at: datetime = Field(description="Measurement timestamp")


# --- AI Analyst Schemas ---

class AIAnalystQueryRequest(BaseModel):
    """Request to query AI analyst."""
    persona_id: UUID = Field(..., description="Persona ID")
    time_range: str = Field(..., description="Time range (7d, 30d, 90d)")
    question: str = Field(..., description="Analysis question")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "persona_id": "550e8400-e29b-41d4-a716-446655440000",
            "time_range": "30d",
            "question": "What are the best performing content topics?"
        }
    })


class AIAnalystCitation(BaseModel):
    """Citation for AI analyst response."""
    published_item_id: UUID = Field(description="Published item ID")
    channel: str = Field(description="Channel")
    published_at: datetime = Field(description="Published at")
    metrics: dict = Field(description="Metrics")


class AIAnalystQueryResponse(BaseModel):
    """Response from AI analyst query."""
    answer: str = Field(description="Analysis answer")
    citations: List[AIAnalystCitation] = Field(description="Citations/post list")
    suggested_actions: List[str] = Field(description="Suggested actions/experiments")
    confidence: float = Field(description="Confidence score (0.0-1.0)")


# --- Persona Flow Schemas ---

class PersonaCreateRequest(BaseModel):
    """Request to create a persona (Dashboard proxy to Genesis)."""
    persona_name: str = Field(..., description="Persona name")
    language: str = Field(default="en", description="Language")
    inspiration_source: Optional[str] = Field(None, description="Inspiration source")
    public_persona: bool = Field(default=False, description="Is public persona")
    public_name: Optional[str] = Field(None, description="Public name")
    gdrive_folder_id: Optional[str] = Field(None, description="Google Drive folder ID")
    sources: List[str] = Field(default_factory=list, description="Source URLs")
    notes: Optional[str] = Field(None, description="Additional notes")


class PersonaStatusResponse(BaseModel):
    """Response for persona status (from Genesis)."""
    job_id: UUID = Field(description="Job ID")
    status: str = Field(description="Job status")
    progress: dict = Field(description="Progress information")
