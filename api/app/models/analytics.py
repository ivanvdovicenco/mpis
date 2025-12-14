"""
MPIS Analytics API - Analytics Module Models

SQLAlchemy models for analytics and EIDOS recommendations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AnalyticsRollup(Base):
    """Computed analytics summaries by time period."""
    __tablename__ = "analytics_rollups"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    rollup_type: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[datetime] = mapped_column(nullable=False)
    period_end: Mapped[datetime] = mapped_column(nullable=False)
    metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    insights: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint(
            "rollup_type IN ('daily', 'weekly', 'monthly')",
            name="analytics_rollups_type_check"
        ),
    )


class EidosRecommendation(Base):
    """AI-generated actionable recommendations from EIDOS engine."""
    __tablename__ = "eidos_recommendations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, default=uuid4)
    recommendations: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    experiments: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    content_briefs: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    computed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'reviewed', 'actioned', 'expired')",
            name="eidos_recommendations_status_check"
        ),
    )


class Experiment(Base):
    """A/B testing and content experiment tracking."""
    __tablename__ = "experiments"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    variants: Mapped[list] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    start_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    results: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'completed', 'cancelled')",
            name="experiments_status_check"
        ),
    )


class DashboardView(Base):
    """User-defined dashboard configurations."""
    __tablename__ = "dashboard_views"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=True
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    view_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
