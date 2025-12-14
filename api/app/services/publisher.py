"""
MPIS Publisher API - Publisher Service

Handles content planning, generation, approval, and publishing.
"""
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID, uuid4
from pathlib import Path

from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.publisher import (
    ContentPlan, ContentDraft, PublishedItem, ChannelAccount, ItemMetric
)
from app.models.persona import Persona, PersonaVersion, AuditLog
from app.schemas.publisher import (
    ContentPlanCreate,
    ContentPlanResponse,
    ContentGenerateRequest,
    ContentDraftResponse,
    ContentVariant,
    DraftApproveRequest,
    DraftApproveResponse,
    PublishRecordRequest,
    PublishRecordResponse,
    MetricsIngestRequest,
    MetricsIngestResponse,
    PUBLISHER_AUDIT_EVENTS,
)
from app.services.llm import LLMService
from app.services.qdrant import QdrantService

logger = logging.getLogger(__name__)
settings = get_settings()


class PublisherService:
    """
    Service for social content publishing.
    
    Handles content planning, generation, approval, and publishing workflows.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.llm = LLMService()
        self.qdrant = QdrantService()
    
    # ========================
    # Content Planning
    # ========================
    
    async def create_plan(self, request: ContentPlanCreate) -> ContentPlanResponse:
        """
        Create a content plan.
        
        Args:
            request: Plan creation request
            
        Returns:
            Created plan response
        """
        # Verify persona exists
        persona = await self._get_persona(request.persona_id)
        if not persona:
            raise ValueError(f"Persona {request.persona_id} not found")
        
        run_id = uuid4()
        
        # Create plan
        plan = ContentPlan(
            persona_id=request.persona_id,
            title=request.title,
            topic=request.topic,
            goal=request.goal,
            target_audience=request.target_audience,
            channel=request.channel,
            language=request.language,
            max_length=request.max_length,
            schedule_window_start=request.schedule_window_start,
            schedule_window_end=request.schedule_window_end,
            constraints=request.constraints or {},
            status="planned",
            run_id=run_id,
        )
        
        self.db.add(plan)
        await self.db.flush()
        
        # Audit log
        await self._audit_log(
            PUBLISHER_AUDIT_EVENTS["PLAN_CREATED"],
            "content_plan",
            plan.id,
            {"title": request.title, "channel": request.channel},
        )
        
        logger.info(f"Created content plan {plan.id} for persona {persona.slug}")
        
        return ContentPlanResponse(
            id=plan.id,
            persona_id=plan.persona_id,
            title=plan.title,
            topic=plan.topic,
            channel=plan.channel,
            status=plan.status,
            created_at=plan.created_at,
        )
    
    # ========================
    # Content Generation
    # ========================
    
    async def generate_content(self, request: ContentGenerateRequest) -> ContentDraftResponse:
        """
        Generate content draft for a plan.
        
        Args:
            request: Generation request
            
        Returns:
            Generated draft response
        """
        # Get plan
        result = await self.db.execute(
            select(ContentPlan).where(ContentPlan.id == request.plan_id)
        )
        plan = result.scalars().first()
        
        if not plan:
            raise ValueError(f"Plan {request.plan_id} not found")
        
        # Get persona and active version
        persona = await self._get_persona(plan.persona_id)
        persona_version = await self._get_active_persona_version(persona)
        
        # Update plan status
        plan.status = "generating"
        
        run_id = uuid4()
        
        # Get next draft number
        result = await self.db.execute(
            select(ContentDraft)
            .where(ContentDraft.plan_id == plan.id)
            .order_by(desc(ContentDraft.draft_no))
            .limit(1)
        )
        last_draft = result.scalars().first()
        draft_no = (last_draft.draft_no + 1) if last_draft else 1
        
        # Generate content
        variants, provenance = await self._generate_variants(
            plan, persona_version, request.variants, request.options
        )
        
        # Create draft
        draft = ContentDraft(
            plan_id=plan.id,
            persona_version_id=persona_version.id if persona_version else None,
            draft_no=draft_no,
            content_json={"variants": [v.model_dump() for v in variants]},
            provenance=provenance,
            run_id=run_id,
            status="draft",
        )
        
        self.db.add(draft)
        
        # Update plan status
        plan.status = "draft_ready"
        
        await self.db.flush()
        
        # Audit log
        await self._audit_log(
            PUBLISHER_AUDIT_EVENTS["DRAFT_GENERATED"],
            "content_draft",
            draft.id,
            {"plan_id": str(plan.id), "variants": len(variants)},
        )
        
        logger.info(f"Generated draft {draft.id} for plan {plan.id}")
        
        return ContentDraftResponse(
            id=draft.id,
            plan_id=draft.plan_id,
            draft_no=draft.draft_no,
            status=draft.status,
            variants=variants,
            provenance=provenance,
            created_at=draft.created_at,
        )
    
    async def _generate_variants(
        self,
        plan: ContentPlan,
        persona_version: Optional[PersonaVersion],
        num_variants: int,
        options: dict,
    ) -> tuple[List[ContentVariant], dict]:
        """Generate content variants."""
        if self.llm.dry_run:
            return self._mock_variants(plan, num_variants), {"source": "mock"}
        
        # Prepare persona context
        persona_context = ""
        if persona_version and persona_version.core_json:
            core = persona_version.core_json
            persona_context = f"""
