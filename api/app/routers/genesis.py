"""
MPIS Genesis API - Genesis Router

API endpoints for persona generation workflow.
"""
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.genesis import (
    GenesisStartRequest,
    GenesisStartResponse,
    GenesisStatusResponse,
    GenesisApproveRequest,
    GenesisApproveResponse,
)
from app.services.genesis import GenesisService

router = APIRouter(prefix="/genesis", tags=["Genesis"])


@router.post(
    "/start",
    response_model=GenesisStartResponse,
    summary="Start persona generation",
    description="""
Start a new persona generation job.

This endpoint initiates the full Genesis workflow:
1. Collects sources from YouTube, Google Drive, and web (if enabled)
2. Processes the corpus and extracts concepts
3. Generates an initial persona draft
4. Returns the job for human review

The job will be in 'awaiting_approval' status until confirmed via /genesis/approve.
"""
)
async def start_genesis(
    request: GenesisStartRequest,
    db: AsyncSession = Depends(get_db)
) -> GenesisStartResponse:
    """Start a new persona generation job."""
    try:
        service = GenesisService(db)
        return await service.start_genesis(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Genesis failed: {str(e)}")


@router.get(
    "/status/{job_id}",
    response_model=GenesisStatusResponse,
    summary="Get job status",
    description="""
Get the current status of a genesis job.

Returns progress information, current draft details, and any errors.
"""
)
async def get_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> GenesisStatusResponse:
    """Get the current status of a genesis job."""
    try:
        service = GenesisService(db)
        return await service.get_status(job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/approve",
    response_model=GenesisApproveResponse,
    summary="Approve or edit draft",
    description="""
Approve a persona draft or submit edits.

**Two modes:**

1. **Confirm**: Set `confirm: true` to finalize and commit the persona.
   - Creates persona and version records
   - Exports persona files to disk
   - Stores embeddings in Qdrant

2. **Edit**: Provide `edits[]` with JSON Patch-like operations.
   - Applies edits to the current draft
   - Creates a new draft version
   - Returns updated human_prompt for review

**Edit operations:**
- `add`: Add a value (to array or object)
- `replace`: Replace an existing value
- `remove`: Remove a value

**Path format:** Use dot notation with array indices.
Examples: `credo.statements[1]`, `ethos.virtues`, `topics.primary[0]`
"""
)
async def approve_draft(
    request: GenesisApproveRequest,
    db: AsyncSession = Depends(get_db)
) -> GenesisApproveResponse:
    """Approve or edit a genesis draft."""
    try:
        service = GenesisService(db)
        return await service.approve(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/export/{persona_id}",
    summary="Get export paths",
    description="""
Get the export paths for a committed persona.

Returns the filesystem paths where persona files are stored.
"""
)
async def get_export_paths(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get export paths for a persona."""
    from sqlalchemy import select
    from app.models.persona import Persona
    from app.config import get_settings
    from pathlib import Path
    
    settings = get_settings()
    
    result = await db.execute(
        select(Persona).where(Persona.id == persona_id)
    )
    persona = result.scalars().first()
    
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    
    base_path = Path(settings.PERSONAS_BASE_DIR) / persona.slug
    
    if not base_path.exists():
        raise HTTPException(status_code=404, detail="Export not found")
    
    return {
        "persona_id": str(persona_id),
        "slug": persona.slug,
        "base_path": str(base_path),
        "files": {
            "core": str(base_path / "core"),
            "memory": str(base_path / "memory"),
            "docs": str(base_path / "docs")
        }
    }
