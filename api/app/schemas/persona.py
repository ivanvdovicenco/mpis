"""
MPIS Genesis API - Persona Core Schemas

Pydantic schemas for the canonical persona_core.json structure.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class Credo(BaseModel):
    """Philosophical and values base."""
    summary: str = Field(default="", description="Brief summary of the persona's credo")
    statements: List[str] = Field(default_factory=list, description="Core belief statements")


class Ethos(BaseModel):
    """Character and emotional tone."""
    virtues: List[str] = Field(default_factory=list, description="Core virtues and strengths")
    anti_patterns: List[str] = Field(default_factory=list, description="Behaviors to avoid")
    emotional_tone: List[str] = Field(default_factory=list, description="Emotional characteristics")


class TheoLogic(BaseModel):
    """Reasoning principles and style."""
    principles: List[str] = Field(default_factory=list, description="Core reasoning principles")
    reasoning_style: str = Field(default="", description="Description of reasoning approach")


class Style(BaseModel):
    """Voice and communication style."""
    voice: str = Field(default="", description="Description of speaking voice")
    cadence: str = Field(default="", description="Rhythm and pace of speech")
    dos: List[str] = Field(default_factory=list, description="Things to do")
    donts: List[str] = Field(default_factory=list, description="Things to avoid")


class Lexicon(BaseModel):
    """Vocabulary and phrases."""
    signature_phrases: List[str] = Field(default_factory=list, description="Characteristic phrases")
    keywords: List[str] = Field(default_factory=list, description="Key vocabulary")
    taboo_words: List[str] = Field(default_factory=list, description="Words to avoid")


class Topics(BaseModel):
    """Subject matter preferences."""
    primary: List[str] = Field(default_factory=list, description="Primary topics of focus")
    secondary: List[str] = Field(default_factory=list, description="Secondary topics")


class Alignment(BaseModel):
    """Faith and worldview alignment."""
    faith_alignment_vector: List[float] = Field(
        default_factory=list,
        description="Numerical vector for faith/worldview alignment"
    )


class Origin(BaseModel):
    """Source and creation metadata."""
    inspiration_source: str = Field(default="", description="Primary inspiration source")
    sources: List[str] = Field(default_factory=list, description="All source references")
    created_at: str = Field(default="", description="Creation timestamp")


class PersonaCore(BaseModel):
    """
    Canonical persona_core.json structure.
    
    This is the complete persona definition with all required blocks.
    """
    credo: Credo = Field(default_factory=Credo)
    ethos: Ethos = Field(default_factory=Ethos)
    theo_logic: TheoLogic = Field(default_factory=TheoLogic)
    style: Style = Field(default_factory=Style)
    lexicon: Lexicon = Field(default_factory=Lexicon)
    topics: Topics = Field(default_factory=Topics)
    alignment: Alignment = Field(default_factory=Alignment)
    origin: Origin = Field(default_factory=Origin)
    language: str = Field(default="en", description="Primary language")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "credo": {
                "summary": "Faith transforms suffering into meaning",
                "statements": [
                    "Every hardship carries the seed of growth",
                    "Doubt is the doorway to deeper faith"
                ]
            },
            "ethos": {
                "virtues": ["humility", "compassion", "wisdom"],
                "anti_patterns": ["pride", "judgment", "despair"],
                "emotional_tone": ["warm", "thoughtful", "hopeful"]
            },
            "theo_logic": {
                "principles": ["Grace precedes effort", "Truth through love"],
                "reasoning_style": "Socratic questioning with pastoral care"
            },
            "style": {
                "voice": "Gentle mentor and wise counselor",
                "cadence": "Measured and contemplative",
                "dos": ["Use metaphors", "Ask reflective questions"],
                "donts": ["Be preachy", "Oversimplify"]
            },
            "lexicon": {
                "signature_phrases": ["The gospel tells us...", "Consider this..."],
                "keywords": ["grace", "redemption", "hope", "love"],
                "taboo_words": []
            },
            "topics": {
                "primary": ["faith", "suffering", "meaning"],
                "secondary": ["culture", "relationships", "work"]
            },
            "alignment": {
                "faith_alignment_vector": []
            },
            "origin": {
                "inspiration_source": "Tim Keller",
                "sources": ["youtube:abc123", "gdrive:doc456"],
                "created_at": "2025-01-15T10:30:00Z"
            },
            "language": "en"
        }
    })
