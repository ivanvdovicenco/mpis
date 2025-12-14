"""
MPIS Life API - Life Service

Handles persona life event ingestion, reflection cycles, and metrics.
"""
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pathlib import Path

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.life import LifeEvent, LifeCycle, LifeCycleDraft, LifeMetric, Recommendation
from app.models.persona import Persona, PersonaVersion, AuditLog
from app.schemas.life import (
    LifeEventCreate,
    LifeEventResponse,
    CycleStartRequest,
    CycleStartResponse,
    CycleStatusResponse,
    CycleApproveRequest,
    CycleApproveResponse,
    ReflectionSummary,
    LIFE_AUDIT_EVENTS,
)
from app.services.llm import LLMService
from app.services.qdrant import QdrantService

logger = logging.getLogger(__name__)
settings = get_settings()


class LifeService:
    """
    Service for persona life management.
    
    Handles event ingestion, reflection cycles, metrics, and memory updates.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.llm = LLMService()
        self.qdrant = QdrantService()
    
    # ========================
    # Event Ingestion
    # ========================
    
    async def ingest_event(self, request: LifeEventCreate) -> LifeEventResponse:
        """
        Ingest a life event for a persona.
        
        Args:
            request: Event creation request
            
        Returns:
            Created event response
        """
        # Verify persona exists
        persona = await self._get_persona(request.persona_id)
        if not persona:
            raise ValueError(f"Persona {request.persona_id} not found")
        
        run_id = uuid4()
        
        # Create event
        event = LifeEvent(
            persona_id=request.persona_id,
            event_type=request.event_type,
            content=request.content,
            tags=request.tags or [],
            run_id=run_id,
            meta=request.meta or {},
        )
        
        self.db.add(event)
        await self.db.flush()
        
        # Audit log
        await self._audit_log(
            LIFE_AUDIT_EVENTS["EVENT_INGESTED"],
            "life_event",
            event.id,
            {"event_type": request.event_type, "tags": request.tags},
        )
        
        logger.info(f"Ingested life event {event.id} for persona {persona.slug}")
        
        return LifeEventResponse(
            id=event.id,
            persona_id=event.persona_id,
            event_type=event.event_type,
            content=event.content,
            tags=event.tags or [],
            run_id=event.run_id,
            created_at=event.created_at,
        )
    
    # ========================
    # Reflection Cycles
    # ========================
    
    async def start_cycle(self, request: CycleStartRequest) -> CycleStartResponse:
        """
        Start a reflection cycle for a persona.
        
        Args:
            request: Cycle start request
            
        Returns:
            Cycle start response
        """
        # Verify persona exists
        persona = await self._get_persona(request.persona_id)
        if not persona:
            raise ValueError(f"Persona {request.persona_id} not found")
        
        run_id = uuid4()
        
        # Create cycle
        cycle = LifeCycle(
            persona_id=request.persona_id,
            cycle_type=request.cycle_type,
            run_id=run_id,
            status="processing",
            options=request.options or {},
        )
        
        self.db.add(cycle)
        await self.db.flush()
        
        # Audit log
        await self._audit_log(
            LIFE_AUDIT_EVENTS["CYCLE_STARTED"],
            "life_cycle",
            cycle.id,
            {"cycle_type": request.cycle_type, "run_id": str(run_id)},
        )
        
        # Process cycle (simplified - in production this would be async)
        try:
            await self._process_cycle(cycle, persona)
        except Exception as e:
            logger.error(f"Cycle processing failed: {e}")
            cycle.status = "failed"
            await self._audit_log(
                LIFE_AUDIT_EVENTS["CYCLE_FAILED"],
                "life_cycle",
                cycle.id,
                {"error": str(e)},
            )
        
        return CycleStartResponse(
            cycle_id=cycle.id,
            run_id=run_id,
            status=cycle.status,
            message=f"Cycle started with status: {cycle.status}",
        )
    
    async def _process_cycle(self, cycle: LifeCycle, persona: Persona) -> None:
        """Process a reflection cycle."""
        # Get lookback period from options
        lookback_days = cycle.options.get("lookback_days", 7 if cycle.cycle_type == "weekly" else 1)
        max_events = cycle.options.get("max_events", 100)
        
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        
        # Fetch recent events
        result = await self.db.execute(
            select(LifeEvent)
            .where(
                and_(
                    LifeEvent.persona_id == persona.id,
                    LifeEvent.created_at >= cutoff,
                )
            )
            .order_by(desc(LifeEvent.created_at))
            .limit(max_events)
        )
        events = list(result.scalars().all())
        
        if not events:
            logger.info(f"No events found for persona {persona.slug} in lookback period")
            cycle.status = "awaiting_approval"
            cycle.finished_at = datetime.utcnow()
            
            # Create empty draft
            draft = LifeCycleDraft(
                cycle_id=cycle.id,
                draft_json={
                    "summary": "No events recorded in this period.",
                    "key_insights": [],
                    "suggested_adjustments": [],
                    "next_actions": ["Continue monitoring and recording events"],
                    "staleness_alerts": [],
                },
            )
            self.db.add(draft)
            return
        
        # Get current persona version for context
        persona_version = await self._get_active_persona_version(persona)
        
        # Generate reflection using LLM
        reflection = await self._generate_reflection(events, persona_version, cycle.cycle_type)
        
        # Create draft
        draft = LifeCycleDraft(
            cycle_id=cycle.id,
            draft_json=reflection.model_dump(),
        )
        self.db.add(draft)
        
        cycle.status = "awaiting_approval"
        cycle.finished_at = datetime.utcnow()
        
        # Audit log
        await self._audit_log(
            LIFE_AUDIT_EVENTS["CYCLE_DRAFT_CREATED"],
            "life_cycle_draft",
            draft.id,
            {"cycle_id": str(cycle.id)},
        )
        
        logger.info(f"Cycle {cycle.id} processed, draft created")
    
    async def _generate_reflection(
        self,
        events: List[LifeEvent],
        persona_version: Optional[PersonaVersion],
        cycle_type: str,
    ) -> ReflectionSummary:
        """Generate a reflection summary from events."""
        if self.llm.dry_run:
            return self._mock_reflection(events, cycle_type)
        
        # Prepare events summary
        events_text = "\n".join([
            f"- [{e.event_type}] ({e.created_at.strftime('%Y-%m-%d')}): {e.content[:500]}"
            for e in events[:50]  # Limit to 50 events
        ])
        
        # Prepare persona context
        persona_context = ""
        if persona_version and persona_version.core_json:
            core = persona_version.core_json
            persona_context = f"""
