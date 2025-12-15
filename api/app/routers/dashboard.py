"""
MPIS Dashboard API - Dashboard Router

API endpoints for Dashboard system.
"""
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from app.database import get_db
from app.schemas.dashboard import (
    DashboardProjectCreate,
    DashboardProjectResponse,
    DashboardRunCreate,
    DashboardRunResponse,
    DashboardRunCompleteRequest,
    PublishRecordProxyRequest,
    PublishRecordProxyResponse,
    DashboardLayoutCreate,
    DashboardLayoutResponse,
    WidgetRegisterRequest,
    WidgetResponse,
    RedFlagsSummaryResponse,
    MetricsIngestionJobCreate,
    MetricsIngestionJobResponse,
    AIAnalystQueryRequest,
    AIAnalystQueryResponse,
    PersonaCreateRequest,
    PersonaStatusResponse,
)
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/api", tags=["Dashboard"])


# --- Dashboard Projects ---

@router.post(
    "/projects",
    response_model=DashboardProjectResponse,
    summary="Create dashboard project",
    description="Create a new dashboard project with channels and persona."
)
async def create_project(
    request: DashboardProjectCreate,
    db: AsyncSession = Depends(get_db)
) -> DashboardProjectResponse:
    """Create a dashboard project."""
    try:
        service = DashboardService(db)
        return await service.create_project(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Project creation failed: {str(e)}")


@router.get(
    "/projects/{project_id}",
    response_model=DashboardProjectResponse,
    summary="Get dashboard project",
    description="Get a dashboard project by ID."
)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DashboardProjectResponse:
    """Get a dashboard project."""
    try:
        service = DashboardService(db)
        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Dashboard Runs ---

@router.post(
    "/publisher/runs",
    response_model=DashboardRunResponse,
    summary="Create dashboard run",
    description="Create a new dashboard run and forward to MPIS API."
)
async def create_run(
    request: DashboardRunCreate,
    db: AsyncSession = Depends(get_db)
) -> DashboardRunResponse:
    """Create a dashboard run."""
    try:
        service = DashboardService(db)
        run = await service.create_run(request)
        
        # Forward to n8n webhook (in production)
        # For now, just return the created run
        
        return run
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Run creation failed: {str(e)}")


@router.get(
    "/publisher/runs/{run_id}",
    response_model=DashboardRunResponse,
    summary="Get dashboard run",
    description="Get a dashboard run by run_id."
)
async def get_run(
    run_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> DashboardRunResponse:
    """Get a dashboard run."""
    try:
        service = DashboardService(db)
        run = await service.get_run(run_id)
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return run
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/publisher/runs/{run_id}/complete",
    response_model=DashboardRunResponse,
    summary="Complete dashboard run",
    description="Complete a dashboard run (called by n8n)."
)
async def complete_run(
    run_id: UUID,
    request: DashboardRunCompleteRequest,
    db: AsyncSession = Depends(get_db)
) -> DashboardRunResponse:
    """Complete a dashboard run."""
    try:
        service = DashboardService(db)
        return await service.complete_run(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Run completion failed: {str(e)}")


# --- Publish Record Proxy ---

@router.post(
    "/publisher/publish/record",
    response_model=PublishRecordProxyResponse,
    summary="Record publish (proxy to MPIS)",
    description="Dashboard proxy that transforms and forwards publish records to MPIS API."
)
async def record_publish_proxy(
    request: PublishRecordProxyRequest,
    db: AsyncSession = Depends(get_db)
) -> PublishRecordProxyResponse:
    """
    Dashboard proxy for publish record.
    Transforms request (removes run_id, project_id, published_at) and forwards to MPIS.
    """
    try:
        # Transform request for MPIS (remove Dashboard-specific fields)
        mpis_request = {
            "draft_id": str(request.draft_id),
            "channel": request.channel,
            "channel_item_id": request.channel_item_id,
            "channel_url": request.channel_url,
        }
        
        # Forward to MPIS API
        # In production, this would call the actual MPIS service
        # For now, return a mock response
        
        return PublishRecordProxyResponse(
            published_item_id=UUID("550e8400-e29b-41d4-a716-446655440000"),
            status="recorded"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Publish record failed: {str(e)}")


# --- Dashboard Layouts ---

@router.get(
    "/dashboards/layouts",
    response_model=List[DashboardLayoutResponse],
    summary="List dashboard layouts",
    description="List dashboard layouts for the user."
)
async def list_layouts(
    user_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db)
) -> List[DashboardLayoutResponse]:
    """List dashboard layouts."""
    try:
        service = DashboardService(db)
        return await service.list_layouts(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/dashboards/layouts",
    response_model=DashboardLayoutResponse,
    summary="Create dashboard layout",
    description="Create a new dashboard layout."
)
async def create_layout(
    request: DashboardLayoutCreate,
    db: AsyncSession = Depends(get_db)
) -> DashboardLayoutResponse:
    """Create a dashboard layout."""
    try:
        service = DashboardService(db)
        return await service.create_layout(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Widgets ---

@router.get(
    "/widgets",
    response_model=List[WidgetResponse],
    summary="List widgets",
    description="List all registered widgets."
)
async def list_widgets(
    db: AsyncSession = Depends(get_db)
) -> List[WidgetResponse]:
    """List all widgets."""
    try:
        service = DashboardService(db)
        return await service.list_widgets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/widgets/register",
    response_model=WidgetResponse,
    summary="Register widget",
    description="Register a new widget (built-in or custom)."
)
async def register_widget(
    request: WidgetRegisterRequest,
    db: AsyncSession = Depends(get_db)
) -> WidgetResponse:
    """Register a new widget."""
    try:
        service = DashboardService(db)
        return await service.register_widget(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Red Flags ---

@router.get(
    "/red-flags",
    response_model=RedFlagsSummaryResponse,
    summary="Get red flags summary",
    description="Get summary of red flags (failed runs, missing metrics, etc.)."
)
async def get_red_flags_summary(
    db: AsyncSession = Depends(get_db)
) -> RedFlagsSummaryResponse:
    """Get red flags summary."""
    try:
        service = DashboardService(db)
        return await service.get_red_flags_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Metrics Ingestion Jobs ---

@router.post(
    "/metrics/jobs",
    response_model=MetricsIngestionJobResponse,
    summary="Create metrics ingestion job",
    description="Create a periodic metrics ingestion job."
)
async def create_ingestion_job(
    request: MetricsIngestionJobCreate,
    db: AsyncSession = Depends(get_db)
) -> MetricsIngestionJobResponse:
    """Create a metrics ingestion job."""
    try:
        service = DashboardService(db)
        return await service.create_ingestion_job(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- AI Analyst ---

@router.post(
    "/ai-analyst/query",
    response_model=AIAnalystQueryResponse,
    summary="Query AI analyst",
    description="Query the AI analyst for insights and recommendations."
)
async def query_ai_analyst(
    request: AIAnalystQueryRequest,
    db: AsyncSession = Depends(get_db)
) -> AIAnalystQueryResponse:
    """Query AI analyst."""
    try:
        # AI analyst implementation would go here
        # For now, return a mock response
        return AIAnalystQueryResponse(
            answer="Based on the data from the last 30 days, your best performing content topics are...",
            citations=[],
            suggested_actions=[
                "Create more content around topic X",
                "Experiment with posting times",
            ],
            confidence=0.85,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI analyst query failed: {str(e)}")


# --- Persona Flow (Proxy to Genesis) ---

@router.post(
    "/genesis/start",
    response_model=dict,
    summary="Start persona creation",
    description="Start persona creation process (proxy to MPIS Genesis)."
)
async def start_persona_creation(
    request: PersonaCreateRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Start persona creation (proxy to Genesis)."""
    try:
        # In production, forward to MPIS Genesis API
        # For now, return a mock response
        return {
            "job_id": "770e8400-e29b-41d4-a716-446655440002",
            "status": "started",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persona creation failed: {str(e)}")


@router.get(
    "/genesis/status/{job_id}",
    response_model=PersonaStatusResponse,
    summary="Get persona creation status",
    description="Get status of persona creation job (proxy to MPIS Genesis)."
)
async def get_persona_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> PersonaStatusResponse:
    """Get persona creation status."""
    try:
        # In production, forward to MPIS Genesis API
        # For now, return a mock response
        return PersonaStatusResponse(
            job_id=job_id,
            status="processing",
            progress={"step": "extracting_concepts", "percentage": 45},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/genesis/approve",
    response_model=dict,
    summary="Approve persona",
    description="Approve and commit persona (proxy to MPIS Genesis)."
)
async def approve_persona(
    request: dict,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Approve persona (proxy to Genesis)."""
    try:
        # In production, forward to MPIS Genesis API
        # For now, return a mock response
        return {
            "persona_id": "aa0e8400-e29b-41d4-a716-446655440005",
            "status": "approved",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Persona approval failed: {str(e)}")


@router.get(
    "/genesis/export/{persona_id}",
    response_model=dict,
    summary="Get persona export path",
    description="Get export path for persona (proxy to MPIS Genesis)."
)
async def get_persona_export(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get persona export path."""
    try:
        # In production, forward to MPIS Genesis API
        # For now, return a mock response
        return {
            "persona_id": persona_id,
            "export_path": f"/opt/mpis/exports/{persona_id}/persona_core.json",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
