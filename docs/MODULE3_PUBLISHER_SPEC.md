# Module 3: Social Publisher - Technical Specification

## Overview

The Social Publisher module handles content planning, generation, approval, scheduling, and publishing under a persona's voice, with full metrics tracking for analytics.

## Core Capabilities

### A) Content Planning

Create content calendar objects with:
- Topics and goals
- Target audience
- Channel selection
- Schedule windows
- Constraints (tone, length, forbidden topics)

**API Endpoint:** `POST /publisher/plan`

```json
{
  "persona_id": "uuid",
  "title": "Finding Hope in Uncertainty",
  "topic": "faith during difficult times",
  "goal": "encourage",
  "target_audience": "believers facing challenges",
  "channel": "telegram",
  "language": "en",
  "max_length": 800,
  "constraints": {
    "tone": ["hopeful", "pastoral"],
    "forbidden_topics": [],
    "scripture_allowed": true
  }
}
```

### B) Content Generation

RAG-powered generation that:
1. Retrieves relevant persona knowledge
2. Generates content matching persona voice
3. Produces multiple variants (1-3)
4. Tracks provenance to source chunks
5. Applies Anti-Quote validation

**API Endpoint:** `POST /publisher/generate`

```json
{
  "plan_id": "uuid",
  "variants": 2,
  "options": {
    "use_rag": true,
    "include_cta": true
  }
}
```

**Output includes:**
- Main content text
- Title/hook
- Call-to-action
- Provenance map

### C) Approval & Publishing

Draft workflow:
1. Generate draft
2. User reviews/edits
3. Approve draft
4. Publish via n8n
5. Record publish result

**API Endpoints:**
- `GET /publisher/draft/{draft_id}` - Get draft
- `POST /publisher/approve` - Approve draft
- `POST /publisher/publish/record` - Record publish

### D) Metrics Ingestion

Accept metrics from n8n or channel APIs:
- Views, reactions, comments, shares
- Clicks, retention proxies
- Custom metrics

**API Endpoint:** `POST /publisher/metrics/ingest`

## Database Schema

### content_plans
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| title | TEXT | Content title |
| topic | TEXT | Content topic |
| goal | TEXT | Content goal |
| target_audience | TEXT | Target audience |
| channel | TEXT | Publishing channel |
| language | TEXT | Content language |
| max_length | INTEGER | Maximum length |
| schedule_window_start | TIMESTAMP | Earliest publish time |
| schedule_window_end | TIMESTAMP | Latest publish time |
| constraints | JSONB | Additional constraints |
| status | TEXT | Plan status |
| run_id | UUID | Trace ID |
| meta | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

### content_drafts
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| plan_id | UUID | Foreign key to content_plans |
| persona_version_id | UUID | Persona version used |
| draft_no | INTEGER | Draft version number |
| content_json | JSONB | Generated variants |
| provenance | JSONB | Source references |
| run_id | UUID | Trace ID |
| status | TEXT | draft/approved/rejected |
| created_at | TIMESTAMP | Creation time |

### published_items
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| draft_id | UUID | Foreign key to content_drafts |
| channel | TEXT | Publishing channel |
| channel_item_id | TEXT | Channel's item ID |
| channel_url | TEXT | URL to published content |
| published_payload | JSONB | Full publish payload |
| published_at | TIMESTAMP | Publish timestamp |
| persona_version_used | TEXT | Persona version at publish |
| meta | JSONB | Additional metadata |

### item_metrics
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| published_item_id | UUID | Foreign key to published_items |
| metric_type | TEXT | Metric type (views, reactions, etc.) |
| metric_value | NUMERIC | Metric value |
| recorded_at | TIMESTAMP | Recording timestamp |
| source | TEXT | Metrics source |
| meta | JSONB | Additional metadata |

### channel_accounts
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| channel | TEXT | Channel type |
| account_id | TEXT | Account identifier |
| account_name | TEXT | Account display name |
| config | JSONB | Channel configuration |
| active | BOOLEAN | Is account active |
| created_at | TIMESTAMP | Creation time |

## Audit Events

- `publisher.plan.created` - Plan created
- `publisher.draft.generated` - Draft generated
- `publisher.draft.approved` - Draft approved
- `publisher.content.published` - Content published
- `publisher.metrics.ingested` - Metrics ingested

## Export Outputs

Location: `/opt/mpis/personas/<slug>/publisher/`

- `drafts/` - Draft versions
- `published/` - Published item records
- `calendar.json` - Content calendar

## n8n Integration

Use the workflow template `content-publishing.json`:

1. Manual or scheduled trigger
2. Generate draft via API
3. Send to Telegram for approval
4. Receive approval response
5. Approve draft via API
6. Publish to Telegram channel
7. Record publish result

## Guardrails

### Anti-Quote Validation
- Prevent verbatim fragments > 50 characters from sources
- Flag potential copyright issues
- Summarize instead of quote

### Content Constraints
- Enforce max_length limits
- Apply tone constraints
- Filter forbidden topics
- Validate scripture references (if enabled)

## Provenance Tracking

Each generated draft includes:
```json
{
  "provenance": {
    "topics_referenced": ["faith", "hope"],
    "style_elements_used": ["pastoral tone", "metaphors"],
    "source_chunks": [
      {"source_id": "uuid", "chunk_index": 5, "relevance": 0.89}
    ],
    "persona_version": "1.2",
    "model": "gpt-4-turbo-preview",
    "prompt_hash": "abc123"
  }
}
```
