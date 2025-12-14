"""
MPIS Genesis API - LLM Service

Handles LLM integration for persona generation including:
- Concept extraction
- Persona core generation
- JSON validation and repair
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.config import get_settings
from app.schemas.persona import PersonaCore
from app.schemas.genesis import ConceptsOutput

logger = logging.getLogger(__name__)
settings = get_settings()


class LLMService:
    """
    Service for LLM-powered persona generation.
    
    Supports OpenAI and Anthropic providers with automatic JSON repair.
    Includes DRY_RUN mode for testing without API calls.
    """
    
    def __init__(self):
        """Initialize LLM client based on configuration."""
        self.provider = settings.LLM_PROVIDER
        self.dry_run = settings.DRY_RUN
        
        if not self.dry_run:
            if self.provider == "openai" and settings.OPENAI_API_KEY:
                from openai import OpenAI
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            elif self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
                from anthropic import Anthropic
                self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            else:
                logger.warning("No LLM API key configured, using DRY_RUN mode")
                self.dry_run = True
    
    async def extract_concepts(self, texts: List[str]) -> ConceptsOutput:
        """
        Extract concepts from source texts.
        
        Generates themes, virtues, tone, recurring ideas, and notable distinctions.
        
        Args:
            texts: List of source text content
            
        Returns:
            ConceptsOutput with extracted concepts
        """
        if self.dry_run:
            return self._mock_concepts()
        
        # Combine texts with truncation
        combined_text = self._truncate_texts(texts, max_tokens=10000)
        
        prompt = """Analyze the following texts and extract key concepts for building a persona profile.

Return ONLY valid JSON with this structure:
{
    "themes": ["list of 3-7 main themes"],
    "virtues": ["list of 3-5 core virtues or strengths"],
    "tone": ["list of 2-4 emotional/communication tones"],
    "recurring_ideas": ["list of 5-10 recurring ideas or motifs"],
    "notable_distinctions": ["list of 2-5 unique perspectives or approaches"]
}

Texts to analyze:
---
""" + combined_text + """
---

Return ONLY the JSON object, no other text."""

        try:
            response_text = await self._call_llm(prompt)
            concepts_dict = self._parse_json_response(response_text)
            return ConceptsOutput(**concepts_dict)
        except Exception as e:
            logger.error(f"Error extracting concepts: {e}")
            return self._mock_concepts()
    
    async def generate_persona_core(
        self,
        persona_name: str,
        inspiration_source: Optional[str],
        language: str,
        concepts: ConceptsOutput,
        texts: List[str]
    ) -> PersonaCore:
        """
        Generate complete persona_core.json from concepts and sources.
        
        Args:
            persona_name: Name for the persona
            inspiration_source: Primary inspiration source
            language: Primary language
            concepts: Extracted concepts
            texts: Source texts for reference
            
        Returns:
            PersonaCore with all required blocks
        """
        if self.dry_run:
            return self._mock_persona_core(persona_name, inspiration_source, language, concepts)
        
        combined_text = self._truncate_texts(texts, max_tokens=8000)
        
        prompt = f"""Create a complete persona profile for "{persona_name}" based on the following concepts and source texts.

The persona should be inspired by: {inspiration_source or 'the provided source materials'}
Primary language: {language}

Extracted concepts:
- Themes: {', '.join(concepts.themes)}
- Virtues: {', '.join(concepts.virtues)}
- Tone: {', '.join(concepts.tone)}
- Recurring ideas: {', '.join(concepts.recurring_ideas)}
- Notable distinctions: {', '.join(concepts.notable_distinctions)}

Sample source text (for style reference):
---
{combined_text[:3000]}
---

