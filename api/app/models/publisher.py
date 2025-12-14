"""
MPIS Publisher API - Publisher Module Models

SQLAlchemy models for content planning and publishing.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Integer, Numeric, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ContentPlan(Base):
    """Content calendar and planning for social publishing."""
    __tablename__ = "content_plans"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(Text, nullable=False)
    goal: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    target_audience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    max_length: Mapped[Optional[int]] = mapped_column(Integer, default=1000)
    schedule_window_start: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    schedule_window_end: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    constraints: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")
    run_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    meta: Mapped[dict] = mapped_column("meta", JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    drafts: Mapped[list["ContentDraft"]] = relationship(
        "ContentDraft", back_populates="plan", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('planned', 'generating', 'draft_ready', 'approved', 'scheduled', 'published', 'cancelled')",
            name="content_plans_status_check"
        ),
    )


class ContentDraft(Base):
    """Generated content drafts with provenance tracking."""
    __tablename__ = "content_drafts"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("content_plans.id", ondelete="CASCADE"),
        nullable=False
    )
    persona_version_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("persona_versions.id", ondelete="SET NULL"),
        nullable=True
    )
    draft_no: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    content_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    run_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    plan: Mapped["ContentPlan"] = relationship("ContentPlan", back_populates="drafts")
    published_items: Mapped[list["PublishedItem"]] = relationship(
        "PublishedItem", back_populates="draft", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'approved', 'rejected')",
            name="content_drafts_status_check"
        ),
    )


class PublishedItem(Base):
    """Records of published content with channel identifiers."""
    __tablename__ = "published_items"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    draft_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("content_drafts.id", ondelete="CASCADE"),
        nullable=False
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    channel_item_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    channel_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_payload: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    published_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    persona_version_used: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    meta: Mapped[dict] = mapped_column("meta", JSONB, default=dict, nullable=False)
    
    # Relationships
    draft: Mapped["ContentDraft"] = relationship("ContentDraft", back_populates="published_items")
    metrics: Mapped[list["ItemMetric"]] = relationship(
        "ItemMetric", back_populates="published_item", cascade="all, delete-orphan"
    )


class ChannelAccount(Base):
    """Channel account configuration per persona."""
    __tablename__ = "channel_accounts"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    channel: Mapped[str] = mapped_column(Text, nullable=False)
    account_id: Mapped[str] = mapped_column(Text, nullable=False)
    account_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)


class ItemMetric(Base):
    """Metrics collected for published content items."""
    __tablename__ = "item_metrics"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    published_item_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("published_items.id", ondelete="CASCADE"),
        nullable=False
    )
    metric_type: Mapped[str] = mapped_column(Text, nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    source: Mapped[str] = mapped_column(Text, default="manual", nullable=False)
    meta: Mapped[dict] = mapped_column("meta", JSONB, default=dict, nullable=False)
    
    # Relationships
    published_item: Mapped["PublishedItem"] = relationship("PublishedItem", back_populates="metrics")