Persona Voice Profile:
- Style: {core.get('style', {}).get('voice', 'Friendly and engaging')}
- Tone: {', '.join(core.get('ethos', {}).get('emotional_tone', []))}
- Do: {', '.join(core.get('style', {}).get('dos', [])[:3])}
- Don't: {', '.join(core.get('style', {}).get('donts', [])[:3])}
"""
        
        # Build constraints text
        constraints_text = ""
        if plan.constraints:
            constraints_text = f"Constraints: {json.dumps(plan.constraints)}"
        
        prompt = f"""Generate {num_variants} content variant(s) for social media.

Topic: {plan.topic}
Title/Theme: {plan.title}
Goal: {plan.goal or 'Engage and inform'}
Target Audience: {plan.target_audience or 'General'}
Channel: {plan.channel}
Language: {plan.language}
Max Length: {plan.max_length} characters

{persona_context}
{constraints_text}

Generate as STRICT JSON with this structure:
{{
    "variants": [
        {{
            "variant_no": 1,
            "text": "Main content text...",
            "title": "Hook/Title (optional)",
            "cta": "Call to action (optional)"
        }}
    ],
    "provenance": {{
        "topics_referenced": ["list of topics"],
        "style_elements_used": ["list of style elements"]
    }}
}}

Requirements:
- Keep text under {plan.max_length} characters
- Match the persona's voice and style
- Avoid verbatim quotes longer than 50 characters
- Make content actionable and engaging

