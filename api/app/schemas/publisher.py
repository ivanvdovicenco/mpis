"""
MPIS Publisher API - Publisher Module Schemas

Pydantic schemas for publisher module API endpoints.
"""
from typing import List, Optional, Any, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- Plan Schemas ---

class ContentPlanCreate(BaseModel):
    """Request to create a content plan."""
    persona_id: UUID = Field(..., description="Persona ID")
    title: str = Field(..., min_length=1, max_length=200, description="Content title")
    topic: str = Field(..., description="Content topic")
    goal: Optional[str] = Field(None, description="Content goal (inform, engage, convert, etc.)")
    target_audience: Optional[str] = Field(None, description="Target audience description")
    channel: str = Field(..., description="Publishing channel (telegram, email, web, etc.)")
    language: str = Field(default="en", description="Content language")
    max_length: int = Field(default=1000, ge=50, le=10000, description="Maximum content length")
    schedule_window_start: Optional[datetime] = Field(None, description="Earliest publish time")
    schedule_window_end: Optional[datetime] = Field(None, description="Latest publish time")
    constraints: dict = Field(default_factory=dict, description="Additional constraints")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "persona_id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "Finding Hope in Uncertainty",
            "topic": "faith during difficult times",
            "goal": "encourage",
            "target_audience": "believers facing challenges",
            "channel": "telegram",
            "language": "en",
            "max_length": 800,
            "constraints": {
                "tone": ["hopeful", "pastoral"],
                "forbidden_topics": [],
                "scripture_allowed": True
            }
        }
    })


class ContentPlanResponse(BaseModel):
    """Response for a content plan."""
    id: UUID = Field(description="Plan ID")
    persona_id: UUID = Field(description="Persona ID")
    title: str = Field(description="Content title")
    topic: str = Field(description="Content topic")
    channel: str = Field(description="Publishing channel")
    status: str = Field(description="Plan status")
    created_at: datetime = Field(description="Creation timestamp")


# --- Draft Schemas ---

class ContentGenerateRequest(BaseModel):
    """Request to generate content draft."""
    plan_id: UUID = Field(..., description="Plan ID to generate content for")
    variants: int = Field(default=1, ge=1, le=3, description="Number of variants to generate")
    options: dict = Field(default_factory=dict, description="Generation options")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "plan_id": "550e8400-e29b-41d4-a716-446655440000",
            "variants": 2,
            "options": {"use_rag": True, "include_cta": True}
        }
    })


class ContentVariant(BaseModel):
    """A content variant."""
    variant_no: int = Field(description="Variant number")
    text: str = Field(description="Main content text")
    title: Optional[str] = Field(None, description="Title/hook")
    cta: Optional[str] = Field(None, description="Call to action")


class ContentDraftResponse(BaseModel):
    """Response for a content draft."""
    id: UUID = Field(description="Draft ID")
    plan_id: UUID = Field(description="Plan ID")
    draft_no: int = Field(description="Draft number")
    status: str = Field(description="Draft status")
    variants: List[ContentVariant] = Field(default_factory=list, description="Generated variants")
    provenance: dict = Field(default_factory=dict, description="Source references")
    created_at: datetime = Field(description="Creation timestamp")


class DraftApproveRequest(BaseModel):
    """Request to approve a content draft."""
    draft_id: UUID = Field(..., description="Draft ID")
    selected_variant: int = Field(default=1, ge=1, le=3, description="Selected variant number")
    edits: dict = Field(default_factory=dict, description="Edits to apply before approval")
    confirm: bool = Field(default=False, description="Confirm approval")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "draft_id": "550e8400-e29b-41d4-a716-446655440000",
            "selected_variant": 1,
            "edits": {"text": "Slightly modified text..."},
            "confirm": True
        }
    })


class DraftApproveResponse(BaseModel):
    """Response from approving a draft."""
    draft_id: UUID = Field(description="Draft ID")
    status: str = Field(description="New status")
    plan_status: str = Field(description="Updated plan status")
    ready_to_publish: bool = Field(description="Whether draft is ready to publish")


# --- Publish Schemas ---

class PublishRecordRequest(BaseModel):
    """Request to record a publish result."""
    draft_id: UUID = Field(..., description="Draft ID that was published")
    channel: str = Field(..., description="Channel published to")
    channel_item_id: Optional[str] = Field(None, description="Channel's item ID (e.g., message_id)")
    channel_url: Optional[str] = Field(None, description="URL to published content")
    published_payload: dict = Field(default_factory=dict, description="Full publish payload")
    persona_version_used: Optional[str] = Field(None, description="Persona version at publish time")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "draft_id": "550e8400-e29b-41d4-a716-446655440000",
            "channel": "telegram",
            "channel_item_id": "12345",
            "channel_url": "https://t.me/channel/12345",
            "published_payload": {"text": "...", "chat_id": "-100..."},
            "persona_version_used": "1.0"
        }
    })


class PublishRecordResponse(BaseModel):
    """Response from recording a publish."""
    id: UUID = Field(description="Published item ID")
    draft_id: UUID = Field(description="Draft ID")
    channel: str = Field(description="Channel")
    published_at: datetime = Field(description="Publish timestamp")


# --- Metrics Schemas ---

class MetricsIngestRequest(BaseModel):
    """Request to ingest metrics for a published item."""
    published_item_id: UUID = Field(..., description="Published item ID")
    metrics: List[dict] = Field(..., description="Metrics to ingest")
    source: str = Field(default="manual", description="Metrics source (manual, api, webhook)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "published_item_id": "550e8400-e29b-41d4-a716-446655440000",
            "metrics": [
                {"type": "views", "value": 1500},
                {"type": "reactions", "value": 45},
                {"type": "shares", "value": 12}
            ],
            "source": "telegram_api"
        }
    })


class MetricsIngestResponse(BaseModel):
    """Response from ingesting metrics."""
    published_item_id: UUID = Field(description="Published item ID")
    metrics_ingested: int = Field(description="Number of metrics ingested")
    recorded_at: datetime = Field(description="Recording timestamp")


# --- Audit Event Types for Publisher Module ---
PUBLISHER_AUDIT_EVENTS = {
    "PLAN_CREATED": "publisher.plan.created",
    "DRAFT_GENERATED": "publisher.draft.generated",
    "DRAFT_APPROVED": "publisher.draft.approved",
    "CONTENT_PUBLISHED": "publisher.content.published",
    "METRICS_INGESTED": "publisher.metrics.ingested",
}
