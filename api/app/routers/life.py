"""
MPIS Life API - Life Router

API endpoints for persona life management.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.life import (
    LifeEventCreate,
    LifeEventResponse,
    CycleStartRequest,
    CycleStartResponse,
    CycleStatusResponse,
    CycleApproveRequest,
    CycleApproveResponse,
)
from app.services.life import LifeService

router = APIRouter(prefix="/life", tags=["Life"])


@router.post(
    "/event",
    response_model=LifeEventResponse,
    summary="Ingest life event",
    description="""
Ingest a life event for a persona.

Events can be:
- **conversation**: Snippets from user interactions
- **note**: User notes or observations
- **journal**: Ministry/leadership journaling
- **decision**: Recorded decisions
- **outcome**: Decision outcomes

Events are used for reflection cycles and persona evolution.
"""
)
async def ingest_event(
    request: LifeEventCreate,
    db: AsyncSession = Depends(get_db)
) -> LifeEventResponse:
    """Ingest a life event."""
    try:
        service = LifeService(db)
        return await service.ingest_event(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Event ingestion failed: {str(e)}")


@router.post(
    "/cycle/start",
    response_model=CycleStartResponse,
    summary="Start reflection cycle",
    description="""
Start a reflection cycle for a persona.

Cycle types:
- **daily**: Reviews last 24 hours of events
- **weekly**: Reviews last 7 days of events
- **manual**: Triggered manually with custom options

The cycle will:
1. Collect recent events
2. Retrieve relevant persona knowledge (RAG)
3. Generate a reflection summary
4. Create a draft for approval
"""
)
async def start_cycle(
    request: CycleStartRequest,
    db: AsyncSession = Depends(get_db)
) -> CycleStartResponse:
    """Start a reflection cycle."""
    try:
        service = LifeService(db)
        return await service.start_cycle(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cycle start failed: {str(e)}")


@router.get(
    "/cycle/status/{cycle_id}",
    response_model=CycleStatusResponse,
    summary="Get cycle status",
    description="""
Get the current status of a reflection cycle.

Returns progress, draft content (if available), and any errors.
"""
)
async def get_cycle_status(
    cycle_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> CycleStatusResponse:
    """Get cycle status."""
    try:
        service = LifeService(db)
        return await service.get_cycle_status(cycle_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/cycle/approve",
    response_model=CycleApproveResponse,
    summary="Approve reflection cycle",
    description="""
Approve a reflection cycle.

**Options:**
- `confirm: true` - Commit the reflection and export files
- `apply_adjustments: true` - Apply suggested persona_core adjustments

If `apply_adjustments` is true, a new persona version will be created.
"""
)
async def approve_cycle(
    request: CycleApproveRequest,
    db: AsyncSession = Depends(get_db)
) -> CycleApproveResponse:
    """Approve a reflection cycle."""
    try:
        service = LifeService(db)
        return await service.approve_cycle(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
