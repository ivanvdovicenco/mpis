"""
MPIS Dashboard API - Dashboard Service

Service layer for Dashboard operations.
"""
from uuid import UUID, uuid4
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc

from app.models.dashboard import (
    DashboardProject,
    DashboardRun,
    DashboardLayout,
    WidgetRegistry,
    RedFlag,
    MetricsIngestionJob,
    NormalizedMetric,
)
from app.models.persona import Persona
from app.models.publisher import PublishedItem, ItemMetric
from app.schemas.dashboard import (
    PersonaSummary,
    DashboardProjectCreate,
    DashboardProjectResponse,
    DashboardRunCreate,
    DashboardRunResponse,
    DashboardRunCompleteRequest,
    DashboardLayoutCreate,
    DashboardLayoutResponse,
    WidgetRegisterRequest,
    WidgetResponse,
    RedFlagsSummaryResponse,
    MetricsIngestionJobCreate,
    MetricsIngestionJobResponse,
    NormalizedMetricsResponse,
)
from app.services.metric_normalizer import MetricNormalizer


class DashboardService:
    """Service for Dashboard operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Personas ---

    async def list_personas(self) -> List[PersonaSummary]:
        """List personas for dashboard UI."""
        result = await self.db.execute(
            select(Persona).order_by(desc(Persona.created_at))
        )
        personas = result.scalars().all()

        return [
            PersonaSummary(
                id=persona.id,
                name=persona.name,
                active_version=persona.active_version,
                created_at=persona.created_at,
            )
            for persona in personas
        ]

    # --- Project Management ---

    async def list_projects(self) -> List[DashboardProjectResponse]:
        """List dashboard projects."""
        result = await self.db.execute(
            select(DashboardProject).order_by(desc(DashboardProject.created_at))
        )
        projects = result.scalars().all()

        return [
            DashboardProjectResponse(
                id=project.id,
                name=project.name,
                persona_id=project.persona_id,
                channels=project.channels,
                created_at=project.created_at,
            )
            for project in projects
        ]

    async def create_project(self, request: DashboardProjectCreate) -> DashboardProjectResponse:
        """Create a new dashboard project."""
        project = DashboardProject(
            name=request.name,
            persona_id=request.persona_id,
            channels=request.channels,
        )
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        
        return DashboardProjectResponse(
            id=project.id,
            name=project.name,
            persona_id=project.persona_id,
            channels=project.channels,
            created_at=project.created_at,
        )
    
    async def get_project(self, project_id: UUID) -> Optional[DashboardProjectResponse]:
        """Get a dashboard project by ID."""
        result = await self.db.execute(
            select(DashboardProject).where(DashboardProject.id == project_id)
        )
        project = result.scalar_one_or_none()
        
        if not project:
            return None
        
        return DashboardProjectResponse(
            id=project.id,
            name=project.name,
            persona_id=project.persona_id,
            channels=project.channels,
            created_at=project.created_at,
        )
    
    # --- Run Management ---
    
    async def create_run(self, request: DashboardRunCreate) -> DashboardRunResponse:
        """Create a new dashboard run."""
        run_id = uuid4()
        
        run = DashboardRun(
            run_id=run_id,
            project_id=request.project_id,
            persona_id=request.persona_id,
            status="pending",
            meta={
                "channels": request.channels,
                "date_from": request.date_from,
                "date_to": request.date_to,
                "templates": request.templates or {},
                "options": request.options or {},
            }
        )
        self.db.add(run)
        await self.db.commit()
        await self.db.refresh(run)
        
        return DashboardRunResponse(
            id=run.id,
            run_id=run.run_id,
            project_id=run.project_id,
            persona_id=run.persona_id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            n8n_execution_id=run.n8n_execution_id,
            error_message=run.error_message,
        )
    
    async def complete_run(self, request: DashboardRunCompleteRequest) -> DashboardRunResponse:
        """Complete a dashboard run with status aggregation."""
        result = await self.db.execute(
            select(DashboardRun).where(DashboardRun.run_id == request.run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            raise ValueError(f"Run not found: {request.run_id}")
        
        # Determine final status with partial support
        final_status = await self._calculate_run_status(
            request.status,
            request.published_items
        )
        
        run.status = final_status
        run.completed_at = datetime.utcnow()
        run.n8n_execution_id = request.n8n_execution_id
        run.error_message = request.error
        
        await self.db.commit()
        await self.db.refresh(run)
        
        return DashboardRunResponse(
            id=run.id,
            run_id=run.run_id,
            project_id=run.project_id,
            persona_id=run.persona_id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            n8n_execution_id=run.n8n_execution_id,
            error_message=run.error_message,
        )
    
    async def _calculate_run_status(
        self, 
        mpis_status: str, 
        published_items: List[Dict[str, Any]]
    ) -> str:
        """
        Calculate final run status with partial support.
        
        Rules:
        - If MPIS returns 'failed' and no published items: 'failed'
        - If MPIS returns 'success' and all items published: 'success'
        - If at least one success and one failure: 'partial'
        """
        if mpis_status == "failed" and len(published_items) == 0:
            return "failed"
        
        if mpis_status == "success" and len(published_items) > 0:
            # Check if any items have failures
            has_failures = any(
                item.get("status") == "failed" for item in published_items
            )
            has_successes = any(
                item.get("status") != "failed" for item in published_items
            )
            
            if has_failures and has_successes:
                return "partial"
            elif has_failures:
                return "failed"
            else:
                return "success"
        
        # Default to MPIS status
        return mpis_status
    
    async def get_run(self, run_id: UUID) -> Optional[DashboardRunResponse]:
        """Get a dashboard run by run_id."""
        result = await self.db.execute(
            select(DashboardRun).where(DashboardRun.run_id == run_id)
        )
        run = result.scalar_one_or_none()
        
        if not run:
            return None
        
        return DashboardRunResponse(
            id=run.id,
            run_id=run.run_id,
            project_id=run.project_id,
            persona_id=run.persona_id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            n8n_execution_id=run.n8n_execution_id,
            error_message=run.error_message,
        )
    
    # --- Dashboard Layouts ---
    
    async def create_layout(self, request: DashboardLayoutCreate) -> DashboardLayoutResponse:
        """Create a new dashboard layout."""
        layout = DashboardLayout(
            user_id=request.user_id,
            name=request.name,
            is_default=request.is_default,
            layout_config=request.layout_config,
        )
        self.db.add(layout)
        await self.db.commit()
        await self.db.refresh(layout)
        
        return DashboardLayoutResponse(
            id=layout.id,
            user_id=layout.user_id,
            name=layout.name,
            is_default=layout.is_default,
            layout_config=layout.layout_config,
            created_at=layout.created_at,
        )
    
    async def list_layouts(self, user_id: Optional[UUID] = None) -> List[DashboardLayoutResponse]:
        """List dashboard layouts."""
        query = select(DashboardLayout)
        if user_id:
            query = query.where(
                (DashboardLayout.user_id == user_id) | (DashboardLayout.user_id.is_(None))
            )
        else:
            query = query.where(DashboardLayout.user_id.is_(None))
        
        result = await self.db.execute(query)
        layouts = result.scalars().all()
        
        return [
            DashboardLayoutResponse(
                id=layout.id,
                user_id=layout.user_id,
                name=layout.name,
                is_default=layout.is_default,
                layout_config=layout.layout_config,
                created_at=layout.created_at,
            )
            for layout in layouts
        ]
    
    # --- Widget Registry ---
    
    async def register_widget(self, request: WidgetRegisterRequest) -> WidgetResponse:
        """Register a new widget."""
        widget = WidgetRegistry(
            widget_id=request.widget_id,
            name=request.name,
            description=request.description,
            widget_type=request.widget_type,
            schema=request.widget_schema,
            renderer_url=request.renderer_url,
        )
        self.db.add(widget)
        await self.db.commit()
        await self.db.refresh(widget)
        
        return WidgetResponse(
            id=widget.id,
            widget_id=widget.widget_id,
            name=widget.name,
            description=widget.description,
            widget_type=widget.widget_type,
            widget_schema=widget.schema,
            renderer_url=widget.renderer_url,
        )
    
    async def list_widgets(self) -> List[WidgetResponse]:
        """List all widgets."""
        result = await self.db.execute(select(WidgetRegistry))
        widgets = result.scalars().all()
        
        return [
            WidgetResponse(
                id=widget.id,
                widget_id=widget.widget_id,
                name=widget.name,
                description=widget.description,
                widget_type=widget.widget_type,
                widget_schema=widget.schema,
                renderer_url=widget.renderer_url,
            )
            for widget in widgets
        ]
    
    # --- Red Flags ---
    
    async def get_red_flags_summary(self) -> RedFlagsSummaryResponse:
        """Get red flags summary."""
        # Calculate failed runs percentage
        failed_runs_24h = await self._get_failed_runs_stats(hours=24)
        failed_runs_7d = await self._get_failed_runs_stats(hours=24*7)
        
        # Get missing metrics
        missing_metrics = await self._get_missing_metrics()
        
        # Get missing publish records
        missing_publish_records = await self._get_missing_publish_records()
        
        return RedFlagsSummaryResponse(
            failed_runs={
                "last_24h": failed_runs_24h,
                "last_7d": failed_runs_7d,
            },
            missing_metrics=missing_metrics,
            missing_publish_records=missing_publish_records,
        )
    
    async def _get_failed_runs_stats(self, hours: int) -> Dict[str, Any]:
        """Get failed runs statistics for a time period."""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        # Count total runs
        total_result = await self.db.execute(
            select(func.count(DashboardRun.id))
            .where(DashboardRun.started_at >= cutoff)
        )
        total_runs = total_result.scalar() or 0
        
        # Count failed runs
        failed_result = await self.db.execute(
            select(func.count(DashboardRun.id))
            .where(
                and_(
                    DashboardRun.started_at >= cutoff,
                    DashboardRun.status == "failed"
                )
            )
        )
        failed_runs = failed_result.scalar() or 0
        
        percentage = (failed_runs / total_runs * 100) if total_runs > 0 else 0.0
        alert = percentage > 10.0
        
        return {
            "total_runs": total_runs,
            "failed_runs": failed_runs,
            "percentage": round(percentage, 1),
            "alert": alert,
        }
    
    async def _get_missing_metrics(self) -> Dict[str, Any]:
        """Get missing metrics statistics."""
        # Count published items without metrics
        result = await self.db.execute(
            select(func.count(PublishedItem.id))
            .outerjoin(NormalizedMetric)
            .where(NormalizedMetric.id.is_(None))
        )
        count = result.scalar() or 0
        
        return {
            "count": count,
            "alert": count > 5,
        }
    
    async def _get_missing_publish_records(self) -> Dict[str, Any]:
        """Get missing publish records statistics."""
        # This would require tracking expected vs actual publish records
        # For now, return placeholder
        return {
            "count": 0,
            "alert": False,
        }
    
    # --- Metrics Ingestion Jobs ---
    
    async def create_ingestion_job(
        self, 
        request: MetricsIngestionJobCreate
    ) -> MetricsIngestionJobResponse:
        """Create a new metrics ingestion job."""
        job = MetricsIngestionJob(
            job_name=request.job_name,
            channel=request.channel,
            persona_id=request.persona_id,
            schedule_cron=request.schedule_cron,
            config=request.config,
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        
        return MetricsIngestionJobResponse(
            id=job.id,
            job_name=job.job_name,
            channel=job.channel,
            persona_id=job.persona_id,
            schedule_cron=job.schedule_cron,
            last_run_at=job.last_run_at,
            next_run_at=job.next_run_at,
            enabled=job.enabled,
        )
    
    # --- Normalized Metrics ---
    
    async def ingest_normalized_metrics(
        self,
        published_item_id: UUID,
        channel: str,
        raw_metrics: Dict[str, Any],
        measured_at: datetime,
        source: str = "api"
    ) -> NormalizedMetricsResponse:
        """Ingest and normalize metrics."""
        # Normalize metrics
        normalized = MetricNormalizer.normalize_metrics(channel, raw_metrics)
        
        # Create normalized metric record
        metric = NormalizedMetric(
            published_item_id=published_item_id,
            channel=channel,
            views=normalized.get("views"),
            impressions=normalized.get("impressions"),
            reach=normalized.get("reach"),
            reactions=normalized.get("reactions"),
            comments=normalized.get("comments"),
            shares=normalized.get("shares"),
            saves=normalized.get("saves"),
            clicks=normalized.get("clicks"),
            engagement_rate=normalized.get("engagement_rate"),
            raw_metrics=raw_metrics,
            measured_at=measured_at,
            source=source,
        )
        
        self.db.add(metric)
        await self.db.commit()
        await self.db.refresh(metric)
        
        return NormalizedMetricsResponse(
            id=metric.id,
            published_item_id=metric.published_item_id,
            channel=metric.channel,
            views=metric.views,
            impressions=metric.impressions,
            reach=metric.reach,
            reactions=metric.reactions,
            comments=metric.comments,
            shares=metric.shares,
            saves=metric.saves,
            clicks=metric.clicks,
            engagement_rate=metric.engagement_rate,
            measured_at=metric.measured_at,
        )
