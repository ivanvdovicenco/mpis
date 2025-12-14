"""
MPIS Analytics API - Analytics Router

API endpoints for analytics and EIDOS recommendations.
"""
from uuid import UUID
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    RecomputeRequest,
    RecomputeResponse,
    EidosRecommendationsResponse,
    ExperimentCreate,
    ExperimentResponse,
)
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get(
    "/persona/{persona_id}/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get analytics summary",
    description="""
Get analytics summary for a persona.

**Time ranges:**
- `7d`: Last 7 days
- `30d`: Last 30 days (default)
- `90d`: Last 90 days
- `all`: All time

Returns:
- Aggregate metrics (views, reactions, shares, engagement rate)
- Best performing topics and times
- AI-generated insights (optional)
"""
)
async def get_summary(
    persona_id: UUID,
    range: str = Query(default="30d", pattern="^(7d|30d|90d|all)$"),
    include_insights: bool = Query(default=True),
    db: AsyncSession = Depends(get_db)
) -> AnalyticsSummaryResponse:
    """Get analytics summary."""
    try:
        service = AnalyticsService(db)
        return await service.get_summary(persona_id, range, include_insights)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/recompute",
    response_model=RecomputeResponse,
    summary="Trigger recomputation",
    description="""
Trigger analytics recomputation.

Computes rollups for specified types:
- `daily`: Current day rollup
- `weekly`: Current week rollup
- `monthly`: Current month rollup

Use `force: true` to recompute even if recent data exists.
"""
)
async def recompute(
    request: RecomputeRequest,
    db: AsyncSession = Depends(get_db)
) -> RecomputeResponse:
    """Trigger analytics recomputation."""
    try:
        service = AnalyticsService(db)
        return await service.recompute(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recomputation failed: {str(e)}")


@router.get(
    "/recommendations/{persona_id}",
    response_model=EidosRecommendationsResponse,
    summary="Get EIDOS recommendations",
    description="""
Get EIDOS AI-powered recommendations for a persona.

EIDOS analyzes:
- Publishing metrics and trends
- Engagement patterns
- Content performance

Returns:
- Top 5 actionable recommendations with evidence
- Ready-to-generate content briefs
- Suggested A/B experiments

Results are cached for 24 hours unless expired.
"""
)
async def get_recommendations(
    persona_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> EidosRecommendationsResponse:
    """Get EIDOS recommendations."""
    try:
        service = AnalyticsService(db)
        return await service.get_recommendations(persona_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendations failed: {str(e)}")


@router.post(
    "/experiments",
    response_model=ExperimentResponse,
    summary="Create experiment",
    description="""
Create a new A/B experiment.

Define:
- Hypothesis to test
- At least 2 variants
- Optional start/end dates

Use experiments to test content strategies and measure results.
"""
)
async def create_experiment(
    request: ExperimentCreate,
    db: AsyncSession = Depends(get_db)
) -> ExperimentResponse:
    """Create an experiment."""
    try:
        service = AnalyticsService(db)
        return await service.create_experiment(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment creation failed: {str(e)}")
