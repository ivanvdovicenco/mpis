"""
MPIS Analytics API - Analytics Service

Handles analytics computations and EIDOS recommendations.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pathlib import Path
from decimal import Decimal

from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.analytics import AnalyticsRollup, EidosRecommendation, Experiment, DashboardView
from app.models.publisher import PublishedItem, ItemMetric, ContentPlan, ContentDraft
from app.models.persona import Persona, PersonaVersion, AuditLog
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    MetricsSummary,
    RecomputeRequest,
    RecomputeResponse,
    EidosRecommendationsResponse,
    EidosRecommendationItem,
    ContentBrief,
    ExperimentSuggestion,
    ExperimentCreate,
    ExperimentResponse,
    ANALYTICS_AUDIT_EVENTS,
)
from app.services.llm import LLMService

logger = logging.getLogger(__name__)
settings = get_settings()


class AnalyticsService:
    """
    Service for analytics and EIDOS recommendations.
    
    Handles metric computations, rollups, and AI-powered recommendations.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.llm = LLMService()
    
    # ========================
    # Analytics Summary
    # ========================
    
    async def get_summary(
        self,
        persona_id: UUID,
        range_type: str = "30d",
        include_insights: bool = True,
    ) -> AnalyticsSummaryResponse:
        """
        Get analytics summary for a persona.
        
        Args:
            persona_id: Persona ID
            range_type: Time range (7d, 30d, 90d, all)
            include_insights: Whether to include AI insights
            
        Returns:
            Analytics summary response
        """
        # Verify persona exists
        persona = await self._get_persona(persona_id)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        # Calculate date range
        now = datetime.utcnow()
        if range_type == "7d":
            period_start = now - timedelta(days=7)
        elif range_type == "30d":
            period_start = now - timedelta(days=30)
        elif range_type == "90d":
            period_start = now - timedelta(days=90)
        else:
            period_start = datetime(2020, 1, 1)  # "all" time
        
        # Get published items in range
        items_result = await self.db.execute(
            select(PublishedItem)
            .join(ContentDraft, PublishedItem.draft_id == ContentDraft.id)
            .join(ContentPlan, ContentDraft.plan_id == ContentPlan.id)
            .where(
                and_(
                    ContentPlan.persona_id == persona_id,
                    PublishedItem.published_at >= period_start,
                )
            )
        )
        published_items = list(items_result.scalars().all())
        
        # Aggregate metrics
        metrics_summary = await self._aggregate_metrics(published_items, period_start)
        
        # Get top topics
        topics_result = await self.db.execute(
            select(ContentPlan.topic, func.count(ContentPlan.id).label("count"))
            .where(
                and_(
                    ContentPlan.persona_id == persona_id,
                    ContentPlan.status == "published",
                    ContentPlan.created_at >= period_start,
                )
            )
            .group_by(ContentPlan.topic)
            .order_by(desc("count"))
            .limit(5)
        )
        best_topics = [row[0] for row in topics_result.all()]
        
        metrics_summary.best_performing_topics = best_topics
        
        # Generate insights if requested
        insights = []
        trends = {}
        if include_insights and published_items:
            insights, trends = await self._generate_insights(
                persona, metrics_summary, published_items
            )
        
        return AnalyticsSummaryResponse(
            persona_id=persona_id,
            range_type=range_type,
            period_start=period_start,
            period_end=now,
            metrics=metrics_summary,
            insights=insights,
            trends=trends,
        )
    
    async def _aggregate_metrics(
        self,
        published_items: List[PublishedItem],
        period_start: datetime,
    ) -> MetricsSummary:
        """Aggregate metrics from published items."""
        if not published_items:
            return MetricsSummary()
        
        item_ids = [item.id for item in published_items]
        
        # Get all metrics for these items
        metrics_result = await self.db.execute(
            select(
                ItemMetric.metric_type,
                func.sum(ItemMetric.metric_value).label("total")
            )
            .where(ItemMetric.published_item_id.in_(item_ids))
            .group_by(ItemMetric.metric_type)
        )
        
        metrics_map = {row[0]: float(row[1]) for row in metrics_result.all()}
        
        total_views = metrics_map.get("views", 0)
        total_reactions = metrics_map.get("reactions", 0)
        total_shares = metrics_map.get("shares", 0)
        
        # Calculate engagement rate
        engagement_rate = 0.0
        if total_views > 0:
            engagement_rate = ((total_reactions + total_shares) / total_views) * 100
        
        return MetricsSummary(
            total_published=len(published_items),
            total_views=total_views,
            total_reactions=total_reactions,
            total_shares=total_shares,
            engagement_rate=round(engagement_rate, 2),
            best_performing_topics=[],
            best_performing_times=[],
        )
    
    async def _generate_insights(
        self,
        persona: Persona,
        metrics: MetricsSummary,
        published_items: List[PublishedItem],
    ) -> tuple[List[str], dict]:
        """Generate AI insights from metrics."""
        if self.llm.dry_run:
            return self._mock_insights(metrics), {"trend": "stable"}
        
        prompt = f"""Analyze these publishing metrics and generate 3-5 actionable insights.

Persona: {persona.name}
Period Metrics:
- Total Published: {metrics.total_published}
- Total Views: {metrics.total_views}
- Total Reactions: {metrics.total_reactions}
- Total Shares: {metrics.total_shares}
- Engagement Rate: {metrics.engagement_rate}%
- Top Topics: {', '.join(metrics.best_performing_topics[:3])}

Generate as JSON:
{{
    "insights": ["insight 1", "insight 2", ...],
    "trends": {{
        "overall": "growing/stable/declining",
        "engagement": "high/medium/low",
        "recommendation": "brief recommendation"
    }}
}}

Return ONLY valid JSON."""
        
        try:
            response = await self.llm._call_llm(prompt, max_tokens=1000)
            result = self.llm._parse_json_response(response)
            return result.get("insights", []), result.get("trends", {})
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
            return self._mock_insights(metrics), {"trend": "unknown"}
    
    def _mock_insights(self, metrics: MetricsSummary) -> List[str]:
        """Return mock insights for DRY_RUN mode."""
        insights = [
            f"Published {metrics.total_published} items with {metrics.engagement_rate}% engagement rate",
        ]
        if metrics.engagement_rate > 5:
            insights.append("Engagement rate is above average - keep up the momentum")
        else:
            insights.append("Consider experimenting with different content formats to boost engagement")
        
        if metrics.best_performing_topics:
            insights.append(f"Top performing topic: {metrics.best_performing_topics[0]}")
        
        return insights
    
    # ========================
    # Rollup Computation
    # ========================
    
    async def recompute(self, request: RecomputeRequest) -> RecomputeResponse:
        """Trigger analytics recomputation."""
        persona = await self._get_persona(request.persona_id)
        if not persona:
            raise ValueError(f"Persona {request.persona_id} not found")
        
        job_id = uuid4()
        now = datetime.utcnow()
        
        for rollup_type in request.rollup_types:
            if rollup_type == "daily":
                period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=1)
            elif rollup_type == "weekly":
                period_start = now - timedelta(days=now.weekday())
                period_start = period_start.replace(hour=0, minute=0, second=0, microsecond=0)
                period_end = period_start + timedelta(days=7)
            else:  # monthly
                period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                if now.month == 12:
                    period_end = period_start.replace(year=now.year + 1, month=1)
                else:
                    period_end = period_start.replace(month=now.month + 1)
            
            # Check if rollup exists and is recent
            if not request.force:
                existing = await self.db.execute(
                    select(AnalyticsRollup)
                    .where(
                        and_(
                            AnalyticsRollup.persona_id == request.persona_id,
                            AnalyticsRollup.rollup_type == rollup_type,
                            AnalyticsRollup.period_start == period_start,
                        )
                    )
                )
                existing_rollup = existing.scalars().first()
                if existing_rollup and not request.force:
                    continue
            
            # Compute rollup
            summary = await self.get_summary(
                request.persona_id,
                range_type="7d" if rollup_type == "weekly" else "30d",
                include_insights=True,
            )
            
            # Check if we should update existing or create new
            existing_check = await self.db.execute(
                select(AnalyticsRollup)
                .where(
                    and_(
                        AnalyticsRollup.persona_id == request.persona_id,
                        AnalyticsRollup.rollup_type == rollup_type,
                        AnalyticsRollup.period_start == period_start,
                    )
                )
            )
            existing_record = existing_check.scalars().first()
            
            if existing_record:
                # Update existing rollup
                existing_record.metrics = summary.metrics.model_dump()
                existing_record.insights = {"insights": summary.insights, "trends": summary.trends}
                existing_record.computed_at = datetime.utcnow()
            else:
                # Create new rollup
                rollup = AnalyticsRollup(
                    persona_id=request.persona_id,
                    rollup_type=rollup_type,
                    period_start=period_start,
                    period_end=period_end,
                    metrics=summary.metrics.model_dump(),
                    insights={"insights": summary.insights, "trends": summary.trends},
                )
                self.db.add(rollup)
        
        await self.db.flush()
        
        # Audit log
        await self._audit_log(
            ANALYTICS_AUDIT_EVENTS["ROLLUP_COMPUTED"],
            "analytics_rollup",
            job_id,
            {"rollup_types": request.rollup_types},
        )
        
        return RecomputeResponse(
            persona_id=request.persona_id,
            job_id=job_id,
            status="completed",
            message=f"Computed {len(request.rollup_types)} rollups",
        )
    
    # ========================
    # EIDOS Recommendations
    # ========================
    
    async def get_recommendations(self, persona_id: UUID) -> EidosRecommendationsResponse:
        """Get EIDOS recommendations for a persona."""
        persona = await self._get_persona(persona_id)
        if not persona:
            raise ValueError(f"Persona {persona_id} not found")
        
        # Check for recent recommendations
        result = await self.db.execute(
            select(EidosRecommendation)
            .where(EidosRecommendation.persona_id == persona_id)
            .order_by(desc(EidosRecommendation.computed_at))
            .limit(1)
        )
        existing = result.scalars().first()
        
        # If recent (within 24h) and not expired, return existing
        if existing and existing.status != "expired":
            if (datetime.utcnow() - existing.computed_at).days < 1:
                return self._format_eidos_response(persona_id, existing)
        
        # Generate new recommendations
        run_id = uuid4()
        
        # Get analytics summary for context
        summary = await self.get_summary(persona_id, "30d", True)
        
        # Generate recommendations
        recs, briefs, experiments = await self._generate_eidos(persona, summary)
        
        # Store recommendations
        eidos = EidosRecommendation(
            persona_id=persona_id,
            run_id=run_id,
            recommendations=[r.model_dump() for r in recs],
            evidence={"metrics_summary": summary.metrics.model_dump()},
            experiments=[e.model_dump() for e in experiments],
            content_briefs=[b.model_dump() for b in briefs],
            status="pending",
        )
        
        self.db.add(eidos)
        await self.db.flush()
        
        # Export recommendations
        await self._export_recommendations(persona, eidos)
        
        # Audit log
        await self._audit_log(
            ANALYTICS_AUDIT_EVENTS["EIDOS_GENERATED"],
            "eidos_recommendation",
            eidos.id,
            {"run_id": str(run_id)},
        )
        
        return self._format_eidos_response(persona_id, eidos)
    
    async def _generate_eidos(
        self,
        persona: Persona,
        summary: AnalyticsSummaryResponse,
    ) -> tuple[List[EidosRecommendationItem], List[ContentBrief], List[ExperimentSuggestion]]:
        """Generate EIDOS recommendations."""
        if self.llm.dry_run:
            return self._mock_eidos(persona, summary)
        
        prompt = f"""You are EIDOS, an AI advisor for content strategy. Analyze these metrics and generate actionable recommendations.

Persona: {persona.name}
Analytics Summary:
- Total Published: {summary.metrics.total_published}
- Engagement Rate: {summary.metrics.engagement_rate}%
- Top Topics: {', '.join(summary.metrics.best_performing_topics[:3])}
- Insights: {'; '.join(summary.insights[:3])}

Generate as STRICT JSON:
{{
    "recommendations": [
        {{
            "id": 1,
            "title": "Short title",
            "description": "Detailed description",
            "priority": "high/medium/low",
            "category": "content/timing/engagement/growth",
            "evidence": ["evidence point 1", "evidence point 2"],
            "measurable_outcome": "How to measure success"
        }}
    ],
    "content_briefs": [
        {{
            "topic": "Topic suggestion",
            "hook": "Suggested hook",
            "key_points": ["point 1", "point 2"],
            "target_channel": "telegram",
            "suggested_length": 500,
            "rationale": "Why this content"
        }}
    ],
    "experiments": [
        {{
            "name": "Experiment name",
            "hypothesis": "What we're testing",
            "variants": ["control description", "treatment description"],
            "success_metric": "How to measure",
            "duration_days": 14
        }}
    ]
}}

Generate 3-5 recommendations, 2-3 content briefs, and 1-2 experiments.
Return ONLY valid JSON."""
        
        try:
            response = await self.llm._call_llm(prompt, max_tokens=3000)
            result = self.llm._parse_json_response(response)
            
            recs = [EidosRecommendationItem(**r) for r in result.get("recommendations", [])]
            briefs = [ContentBrief(**b) for b in result.get("content_briefs", [])]
            experiments = [ExperimentSuggestion(**e) for e in result.get("experiments", [])]
            
            return recs, briefs, experiments
        except Exception as e:
            logger.error(f"Error generating EIDOS: {e}")
            return self._mock_eidos(persona, summary)
    
    def _mock_eidos(
        self,
        persona: Persona,
        summary: AnalyticsSummaryResponse,
    ) -> tuple[List[EidosRecommendationItem], List[ContentBrief], List[ExperimentSuggestion]]:
        """Return mock EIDOS for DRY_RUN mode."""
        recs = [
            EidosRecommendationItem(
                id=1,
                title="Increase posting frequency",
                description="Consider posting more frequently to maintain engagement momentum.",
                priority="medium",
                category="content",
                evidence=["Current engagement rate shows room for growth"],
                measurable_outcome="Track weekly engagement rate change",
            ),
            EidosRecommendationItem(
                id=2,
                title="Diversify content topics",
                description="Explore adjacent topics to expand audience reach.",
                priority="low",
                category="growth",
                evidence=["Top topics show concentration in few areas"],
                measurable_outcome="Monitor new follower growth",
            ),
        ]
        
        briefs = [
            ContentBrief(
                topic="Community engagement",
                hook="What's been on your mind lately?",
                key_points=["Invite discussion", "Share personal reflection", "Ask questions"],
                target_channel="telegram",
                suggested_length=500,
                rationale="Interactive content tends to boost engagement",
            ),
        ]
        
        experiments = [
            ExperimentSuggestion(
                name="Posting time test",
                hypothesis="Morning posts get more engagement than evening",
                variants=["Post at 9am", "Post at 7pm"],
                success_metric="Engagement rate within first 24 hours",
                duration_days=14,
            ),
        ]
        
        return recs, briefs, experiments
    
    def _format_eidos_response(
        self,
        persona_id: UUID,
        eidos: EidosRecommendation,
    ) -> EidosRecommendationsResponse:
        """Format EIDOS recommendation response."""
        return EidosRecommendationsResponse(
            persona_id=persona_id,
            run_id=eidos.run_id,
            computed_at=eidos.computed_at,
            recommendations=[
                EidosRecommendationItem(**r) for r in eidos.recommendations
            ],
            content_briefs=[
                ContentBrief(**b) for b in eidos.content_briefs
            ],
            experiments=[
                ExperimentSuggestion(**e) for e in eidos.experiments
            ],
            status=eidos.status,
        )
    
    async def _export_recommendations(
        self,
        persona: Persona,
        eidos: EidosRecommendation,
    ) -> None:
        """Export EIDOS recommendations to persona directory."""
        base_path = Path(settings.PERSONAS_BASE_DIR) / persona.slug / "analytics"
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Export summary
        summary_path = base_path / "summary.json"
        with open(summary_path, "w") as f:
            json.dump({
                "run_id": str(eidos.run_id),
                "computed_at": eidos.computed_at.isoformat(),
                "status": eidos.status,
                "evidence": eidos.evidence,
            }, f, indent=2)
        
        # Export recommendations as markdown
        recs_path = base_path / "recommendations.md"
        with open(recs_path, "w") as f:
            f.write(f"# EIDOS Recommendations\n\n")
            f.write(f"Generated: {eidos.computed_at.strftime('%Y-%m-%d %H:%M')}\n\n")
            for rec in eidos.recommendations:
                # Handle both dict and object formats
                if isinstance(rec, dict):
                    rec_id = rec.get('id', '?')
                    rec_title = rec.get('title', 'Untitled')
                    rec_priority = rec.get('priority', 'medium')
                    rec_category = rec.get('category', 'general')
                    rec_description = rec.get('description', '')
                    rec_evidence = rec.get('evidence', [])
                else:
                    rec_id = getattr(rec, 'id', '?')
                    rec_title = getattr(rec, 'title', 'Untitled')
                    rec_priority = getattr(rec, 'priority', 'medium')
                    rec_category = getattr(rec, 'category', 'general')
                    rec_description = getattr(rec, 'description', '')
                    rec_evidence = getattr(rec, 'evidence', [])
                
                f.write(f"## {rec_id}. {rec_title}\n")
                f.write(f"**Priority:** {rec_priority}\n")
                f.write(f"**Category:** {rec_category}\n\n")
                f.write(f"{rec_description}\n\n")
                if rec_evidence:
                    f.write("**Evidence:**\n")
                    for e in rec_evidence:
                        f.write(f"- {e}\n")
                f.write("\n---\n\n")
        
        # Export experiments
        exp_path = base_path / "experiments.json"
        with open(exp_path, "w") as f:
            json.dump(eidos.experiments, f, indent=2)
    
    # ========================
    # Experiments
    # ========================
    
    async def create_experiment(self, request: ExperimentCreate) -> ExperimentResponse:
        """Create a new experiment."""
        persona = await self._get_persona(request.persona_id)
        if not persona:
            raise ValueError(f"Persona {request.persona_id} not found")
        
        experiment = Experiment(
            persona_id=request.persona_id,
            name=request.name,
            hypothesis=request.hypothesis,
            variants=request.variants,
            status="draft",
            start_date=request.start_date,
            end_date=request.end_date,
        )
        
        self.db.add(experiment)
        await self.db.flush()
        
        # Audit log
        await self._audit_log(
            ANALYTICS_AUDIT_EVENTS["EXPERIMENT_CREATED"],
            "experiment",
            experiment.id,
            {"name": request.name},
        )
        
        return ExperimentResponse(
            id=experiment.id,
            persona_id=experiment.persona_id,
            name=experiment.name,
            hypothesis=experiment.hypothesis,
            status=experiment.status,
            variants=experiment.variants,
            results=experiment.results,
            created_at=experiment.created_at,
        )
    
    # ========================
    # Helper Methods
    # ========================
    
    async def _get_persona(self, persona_id: UUID) -> Optional[Persona]:
        """Get persona by ID."""
        result = await self.db.execute(
            select(Persona).where(Persona.id == persona_id)
        )
        return result.scalars().first()
    
    async def _audit_log(
        self,
        event_type: str,
        entity_type: str,
        entity_id: UUID,
        details: Dict[str, Any],
    ) -> None:
        """Create audit log entry."""
        log = AuditLog(
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        self.db.add(log)
        await self.db.flush()
