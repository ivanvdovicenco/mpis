"""
MPIS Genesis API - Genesis Service

Main orchestration service for the persona generation workflow.
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.config import get_settings
from app.models.genesis import GenesisJob, GenesisDraft, GenesisMessage
from app.models.persona import Persona, PersonaVersion, Source
from app.schemas.genesis import (
    GenesisStartRequest,
    GenesisStartResponse,
    GenesisStatusResponse,
    GenesisApproveRequest,
    GenesisApproveResponse,
    PersonaCard,
    ProgressInfo,
    EditOperation,
)
from app.schemas.persona import PersonaCore
from app.services.sources import SourceCollector
from app.services.llm import LLMService
from app.services.qdrant import QdrantService
from app.services.exporter import PersonaExporter
from app.services.audit import AuditService
from app.utils.text import slugify, chunk_text, extract_text_preview
from app.utils.json_patch import apply_json_patch, JsonPatchError

logger = logging.getLogger(__name__)
settings = get_settings()


class GenesisService:
    """
    Main service for persona generation workflow.
    
    Orchestrates the full pipeline:
    1. Source collection (YouTube, GDrive, Web)
    2. Corpus processing and chunking
    3. Concept extraction
    4. Persona core generation
    5. Human approval loop
    6. Persona commit and export
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.llm = LLMService()
        self.qdrant = QdrantService()
        self.exporter = PersonaExporter(db)
        self.audit = AuditService(db)
    
    async def start_genesis(self, request: GenesisStartRequest) -> GenesisStartResponse:
        """
        Start a new persona generation job.
        
        Creates a job, collects sources, processes corpus,
        extracts concepts, and generates initial draft.
        
        Args:
            request: Genesis start request with persona parameters
            
        Returns:
            GenesisStartResponse with job ID and initial status
        """
        # Generate slug
        slug = slugify(request.persona_name)
        
        # Ensure slug is unique
        slug = await self._ensure_unique_slug(slug)
        
        # Create genesis job
        job = GenesisJob(
            persona_name=request.persona_name,
            slug=slug,
            input_json={
                "persona_name": request.persona_name,
                "inspiration_source": request.inspiration_source,
                "language": request.language,
                "public_persona": request.public_persona,
                "public_name": request.public_name,
                "gdrive_folder_id": request.gdrive_folder_id,
                "notes": request.notes,
                "sources": [s.model_dump() for s in request.sources]
            },
            config_json={
                "chunk_min_tokens": settings.CHUNK_MIN_TOKENS,
                "chunk_max_tokens": settings.CHUNK_MAX_TOKENS,
                "dry_run": settings.DRY_RUN
            },
            status="queued"
        )
        
        self.db.add(job)
        await self.db.flush()
        
        await self.audit.log(
            AuditService.SOURCES_DISCOVERED,
            entity_type="genesis_job",
            entity_id=job.id,
            job_id=job.id,
            details={"persona_name": request.persona_name}
        )
        
        try:
            # Update status to collecting
            job.status = "collecting"
            await self.db.flush()
            
            # Collect sources
            collector = SourceCollector(self.db, job.id, slug)
            source_results = await collector.collect_all(
                gdrive_folder_id=request.gdrive_folder_id,
                public_persona=request.public_persona,
                public_name=request.public_name,
                additional_sources=[s.model_dump() for s in request.sources]
            )
            
            await self.audit.log(
                AuditService.SOURCES_FETCHED,
                job_id=job.id,
                details=source_results
            )
            
            # Update status to processing
            job.status = "processing"
            await self.db.flush()
            
            # Get all source texts
            texts = await collector.get_all_source_texts()
            
            # Process corpus - chunk texts
            all_chunks = []
            for text in texts:
                chunks = chunk_text(
                    text,
                    min_tokens=settings.CHUNK_MIN_TOKENS,
                    max_tokens=settings.CHUNK_MAX_TOKENS
                )
                all_chunks.extend(chunks)
            
            await self.audit.log(
                AuditService.CORPUS_CHUNKED,
                job_id=job.id,
                details={"chunk_count": len(all_chunks)}
            )
            
            # Generate embeddings and store in Qdrant
            if all_chunks and self.qdrant.is_available():
                await self.qdrant.ensure_collections()
                embeddings = await self.llm.generate_embeddings(all_chunks[:100])  # Limit
                
                chunk_dicts = [
                    {
                        "chunk_id": f"{job.id}_{i}",
                        "text": c,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    for i, c in enumerate(all_chunks[:100])
                ]
                
                await self.qdrant.upsert_source_embeddings(
                    job_id=job.id,
                    persona_slug=slug,
                    chunks=chunk_dicts,
                    embeddings=embeddings
                )
                
                await self.audit.log(
                    AuditService.EMBEDDINGS_UPSERTED,
                    job_id=job.id,
                    details={"count": len(embeddings)}
                )
            
            # Extract concepts
            concepts = await self.llm.extract_concepts(texts)
            
            await self.audit.log(
                AuditService.CONCEPTS_EXTRACTED,
                job_id=job.id,
                details=concepts.model_dump()
            )
            
            # Generate persona core
            persona_core = await self.llm.generate_persona_core(
                persona_name=request.persona_name,
                inspiration_source=request.inspiration_source,
                language=request.language,
                concepts=concepts,
                texts=texts
            )
            
            # Generate human prompt
            human_prompt = await self.llm.generate_human_prompt(persona_core, draft_no=1)
            
            # Create first draft
            draft = GenesisDraft(
                job_id=job.id,
                draft_no=1,
                draft_core_json=persona_core.model_dump(),
                human_prompt=human_prompt
            )
            self.db.add(draft)
            
            # Store concepts in job config
            job.config_json = {
                **job.config_json,
                "concepts": concepts.model_dump()
            }
            
            # Update job status
            job.status = "awaiting_approval"
            job.draft_no = 1
            
            await self.db.flush()
            
            await self.audit.log(
                AuditService.DRAFT_GENERATED,
                job_id=job.id,
                details={"draft_no": 1}
            )
            
            await self.audit.log(
                AuditService.APPROVAL_REQUESTED,
                job_id=job.id,
                details={"draft_no": 1}
            )
            
            # Build preview card
            preview = self._build_persona_card(
                persona_id=None,
                name=request.persona_name,
                slug=slug,
                core=persona_core
            )
            
            return GenesisStartResponse(
                job_id=job.id,
                status=job.status,
                draft_no=job.draft_no,
                human_prompt=human_prompt,
                preview=preview
            )
            
        except Exception as e:
            logger.error(f"Genesis error: {e}")
            job.status = "failed"
            job.error = str(e)
            await self.db.flush()
            raise
    
    async def get_status(self, job_id: UUID) -> GenesisStatusResponse:
        """
        Get current status of a genesis job.
        
        Args:
            job_id: Genesis job ID
            
        Returns:
            GenesisStatusResponse with current status
        """
        result = await self.db.execute(
            select(GenesisJob).where(GenesisJob.id == job_id)
        )
        job = result.scalars().first()
        
        if not job:
            raise ValueError(f"Job not found: {job_id}")
        
        # Get latest draft
        draft_result = await self.db.execute(
            select(GenesisDraft)
            .where(GenesisDraft.job_id == job_id)
            .where(GenesisDraft.draft_no == job.draft_no)
        )
        draft = draft_result.scalars().first()
        
        # Build progress info
        progress = self._build_progress(job)
        
        # Build preview if draft exists
        preview = None
        human_prompt = None
        if draft:
            core = PersonaCore(**draft.draft_core_json)
            preview = self._build_persona_card(
                persona_id=job.persona_id,
                name=job.persona_name,
                slug=job.slug,
                core=core
            )
            human_prompt = draft.human_prompt
        
        errors = [job.error] if job.error else []
        
        return GenesisStatusResponse(
            job_id=job.id,
            status=job.status,
            progress=progress,
            draft_no=job.draft_no,
            human_prompt=human_prompt,
            preview=preview,
            errors=errors
        )
    
    async def approve(self, request: GenesisApproveRequest) -> GenesisApproveResponse:
        """
        Process approval or edits for a genesis job.
        
        If confirm=true, commits the persona.
        If edits provided, applies edits and creates new draft.
        
        Args:
            request: Approval request with job_id, draft_no, confirm/edits
            
        Returns:
            GenesisApproveResponse with updated status
        """
        result = await self.db.execute(
            select(GenesisJob).where(GenesisJob.id == request.job_id)
        )
        job = result.scalars().first()
        
        if not job:
            raise ValueError(f"Job not found: {request.job_id}")
        
        if job.status not in ["awaiting_approval"]:
            raise ValueError(f"Job is not awaiting approval: {job.status}")
        
        if job.draft_no != request.draft_no:
            raise ValueError(
                f"Draft number mismatch: expected {job.draft_no}, got {request.draft_no}"
            )
        
        # Get current draft
        draft_result = await self.db.execute(
            select(GenesisDraft)
            .where(GenesisDraft.job_id == request.job_id)
            .where(GenesisDraft.draft_no == request.draft_no)
        )
        current_draft = draft_result.scalars().first()
        
        if not current_draft:
            raise ValueError(f"Draft not found: {request.draft_no}")
        
        current_core = current_draft.draft_core_json
        
        # Apply edits if provided
        if request.edits:
            try:
                updated_core = apply_json_patch(current_core, request.edits)
            except JsonPatchError as e:
                raise ValueError(f"Edit error: {e}")
            
            # Validate updated core
            try:
                validated_core = PersonaCore(**updated_core)
            except Exception as e:
                raise ValueError(f"Validation error: {e}")
            
            # Generate new human prompt
            new_draft_no = job.draft_no + 1
            human_prompt = await self.llm.generate_human_prompt(validated_core, new_draft_no)
            
            # Create new draft
            new_draft = GenesisDraft(
                job_id=job.id,
                draft_no=new_draft_no,
                draft_core_json=updated_core,
                human_prompt=human_prompt
            )
            self.db.add(new_draft)
            
            job.draft_no = new_draft_no
            await self.db.flush()
            
            await self.audit.log(
                AuditService.APPROVAL_APPLIED,
                job_id=job.id,
                details={"draft_no": new_draft_no, "edits_count": len(request.edits)}
            )
            
            preview = self._build_persona_card(
                persona_id=None,
                name=job.persona_name,
                slug=job.slug,
                core=validated_core
            )
            
            return GenesisApproveResponse(
                job_id=job.id,
                status=job.status,
                draft_no=new_draft_no,
                human_prompt=human_prompt,
                preview=preview
            )
        
        # Confirm - commit the persona
        if request.confirm:
            return await self._commit_persona(job, current_core)
        
        raise ValueError("Either confirm=true or edits[] must be provided")
    
    async def _commit_persona(
        self,
        job: GenesisJob,
        core_json: dict
    ) -> GenesisApproveResponse:
        """
        Commit a persona from the approved draft.
        
        Creates persona record, version, and exports files.
        """
        # Create persona record
        persona = Persona(
            name=job.persona_name,
            slug=job.slug,
            description=core_json.get("credo", {}).get("summary", ""),
            language=core_json.get("language", "en"),
            active_version="1.0"
        )
        self.db.add(persona)
        await self.db.flush()
        
        # Create version record
        version = PersonaVersion(
            persona_id=persona.id,
            version="1.0",
            core_json=core_json,
            reason="Initial persona creation via Genesis"
        )
        self.db.add(version)
        
        # Update sources with persona_id
        await self.db.execute(
            update(Source)
            .where(Source.job_id == job.id)
            .values(persona_id=persona.id)
        )
        
        # Get concepts from job config
        concepts_json = job.config_json.get("concepts", {})
        
        # Export persona files
        export_result = await self.exporter.export_persona(
            persona_id=persona.id,
            persona_slug=job.slug,
            version="1.0",
            core_json=core_json,
            concepts_json=concepts_json,
            job_id=job.id
        )
        
        # Store core embeddings in Qdrant
        memory_pending = False
        if self.qdrant.is_available():
            try:
                core = PersonaCore(**core_json)
                core_sections = [
                    {"section": "credo", "text": core.credo.summary + " " + " ".join(core.credo.statements)},
                    {"section": "ethos", "text": " ".join(core.ethos.virtues + core.ethos.emotional_tone)},
                    {"section": "style", "text": core.style.voice + " " + core.style.cadence}
                ]
                texts = [s["text"] for s in core_sections]
                embeddings = await self.llm.generate_embeddings(texts)
                
                await self.qdrant.upsert_core_embeddings(
                    persona_id=persona.id,
                    persona_slug=job.slug,
                    core_sections=core_sections,
                    embeddings=embeddings
                )
            except Exception as e:
                logger.warning(f"Failed to store core embeddings: {e}")
                memory_pending = True
        else:
            memory_pending = True
        
        # Update job status
        job.status = "committed_with_memory_pending" if memory_pending else "committed"
        job.persona_id = persona.id
        await self.db.flush()
        
        await self.audit.log(
            AuditService.PERSONA_COMMITTED,
            entity_type="persona",
            entity_id=persona.id,
            job_id=job.id,
            details={"version": "1.0", "memory_pending": memory_pending}
        )
        
        await self.audit.log(
            AuditService.EXPORT_COMPLETED,
            entity_type="persona",
            entity_id=persona.id,
            job_id=job.id,
            details=export_result
        )
        
        preview = self._build_persona_card(
            persona_id=persona.id,
            name=job.persona_name,
            slug=job.slug,
            core=PersonaCore(**core_json),
            version="1.0"
        )
        
        return GenesisApproveResponse(
            job_id=job.id,
            status=job.status,
            draft_no=job.draft_no,
            persona_id=persona.id,
            version="1.0",
            export_paths=export_result,
            preview=preview
        )
    
    async def _ensure_unique_slug(self, slug: str) -> str:
        """Ensure slug is unique by appending number if needed."""
        original_slug = slug
        counter = 1
        
        while True:
            result = await self.db.execute(
                select(Persona).where(Persona.slug == slug)
            )
            if not result.scalars().first():
                # Also check jobs
                job_result = await self.db.execute(
                    select(GenesisJob).where(GenesisJob.slug == slug)
                )
                if not job_result.scalars().first():
                    return slug
            
            counter += 1
            slug = f"{original_slug}-{counter}"
    
    def _build_progress(self, job: GenesisJob) -> ProgressInfo:
        """Build progress info from job status."""
        status_progress = {
            "queued": (0, "Queued"),
            "collecting": (20, "Collecting sources"),
            "processing": (50, "Processing corpus"),
            "awaiting_approval": (80, "Awaiting human approval"),
            "committed": (100, "Completed"),
            "committed_with_memory_pending": (100, "Completed (memory sync pending)"),
            "failed": (0, "Failed")
        }
        
        percent, message = status_progress.get(job.status, (0, "Unknown"))
        
        return ProgressInfo(
            stage=job.status,
            percent=percent,
            message=message
        )
    
    def _build_persona_card(
        self,
        persona_id: Optional[UUID],
        name: str,
        slug: str,
        core: PersonaCore,
        version: str = "draft"
    ) -> PersonaCard:
        """Build persona preview card."""
        return PersonaCard(
            persona_id=persona_id,
            name=name,
            slug=slug,
            active_version=version,
            summary=core.credo.summary,
            top_topics=core.topics.primary[:5],
            dominant_tones=core.ethos.emotional_tone[:3],
            next_actions=self._suggest_next_actions(core)
        )
    
    def _suggest_next_actions(self, core: PersonaCore) -> List[str]:
        """Suggest next actions based on persona state."""
        actions = []
        
        if not core.credo.statements:
            actions.append("Add core belief statements")
        
        if not core.lexicon.signature_phrases:
            actions.append("Add signature phrases")
        
        if len(core.topics.primary) < 3:
            actions.append("Expand primary topics")
        
        if not actions:
            actions = ["Review and confirm persona", "Test with sample prompts"]
        
        return actions[:3]