Persona Core Summary:
- Credo: {core.get('credo', {}).get('summary', 'N/A')}
- Virtues: {', '.join(core.get('ethos', {}).get('virtues', [])[:5])}
- Primary Topics: {', '.join(core.get('topics', {}).get('primary', [])[:5])}
"""
        
        prompt = f"""You are analyzing a {cycle_type} reflection period for a persona.

{persona_context}

Recent Events:
{events_text}

Generate a reflection summary as STRICT JSON with this structure:
{{
    "summary": "Brief actionable summary (1-2 sentences)",
    "key_insights": ["insight 1", "insight 2", ...],
    "suggested_adjustments": [
        {{"field": "path.to.field", "change": "description", "reason": "why"}}
    ],
    "next_actions": ["action 1", "action 2", ...],
    "staleness_alerts": [
        {{"topic": "topic name", "issue": "stale/contradicted", "details": "explanation"}}
    ]
}}

Return ONLY valid JSON."""
        
        try:
            response = await self.llm._call_llm(prompt, max_tokens=2000)
            result = self.llm._parse_json_response(response)
            return ReflectionSummary(**result)
        except Exception as e:
            logger.error(f"Error generating reflection: {e}")
            return self._mock_reflection(events, cycle_type)
    
    def _mock_reflection(self, events: List[LifeEvent], cycle_type: str) -> ReflectionSummary:
        """Return mock reflection for DRY_RUN mode."""
        event_types = list(set(e.event_type for e in events))
        return ReflectionSummary(
            summary=f"Processed {len(events)} events in this {cycle_type} cycle.",
            key_insights=[
                f"Most common event type: {event_types[0] if event_types else 'none'}",
                "Engagement patterns show consistent activity",
            ],
            suggested_adjustments=[],
            next_actions=[
                "Continue monitoring interactions",
                "Review engagement patterns",
            ],
            staleness_alerts=[],
        )
    
    async def get_cycle_status(self, cycle_id: UUID) -> CycleStatusResponse:
        """Get the status of a reflection cycle."""
        result = await self.db.execute(
            select(LifeCycle).where(LifeCycle.id == cycle_id)
        )
        cycle = result.scalars().first()
        
        if not cycle:
            raise ValueError(f"Cycle {cycle_id} not found")
        
        # Get latest draft if exists
        draft_result = await self.db.execute(
            select(LifeCycleDraft)
            .where(LifeCycleDraft.cycle_id == cycle_id)
            .order_by(desc(LifeCycleDraft.created_at))
            .limit(1)
        )
        draft = draft_result.scalars().first()
        
        draft_summary = None
        if draft and draft.draft_json:
            try:
                draft_summary = ReflectionSummary(**draft.draft_json)
            except Exception:
                pass
        
        return CycleStatusResponse(
            cycle_id=cycle.id,
            persona_id=cycle.persona_id,
            status=cycle.status,
            cycle_type=cycle.cycle_type,
            started_at=cycle.started_at,
            finished_at=cycle.finished_at,
            draft=draft_summary,
        )
    
    async def approve_cycle(self, request: CycleApproveRequest) -> CycleApproveResponse:
        """Approve a reflection cycle and optionally apply changes."""
        result = await self.db.execute(
            select(LifeCycle).where(LifeCycle.id == request.cycle_id)
        )
        cycle = result.scalars().first()
        
        if not cycle:
            raise ValueError(f"Cycle {request.cycle_id} not found")
        
        if cycle.status != "awaiting_approval":
            raise ValueError(f"Cycle is not awaiting approval (status: {cycle.status})")
        
        persona = await self._get_persona(cycle.persona_id)
        
        # Get the draft
        draft_result = await self.db.execute(
            select(LifeCycleDraft)
            .where(LifeCycleDraft.cycle_id == cycle.id)
            .order_by(desc(LifeCycleDraft.created_at))
            .limit(1)
        )
        draft = draft_result.scalars().first()
        
        export_paths = None
        new_version = None
        
        if request.confirm:
            cycle.status = "committed"
            
            # Apply persona adjustments if requested
            if request.apply_adjustments and draft and draft.draft_json.get("suggested_adjustments"):
                new_version = await self._apply_adjustments(
                    persona, 
                    draft.draft_json["suggested_adjustments"],
                    cycle.run_id,
                )
            
            # Export reflection files
            export_paths = await self._export_life_files(persona, draft)
            
            # Audit log
            await self._audit_log(
                LIFE_AUDIT_EVENTS["CYCLE_COMMITTED"],
                "life_cycle",
                cycle.id,
                {"applied_adjustments": request.apply_adjustments},
            )
        
        return CycleApproveResponse(
            cycle_id=cycle.id,
            status=cycle.status,
            persona_version=new_version,
            export_paths=export_paths,
            message="Cycle committed successfully" if request.confirm else "Review pending",
        )
    
    async def _apply_adjustments(
        self,
        persona: Persona,
        adjustments: List[Dict],
        run_id: UUID,
    ) -> str:
        """Apply suggested adjustments to persona core."""
        # Get current version
        current_version = await self._get_active_persona_version(persona)
        if not current_version:
            return None
        
        # Parse current version number and increment
        try:
            major, minor = current_version.version.split(".")
            new_version = f"{major}.{int(minor) + 1}"
        except:
            new_version = "1.1"
        
        # Apply adjustments (simplified - just log them)
        new_core = dict(current_version.core_json)
        
        # Create new version
        version = PersonaVersion(
            persona_id=persona.id,
            version=new_version,
            core_json=new_core,
            reason=f"Life cycle adjustments from run {run_id}",
        )
        self.db.add(version)
        
        # Update persona active version
        persona.active_version = new_version
        
        return new_version
    
    async def _export_life_files(
        self,
        persona: Persona,
        draft: Optional[LifeCycleDraft],
    ) -> Dict[str, str]:
        """Export life files to persona directory."""
        base_path = Path(settings.PERSONAS_BASE_DIR) / persona.slug / "life"
        base_path.mkdir(parents=True, exist_ok=True)
        
        paths = {}
        
        # Export latest reflection
        if draft and draft.draft_json:
            reflection_path = base_path / "latest_reflection.md"
            with open(reflection_path, "w") as f:
                data = draft.draft_json
                f.write(f"# Reflection - {datetime.utcnow().strftime('%Y-%m-%d')}\n\n")
                f.write(f"## Summary\n{data.get('summary', 'No summary')}\n\n")
                f.write("## Key Insights\n")
                for insight in data.get("key_insights", []):
                    f.write(f"- {insight}\n")
                f.write("\n## Next Actions\n")
                for action in data.get("next_actions", []):
                    f.write(f"- {action}\n")
            paths["reflection"] = str(reflection_path)
        
        # Export metrics
        metrics_path = base_path / "metrics.json"
        result = await self.db.execute(
            select(LifeMetric)
            .where(LifeMetric.persona_id == persona.id)
            .order_by(desc(LifeMetric.computed_at))
            .limit(100)
        )
        metrics = [
            {
                "key": m.metric_key,
                "value": float(m.metric_value),
                "period_start": m.period_start.isoformat(),
                "period_end": m.period_end.isoformat(),
            }
            for m in result.scalars().all()
        ]
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)
        paths["metrics"] = str(metrics_path)
        
        # Export recommendations
        recommendations_path = base_path / "recommendations.json"
        result = await self.db.execute(
            select(Recommendation)
            .where(
                and_(
                    Recommendation.persona_id == persona.id,
                    Recommendation.source == "life",
                )
            )
            .order_by(desc(Recommendation.created_at))
            .limit(20)
        )
        recs = [r.rec_json for r in result.scalars().all()]
        with open(recommendations_path, "w") as f:
            json.dump(recs, f, indent=2)
        paths["recommendations"] = str(recommendations_path)
        
        return paths
    
    # ========================
    # Helper Methods
    # ========================
    
    async def _get_persona(self, persona_id: UUID) -> Optional[Persona]:
        """Get persona by ID."""
        result = await self.db.execute(
            select(Persona).where(Persona.id == persona_id)
        )
        return result.scalars().first()
    
    async def _get_active_persona_version(self, persona: Persona) -> Optional[PersonaVersion]:
        """Get active persona version."""
        result = await self.db.execute(
            select(PersonaVersion)
            .where(
                and_(
                    PersonaVersion.persona_id == persona.id,
                    PersonaVersion.version == persona.active_version,
                )
            )
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
