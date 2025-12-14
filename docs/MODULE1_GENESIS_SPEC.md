# MPIS Module 1: Persona Genesis Engine Specification

**Version:** 1.0.0  
**Status:** MVP Production-Ready  
**Module:** Persona Generator / Genesis Engine

## Overview

The Persona Genesis Engine is Module 1 of the Multi-Persona Intelligence System (MPIS). It handles the creation of AI personas from various source materials through an automated yet human-supervised workflow.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Genesis API (FastAPI)                       │
├─────────────────────────────────────────────────────────────────┤
│  POST /genesis/start     - Start generation job                  │
│  GET  /genesis/status    - Check job progress                    │
│  POST /genesis/approve   - Approve/edit draft                    │
│  GET  /genesis/export    - Get export paths                      │
└─────────────────────────────────────────────────────────────────┘
           │                    │                    │
           ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Source         │  │  LLM Service    │  │  Qdrant         │
│  Collector      │  │  (OpenAI/       │  │  Vector Store   │
│  (YouTube,      │  │   Anthropic)    │  │                 │
│   GDrive, Web)  │  │                 │  │                 │
└─────────────────┘  └─────────────────┘  └─────────────────┘
           │                    │                    │
           └────────────────────┼────────────────────┘
                               ▼
                    ┌─────────────────┐
                    │  PostgreSQL     │
                    │  (mpis-postgres)│
                    └─────────────────┘
```

## Source Channels

### Channel A: YouTube Links File

- **Input:** `youtube_links.txt` in `/opt/mpis/input`
- **Format:** One YouTube URL per line, `#` for comments
- **Supported URLs:** `youtube.com/watch`, `youtu.be`, `youtube.com/shorts`
- **Extraction:** Uses `youtube-transcript-api` for transcripts
- **Fallback:** Marks as `failed_transcript` if unavailable

### Channel B: Google Drive Folder

- **Input:** Google Drive folder ID in request
- **Auth:** Service account JSON at `/opt/mpis/secrets/gdrive_sa.json`
- **Supported formats:** Google Docs, PDF, DOCX, plain text
- **Note:** DOC (legacy) files marked as `failed_parse`

### Channel C: Public Persona Web Enrichment

- **Trigger:** `public_persona=true` with `public_name`
- **Discovery:** SerpAPI (if key configured) or Wikipedia fallback
- **Limit:** `PUBLIC_WEB_MAX_SOURCES` (default: 20)
- **Safety:** Domain allowlist/denylist, rate limiting
- **Storage:** Short summaries only (no full copyrighted content)

## Pipeline Stages

1. **Source Collection** - Gather materials from all channels
2. **Corpus Processing** - Normalize text, split into chunks (500-1200 tokens)
3. **Embeddings** - Generate and store in Qdrant
4. **Concept Extraction** - Extract themes, virtues, tone
5. **Persona Core Generation** - LLM generates persona_core.json
6. **Human Approval** - Review, edit, or confirm
7. **Commit & Export** - Save to database and filesystem

## Data Model

### genesis_jobs
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_name | TEXT | Display name |
| slug | TEXT | URL-safe identifier |
| input_json | JSONB | Original request |
| config_json | JSONB | Configuration + concepts |
| status | TEXT | Job status |
| draft_no | INT | Current draft number |
| persona_id | UUID | Created persona (after commit) |

### Status Values
- `queued` - Job created, not started
- `collecting` - Gathering sources
- `processing` - Processing corpus
- `awaiting_approval` - Ready for human review
- `committed` - Persona created successfully
- `committed_with_memory_pending` - Created but Qdrant unavailable
- `failed` - Job failed with error

## Persona Core Structure

