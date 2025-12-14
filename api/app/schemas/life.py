"""
MPIS Life API - Life Module Schemas

Pydantic schemas for life module API endpoints.
"""
from typing import List, Optional, Any, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- Event Schemas ---

class LifeEventCreate(BaseModel):
    """Request to create a new life event."""
    persona_id: UUID = Field(..., description="Persona ID")
    event_type: str = Field(..., description="Type of event (conversation, note, decision, outcome, journal)")
    content: str = Field(..., min_length=1, description="Event content")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    meta: dict = Field(default_factory=dict, description="Additional metadata")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "persona_id": "550e8400-e29b-41d4-a716-446655440000",
            "event_type": "conversation",
            "content": "User asked about dealing with grief and loss",
            "tags": ["grief", "pastoral", "question"],
            "meta": {"source": "telegram", "user_id": "123"}
        }
    })


class LifeEventResponse(BaseModel):
    """Response for a created life event."""
    id: UUID = Field(description="Event ID")
    persona_id: UUID = Field(description="Persona ID")
    event_type: str = Field(description="Event type")
    content: str = Field(description="Event content")
    tags: List[str] = Field(default_factory=list)
    run_id: Optional[UUID] = Field(None, description="Run ID for tracing")
    created_at: datetime = Field(description="Creation timestamp")


# --- Cycle Schemas ---

class CycleStartRequest(BaseModel):
    """Request to start a reflection cycle."""
    persona_id: UUID = Field(..., description="Persona ID")
    cycle_type: Literal["daily", "weekly", "manual"] = Field(
        default="manual", 
        description="Type of reflection cycle"
    )
    options: dict = Field(default_factory=dict, description="Cycle options (lookback_days, focus_topics, etc.)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "persona_id": "550e8400-e29b-41d4-a716-446655440000",
            "cycle_type": "daily",
            "options": {"lookback_days": 1, "max_events": 50}
        }
    })


class ReflectionSummary(BaseModel):
    """Reflection summary output."""
    summary: str = Field(description="Short actionable summary")
    key_insights: List[str] = Field(default_factory=list, description="Key insights from the period")
    suggested_adjustments: List[dict] = Field(
        default_factory=list, 
        description="Suggested persona_core adjustments"
    )
    next_actions: List[str] = Field(default_factory=list, description="Suggested next actions")
    staleness_alerts: List[dict] = Field(
        default_factory=list, 
        description="Alerts about stale or contradictory information"
    )


class CycleStartResponse(BaseModel):
    """Response from starting a reflection cycle."""
    cycle_id: UUID = Field(description="Cycle job ID")
    run_id: UUID = Field(description="Run ID for tracing")
    status: str = Field(description="Cycle status")
    message: str = Field(default="Cycle started", description="Status message")


class CycleStatusResponse(BaseModel):
    """Response for cycle status query."""
    cycle_id: UUID = Field(description="Cycle ID")
    persona_id: UUID = Field(description="Persona ID")
    status: str = Field(description="Current status")
    cycle_type: str = Field(description="Cycle type")
    started_at: datetime = Field(description="Start timestamp")
    finished_at: Optional[datetime] = Field(None, description="Finish timestamp")
    draft: Optional[ReflectionSummary] = Field(None, description="Draft output if available")


class CycleApproveRequest(BaseModel):
    """Request to approve a reflection cycle."""
    cycle_id: UUID = Field(..., description="Cycle ID")
    confirm: bool = Field(default=False, description="Confirm to commit changes")
    apply_adjustments: bool = Field(
        default=False, 
        description="Apply suggested persona_core adjustments"
    )
    edits: dict = Field(default_factory=dict, description="Edits to the draft before committing")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "cycle_id": "550e8400-e29b-41d4-a716-446655440000",
            "confirm": True,
            "apply_adjustments": False,
            "edits": {}
        }
    })


class CycleApproveResponse(BaseModel):
    """Response from approving a cycle."""
    cycle_id: UUID = Field(description="Cycle ID")
    status: str = Field(description="New status")
    persona_version: Optional[str] = Field(None, description="New persona version if adjustments applied")
    export_paths: Optional[dict] = Field(None, description="Export paths for generated files")
    message: str = Field(description="Status message")


# --- Metrics Schemas ---

class LifeMetricResponse(BaseModel):
    """Response for a life metric."""
    id: UUID = Field(description="Metric ID")
    persona_id: UUID = Field(description="Persona ID")
    metric_key: str = Field(description="Metric key")
    metric_value: float = Field(description="Metric value")
    period_start: datetime = Field(description="Period start")
    period_end: datetime = Field(description="Period end")
    computed_at: datetime = Field(description="Computation timestamp")


# --- Audit Event Types for Life Module ---
LIFE_AUDIT_EVENTS = {
    "EVENT_INGESTED": "life.event.ingested",
    "CYCLE_STARTED": "life.cycle.started",
    "CYCLE_DRAFT_CREATED": "life.cycle.draft.created",
    "CYCLE_COMMITTED": "life.cycle.committed",
    "CYCLE_FAILED": "life.cycle.failed",
    "METRICS_COMPUTED": "life.metrics.computed",
}
