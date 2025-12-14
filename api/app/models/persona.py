"""
MPIS Genesis API - Persona Models

SQLAlchemy models for persona-related tables.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlalchemy import String, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Persona(Base):
    """Core persona entity."""
    __tablename__ = "personas"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="en", nullable=False)
    active_version: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    versions: Mapped[list["PersonaVersion"]] = relationship(
        "PersonaVersion", back_populates="persona", cascade="all, delete-orphan"
    )
    sources: Mapped[list["Source"]] = relationship(
        "Source", back_populates="persona"
    )


class PersonaVersion(Base):
    """Versioned persona core configurations."""
    __tablename__ = "persona_versions"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="CASCADE"),
        nullable=False
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    core_json: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    persona: Mapped["Persona"] = relationship("Persona", back_populates="versions")


class Source(Base):
    """Source materials used to generate personas."""
    __tablename__ = "sources"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    persona_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("personas.id", ondelete="SET NULL"),
        nullable=True
    )
    job_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("genesis_jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    source_ref: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    extracted_text_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
    
    # Relationships
    persona: Mapped[Optional["Persona"]] = relationship("Persona", back_populates="sources")
    
    __table_args__ = (
        CheckConstraint(
            "source_type IN ('youtube', 'file', 'url', 'text')",
            name="sources_type_check"
        ),
    )


class AuditLog(Base):
    """Audit trail for all major system events."""
    __tablename__ = "audit_log"
    
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    entity_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    entity_id: Mapped[Optional[UUID]] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    job_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("genesis_jobs.id", ondelete="SET NULL"),
        nullable=True
    )
    details: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, nullable=False)