```json
{
  "credo": {
    "summary": "Brief philosophical summary",
    "statements": ["Core belief 1", "Core belief 2"]
  },
  "ethos": {
    "virtues": ["humility", "wisdom"],
    "anti_patterns": ["pride", "cynicism"],
    "emotional_tone": ["warm", "thoughtful"]
  },
  "theo_logic": {
    "principles": ["Principle 1"],
    "reasoning_style": "Description"
  },
  "style": {
    "voice": "Gentle mentor",
    "cadence": "Measured",
    "dos": ["Use metaphors"],
    "donts": ["Oversimplify"]
  },
  "lexicon": {
    "signature_phrases": ["Consider this..."],
    "keywords": ["grace", "hope"],
    "taboo_words": []
  },
  "topics": {
    "primary": ["faith", "meaning"],
    "secondary": ["culture"]
  },
  "alignment": {
    "faith_alignment_vector": []
  },
  "origin": {
    "inspiration_source": "Tim Keller",
    "sources": [],
    "created_at": "2025-01-15T10:30:00Z"
  },
  "language": "en"
}
```

## Export Structure

```
/opt/mpis/personas/<slug>/
├── core/
│   ├── persona_core.json    # Complete persona definition
│   ├── credo.json           # Beliefs and values
│   ├── ethos.json           # Character traits
│   ├── theologic.txt        # Reasoning principles
│   ├── tone_profile.json    # Voice and tone
│   ├── style.json           # Communication style
│   └── language_profile.json # Vocabulary
├── memory/
│   ├── concepts.json        # Extracted concepts
│   └── sources_index.json   # Source materials list
└── docs/
    ├── readme.md            # Human-readable description
    ├── usage_prompt.txt     # LLM system prompt
    ├── changelog.json       # Version history
    └── technical_spec.json  # Technical metadata
```

## API Reference

### POST /genesis/start

Start a new persona generation job.

**Request:**
```json
{
  "persona_name": "Alexey",
  "inspiration_source": "Tim Keller",
  "language": "ru",
  "public_persona": true,
  "public_name": "Tim Keller",
  "gdrive_folder_id": "optional_folder_id",
  "notes": "Additional context",
  "sources": [
    {"type": "text", "ref": "Additional notes"}
  ]
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "awaiting_approval",
  "draft_no": 1,
  "human_prompt": "Review prompt...",
  "preview": { /* PersonaCard */ }
}
```

### POST /genesis/approve

Approve or edit a draft.

**Confirm Request:**
```json
{
  "job_id": "uuid",
  "draft_no": 1,
  "confirm": true
}
```

**Edit Request:**
```json
{
  "job_id": "uuid",
  "draft_no": 1,
  "edits": [
    {"path": "credo.statements[1]", "op": "replace", "value": "New statement"}
  ]
}
```

## Idempotency

All source content is hashed (SHA-256) before import. Duplicate content is automatically skipped, ensuring:
- Re-running a job won't duplicate sources
- Same video/document can be in multiple link files safely
- Incremental updates are efficient

## Error Handling

- **YouTube transcript unavailable:** Source marked `failed_transcript`, job continues
- **GDrive file parse error:** Source marked `failed_parse`, job continues
- **Qdrant unavailable:** Job completes with status `committed_with_memory_pending`
- **LLM JSON invalid:** Auto-retry with repair prompt (up to 2 attempts)

## Security Considerations

1. **No public exposure of secrets** - API keys via environment variables
2. **Internal Docker networking** - Postgres/Qdrant not exposed publicly
3. **Rate limiting on web scraping** - Configurable delays
4. **Content summarization** - Full copyrighted text not stored
5. **Audit logging** - All major events logged

## Defaults & Configuration

See [ENV.md](ENV.md) for complete configuration reference.

Key defaults:
- Chunk size: 500-1200 tokens
- Web sources limit: 20
- LLM model: gpt-4-turbo-preview
- Embedding model: text-embedding-3-small

## Future Modules (Not Implemented)

- **Module 2:** Persona Life (metrics, reflection)
- **Module 3:** Social Publisher (content creation)
- **Module 4:** Analytics Dashboard + EIDOS

Data structures are designed to support these future modules without refactoring.
