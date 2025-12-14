"""
MPIS Genesis API - Audit Service

Handles audit logging for major system events.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.persona import AuditLog


class AuditService:
    """Service for audit logging."""
    
    # Event types for Genesis flow
    SOURCES_DISCOVERED = "sources.discovered"
    SOURCES_FETCHED = "sources.fetched"
    CORPUS_CHUNKED = "corpus.chunked"
    EMBEDDINGS_UPSERTED = "embeddings.upserted"
    CONCEPTS_EXTRACTED = "concepts.extracted"
    DRAFT_GENERATED = "draft.generated"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPLIED = "approval.applied"
    PERSONA_COMMITTED = "persona.committed"
    EXPORT_COMPLETED = "export.completed"
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
    
    async def log(
        self,
        event_type: str,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        job_id: Optional[UUID] = None,
        details: Optional[dict] = None
    ) -> AuditLog:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (e.g., 'sources.discovered')
            entity_type: Type of entity involved (e.g., 'persona', 'source')
            entity_id: ID of the entity
            job_id: Genesis job ID if applicable
            details: Additional event details
            
        Returns:
            Created AuditLog entry
        """
        log_entry = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            job_id=job_id,
            details=details or {}
        )
        
        self.db.add(log_entry)
        await self.db.flush()
        
        return log_entry
    
    async def get_job_logs(self, job_id: UUID) -> list[AuditLog]:
        """
        Get all audit logs for a specific job.
        
        Args:
            job_id: Genesis job ID
            
        Returns:
            List of AuditLog entries ordered by creation time
        """
        result = await self.db.execute(
            select(AuditLog)
            .where(AuditLog.job_id == job_id)
            .order_by(AuditLog.created_at)
        )
        return list(result.scalars().all())
