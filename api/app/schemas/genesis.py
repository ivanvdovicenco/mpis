"""
MPIS Genesis API - Genesis Workflow Schemas

Pydantic schemas for genesis API endpoints.
"""
from typing import List, Optional, Literal, Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class SourceInput(BaseModel):
    """Input source specification."""
    type: Literal["text", "url", "file", "youtube"] = Field(description="Source type")
    ref: str = Field(description="Source reference (URL, text content, file path)")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")


class GenesisStartRequest(BaseModel):
    """Request to start a new persona generation job."""
    persona_name: str = Field(..., min_length=1, max_length=100, description="Name for the persona")
    inspiration_source: Optional[str] = Field(None, description="Primary inspiration source (e.g., 'Tim Keller')")
    language: str = Field(default="en", description="Primary language for the persona")
    public_persona: bool = Field(default=False, description="Enable public persona web enrichment")
    public_name: Optional[str] = Field(None, description="Public name to search for (required if public_persona=true)")
    gdrive_folder_id: Optional[str] = Field(None, description="Google Drive folder ID for document import")
    notes: Optional[str] = Field(None, description="Additional notes or context")
    sources: List[SourceInput] = Field(default_factory=list, description="Additional sources to process")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "persona_name": "Alexey",
            "inspiration_source": "Tim Keller",
            "language": "ru",
            "public_persona": True,
            "public_name": "Tim Keller",
            "gdrive_folder_id": "1abc123def456",
            "notes": "Focus on pastoral wisdom and apologetics",
            "sources": [
                {"type": "text", "ref": "Additional context notes", "metadata": {"lang": "ru"}}
            ]
        }
    })


class PersonaCard(BaseModel):
    """Brief persona summary card for display."""
    persona_id: Optional[UUID] = Field(None, description="Persona ID (null until committed)")
    name: str = Field(description="Persona name")
    slug: str = Field(description="URL-safe slug")
    active_version: str = Field(default="draft", description="Current version")
    summary: str = Field(default="", description="Brief persona summary")
    top_topics: List[str] = Field(default_factory=list, description="Top 5 topics")
    dominant_tones: List[str] = Field(default_factory=list, description="Dominant emotional tones")
    next_actions: List[str] = Field(default_factory=list, description="Suggested next actions")


class ProgressInfo(BaseModel):
    """Job progress information."""
    stage: str = Field(description="Current processing stage")
    percent: int = Field(ge=0, le=100, description="Progress percentage")
    message: str = Field(default="", description="Human-readable status message")


class GenesisStartResponse(BaseModel):
    """Response from starting a genesis job."""
    job_id: UUID = Field(description="Job identifier")
    status: str = Field(description="Current job status")
    draft_no: int = Field(description="Current draft number")
    human_prompt: Optional[str] = Field(None, description="Prompt for human review")
    preview: Optional[PersonaCard] = Field(None, description="Persona preview card")


class GenesisStatusResponse(BaseModel):
    """Response for job status query."""
    job_id: UUID = Field(description="Job identifier")
    status: str = Field(description="Current job status")
    progress: ProgressInfo = Field(description="Progress information")
    draft_no: int = Field(description="Current draft number")
    human_prompt: Optional[str] = Field(None, description="Prompt for human review")
    preview: Optional[PersonaCard] = Field(None, description="Persona preview card")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")


class EditOperation(BaseModel):
    """JSON Patch-like edit operation."""
    path: str = Field(description="JSON path to edit (e.g., 'credo.statements[1]')")
    op: Literal["add", "replace", "remove"] = Field(description="Operation type")
    value: Optional[Any] = Field(None, description="New value (required for add/replace)")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "path": "credo.statements[1]",
            "op": "replace",
            "value": "Updated statement"
        }
    })


class GenesisApproveRequest(BaseModel):
    """Request to approve or edit a genesis draft."""
    job_id: UUID = Field(description="Job identifier")
    draft_no: int = Field(description="Draft number being reviewed")
    confirm: bool = Field(default=False, description="Set to true to commit the persona")
    edits: List[EditOperation] = Field(default_factory=list, description="Edits to apply before committing")
    
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "job_id": "550e8400-e29b-41d4-a716-446655440000",
            "draft_no": 1,
            "confirm": False,
            "edits": [
                {"path": "credo.statements[1]", "op": "replace", "value": "Updated statement"},
                {"path": "ethos.virtues", "op": "add", "value": "humility"}
            ]
        }
    })


class GenesisApproveResponse(BaseModel):
    """Response from approval endpoint."""
    job_id: UUID = Field(description="Job identifier")
    status: str = Field(description="Current job status")
    draft_no: int = Field(description="Current/new draft number")
    human_prompt: Optional[str] = Field(None, description="Updated prompt for human review")
    preview: Optional[PersonaCard] = Field(None, description="Updated persona preview")
    persona_id: Optional[UUID] = Field(None, description="Committed persona ID (if confirmed)")
    version: Optional[str] = Field(None, description="Committed version (if confirmed)")
    export_paths: Optional[dict] = Field(None, description="Export paths (if confirmed)")


class ConceptsOutput(BaseModel):
    """Output from concept extraction."""
    themes: List[str] = Field(default_factory=list)
    virtues: List[str] = Field(default_factory=list)
    tone: List[str] = Field(default_factory=list)
    recurring_ideas: List[str] = Field(default_factory=list)
    notable_distinctions: List[str] = Field(default_factory=list)
