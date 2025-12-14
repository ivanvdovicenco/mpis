"""
MPIS Genesis API - Genesis Models

SQLAlchemy models for the genesis workflow tables.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, Integer, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class GenesisJob(Base):
    """Genesis job tracking table."""
    __tablename__ = "genesis_jobs"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    input_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    config_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="queued",
    )
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    persona_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True
    )
    draft_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    drafts: Mapped[list["GenesisDraft"]] = relationship(
        "GenesisDraft", back_populates="job", cascade="all, delete-orphan"
    )
    messages: Mapped[list["GenesisMessage"]] = relationship(
        "GenesisMessage", back_populates="job", cascade="all, delete-orphan"
    )
    
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued', 'collecting', 'processing', 'awaiting_approval', 'committed', 'failed', 'committed_with_memory_pending')",
            name="genesis_jobs_status_check"
        ),
    )


class GenesisDraft(Base):
    """Genesis draft versions table."""
    __tablename__ = "genesis_drafts"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("genesis_jobs.id", ondelete="CASCADE"),
        nullable=False
    )
    draft_no: Mapped[int] = mapped_column(Integer, nullable=False)
    draft_core_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    human_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    job: Mapped["GenesisJob"] = relationship("GenesisJob", back_populates="drafts")


class GenesisMessage(Base):
    """Genesis conversation messages table."""
    __tablename__ = "genesis_messages"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    job_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("genesis_jobs.id", ondelete="CASCADE"),
        nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    job: Mapped["GenesisJob"] = relationship("GenesisJob", back_populates="messages")
    
    __table_args__ = (
        CheckConstraint(
            "role IN ('system', 'assistant', 'user')",
            name="genesis_messages_role_check"
        ),
    )
