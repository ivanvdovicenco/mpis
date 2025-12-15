# MPIS Dashboard - Technical Specification

**Version:** 1.0  
**Date:** 2025-12-15  
**Purpose:** Technical specification for MPIS Dashboard including observability, contracts, metrics, widgets, developer experience, and security.

---

## Table of Contents

1. [Overview](#overview)
2. [Observability](#observability)
3. [Contract v1 (Dashboard ↔ n8n)](#contract-v1-dashboard--n8n)
4. [Metric Normalization](#metric-normalization)
5. [Widget System](#widget-system)
6. [Developer Experience](#developer-experience)
7. [Security](#security)
8. [Onboarding](#onboarding)

---

## Overview

The MPIS Dashboard is the central interface for managing personas, monitoring content performance, viewing analytics, and interacting with the EIDOS AI analyst. This specification defines the technical requirements for enhanced debugging, observability, integration contracts, metric normalization, widget architecture, developer experience, and user onboarding.

---

## Observability

### 1. Correlation IDs

**Purpose:** Enable end-to-end tracing across all MPIS systems (Dashboard, n8n, API, Database).

#### Required Correlation IDs

All systems must use and propagate the following correlation IDs:

| ID | Description | Scope | Example |
|----|-------------|-------|---------|
| `run_id` | Unique identifier for a content generation run | Dashboard → n8n → API | `550e8400-e29b-41d4-a716-446655440000` |
| `project_id` | Project identifier | Dashboard → n8n → API | `660e8400-e29b-41d4-a716-446655440001` |
| `n8n_execution_id` | n8n workflow execution identifier | n8n → Dashboard | `770e8400-e29b-41d4-a716-446655440002` |
| `draft_id` | Draft content identifier | Dashboard → n8n → API | `880e8400-e29b-41d4-a716-446655440003` |
| `published_item_id` | Published item identifier | API → Dashboard | `990e8400-e29b-41d4-a716-446655440004` |

#### Implementation Requirements

1. **Logging**
   - All log entries MUST include relevant correlation IDs
   - Log format: `[TIMESTAMP] [LEVEL] [run_id:xxx] [project_id:yyy] Message`
   - Example: `[2025-12-15T10:30:00Z] [INFO] [run_id:550e8400] [project_id:660e8400] Starting content generation`

2. **Run Logs UI**
   - Display all correlation IDs prominently in the Run Logs interface
   - Make IDs copyable with one click
   - Provide filter/search by any correlation ID
   - Link related logs using correlation IDs

3. **API Communication**
   - Include correlation IDs in all API request/response headers
   - Header format: `X-Run-ID`, `X-Project-ID`, `X-N8N-Execution-ID`, etc.
   - Propagate IDs through the entire request chain

#### Example Log Entry

```json
{
  "timestamp": "2025-12-15T10:30:00Z",
  "level": "INFO",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "n8n_execution_id": "770e8400-e29b-41d4-a716-446655440002",
  "message": "Content generation started",
  "service": "n8n-workflow",
  "workflow_name": "publisher-flow"
}
```

---

### 2. Error Logs

**Purpose:** Provide detailed error information for debugging and troubleshooting.

#### Error Logging Requirements

1. **Stack Trace**
   - Log full stack trace for all errors
   - Include file names, line numbers, and function names
   - Preserve error chain for nested errors

2. **Input/Output Payloads**
   - Log last input payload before error
   - Log partial output (if any) before error
   - Sanitize sensitive data (API keys, passwords)

3. **Context Information**
   - Timestamp
   - All relevant correlation IDs
   - User/session identifier
   - System state at time of error
   - Related entity IDs (persona_id, draft_id, etc.)

#### Error Log Format

```json
{
  "timestamp": "2025-12-15T10:35:00Z",
  "level": "ERROR",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "error_type": "PublishingError",
  "error_message": "Failed to publish to Telegram channel",
  "stack_trace": [
    "at TelegramPublisher.publish (telegram.js:142)",
    "at PublishingService.publishToChannel (publishing.js:89)",
    "at n8n.workflow.execute (workflow.js:234)"
  ],
  "last_input": {
    "channel": "telegram",
    "content": "Post content here...",
    "channel_id": "@my_channel"
  },
  "last_output": {
    "status": "failed",
    "api_response": {
      "error_code": 403,
      "description": "Bot was blocked by the user"
    }
  },
  "context": {
    "persona_id": "aa0e8400-e29b-41d4-a716-446655440005",
    "draft_id": "880e8400-e29b-41d4-a716-446655440003"
  }
}
```

#### Errors Tab in Run Logs UI

**Requirements:**

1. **Dedicated "Errors" Tab**
   - Show all errors for the current run
   - Display error count badge
   - Sort by timestamp (newest first)

2. **Error Display**
   - Error type and message (prominent)
   - Timestamp
   - Correlation IDs (clickable)
   - Expandable stack trace
   - Input/output payloads (expandable)
   - Context information

3. **Interactive Features**
   - Click error to view full details
   - Copy error details to clipboard
   - Link to related logs using correlation IDs
   - Filter by error type
   - Search in error messages

4. **Error Actions**
   - "Retry" button (if applicable)
   - "Report Issue" button (creates GitHub issue with error details)
   - "View Documentation" link (context-sensitive)

---

### 3. Red Flags Panel

**Purpose:** Highlight critical system issues that require immediate attention.

#### Red Flags to Monitor

1. **Failed Runs Percentage**
   - Track % of failed runs over last 24h, 7d, 30d
   - Alert threshold: > 10% failed runs
   - Display: Red badge with percentage

2. **Missing Metrics for Published Items**
   - Track published items without metric data
   - Alert threshold: > 5% items without metrics
   - Display: Warning badge with count

3. **Missing Publish Records**
   - Track publish attempts without corresponding records
   - Alert threshold: Any missing record
   - Display: Critical badge with count

#### Red Flags Panel UI

**Location:** Dashboard home page, top-right corner

**Display:**

```
┌─────────────────────────────────────────────┐
│ 🔴 Red Flags Panel                          │
├─────────────────────────────────────────────┤
│ ⚠️  Failed Runs: 15% (last 24h)             │
│     → 3 out of 20 runs failed               │
│     [View Details]                          │
│                                             │
│ ⚠️  Missing Metrics: 8 items                │
│     → Published but no metrics ingested     │
│     [View Items]                            │
│                                             │
│ 🔴 Missing Publish Records: 2               │
│     → Publish attempts without records      │
│     [Investigate]                           │
└─────────────────────────────────────────────┘
```

#### Red Flags API Endpoint

```
GET /api/red-flags
```

**Response:**

```json
{
  "failed_runs": {
    "last_24h": {
      "total_runs": 20,
      "failed_runs": 3,
      "percentage": 15.0,
      "alert": true
    },
    "last_7d": {
      "total_runs": 140,
      "failed_runs": 12,
      "percentage": 8.6,
      "alert": false
    }
  },
  "missing_metrics": {
    "count": 8,
    "alert": true,
    "items": [
      {
        "published_item_id": "990e8400-e29b-41d4-a716-446655440004",
        "published_at": "2025-12-15T08:00:00Z",
        "channel": "telegram"
      }
    ]
  },
  "missing_publish_records": {
    "count": 2,
    "alert": true,
    "runs": [
      {
        "run_id": "550e8400-e29b-41d4-a716-446655440000",
        "started_at": "2025-12-15T09:00:00Z"
      }
    ]
  }
}
```

---

## Contract v1 (Dashboard ↔ n8n)

### 1. Input JSON (Dashboard → n8n)

**Purpose:** Standard contract for initiating content generation and publishing workflows.

**Endpoint:** `POST /n8n/webhooks/publisher/run`

**Schema:**

```json
{
  "run_id": "uuid",
  "project_id": "uuid",
  "persona_id": "uuid",
  "channels": ["telegram", "instagram"],
  "date_from": "YYYY-MM-DD",
  "date_to": "YYYY-MM-DD",
  "templates": {
    "news_prompt_id": "uuid",
    "format_telegram_id": "uuid",
    "format_instagram_id": "uuid",
    "image_prompt_id": "uuid"
  },
  "options": {
    "lookback_days": 1,
    "max_items": 10,
    "include_image": true,
    "include_products_weekly": false
  }
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | UUID | Yes | Unique identifier for this run (correlation ID) |
| `project_id` | UUID | Yes | Project identifier |
| `persona_id` | UUID | Yes | Persona to use for content generation |
| `channels` | Array[String] | Yes | Target channels: `telegram`, `instagram`, `tiktok`, etc. |
| `date_from` | Date (YYYY-MM-DD) | Yes | Content search start date |
| `date_to` | Date (YYYY-MM-DD) | Yes | Content search end date |
| `templates` | Object | Yes | Template IDs for prompts and formatting |
| `templates.news_prompt_id` | UUID | Yes | News collection prompt template |
| `templates.format_telegram_id` | UUID | Conditional | Telegram format template (if telegram in channels) |
| `templates.format_instagram_id` | UUID | Conditional | Instagram format template (if instagram in channels) |
| `templates.image_prompt_id` | UUID | No | Image generation prompt template |
| `options` | Object | Yes | Run options |
| `options.lookback_days` | Integer | No | Days to look back for content (default: 1) |
| `options.max_items` | Integer | No | Maximum items to generate (default: 10) |
| `options.include_image` | Boolean | No | Generate images (default: true) |
| `options.include_products_weekly` | Boolean | No | Include product recommendations (default: false) |

#### Example Request

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "persona_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "channels": ["telegram", "instagram"],
  "date_from": "2025-12-14",
  "date_to": "2025-12-15",
  "templates": {
    "news_prompt_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "format_telegram_id": "cc0e8400-e29b-41d4-a716-446655440007",
    "format_instagram_id": "dd0e8400-e29b-41d4-a716-446655440008",
    "image_prompt_id": "ee0e8400-e29b-41d4-a716-446655440009"
  },
  "options": {
    "lookback_days": 1,
    "max_items": 10,
    "include_image": true,
    "include_products_weekly": false
  }
}
```

---

### 2. Output JSON (n8n → Dashboard Run Logs)

**Purpose:** Standard contract for reporting workflow execution results.

**Endpoint:** `POST /api/publisher/runs/{run_id}/complete`

**Schema:**

```json
{
  "run_id": "uuid",
  "status": "success|failed",
  "persona_id": "uuid",
  "project_id": "uuid",
  "n8n_execution_id": "uuid",
  "error": "string|null",
  "published_items": [
    {
      "draft_id": "uuid",
      "channel": "telegram",
      "channel_item_id": "string",
      "channel_url": "string",
      "metrics": {
        "views": 100,
        "reactions": 10,
        "shares": 5
      }
    }
  ]
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | UUID | Yes | Run identifier (must match input) |
| `status` | Enum | Yes | Run status: `success`, `failed`, `partial` |
| `persona_id` | UUID | Yes | Persona identifier (must match input) |
| `project_id` | UUID | Yes | Project identifier (must match input) |
| `n8n_execution_id` | UUID | Yes | n8n workflow execution ID (correlation ID) |
| `error` | String | No | Error message (required if status = failed) |
| `published_items` | Array | No | List of published items (empty if failed) |
| `published_items[].draft_id` | UUID | Yes | Draft identifier |
| `published_items[].channel` | String | Yes | Channel name: `telegram`, `instagram`, etc. |
| `published_items[].channel_item_id` | String | Yes | Channel-specific item ID (e.g., Telegram message ID) |
| `published_items[].channel_url` | String | No | Public URL to the published item |
| `published_items[].metrics` | Object | No | Initial metric snapshot |
| `published_items[].metrics.views` | Integer | No | Initial view count |
| `published_items[].metrics.reactions` | Integer | No | Initial reaction count |
| `published_items[].metrics.shares` | Integer | No | Initial share count |

#### Example Response (Success)

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "success",
  "persona_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "n8n_execution_id": "770e8400-e29b-41d4-a716-446655440002",
  "error": null,
  "published_items": [
    {
      "draft_id": "880e8400-e29b-41d4-a716-446655440003",
      "channel": "telegram",
      "channel_item_id": "12345",
      "channel_url": "https://t.me/my_channel/12345",
      "metrics": {
        "views": 100,
        "reactions": 10,
        "shares": 5
      }
    },
    {
      "draft_id": "880e8400-e29b-41d4-a716-446655440010",
      "channel": "instagram",
      "channel_item_id": "IGPost_67890",
      "channel_url": "https://instagram.com/p/67890",
      "metrics": {
        "views": 250,
        "reactions": 25,
        "shares": 3
      }
    }
  ]
}
```

#### Example Response (Failed)

```json
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "persona_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "n8n_execution_id": "770e8400-e29b-41d4-a716-446655440002",
  "error": "Failed to authenticate with Telegram API: Invalid bot token",
  "published_items": []
}
```

---

### 3. Mandatory MPIS API Calls

n8n workflows MUST call the following MPIS API endpoints for proper tracking and observability.

#### 3.1. Record Publish Event

**Purpose:** Record that content was published to a specific channel.

**Endpoint:** `POST /api/publisher/publish/record`

**When to Call:** Immediately after successful publish to any channel.

**Request:**

```json
{
  "run_id": "uuid",
  "draft_id": "uuid",
  "channel": "telegram",
  "channel_item_id": "string",
  "channel_url": "string",
  "published_at": "ISO8601 timestamp",
  "persona_id": "uuid",
  "project_id": "uuid"
}
```

**Response:**

```json
{
  "published_item_id": "uuid",
  "status": "recorded"
}
```

#### 3.2. Ingest Initial Metrics

**Purpose:** Store the initial metric snapshot immediately after publishing.

**Endpoint:** `POST /api/publisher/metrics/ingest`

**When to Call:** Immediately after recording publish event (if metrics are available).

**Request:**

```json
{
  "published_item_id": "uuid",
  "channel": "telegram",
  "metrics": {
    "views": 100,
    "reactions": 10,
    "shares": 5,
    "comments": 2
  },
  "measured_at": "ISO8601 timestamp"
}
```

**Response:**

```json
{
  "metric_id": "uuid",
  "status": "ingested"
}
```

#### n8n Workflow Integration Example

```
┌─────────────────────────────────────────────────────────────┐
│                     n8n Publisher Workflow                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Receive Input (Dashboard → n8n)                        │
│     ↓                                                       │
│  2. Generate Content (LLM)                                 │
│     ↓                                                       │
│  3. Publish to Telegram                                    │
│     ↓                                                       │
│  4. POST /api/publisher/publish/record ✅ MANDATORY        │
│     ↓                                                       │
│  5. Get Initial Metrics from Telegram API                  │
│     ↓                                                       │
│  6. POST /api/publisher/metrics/ingest ✅ MANDATORY        │
│     ↓                                                       │
│  7. Publish to Instagram                                   │
│     ↓                                                       │
│  8. POST /api/publisher/publish/record ✅ MANDATORY        │
│     ↓                                                       │
│  9. POST /api/publisher/metrics/ingest ✅ MANDATORY        │
│     ↓                                                       │
│  10. POST /api/publisher/runs/{run_id}/complete            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Metric Normalization

### Purpose

Different social media platforms use different metric names and structures. This mapping table standardizes metrics across all channels for consistent analytics and reporting.

### Channel Mapping Table

| Channel   | Source Field      | Normalized Key    | Comments                          |
|-----------|-------------------|-------------------|-----------------------------------|
| Telegram  | `views`           | `views`           | View Count                        |
| Telegram  | `reactions`       | `reactions`       | User Reactions (emoji reactions)  |
| Telegram  | `forwards`        | `shares`          | Message forwards                  |
| Instagram | `impressions`     | `impressions`     | Impressions (may differ from reach) |
| Instagram | `reach`           | `reach`           | Unique accounts reached           |
| Instagram | `likes`           | `reactions`       | User Likes                        |
| Instagram | `comments`        | `comments`        | Comments                          |
| Instagram | `shares`          | `shares`          | Shares (DMs, Stories, etc.)       |
| Instagram | `saves`           | `saves`           | Post Saves                        |
| TikTok    | `views`           | `views`           | Video Views                       |
| TikTok    | `likes`           | `reactions`       | User Likes                        |
| TikTok    | `comments`        | `comments`        | Comments                          |
| TikTok    | `shares`          | `shares`          | Shares                            |
| YouTube   | `views`           | `views`           | Video Views                       |
| YouTube   | `likes`           | `reactions`       | Likes                             |
| YouTube   | `comments`        | `comments`        | Comments                          |
| YouTube   | `shares`          | `shares`          | Shares                            |

### Normalized Metric Schema

**Database Table:** `item_metrics`

```sql
CREATE TABLE item_metrics (
  id UUID PRIMARY KEY,
  published_item_id UUID NOT NULL REFERENCES published_items(id),
  channel VARCHAR(50) NOT NULL,
  
  -- Normalized metrics (all nullable)
  views INTEGER,
  impressions INTEGER,
  reach INTEGER,
  reactions INTEGER,
  comments INTEGER,
  shares INTEGER,
  saves INTEGER,
  clicks INTEGER,
  
  -- Raw data (for reference)
  raw_metrics JSONB,
  
  -- Metadata
  measured_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Engagement Rate Formula

**Standard Formula:**

```
engagement_rate = (reactions + comments + shares) / max(reach, 1)
```

**Fallback (if reach not available):**

```
engagement_rate = (reactions + comments + shares) / max(views, 1)
```

**Percentage Display:**

```
engagement_rate_percent = engagement_rate * 100
```

### Example Metric Normalization

#### Telegram Raw Metrics

```json
{
  "views": 1500,
  "reactions": {
    "👍": 45,
    "❤️": 32,
    "🔥": 18
  },
  "forwards": 23
}
```

#### Normalized Metrics

```json
{
  "channel": "telegram",
  "views": 1500,
  "reactions": 95,
  "shares": 23,
  "engagement_rate": 0.0787,
  "engagement_rate_percent": 7.87
}
```

#### Instagram Raw Metrics

```json
{
  "impressions": 2500,
  "reach": 2100,
  "likes": 180,
  "comments": 24,
  "shares": 15,
  "saves": 42
}
```

#### Normalized Metrics

```json
{
  "channel": "instagram",
  "impressions": 2500,
  "reach": 2100,
  "reactions": 180,
  "comments": 24,
  "shares": 15,
  "saves": 42,
  "engagement_rate": 0.1043,
  "engagement_rate_percent": 10.43
}
```

### Metric Normalization Service

**Location:** `api/app/services/metric_normalizer.py`

**Interface:**

```python
def normalize_metrics(channel: str, raw_metrics: dict) -> dict:
    """
    Normalize channel-specific metrics to standard schema.
    
    Args:
        channel: Channel name (telegram, instagram, tiktok, youtube)
        raw_metrics: Raw metrics from channel API
    
    Returns:
        Normalized metrics dictionary
    """
    pass

def calculate_engagement_rate(normalized_metrics: dict) -> float:
    """
    Calculate engagement rate from normalized metrics.
    
    Args:
        normalized_metrics: Normalized metrics dictionary
    
    Returns:
        Engagement rate (0.0 to 1.0)
    """
    pass
```

---

## Widget System

### MVP Implementation

**Goal:** Built-in widgets with user-customizable layouts.

#### Built-in Widgets

1. **Persona Overview Widget**
   - Display: Persona name, avatar, health score
   - Metrics: Empathy, Clarity, Faith Integrity
   - Actions: View details, Edit persona

2. **Recent Posts Widget**
   - Display: Last 5 published posts
   - Metrics: Views, reactions, engagement rate per post
   - Actions: View post, View analytics

3. **Engagement Chart Widget**
   - Display: Line chart of engagement over time
   - Filters: Time range (7d, 30d, 90d)
   - Actions: Export data

4. **Red Flags Widget**
   - Display: Current red flags and alerts
   - Actions: View details, Dismiss

5. **EIDOS Recommendations Widget**
   - Display: Top 3 recommendations
   - Actions: View all, Apply recommendation

6. **Channel Performance Widget**
   - Display: Bar chart comparing channels
   - Metrics: Average engagement by channel
   - Actions: Filter by persona

#### Layout Configuration

**User Layout Storage:** `dashboard_views` table

```json
{
  "layout_id": "uuid",
  "user_id": "uuid",
  "name": "My Dashboard",
  "is_default": true,
  "widgets": [
    {
      "widget_id": "persona-overview",
      "position": { "x": 0, "y": 0, "w": 4, "h": 2 },
      "config": {
        "persona_id": "aa0e8400-e29b-41d4-a716-446655440005"
      }
    },
    {
      "widget_id": "engagement-chart",
      "position": { "x": 4, "y": 0, "w": 8, "h": 3 },
      "config": {
        "time_range": "30d",
        "persona_id": "aa0e8400-e29b-41d4-a716-446655440005"
      }
    }
  ]
}
```

**API Endpoints:**

```
GET  /api/dashboards/layouts          - List user layouts
POST /api/dashboards/layouts          - Create layout
PUT  /api/dashboards/layouts/{id}     - Update layout
DELETE /api/dashboards/layouts/{id}   - Delete layout
```

#### UI Implementation

- **Framework:** React Grid Layout or similar
- **Drag-and-drop:** Enabled
- **Resize:** Enabled
- **Save:** Auto-save on change
- **Reset:** "Reset to Default" button

---

### v2 Implementation (Future)

**Goal:** Support external custom widgets defined via JSON Schema.

#### Widget Registry

**Storage:** `widget_registry` table

```sql
CREATE TABLE widget_registry (
  id UUID PRIMARY KEY,
  widget_id VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  widget_type VARCHAR(50) NOT NULL, -- 'builtin' or 'custom'
  schema JSONB NOT NULL,
  renderer_url TEXT, -- For custom widgets
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### Custom Widget Schema

```json
{
  "widget_id": "custom-sentiment-analysis",
  "name": "Sentiment Analysis Chart",
  "description": "Display sentiment trends over time",
  "widget_type": "custom",
  "schema": {
    "data_source": {
      "type": "api",
      "endpoint": "/api/analytics/sentiment",
      "params": {
        "persona_id": { "type": "uuid", "required": true },
        "time_range": { "type": "string", "default": "30d" }
      }
    },
    "config": {
      "chart_type": { "type": "enum", "values": ["line", "bar", "area"] },
      "colors": { "type": "object" }
    }
  },
  "renderer_url": "https://cdn.example.com/widgets/sentiment-v1.js"
}
```

#### Custom Widget Lifecycle

1. **Register Widget**
   ```
   POST /api/widgets/register
   ```

2. **Load Widget**
   - Dashboard loads widget definition from registry
   - Fetches renderer script from `renderer_url`
   - Injects widget into layout

3. **Widget Communication**
   - Widget sends data requests to Dashboard API
   - Dashboard validates requests against schema
   - Dashboard returns data

4. **Security**
   - Widgets run in sandboxed iframes
   - CSP headers enforce origin restrictions
   - Data access limited to schema-defined endpoints

---

## Developer Experience

### 1. API Explorer

**Purpose:** Interactive API documentation with auto-generated examples.

**Implementation:** Swagger UI / ReDoc with enhancements

#### Features

1. **Auto-generated curl Examples**
   
   For every endpoint, automatically generate:
   
   ```bash
   # Example: Create a new run
   curl -X POST "https://api.mpis.example.com/api/publisher/runs" \
     -H "Authorization: Bearer YOUR_TOKEN_HERE" \
     -H "Content-Type: application/json" \
     -d '{
       "run_id": "550e8400-e29b-41d4-a716-446655440000",
       "project_id": "660e8400-e29b-41d4-a716-446655440001",
       "persona_id": "aa0e8400-e29b-41d4-a716-446655440005",
       "channels": ["telegram"],
       "date_from": "2025-12-14",
       "date_to": "2025-12-15"
     }'
   ```

2. **Multiple Language Examples**
   
   - curl
   - Python (requests)
   - JavaScript (fetch)
   - Node.js (axios)

3. **Try It Out**
   
   - Interactive request builder
   - Pre-filled with example data
   - Execute directly from browser
   - View response in real-time

4. **Response Examples**
   
   - Success responses (200, 201)
   - Error responses (400, 401, 404, 500)
   - Full response schemas

#### API Explorer Endpoint

```
GET /api/docs
```

Serves interactive API documentation.

---

### 2. Mock Mode

**Purpose:** Enable local development and testing without external dependencies.

#### Implementation

1. **Environment Variable**
   ```
   MOCK_MODE=true
   ```

2. **Mock Data Fixtures**
   
   **Location:** `api/tests/fixtures/`
   
   ```
   api/tests/fixtures/
   ├── personas.json
   ├── projects.json
   ├── runs.json
   ├── published_items.json
   ├── metrics.json
   └── recommendations.json
   ```

3. **Mock Service Layer**
   
   **Location:** `api/app/services/mock/`
   
   ```python
   # api/app/services/mock/persona_service.py
   
   class MockPersonaService:
       def __init__(self):
           self.fixtures = load_fixtures('personas.json')
       
       async def get_persona(self, persona_id: str):
           return self.fixtures.get(persona_id)
       
       async def list_personas(self):
           return list(self.fixtures.values())
   ```

4. **Service Factory**
   
   ```python
   # api/app/services/factory.py
   
   def get_persona_service():
       if os.getenv('MOCK_MODE') == 'true':
           return MockPersonaService()
       else:
           return RealPersonaService()
   ```

#### Mock Mode Features

- **Fast:** No database or external API calls
- **Predictable:** Same data every time
- **Isolated:** No side effects
- **Complete:** All endpoints work in mock mode

#### Usage

```bash
# Start API in mock mode
MOCK_MODE=true python api/app/main.py

# Run tests with mock mode
MOCK_MODE=true pytest api/tests/
```

---

### 3. End-to-End Tests

**Purpose:** Validate the complete "Happy Path" flow from persona creation to metric viewing.

#### Test Scenario: Happy Path

**Test File:** `e2e/test_happy_path.py`

**Steps:**

1. **Persona Creation**
   ```python
   # Create a new persona
   response = await client.post('/api/personas', json={
       'name': 'Test Persona',
       'credo': {'beliefs': ['Test belief']},
       'ethos': {'tone': 'inspirational'}
   })
   assert response.status_code == 201
   persona_id = response.json()['id']
   ```

2. **Project Creation**
   ```python
   # Create a new project
   response = await client.post('/api/projects', json={
       'name': 'Test Project',
       'persona_id': persona_id,
       'channels': ['telegram']
   })
   assert response.status_code == 201
   project_id = response.json()['id']
   ```

3. **Manual Run**
   ```python
   # Start a manual run
   run_id = str(uuid.uuid4())
   response = await client.post('/api/publisher/runs', json={
       'run_id': run_id,
       'project_id': project_id,
       'persona_id': persona_id,
       'channels': ['telegram'],
       'date_from': '2025-12-14',
       'date_to': '2025-12-15'
   })
   assert response.status_code == 202
   ```

4. **Wait for Completion**
   ```python
   # Poll run status
   for _ in range(30):
       response = await client.get(f'/api/publisher/runs/{run_id}')
       status = response.json()['status']
       if status in ['success', 'failed']:
           break
       await asyncio.sleep(2)
   
   assert status == 'success'
   ```

5. **Validate Run Logs**
   ```python
   # Check run logs
   response = await client.get(f'/api/publisher/runs/{run_id}/logs')
   assert response.status_code == 200
   logs = response.json()
   assert len(logs) > 0
   assert any('published' in log['message'].lower() for log in logs)
   ```

6. **Validate Published Items**
   ```python
   # Check published items
   response = await client.get(f'/api/publisher/runs/{run_id}/published-items')
   assert response.status_code == 200
   items = response.json()
   assert len(items) > 0
   
   published_item_id = items[0]['id']
   assert items[0]['channel'] == 'telegram'
   assert items[0]['channel_item_id'] is not None
   ```

7. **Validate Metrics**
   ```python
   # Check metrics were ingested
   response = await client.get(f'/api/publisher/published-items/{published_item_id}/metrics')
   assert response.status_code == 200
   metrics = response.json()
   assert len(metrics) > 0
   assert metrics[0]['views'] >= 0
   ```

#### Running E2E Tests

```bash
# With mock mode (fast)
MOCK_MODE=true pytest e2e/test_happy_path.py -v

# With real services (slow)
pytest e2e/test_happy_path.py -v

# With Docker Compose
docker-compose -f docker-compose.test.yml up --abort-on-container-exit
```

#### Test Output

```
e2e/test_happy_path.py::test_happy_path_flow PASSED

========== Test Steps ==========
✅ 1. Persona created (id: aa0e8400-...)
✅ 2. Project created (id: 660e8400-...)
✅ 3. Manual run started (run_id: 550e8400-...)
✅ 4. Run completed successfully (status: success)
✅ 5. Run logs validated (12 log entries)
✅ 6. Published items validated (1 item to telegram)
✅ 7. Metrics validated (views: 100, reactions: 10)

========== 1 passed in 45.2s ==========
```

---

## Security

### MVP Security

**Goal:** Simple, effective security for initial deployment.

#### 1. Single Admin Password

**Environment Variable:**

```bash
ADMIN_PASSWORD=your_secure_password_here
```

**Login Endpoint:**

```
POST /api/auth/login
```

**Request:**

```json
{
  "password": "your_secure_password_here"
}
```

**Response:**

```json
{
  "token": "jwt_token_here",
  "expires_at": "2025-12-16T10:00:00Z"
}
```

**Token Format:** JWT with 24-hour expiration

#### 2. Basic Authentication (Alternative)

**Header:**

```
Authorization: Basic base64(admin:password)
```

**Nginx Configuration:**

```nginx
location /api/ {
    auth_basic "MPIS Dashboard";
    auth_basic_user_file /etc/nginx/.htpasswd;
    proxy_pass http://api:3050;
}
```

#### 3. Security Requirements

- ✅ HTTPS only (enforce TLS 1.2+)
- ✅ Secure password storage (bcrypt)
- ✅ JWT token expiration
- ✅ Rate limiting (10 req/sec per IP)
- ✅ CORS configuration
- ✅ Input validation
- ✅ SQL injection protection (parameterized queries)
- ✅ XSS protection (content security policy)

---

### Future-Ready: Bearer Token Support

**Goal:** Prepare infrastructure for multi-user authentication.

#### 1. Authentication Middleware

**Location:** `api/app/middleware/auth.py`

```python
async def bearer_token_auth(request: Request, call_next):
    """
    Middleware to validate Bearer tokens.
    Supports both admin password (MVP) and user tokens (future).
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return JSONResponse(
            status_code=401,
            content={'error': 'Missing authorization header'}
        )
    
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        user = await validate_bearer_token(token)
    elif auth_header.startswith('Basic '):
        user = await validate_basic_auth(auth_header)
    else:
        return JSONResponse(
            status_code=401,
            content={'error': 'Invalid authorization scheme'}
        )
    
    if not user:
        return JSONResponse(
            status_code=401,
            content={'error': 'Invalid credentials'}
        )
    
    request.state.user = user
    response = await call_next(request)
    return response
```

#### 2. User Management (Future)

**Database Schema:**

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL, -- 'admin', 'editor', 'viewer'
  created_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP
);

CREATE TABLE api_tokens (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  token_hash VARCHAR(255) NOT NULL,
  name VARCHAR(100),
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### 3. Role-Based Access Control (Future)

| Role | Permissions |
|------|-------------|
| `admin` | Full access (create, read, update, delete) |
| `editor` | Create and edit personas, projects, runs |
| `viewer` | Read-only access to all data |

**Implementation:**

```python
@require_role('admin')
async def delete_persona(persona_id: str):
    """Only admins can delete personas."""
    pass

@require_role('editor')
async def create_run(run_data: dict):
    """Editors and admins can create runs."""
    pass

@require_role('viewer')
async def get_analytics(persona_id: str):
    """All authenticated users can view analytics."""
    pass
```

---

## Onboarding

### First-Run Wizard

**Purpose:** Guide new users through their first experience with MPIS.

**Trigger:** Display wizard on first login or when no personas exist.

#### Wizard Steps

##### Step 1: Welcome

**UI:**

```
┌─────────────────────────────────────────────┐
│  Welcome to MPIS Dashboard! 🎉              │
│                                             │
│  Let's get you started with a demo         │
│  to explore the system.                    │
│                                             │
│  This wizard will help you:                │
│  ✓ Create a demo persona                   │
│  ✓ Create a demo project                   │
│  ✓ Run a demo publishing workflow          │
│  ✓ View metrics and published items        │
│                                             │
│            [Get Started] [Skip]             │
└─────────────────────────────────────────────┘
```

---

##### Step 2: Create Demo Persona

**UI:**

```
┌─────────────────────────────────────────────┐
│  Step 1/4: Create a Demo Persona            │
│                                             │
│  We'll create a sample persona for you     │
│  called "Alex - The Tech Philosopher"       │
│                                             │
│  Persona Details:                           │
│  • Focuses on technology ethics             │
│  • Inspirational and thoughtful tone        │
│  • Topics: AI, philosophy, innovation       │
│                                             │
│  [Preview Persona] [Create Persona]         │
└─────────────────────────────────────────────┘
```

**Backend Action:**

```python
demo_persona = {
    'id': str(uuid.uuid4()),
    'name': 'Alex - The Tech Philosopher',
    'slug': 'alex-tech-philosopher-demo',
    'credo': {
        'beliefs': [
            'Technology should serve humanity',
            'Ethics must guide innovation',
            'Question everything, build with purpose'
        ]
    },
    'ethos': {
        'tone': 'inspirational',
        'virtues': ['wisdom', 'integrity', 'curiosity']
    },
    'topics': ['AI ethics', 'philosophy', 'innovation', 'technology'],
    'is_demo': True
}
```

---

##### Step 3: Create Demo Project

**UI:**

```
┌─────────────────────────────────────────────┐
│  Step 2/4: Create a Demo Project            │
│                                             │
│  Now let's create a project for publishing │
│  content from your demo persona.            │
│                                             │
│  Project Details:                           │
│  • Name: "Demo Tech Blog"                   │
│  • Persona: Alex - The Tech Philosopher     │
│  • Channels: Telegram (demo)                │
│                                             │
│  [Create Project]                           │
└─────────────────────────────────────────────┘
```

**Backend Action:**

```python
demo_project = {
    'id': str(uuid.uuid4()),
    'name': 'Demo Tech Blog',
    'persona_id': demo_persona['id'],
    'channels': ['telegram_demo'],
    'is_demo': True
}
```

---

##### Step 4: Run Demo

**UI:**

```
┌─────────────────────────────────────────────┐
│  Step 3/4: Run a Demo Workflow              │
│                                             │
│  We'll simulate a publishing workflow       │
│  and generate sample content and metrics.   │
│                                             │
│  This will:                                 │
│  ✓ Generate demo content                    │
│  ✓ "Publish" to a demo channel              │
│  ✓ Create sample metrics                    │
│                                             │
│  [Start Demo Run]                           │
│                                             │
│  Status: ⏳ Running... (Step 2 of 5)        │
└─────────────────────────────────────────────┘
```

**Backend Action:**

```python
# Simulate publishing workflow with mock data
demo_run = {
    'run_id': str(uuid.uuid4()),
    'project_id': demo_project['id'],
    'persona_id': demo_persona['id'],
    'status': 'success',
    'is_demo': True
}

demo_published_item = {
    'id': str(uuid.uuid4()),
    'run_id': demo_run['run_id'],
    'channel': 'telegram_demo',
    'content': 'Sample post about AI ethics...',
    'channel_url': 'https://demo.mpis.example.com/posts/demo-1',
    'is_demo': True
}

demo_metrics = {
    'published_item_id': demo_published_item['id'],
    'views': 1200,
    'reactions': 85,
    'shares': 23,
    'comments': 12,
    'engagement_rate': 0.10
}
```

---

##### Step 5: View Results

**UI:**

```
┌─────────────────────────────────────────────┐
│  Step 4/4: View Your Results 🎉             │
│                                             │
│  Your demo run completed successfully!      │
│                                             │
│  📊 Results:                                │
│  • 1 item published to Telegram (demo)      │
│  • 1,200 views                              │
│  • 85 reactions                             │
│  • 10% engagement rate                      │
│                                             │
│  [View Run Logs]                            │
│  [View Published Items]                     │
│  [View Analytics Dashboard]                 │
│                                             │
│  [Finish Setup]                             │
└─────────────────────────────────────────────┘
```

---

#### Post-Wizard Experience

**After completing the wizard:**

1. User is redirected to the main dashboard
2. Demo data is clearly marked with a "DEMO" badge
3. User can:
   - Explore demo data
   - Create their first real persona
   - Delete demo data (button in settings)

**Demo Data Banner:**

```
┌─────────────────────────────────────────────┐
│ ℹ️ You're viewing demo data                 │
│ [Create Your First Persona] [Delete Demo]   │
└─────────────────────────────────────────────┘
```

---

## Appendix

### A. Database Schema Updates

**New Tables:**

```sql
-- Red Flags tracking
CREATE TABLE red_flags (
  id UUID PRIMARY KEY,
  flag_type VARCHAR(50) NOT NULL,
  severity VARCHAR(20) NOT NULL, -- 'warning', 'critical'
  description TEXT,
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  resolved_at TIMESTAMP
);

-- Widget Registry
CREATE TABLE widget_registry (
  id UUID PRIMARY KEY,
  widget_id VARCHAR(100) UNIQUE NOT NULL,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  widget_type VARCHAR(50) NOT NULL,
  schema JSONB NOT NULL,
  renderer_url TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Dashboard Layouts
CREATE TABLE dashboard_layouts (
  id UUID PRIMARY KEY,
  user_id UUID, -- NULL for default layout
  name VARCHAR(200) NOT NULL,
  is_default BOOLEAN DEFAULT FALSE,
  layout_config JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### B. Environment Variables

```bash
# Application
APP_ENV=production
LOG_LEVEL=INFO
MOCK_MODE=false

# Security
ADMIN_PASSWORD=your_secure_password_here
JWT_SECRET=your_jwt_secret_here
JWT_EXPIRATION_HOURS=24

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/mpis

# n8n
N8N_WEBHOOK_URL=http://n8n:5678/webhook
N8N_API_KEY=your_n8n_api_key

# Redis (for caching)
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
```

---

### C. API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login` | POST | Authenticate user |
| `/api/red-flags` | GET | Get red flags summary |
| `/api/publisher/runs` | POST | Create new run |
| `/api/publisher/runs/{run_id}` | GET | Get run details |
| `/api/publisher/runs/{run_id}/complete` | POST | Complete run (from n8n) |
| `/api/publisher/runs/{run_id}/logs` | GET | Get run logs |
| `/api/publisher/publish/record` | POST | Record publish event |
| `/api/publisher/metrics/ingest` | POST | Ingest metrics |
| `/api/publisher/published-items/{id}/metrics` | GET | Get item metrics |
| `/api/dashboards/layouts` | GET | List user layouts |
| `/api/dashboards/layouts` | POST | Create layout |
| `/api/dashboards/layouts/{id}` | PUT | Update layout |
| `/api/widgets/register` | POST | Register custom widget |
| `/api/onboarding/wizard/start` | POST | Start onboarding wizard |
| `/api/onboarding/demo/create` | POST | Create demo data |
| `/api/onboarding/demo/delete` | DELETE | Delete demo data |

---

### D. Glossary

| Term | Definition |
|------|------------|
| **Correlation ID** | Unique identifier used to track a request across multiple systems |
| **Run** | A single execution of a content generation and publishing workflow |
| **Red Flag** | Critical system issue that requires immediate attention |
| **Engagement Rate** | Metric calculated as (reactions + comments + shares) / reach |
| **Widget** | Self-contained UI component displaying specific data or functionality |
| **Mock Mode** | Development mode using fixture data instead of real services |
| **Bearer Token** | Authentication token passed in the Authorization header |

---

## Conclusion

This technical specification defines the requirements for enhancing the MPIS Dashboard with robust debugging tools, clear integration contracts, metric normalization, extensible widget architecture, improved developer experience, and user-friendly onboarding.

**Implementation Priority:**

1. ✅ **Phase 1 (MVP):** Observability, Contract v1, Metric Normalization
2. ✅ **Phase 2:** Widget System MVP, Security MVP
3. ✅ **Phase 3:** Developer Experience, Onboarding
4. 🔮 **Phase 4 (Future):** Widget System v2, Multi-user Auth

**Document Status:** ✅ Complete

**Last Updated:** 2025-12-15

---

*For questions or clarifications, please contact the MPIS development team.*
