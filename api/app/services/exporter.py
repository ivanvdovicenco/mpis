"""
MPIS Genesis API - Persona Exporter Service

Handles exporting persona files to the filesystem.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.persona import Persona, PersonaVersion, Source
from app.schemas.persona import PersonaCore

logger = logging.getLogger(__name__)
settings = get_settings()


class PersonaExporter:
    """
    Service for exporting persona files to disk.
    
    Creates the standard persona folder structure with all required files.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.base_dir = Path(settings.PERSONAS_BASE_DIR)
    
    async def export_persona(
        self,
        persona_id: UUID,
        persona_slug: str,
        version: str,
        core_json: dict,
        concepts_json: dict,
        job_id: Optional[UUID] = None
    ) -> Dict[str, str]:
        """
        Export persona to filesystem.
        
        Creates the full persona folder structure:
        /personas/<slug>/
          core/persona_core.json
          core/credo.json
          core/ethos.json
          core/theologic.txt
          core/tone_profile.json
          core/style.json
          core/language_profile.json
          memory/concepts.json
          memory/sources_index.json
          docs/readme.md
          docs/usage_prompt.txt
          docs/changelog.json
          docs/technical_spec.json
        
        Args:
            persona_id: Persona ID
            persona_slug: Persona slug for folder name
            version: Version string (e.g., "1.0")
            core_json: Complete persona core JSON
            concepts_json: Extracted concepts
            job_id: Optional job ID for source lookup
            
        Returns:
            Dict of created file paths
        """
        persona_dir = self.base_dir / persona_slug
        
        # Create directory structure
        (persona_dir / "core").mkdir(parents=True, exist_ok=True)
        (persona_dir / "memory").mkdir(exist_ok=True)
        (persona_dir / "docs").mkdir(exist_ok=True)
        
        created_files = {}
        
        # Parse core JSON with defaults
        core = PersonaCore(**(core_json or {}))
        
        # === CORE FILES ===
        
        # persona_core.json (complete)
        core_path = persona_dir / "core" / "persona_core.json"
        core_path.write_text(
            json.dumps(core_json, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["persona_core.json"] = str(core_path)
        
        # credo.json
        credo_path = persona_dir / "core" / "credo.json"
        credo_path.write_text(
            json.dumps(core.credo.model_dump(), indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["credo.json"] = str(credo_path)
        
        # ethos.json
        ethos_path = persona_dir / "core" / "ethos.json"
        ethos_path.write_text(
            json.dumps(core.ethos.model_dump(), indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["ethos.json"] = str(ethos_path)
        
        # theologic.txt
        theologic_path = persona_dir / "core" / "theologic.txt"
        theologic_content = f"""# Theo-Logic Profile

## Reasoning Principles
{chr(10).join('- ' + p for p in core.theo_logic.principles)}

## Reasoning Style
{core.theo_logic.reasoning_style}
"""
        theologic_path.write_text(theologic_content, encoding='utf-8')
        created_files["theologic.txt"] = str(theologic_path)
        
        # tone_profile.json
        tone_path = persona_dir / "core" / "tone_profile.json"
        tone_path.write_text(
            json.dumps({
                "emotional_tone": core.ethos.emotional_tone,
                "voice": core.style.voice,
                "cadence": core.style.cadence
            }, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["tone_profile.json"] = str(tone_path)
        
        # style.json
        style_path = persona_dir / "core" / "style.json"
        style_path.write_text(
            json.dumps(core.style.model_dump(), indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["style.json"] = str(style_path)
        
        # language_profile.json
        lang_path = persona_dir / "core" / "language_profile.json"
        lang_path.write_text(
            json.dumps({
                "language": core.language,
                "lexicon": core.lexicon.model_dump()
            }, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["language_profile.json"] = str(lang_path)
        
        # === MEMORY FILES ===
        
        # concepts.json
        concepts_path = persona_dir / "memory" / "concepts.json"
        concepts_path.write_text(
            json.dumps(concepts_json, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["concepts.json"] = str(concepts_path)
        
        # sources_index.json
        sources_index = await self._build_sources_index(job_id)
        sources_index_path = persona_dir / "memory" / "sources_index.json"
        sources_index_path.write_text(
            json.dumps(sources_index, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["sources_index.json"] = str(sources_index_path)
        
        # === DOCS FILES ===
        
        # readme.md
        readme_path = persona_dir / "docs" / "readme.md"
        readme_content = self._generate_readme(core, persona_slug, version)
        readme_path.write_text(readme_content, encoding='utf-8')
        created_files["readme.md"] = str(readme_path)
        
        # usage_prompt.txt
        usage_path = persona_dir / "docs" / "usage_prompt.txt"
        usage_content = self._generate_usage_prompt(core, persona_slug)
        usage_path.write_text(usage_content, encoding='utf-8')
        created_files["usage_prompt.txt"] = str(usage_path)
        
        # changelog.json
        changelog_path = persona_dir / "docs" / "changelog.json"
        changelog_path.write_text(
            json.dumps({
                "versions": [
                    {
                        "version": version,
                        "date": datetime.utcnow().isoformat() + "Z",
                        "changes": ["Initial persona creation"]
                    }
                ]
            }, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["changelog.json"] = str(changelog_path)
        
        # technical_spec.json
        spec_path = persona_dir / "docs" / "technical_spec.json"
        spec_path.write_text(
            json.dumps({
                "persona_id": str(persona_id),
                "slug": persona_slug,
                "version": version,
                "language": core.language,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "files": list(created_files.keys()),
                "qdrant_collections": [
                    settings.QDRANT_COLLECTION_SOURCES,
                    settings.QDRANT_COLLECTION_CORE
                ]
            }, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )
        created_files["technical_spec.json"] = str(spec_path)
        
        logger.info(f"Exported persona to {persona_dir}")
        
        return {
            "base_path": str(persona_dir),
            "files": created_files
        }
    
    async def _build_sources_index(self, job_id: Optional[UUID]) -> dict:
        """Build sources index from database."""
        if not job_id:
            return {"sources": []}
        
        result = await self.db.execute(
            select(Source).where(Source.job_id == job_id)
        )
        sources = result.scalars().all()
        
        return {
            "sources": [
                {
                    "id": str(s.id),
                    "type": s.source_type,
                    "ref": s.source_ref,
                    "provider": s.metadata.get("provider", "unknown"),
                    "status": s.metadata.get("status", "unknown"),
                    "content_hash": s.content_hash
                }
                for s in sources
            ],
            "total": len(sources),
            "by_type": self._count_by_type(sources)
        }
    
    def _count_by_type(self, sources: List[Source]) -> dict:
        """Count sources by type."""
        counts = {}
        for s in sources:
            counts[s.source_type] = counts.get(s.source_type, 0) + 1
        return counts
    
    def _generate_readme(self, core: PersonaCore, slug: str, version: str) -> str:
        """Generate persona readme.md content."""
        return f"""# Persona: {slug}

**Version:** {version}  
**Language:** {core.language}  
**Inspired by:** {core.origin.inspiration_source}  
**Created:** {core.origin.created_at}

## Overview

{core.credo.summary}

## Core Beliefs

{chr(10).join('- ' + s for s in core.credo.statements)}

## Character Traits

**Virtues:** {', '.join(core.ethos.virtues)}  
**Tone:** {', '.join(core.ethos.emotional_tone)}

## Communication Style

**Voice:** {core.style.voice}  
**Cadence:** {core.style.cadence}

### Do's
{chr(10).join('- ' + d for d in core.style.dos)}

### Don'ts
{chr(10).join('- ' + d for d in core.style.donts)}

## Topics

**Primary:** {', '.join(core.topics.primary)}  
**Secondary:** {', '.join(core.topics.secondary)}

## Signature Phrases

{chr(10).join('- "' + p + '"' for p in core.lexicon.signature_phrases)}

---

*Generated by MPIS Genesis Engine*
"""
    
    def _generate_usage_prompt(self, core: PersonaCore, slug: str) -> str:
        """Generate usage prompt for LLM integration."""
        return f"""You are {slug}, a persona with the following characteristics:

## Core Identity
{core.credo.summary}

## Key Beliefs
{chr(10).join('- ' + s for s in core.credo.statements[:5])}

## Character
- Virtues: {', '.join(core.ethos.virtues)}
- Avoid: {', '.join(core.ethos.anti_patterns)}
- Tone: {', '.join(core.ethos.emotional_tone)}

## How You Communicate
- Voice: {core.style.voice}
- Cadence: {core.style.cadence}

## Topics You Focus On
- Primary: {', '.join(core.topics.primary)}
- Secondary: {', '.join(core.topics.secondary)}

## Your Vocabulary
- Signature phrases: {', '.join('"' + p + '"' for p in core.lexicon.signature_phrases[:5])}
- Keywords to use: {', '.join(core.lexicon.keywords[:10])}
{('- Words to avoid: ' + ', '.join(core.lexicon.taboo_words)) if core.lexicon.taboo_words else ''}

## Reasoning Approach
{core.theo_logic.reasoning_style}

---
Always stay true to these characteristics while responding naturally and authentically.
"""
