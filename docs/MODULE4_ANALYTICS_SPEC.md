# Module 4: Analytics Dashboard + EIDOS - Technical Specification

## Overview

The Analytics Dashboard + EIDOS module provides performance analytics and AI-powered actionable recommendations for persona publishing strategies.

## Core Capabilities

### A) Analytics Computations

Daily/weekly rollups computing:
- Engagement rate
- Reach growth
- Best-performing topics, hooks, CTAs
- Time-of-day effects
- Trend analysis

**API Endpoint:** `GET /analytics/persona/{persona_id}/summary?range=30d`

```json
{
  "persona_id": "uuid",
  "range_type": "30d",
  "period_start": "2025-01-01T00:00:00Z",
  "period_end": "2025-01-31T00:00:00Z",
  "metrics": {
    "total_published": 25,
    "total_views": 15000,
    "total_reactions": 450,
    "total_shares": 120,
    "engagement_rate": 3.8,
    "best_performing_topics": ["faith", "hope", "community"],
    "best_performing_times": ["9:00 AM", "7:00 PM"]
  },
  "insights": [
    "Engagement rate increased 15% this month",
    "Posts about 'faith' get 2x more reactions"
  ],
  "trends": {
    "overall": "growing",
    "engagement": "high"
  }
}
```

### B) EIDOS Recommendation Engine

AI-powered recommendations using:
- Computed metrics analysis
- LLM reasoning over summarized history
- Persona goals alignment

**API Endpoint:** `GET /analytics/recommendations/{persona_id}`

Produces:
1. Top 5 recommendations with evidence
2. Ready-to-generate content briefs
3. Suggested A/B experiments

### C) Rollup Computation

Trigger manual recomputation:

**API Endpoint:** `POST /analytics/recompute`

```json
{
  "persona_id": "uuid",
  "rollup_types": ["daily", "weekly"],
  "force": false
}
```

## Database Schema

### analytics_rollups
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| rollup_type | TEXT | daily/weekly/monthly |
| period_start | TIMESTAMP | Period start |
| period_end | TIMESTAMP | Period end |
| metrics | JSONB | Computed metrics |
| insights | JSONB | Generated insights |
| computed_at | TIMESTAMP | Computation time |

### eidos_recommendations
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| run_id | UUID | Trace ID |
| recommendations | JSONB | Top recommendations |
| evidence | JSONB | Supporting evidence |
| experiments | JSONB | Suggested experiments |
| content_briefs | JSONB | Ready-to-use briefs |
| status | TEXT | pending/reviewed/actioned/expired |
| computed_at | TIMESTAMP | Computation time |

### experiments
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| name | TEXT | Experiment name |
| hypothesis | TEXT | What we're testing |
| variants | JSONB | Variant definitions |
| status | TEXT | draft/active/completed/cancelled |
| start_date | TIMESTAMP | Start date |
| end_date | TIMESTAMP | End date |
| results | JSONB | Experiment results |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

### dashboard_views
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| persona_id | UUID | Foreign key to personas |
| name | TEXT | View name |
| view_config | JSONB | View configuration |
| is_default | BOOLEAN | Is default view |
| created_at | TIMESTAMP | Creation time |
| updated_at | TIMESTAMP | Last update |

## EIDOS Recommendation Structure

```json
{
  "recommendations": [
    {
      "id": 1,
      "title": "Increase posting frequency",
      "description": "Data shows engagement drops after 3+ days without posts",
      "priority": "high",
      "category": "content",
      "evidence": [
        "Engagement drops 40% after 3-day gaps",
        "Weekly posters have 2x retention"
      ],
      "measurable_outcome": "Track engagement rate over 2 weeks"
    }
  ],
  "content_briefs": [
    {
      "topic": "Community building",
      "hook": "What brings you hope this week?",
      "key_points": ["Invite discussion", "Share personal reflection"],
      "target_channel": "telegram",
      "suggested_length": 500,
      "rationale": "Interactive content drives engagement"
    }
  ],
  "experiments": [
    {
      "name": "CTA Style Test",
      "hypothesis": "Questions in CTAs increase engagement",
      "variants": ["Imperative CTA", "Question CTA"],
      "success_metric": "Reaction rate within 24 hours",
      "duration_days": 14
    }
  ]
}
```

## Audit Events

- `analytics.rollup.computed` - Rollup computed
- `analytics.eidos.generated` - EIDOS recommendations generated
- `analytics.experiment.created` - Experiment created
- `analytics.experiment.completed` - Experiment completed

## Export Outputs

Location: `/opt/mpis/personas/<slug>/analytics/`

- `summary.json` - Latest analytics summary
- `recommendations.md` - Human-readable recommendations
- `experiments.json` - Experiment definitions and results

## Metrics Aggregation

Metrics are aggregated from `item_metrics` table:

| Metric Type | Description |
|------------|-------------|
| views | Total views |
| reactions | Likes, hearts, etc. |
| comments | Comment count |
| shares | Share/forward count |
| clicks | Link clicks |
| retention | View duration proxy |

### Engagement Rate Calculation

```
engagement_rate = (reactions + shares) / views * 100
```

## Time Range Options

| Range | Description |
|-------|-------------|
| 7d | Last 7 days |
| 30d | Last 30 days (default) |
| 90d | Last 90 days |
| all | All time |

## Caching

EIDOS recommendations are cached for 24 hours unless:
- Status is "expired"
- Force refresh is requested

## Dashboard UI Options

The module supports API-only mode (default). Future options:

1. **API-only**: JSON endpoints for external dashboards
2. **Minimal Web UI**: FastAPI + Jinja2 templates
3. **Separate Dashboard**: React/Vue frontend

Current implementation: API-only mode.

## n8n Integration

Weekly analytics report workflow:

1. Schedule trigger (weekly)
2. Get analytics summary via API
3. Get EIDOS recommendations
4. Format report
5. Send to Telegram/email

## Performance Considerations

- Rollups are computed incrementally
- Heavy computations run in background
- Results are cached
- Metrics are indexed for fast aggregation