Return ONLY valid JSON."""
        
        try:
            response = await self.llm._call_llm(prompt, max_tokens=3000)
            result = self.llm._parse_json_response(response)
            
            variants = [
                ContentVariant(**v) for v in result.get("variants", [])
            ]
            provenance = result.get("provenance", {})
            
            if not variants:
                logger.warning("LLM returned no variants, using fallback")
                return self._mock_variants(plan, num_variants), {"source": "fallback", "reason": "empty_response"}
            
            return variants, provenance
        except Exception as e:
            # Log the error with full context for debugging
            logger.error(f"Error generating variants for plan {plan.id}: {e}", exc_info=True)
            # Return fallback but mark clearly in provenance for monitoring
            return self._mock_variants(plan, num_variants), {
                "source": "fallback", 
                "error": str(e),
                "warning": "LLM generation failed, using mock content"
            }
    
    def _mock_variants(self, plan: ContentPlan, num_variants: int) -> List[ContentVariant]:
        """Return mock variants for DRY_RUN mode."""
        variants = []
        for i in range(num_variants):
            variants.append(ContentVariant(
                variant_no=i + 1,
                text=f"[Mock content about {plan.topic}] This is a sample post that would be generated based on the persona's voice and the topic '{plan.title}'. It would be engaging and match the target audience.",
                title=f"Variant {i + 1}: {plan.title[:50]}",
                cta="What do you think? Share your thoughts below!",
            ))
        return variants
    
    # ========================
    # Draft Approval
    # ========================
    
    async def get_draft(self, draft_id: UUID) -> ContentDraftResponse:
        """Get a content draft by ID."""
        result = await self.db.execute(
            select(ContentDraft).where(ContentDraft.id == draft_id)
        )
        draft = result.scalars().first()
        
        if not draft:
            raise ValueError(f"Draft {draft_id} not found")
        
        variants = [
            ContentVariant(**v) for v in draft.content_json.get("variants", [])
        ]
        
        return ContentDraftResponse(
            id=draft.id,
            plan_id=draft.plan_id,
            draft_no=draft.draft_no,
            status=draft.status,
            variants=variants,
            provenance=draft.provenance,
            created_at=draft.created_at,
        )
    
    async def approve_draft(self, request: DraftApproveRequest) -> DraftApproveResponse:
        """Approve a content draft."""
        result = await self.db.execute(
            select(ContentDraft).where(ContentDraft.id == request.draft_id)
        )
        draft = result.scalars().first()
        
        if not draft:
            raise ValueError(f"Draft {request.draft_id} not found")
        
        if draft.status != "draft":
            raise ValueError(f"Draft is not in draft status (status: {draft.status})")
        
        # Get plan
        plan_result = await self.db.execute(
            select(ContentPlan).where(ContentPlan.id == draft.plan_id)
        )
        plan = plan_result.scalars().first()
        
        if request.confirm:
            draft.status = "approved"
            plan.status = "approved"
            
            # Apply edits if provided
            if request.edits:
                variants = draft.content_json.get("variants", [])
                if request.selected_variant <= len(variants):
                    variants[request.selected_variant - 1].update(request.edits)
                    draft.content_json = {"variants": variants}
            
            # Audit log
            await self._audit_log(
                PUBLISHER_AUDIT_EVENTS["DRAFT_APPROVED"],
                "content_draft",
                draft.id,
                {"selected_variant": request.selected_variant},
            )
        
        return DraftApproveResponse(
            draft_id=draft.id,
            status=draft.status,
            plan_status=plan.status,
            ready_to_publish=draft.status == "approved",
        )
    
    # ========================
    # Publishing
    # ========================
    
    async def record_publish(self, request: PublishRecordRequest) -> PublishRecordResponse:
        """Record a publish result from n8n or external system."""
        # Get draft
        result = await self.db.execute(
            select(ContentDraft).where(ContentDraft.id == request.draft_id)
        )
        draft = result.scalars().first()
        
        if not draft:
            raise ValueError(f"Draft {request.draft_id} not found")
        
        # Get plan and update status
        plan_result = await self.db.execute(
            select(ContentPlan).where(ContentPlan.id == draft.plan_id)
        )
        plan = plan_result.scalars().first()
        plan.status = "published"
        
        # Create published item
        published = PublishedItem(
            draft_id=draft.id,
            channel=request.channel,
            channel_item_id=request.channel_item_id,
            channel_url=request.channel_url,
            published_payload=request.published_payload or {},
            persona_version_used=request.persona_version_used,
        )
        
        self.db.add(published)
        await self.db.flush()
        
        # Export published files
        persona = await self._get_persona(plan.persona_id)
        await self._export_published(persona, published, draft)
        
        # Audit log
        await self._audit_log(
            PUBLISHER_AUDIT_EVENTS["CONTENT_PUBLISHED"],
            "published_item",
            published.id,
            {"channel": request.channel, "channel_item_id": request.channel_item_id},
        )
        
        logger.info(f"Recorded publish {published.id} for draft {draft.id}")
        
        return PublishRecordResponse(
            id=published.id,
            draft_id=published.draft_id,
            channel=published.channel,
            published_at=published.published_at,
        )
    
    async def _export_published(
        self,
        persona: Persona,
        published: PublishedItem,
        draft: ContentDraft,
    ) -> None:
        """Export published item to persona directory."""
        base_path = Path(settings.PERSONAS_BASE_DIR) / persona.slug / "publisher" / "published"
        base_path.mkdir(parents=True, exist_ok=True)
        
        # Export published item
        item_path = base_path / f"{published.id}.json"
        with open(item_path, "w") as f:
            json.dump({
                "id": str(published.id),
                "channel": published.channel,
                "channel_item_id": published.channel_item_id,
                "channel_url": published.channel_url,
                "published_at": published.published_at.isoformat(),
                "content": draft.content_json,
            }, f, indent=2)
    
    # ========================
    # Metrics Ingestion
    # ========================
    
    async def ingest_metrics(self, request: MetricsIngestRequest) -> MetricsIngestResponse:
        """Ingest metrics for a published item."""
        # Verify published item exists
        result = await self.db.execute(
            select(PublishedItem).where(PublishedItem.id == request.published_item_id)
        )
        published = result.scalars().first()
        
        if not published:
            raise ValueError(f"Published item {request.published_item_id} not found")
        
        recorded_at = datetime.utcnow()
        count = 0
        
        for metric in request.metrics:
            if "type" not in metric or "value" not in metric:
                continue
            
            item_metric = ItemMetric(
                published_item_id=published.id,
                metric_type=metric["type"],
                metric_value=float(metric["value"]),
                recorded_at=recorded_at,
                source=request.source,
                meta=metric.get("meta", {}),
            )
            self.db.add(item_metric)
            count += 1
        
        await self.db.flush()
        
        # Audit log
        await self._audit_log(
            PUBLISHER_AUDIT_EVENTS["METRICS_INGESTED"],
            "item_metrics",
            published.id,
            {"metrics_count": count, "source": request.source},
        )
        
        logger.info(f"Ingested {count} metrics for published item {published.id}")
        
        return MetricsIngestResponse(
            published_item_id=published.id,
            metrics_ingested=count,
            recorded_at=recorded_at,
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
