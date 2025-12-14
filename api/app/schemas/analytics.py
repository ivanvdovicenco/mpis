"""
MPIS Analytics API - Analytics Module Schemas

Pydantic schemas for analytics and EIDOS API endpoints.
"""
from typing import List, Optional, Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# --- Analytics Schemas ---

class AnalyticsSummaryRequest(BaseModel):
    """Request for analytics summary."""
    persona_id: UUID = Field(..., description="Persona ID")
    range_type: Literal["7d", "30d", "90d", "all"] = Field(
        default="30d",
        description="Time range for analytics"
    )
    include_insights: bool = Field(default=True, description="Include AI-generated insights")


class MetricsSummary(BaseModel):
    """Summary of engagement metrics."""
    total_published: int = Field(default=0, description="Total items published")
    total_views: float = Field(default=0, description="Total views")
    total_reactions: float = Field(default=0, description="Total reactions")
    total_shares: float = Field(default=0, description="Total shares")
    engagement_rate: float = Field(default=0, description="Average engagement rate")
    best_performing_topics: List[str] = Field(default_factory=list, description="Top performing topics")
    best_performing_times: List[str] = Field(default_factory=list, description="Best posting times")


class AnalyticsSummaryResponse(BaseModel):
    """Response for analytics summary."""
    persona_id: UUID = Field(description="Persona ID")
    range_type: str = Field(description="Time range")
    period_start: datetime = Field(description="Period start")
    period_end: datetime = Field(description="Period end")
    metrics: MetricsSummary = Field(description="Metrics summary")
    insights: List[str] = Field(default_factory=list, description="AI-generated insights")
    trends: dict = Field(default_factory=dict, description="Trend data")


# --- Recompute Schemas ---

class RecomputeRequest(BaseModel):
    """Request to trigger analytics recomputation."""
    persona_id: UUID = Field(..., description="Persona ID")
    rollup_types: List[Literal["daily", "weekly", "monthly"]] = Field(
        default=["daily", "weekly"],
        description="Types of rollups to compute"
    )
    force: bool = Field(default=False, description="Force recomputation even if recent")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "persona_id": "550e8400-e29b-41d4-a716-446655440000",
            "rollup_types": ["daily", "weekly"],
            "force": False
        }
    })


class RecomputeResponse(BaseModel):
    """Response from recomputation request."""
    persona_id: UUID = Field(description="Persona ID")
    job_id: UUID = Field(description="Recomputation job ID")
    status: str = Field(default="started", description="Job status")
    message: str = Field(description="Status message")


# --- EIDOS Recommendation Schemas ---

class EidosRecommendationItem(BaseModel):
    """A single EIDOS recommendation."""
    id: int = Field(description="Recommendation number")
    title: str = Field(description="Short recommendation title")
    description: str = Field(description="Detailed description")
    priority: Literal["high", "medium", "low"] = Field(description="Priority level")
    category: str = Field(description="Category (content, timing, engagement, etc.)")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence")
    measurable_outcome: Optional[str] = Field(None, description="How to measure success")


class ContentBrief(BaseModel):
    """Ready-to-generate content brief."""
    topic: str = Field(description="Suggested topic")
    hook: str = Field(description="Suggested hook/title")
    key_points: List[str] = Field(default_factory=list, description="Key points to cover")
    target_channel: str = Field(description="Target channel")
    suggested_length: int = Field(description="Suggested length in characters")
    rationale: str = Field(description="Why this content is recommended")


class ExperimentSuggestion(BaseModel):
    """Suggested A/B experiment."""
    name: str = Field(description="Experiment name")
    hypothesis: str = Field(description="Hypothesis to test")
    variants: List[str] = Field(description="Variant descriptions")
    success_metric: str = Field(description="How to measure success")
    duration_days: int = Field(description="Suggested duration in days")


class EidosRecommendationsResponse(BaseModel):
    """Response for EIDOS recommendations."""
    persona_id: UUID = Field(description="Persona ID")
    run_id: UUID = Field(description="Recommendation run ID")
    computed_at: datetime = Field(description="Computation timestamp")
    recommendations: List[EidosRecommendationItem] = Field(
        default_factory=list,
        description="Top recommendations"
    )
    content_briefs: List[ContentBrief] = Field(
        default_factory=list,
        description="Ready-to-generate content briefs"
    )
    experiments: List[ExperimentSuggestion] = Field(
        default_factory=list,
        description="Suggested experiments"
    )
    status: str = Field(description="Recommendation status")


# --- Experiment Schemas ---

class ExperimentCreate(BaseModel):
    """Request to create an experiment."""
    persona_id: UUID = Field(..., description="Persona ID")
    name: str = Field(..., min_length=1, max_length=200, description="Experiment name")
    hypothesis: str = Field(..., description="Hypothesis to test")
    variants: List[dict] = Field(..., min_length=2, description="At least 2 variants")
    start_date: Optional[datetime] = Field(None, description="Planned start date")
    end_date: Optional[datetime] = Field(None, description="Planned end date")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "persona_id": "550e8400-e29b-41d4-a716-446655440000",
            "name": "CTA Style Test",
            "hypothesis": "Question-based CTAs increase engagement",
            "variants": [
                {"name": "control", "cta_style": "imperative"},
                {"name": "treatment", "cta_style": "question"}
            ],
            "start_date": "2025-01-15T00:00:00Z",
            "end_date": "2025-01-29T00:00:00Z"
        }
    })


class ExperimentResponse(BaseModel):
    """Response for an experiment."""
    id: UUID = Field(description="Experiment ID")
    persona_id: UUID = Field(description="Persona ID")
    name: str = Field(description="Experiment name")
    hypothesis: str = Field(description="Hypothesis")
    status: str = Field(description="Experiment status")
    variants: List[dict] = Field(description="Variants")
    results: dict = Field(default_factory=dict, description="Results if available")
    created_at: datetime = Field(description="Creation timestamp")


# --- Audit Event Types for Analytics Module ---
ANALYTICS_AUDIT_EVENTS = {
    "ROLLUP_COMPUTED": "analytics.rollup.computed",
    "EIDOS_GENERATED": "analytics.eidos.generated",
    "EXPERIMENT_CREATED": "analytics.experiment.created",
    "EXPERIMENT_COMPLETED": "analytics.experiment.completed",
}
