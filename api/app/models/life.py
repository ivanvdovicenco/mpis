"""
MPIS Life API - Life Module Models

SQLAlchemy models for persona life tracking.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Integer, Numeric, ForeignKey, CheckConstraint, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, TIMESTAMP
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class LifeEvent(Base):
    """Life events for persona evolution tracking."""
    __tablename__ = "life_events"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    run_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    meta: Mapped[dict] = mapped_column("meta", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


class LifeCycle(Base):
    """Reflection cycle job tracking."""
    __tablename__ = "life_cycles"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    cycle_type: Mapped[str] = mapped_column(String(20), nullable=False, default="daily")
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, default=uuid4)
    options: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    
    # Relationships
    drafts: Mapped[list["LifeCycleDraft"]] = relationship(
        "LifeCycleDraft", back_populates="cycle", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'processing', 'awaiting_approval', 'committed', 'failed')",
            name="life_cycles_status_check"
        ),
        CheckConstraint(
            "cycle_type IN ('daily', 'weekly', 'manual')",
            name="life_cycles_type_check"
        ),
    )


class LifeCycleDraft(Base):
    """Draft outputs from reflection cycles."""
    __tablename__ = "life_cycle_drafts"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    cycle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("life_cycles.id", ondelete="CASCADE"),
        nullable=False
    )
    draft_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    cycle: Mapped["LifeCycle"] = relationship("LifeCycle", back_populates="drafts")


class LifeMetric(Base):
    """Computed persona metrics over time periods."""
    __tablename__ = "life_metrics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    metric_key: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    period_start: Mapped[datetime] = mapped_column(nullable=False)
    period_end: Mapped[datetime] = mapped_column(nullable=False)
    computed_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


class Recommendation(Base):
    """AI-generated recommendations from various sources."""
    __tablename__ = "recommendations"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    rec_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint(
            "source IN ('life', 'publisher', 'analytics', 'eidos')",
            name="recommendations_source_check"
        ),
        CheckConstraint(
            "status IN ('pending', 'accepted', 'rejected', 'expired')",
            name="recommendations_status_check"
        ),
    )