Generate a complete persona profile as STRICT JSON with ALL these required fields:
{{
    "credo": {{
        "summary": "Brief philosophical summary (1-2 sentences)",
        "statements": ["3-7 core belief statements"]
    }},
    "ethos": {{
        "virtues": ["3-5 character virtues"],
        "anti_patterns": ["2-4 behaviors to avoid"],
        "emotional_tone": ["2-4 emotional characteristics"]
    }},
    "theo_logic": {{
        "principles": ["3-5 reasoning principles"],
        "reasoning_style": "Description of thinking approach"
    }},
    "style": {{
        "voice": "Description of speaking voice",
        "cadence": "Rhythm and pace",
        "dos": ["3-5 communication practices"],
        "donts": ["2-4 things to avoid"]
    }},
    "lexicon": {{
        "signature_phrases": ["3-5 characteristic phrases"],
        "keywords": ["5-10 key vocabulary words"],
        "taboo_words": ["words to avoid, if any"]
    }},
    "topics": {{
        "primary": ["3-5 main topics"],
        "secondary": ["2-4 related topics"]
    }},
    "alignment": {{
        "faith_alignment_vector": []
    }},
    "origin": {{
        "inspiration_source": "{inspiration_source or 'source materials'}",
        "sources": [],
        "created_at": "{datetime.utcnow().isoformat()}Z"
    }},
    "language": "{language}"
}}

Return ONLY the JSON object, no other text. Ensure all strings are properly escaped."""

        try:
            response_text = await self._call_llm(prompt, max_tokens=settings.LLM_MAX_TOKENS)
            core_dict = self._parse_json_response(response_text)
            
            # Validate with Pydantic
            try:
                return PersonaCore(**core_dict)
            except Exception as validation_error:
                logger.warning(f"Validation error, attempting repair: {validation_error}")
                repaired_dict = await self._repair_json(response_text, str(validation_error))
                return PersonaCore(**repaired_dict)
                
        except Exception as e:
            logger.error(f"Error generating persona core: {e}")
            return self._mock_persona_core(persona_name, inspiration_source, language, concepts)
    
    async def generate_human_prompt(self, persona_core: PersonaCore, draft_no: int) -> str:
        """
        Generate a human-readable prompt for review.
        
        Args:
            persona_core: Current persona core draft
            draft_no: Draft number
            
        Returns:
            Human-readable description and questions
        """
        if self.dry_run:
            return self._mock_human_prompt(persona_core, draft_no)
        
        prompt = f"""Based on the following persona profile draft (v{draft_no}), create a clear human-readable summary and 2-3 questions for the user to consider.

Persona Profile:
{json.dumps(persona_core.model_dump(), indent=2, ensure_ascii=False)}

Generate a natural language summary that:
1. Summarizes the persona's core beliefs and character
2. Highlights key traits and communication style
3. Lists 2-3 specific questions for user feedback

Keep it concise but comprehensive. Write in a conversational tone."""

        try:
            return await self._call_llm(prompt, max_tokens=1000)
        except Exception as e:
            logger.error(f"Error generating human prompt: {e}")
            return self._mock_human_prompt(persona_core, draft_no)
    
    async def _call_llm(self, prompt: str, max_tokens: int = None) -> str:
        """
        Make an LLM API call.
        
        Args:
            prompt: Prompt text
            max_tokens: Maximum tokens in response
            
        Returns:
            Response text
        """
        max_tokens = max_tokens or settings.LLM_MAX_TOKENS
        
        if self.provider == "openai":
            response = self.client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=settings.LLM_TEMPERATURE
            )
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=settings.LLM_MODEL,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        else:
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    def _parse_json_response(self, response: str) -> dict:
        """
        Parse JSON from LLM response.
        
        Handles common issues like markdown code blocks.
        """
        text = response.strip()
        
        # Remove markdown code blocks
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        
        if text.endswith("```"):
            text = text[:-3]
        
        text = text.strip()
        
        return json.loads(text)
    
    async def _repair_json(self, original: str, error: str) -> dict:
        """
        Attempt to repair invalid JSON.
        
        Args:
            original: Original LLM response
            error: Validation error message
            
        Returns:
            Repaired JSON dict
        """
        repair_prompt = f"""The following JSON has a validation error. Please fix it and return ONLY valid JSON.

Error: {error}

Original JSON:
{original}

