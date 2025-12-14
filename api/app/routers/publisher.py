"""
MPIS Publisher API - Publisher Router

API endpoints for content planning and publishing.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.publisher import (
    ContentPlanCreate,
    ContentPlanResponse,
    ContentGenerateRequest,
    ContentDraftResponse,
    DraftApproveRequest,
    DraftApproveResponse,
    PublishRecordRequest,
    PublishRecordResponse,
    MetricsIngestRequest,
    MetricsIngestResponse,
)
from app.services.publisher import PublisherService

router = APIRouter(prefix="/publisher", tags=["Publisher"])


@router.post(
    "/plan",
    response_model=ContentPlanResponse,
    summary="Create content plan",
    description="""
Create a content plan/calendar item.

Plans define:
- Topic and title
- Target channel and audience
- Scheduling windows
- Constraints (tone, length, forbidden topics)

After creating a plan, use `/publisher/generate` to create drafts.
"""
)
async def create_plan(
    request: ContentPlanCreate,
    db: AsyncSession = Depends(get_db)
) -> ContentPlanResponse:
    """Create a content plan."""
    try:
        service = PublisherService(db)
        return await service.create_plan(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plan creation failed: {str(e)}")


@router.post(
    "/generate",
    response_model=ContentDraftResponse,
    summary="Generate content draft",
    description="""
Generate content draft(s) for a plan.

Uses RAG to retrieve relevant persona knowledge and generates:
- Content text matching persona voice
- Optional title/hook
- Optional call-to-action
- Multiple variants (1-3)

Includes provenance tracking for source references.
"""
)
async def generate_content(
    request: ContentGenerateRequest,
    db: AsyncSession = Depends(get_db)
) -> ContentDraftResponse:
    """Generate content draft."""
    try:
        service = PublisherService(db)
        return await service.generate_content(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Content generation failed: {str(e)}")


@router.get(
    "/draft/{draft_id}",
    response_model=ContentDraftResponse,
    summary="Get content draft",
    description="""
Get a content draft by ID.

Returns the draft variants, status, and provenance information.
"""
)
async def get_draft(
    draft_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> ContentDraftResponse:
    """Get content draft."""
    try:
        service = PublisherService(db)
        return await service.get_draft(draft_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/approve",
    response_model=DraftApproveResponse,
    summary="Approve content draft",
    description="""
Approve a content draft.

**Options:**
- `confirm: true` - Approve the draft for publishing
- `selected_variant` - Which variant to use (1-3)
- `edits` - Optional edits to apply before approval

After approval, use n8n or `/publisher/publish/record` to record the publish.
"""
)
async def approve_draft(
    request: DraftApproveRequest,
    db: AsyncSession = Depends(get_db)
) -> DraftApproveResponse:
    """Approve content draft."""
    try:
        service = PublisherService(db)
        return await service.approve_draft(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/publish/record",
    response_model=PublishRecordResponse,
    summary="Record publish result",
    description="""
Record the result of publishing content.

Called by n8n or external systems after publishing to record:
- Channel and channel item ID
- Published URL
- Publish payload
- Persona version used

This enables metrics tracking and analytics.
"""
)
async def record_publish(
    request: PublishRecordRequest,
    db: AsyncSession = Depends(get_db)
) -> PublishRecordResponse:
    """Record publish result."""
    try:
        service = PublisherService(db)
        return await service.record_publish(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publish record failed: {str(e)}")


@router.post(
    "/metrics/ingest",
    response_model=MetricsIngestResponse,
    summary="Ingest metrics",
    description="""
Ingest metrics for a published item.

Metrics can include:
- views, reactions, comments, shares
- clicks, retention proxies
- Any custom metrics

Source can be 'manual', 'api', 'webhook', etc.
"""
)
async def ingest_metrics(
    request: MetricsIngestRequest,
    db: AsyncSession = Depends(get_db)
) -> MetricsIngestResponse:
    """Ingest metrics."""
    try:
        service = PublisherService(db)
        return await service.ingest_metrics(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metrics ingestion failed: {str(e)}")
