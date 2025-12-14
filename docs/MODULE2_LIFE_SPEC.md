# Module 2: Persona Life - Technical Specification

## Overview

The Persona Life module enables continuous persona evolution through real interactions, reflection cycles, metrics tracking, and curated memory updates.

## Core Workflows

### A) Event Ingestion

Accept events from n8n or direct API calls:

- **Conversation snippets**: Interactions with users
- **User notes**: Observations and feedback
- **Ministry/leadership journaling**: Reflections and decisions
- **Decisions and outcomes**: Tracking cause and effect

**API Endpoint:** `POST /life/event`

```json
{
  "persona_id": "uuid",
  "event_type": "conversation|note|journal|decision|outcome",
  "content": "Event content text",
  "tags": ["tag1", "tag2"],
  "meta": {"source": "telegram", "user_id": "123"}
}
```

### B) Reflection Cycles

Daily/weekly cycles triggered by n8n Cron that:

1. Select recent events based on lookback period
2. Retrieve relevant persona knowledge via RAG
3. Generate reflection summary with:
   - Short actionable summary
   - Key insights
   - Suggested persona_core adjustments (optional)
   - Next actions list
   - Staleness alerts

**API Endpoints:**
- `POST /life/cycle/start` - Start a cycle
- `GET /life/cycle/status/{cycle_id}` - Check status
- `POST /life/cycle/approve` - Approve and commit

### C) Memory Hygiene / Decay

The system tracks:
- **Staleness**: Information that hasn't been referenced recently
- **Conflicts**: Contradictory information between events
- **Repetition**: Frequently recurring themes

## Database Schema

### life_events
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| event_type | TEXT | Event type enum |
| content | TEXT | Event content |
| tags | TEXT[] | Array of tags |
| run_id | UUID | Trace ID |
| meta | JSONB | Additional metadata |
| created_at | TIMESTAMP | Creation time |

### life_cycles
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| status | TEXT | pending/processing/awaiting_approval/committed/failed |
| cycle_type | TEXT | daily/weekly/manual |
| run_id | UUID | Trace ID |
| options | JSONB | Cycle configuration |
| started_at | TIMESTAMP | Start time |
| finished_at | TIMESTAMP | Completion time |

### life_cycle_drafts
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| cycle_id | UUID | Foreign key to life_cycles |
| draft_json | JSONB | Reflection output |
| created_at | TIMESTAMP | Creation time |

### life_metrics
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| metric_key | TEXT | Metric identifier |
| metric_value | NUMERIC | Metric value |
| period_start | TIMESTAMP | Period start |
| period_end | TIMESTAMP | Period end |
| computed_at | TIMESTAMP | Computation time |

### recommendations
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| source | TEXT | life/publisher/analytics/eidos |
| rec_json | JSONB | Recommendation content |
| status | TEXT | pending/accepted/rejected/expired |
| created_at | TIMESTAMP | Creation time |

## Audit Events

- `life.event.ingested` - Event ingested
- `life.cycle.started` - Cycle started
- `life.cycle.draft.created` - Draft generated
- `life.cycle.committed` - Cycle approved and committed
- `life.cycle.failed` - Cycle failed
- `life.metrics.computed` - Metrics computed

## Export Outputs

Location: `/opt/mpis/personas/<slug>/life/`

- `latest_reflection.md` - Human-readable reflection summary
- `metrics.json` - Computed metrics
- `recommendations.json` - Generated recommendations

## n8n Integration

Use the workflow template `daily-reflection.json`:

1. Cron trigger at 6 AM daily
2. Start reflection cycle via API
3. Poll for completion
4. Send to Telegram for approval
5. Approve and commit

## Versioning

When persona adjustments are applied:
1. Read current persona_core version
2. Apply adjustments
3. Create new version (e.g., 1.1 → 1.2)
4. Update persona.active_version
5. Log change reason and origin metadata