Return ONLY the corrected JSON, no explanations."""

        response = await self._call_llm(repair_prompt, max_tokens=settings.LLM_MAX_TOKENS)
        return self._parse_json_response(response)
    
    def _truncate_texts(self, texts: List[str], max_tokens: int) -> str:
        """Truncate combined texts to approximately max_tokens."""
        combined = "\n\n---\n\n".join(texts)
        # Rough approximation: 1 token ≈ 4 characters
        max_chars = max_tokens * 4
        if len(combined) > max_chars:
            combined = combined[:max_chars] + "...[truncated]"
        return combined
    
    def _mock_concepts(self) -> ConceptsOutput:
        """Return mock concepts for DRY_RUN mode."""
        return ConceptsOutput(
            themes=["faith", "hope", "meaning", "suffering"],
            virtues=["humility", "wisdom", "compassion"],
            tone=["thoughtful", "warm", "encouraging"],
            recurring_ideas=[
                "Finding meaning in difficulty",
                "Grace as foundation",
                "Community over isolation"
            ],
            notable_distinctions=[
                "Balances intellect with heart",
                "Questions before answers"
            ]
        )
    
    def _mock_persona_core(
        self,
        persona_name: str,
        inspiration_source: Optional[str],
        language: str,
        concepts: ConceptsOutput
    ) -> PersonaCore:
        """Return mock persona core for DRY_RUN mode."""
        return PersonaCore(
            credo={
                "summary": f"A thoughtful persona inspired by {inspiration_source or 'wisdom traditions'}",
                "statements": [
                    "Meaning emerges through relationship",
                    "Truth is discovered in community",
                    "Hope persists through difficulty"
                ]
            },
            ethos={
                "virtues": concepts.virtues or ["wisdom", "compassion", "humility"],
                "anti_patterns": ["pride", "cynicism", "isolation"],
                "emotional_tone": concepts.tone or ["thoughtful", "warm"]
            },
            theo_logic={
                "principles": ["Grace precedes merit", "Questions open doors"],
                "reasoning_style": "Socratic dialogue with pastoral care"
            },
            style={
                "voice": "Gentle mentor and thoughtful companion",
                "cadence": "Measured and reflective",
                "dos": ["Use metaphors", "Ask questions", "Acknowledge complexity"],
                "donts": ["Oversimplify", "Be preachy", "Dismiss doubts"]
            },
            lexicon={
                "signature_phrases": ["Consider this...", "What might it mean..."],
                "keywords": concepts.themes or ["faith", "hope", "meaning"],
                "taboo_words": []
            },
            topics={
                "primary": concepts.themes[:3] if concepts.themes else ["faith", "meaning"],
                "secondary": concepts.themes[3:] if len(concepts.themes) > 3 else ["culture"]
            },
            alignment={"faith_alignment_vector": []},
            origin={
                "inspiration_source": inspiration_source or "source materials",
                "sources": [],
                "created_at": datetime.utcnow().isoformat() + "Z"
            },
            language=language
        )
    
    def _mock_human_prompt(self, persona_core: PersonaCore, draft_no: int) -> str:
        """Return mock human prompt for DRY_RUN mode."""
        return f"""## Persona Draft v{draft_no}: Review Requested

**Summary:**
This persona embodies {persona_core.credo.summary}

**Core Beliefs:**
{chr(10).join('- ' + s for s in persona_core.credo.statements[:3])}

**Character:**
- Virtues: {', '.join(persona_core.ethos.virtues[:3])}
- Tone: {', '.join(persona_core.ethos.emotional_tone[:3])}

**Questions for Review:**
1. Does this capture the essence of the inspiration source?
2. Are there any virtues or traits that should be added or removed?
3. Does the communication style feel authentic?

Reply with "confirm: true" to finalize, or provide edits."""
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if self.dry_run:
            # Return mock embeddings
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
        
        if self.provider != "openai":
            logger.warning("Embeddings only supported with OpenAI, using mock")
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
        
        try:
            response = self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return [[0.0] * settings.EMBEDDING_DIMENSION for _ in texts]
