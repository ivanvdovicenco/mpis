"""
MPIS Dashboard API - Dashboard Module Models

SQLAlchemy models for Dashboard system.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Integer, Numeric, Boolean, ForeignKey, CheckConstraint, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class DashboardProject(Base):
    """Dashboard project metadata with channel configurations."""
    __tablename__ = "dashboard_projects"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    channels: Mapped[list] = mapped_column(ARRAY(Text), nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    meta: Mapped[dict] = mapped_column("meta", JSONB, default=dict, nullable=False)
    
    # Relationships
    runs: Mapped[list["DashboardRun"]] = relationship(
        "DashboardRun", back_populates="project", cascade="all, delete-orphan"
    )


class DashboardRun(Base):
    """Dashboard run tracking with status aggregation including partial status."""
    __tablename__ = "dashboard_runs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, unique=True)
    project_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("dashboard_projects.id", ondelete="CASCADE"),
        nullable=False
    )
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    started_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    n8n_execution_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta: Mapped[dict] = mapped_column("meta", JSONB, default=dict, nullable=False)
    
    # Relationships
    project: Mapped["DashboardProject"] = relationship("DashboardProject", back_populates="runs")
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'running', 'success', 'failed', 'partial')",
            name="dashboard_runs_status_check"
        ),
    )


class DashboardLayout(Base):
    """User dashboard layout configurations."""
    __tablename__ = "dashboard_layouts"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False, default="My Dashboard")
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    layout_config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class WidgetRegistry(Base):
    """Registry of built-in and custom dashboard widgets."""
    __tablename__ = "widget_registry"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    widget_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    widget_type: Mapped[str] = mapped_column(Text, nullable=False)
    schema: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    renderer_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        CheckConstraint(
            "widget_type IN ('builtin', 'custom')",
            name="widget_registry_type_check"
        ),
    )


class RedFlag(Base):
    """Critical system issues requiring attention."""
    __tablename__ = "red_flags"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    flag_type: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    resolved_by: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    __table_args__ = (
        CheckConstraint(
            "severity IN ('warning', 'critical')",
            name="red_flags_severity_check"
        ),
    )


class MetricsIngestionJob(Base):
    """Scheduled jobs for periodic metrics collection."""
    __tablename__ = "metrics_ingestion_jobs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    persona_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=True
    )
    schedule_cron: Mapped[str] = mapped_column(Text, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


class NormalizedMetric(Base):
    """Normalized metrics across all channels."""
    __tablename__ = "normalized_metrics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    published_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("published_items.id", ondelete="CASCADE"),
        nullable=False
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Normalized metric fields
    views: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    impressions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reach: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reactions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    saves: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    clicks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Calculated fields
    engagement_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 4), nullable=True)
    
    # Raw data
    raw_metrics: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    
    # Metadata
    measured_at: Mapped[datetime] = mapped_column(nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="manual")
