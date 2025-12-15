# MPIS Dashboard API Documentation

**Version:** 1.0  
**Date:** 2025-12-15

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Authentication](#authentication)
4. [API Endpoints](#api-endpoints)
5. [Examples](#examples)
6. [Integration Guide](#integration-guide)

---

## Overview

The MPIS Dashboard API provides a centralized interface for managing AI personas, monitoring content performance, and analyzing metrics. It acts as:

1. **Independent Service**: Dashboard has its own database and business logic
2. **Proxy/Aggregator**: Transforms and forwards requests to MPIS API modules
3. **Analytics Hub**: Aggregates and normalizes metrics from multiple channels

### Key Features

- **Project Management**: Create and manage publishing projects
- **Run Tracking**: Track content generation runs with status aggregation (including `partial` status)
- **Metrics Normalization**: Normalize metrics across Telegram, Instagram, TikTok, YouTube
- **Dashboard Layouts**: Customizable dashboard layouts and widgets
- **AI Analyst**: Query-based analytics and recommendations
- **Persona Flow**: Complete persona creation and management workflow
- **Red Flags**: Monitor system health and critical issues

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Dashboard System                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Dashboard  │  │   Dashboard  │  │   Dashboard  │    │
│  │   Frontend   │→ │   API        │→ │   Database   │    │
│  │  (Next.js)   │  │  (FastAPI)   │  │ (PostgreSQL) │    │
│  └──────────────┘  └──────┬───────┘  └──────────────┘    │
│                            │                               │
└────────────────────────────┼───────────────────────────────┘
                             │
                             ↓ Proxy/Transform
           ┌─────────────────────────────────────┐
           │         MPIS API Modules            │
           ├─────────────────────────────────────┤
           │  /genesis  │  /life  │  /publisher  │
           │            │         │  /analytics   │
           └─────────────────────────────────────┘
```

### Dashboard as Proxy

The Dashboard API transforms requests before forwarding to MPIS:

1. **PublishRecordRequest Transformation**:
   - Dashboard receives: `draft_id`, `channel`, `channel_item_id`, `channel_url`, `run_id`, `project_id`, `published_at`
   - Dashboard stores: `run_id`, `project_id`, `published_at` in local DB
   - Dashboard forwards to MPIS: `draft_id`, `channel`, `channel_item_id`, `channel_url` (without Dashboard-specific fields)

2. **Status Aggregation**:
   - MPIS returns: `success` or `failed`
   - Dashboard calculates: `success`, `failed`, or `partial`
   - `partial` = at least one success AND one failure in a run

---

## Authentication

### MVP: Admin Password

For the initial deployment, Dashboard uses a simple admin password.

#### Environment Variable

```bash
ADMIN_PASSWORD=your_secure_password_here
```

#### Login Endpoint

```http
POST /api/auth/login
Content-Type: application/json

{
  "password": "your_secure_password_here"
}
```

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2025-12-16T10:00:00Z"
}
```

#### Using the Token

Include the JWT token in the Authorization header:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## API Endpoints

### Dashboard Projects

#### Create Project

Create a new dashboard project.

```http
POST /api/projects
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "Tech Blog Project",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "channels": ["telegram", "instagram"]
}
```

**Response:**

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Tech Blog Project",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "channels": ["telegram", "instagram"],
  "created_at": "2025-12-15T10:00:00Z"
}
```

#### Get Project

```http
GET /api/projects/{project_id}
Authorization: Bearer {token}
```

---

### Dashboard Runs

#### Create Run

Start a new content generation run.

```http
POST /api/publisher/runs
Content-Type: application/json
Authorization: Bearer {token}

{
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "channels": ["telegram"],
  "date_from": "2025-12-14",
  "date_to": "2025-12-15",
  "templates": {
    "news_prompt_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "format_telegram_id": "cc0e8400-e29b-41d4-a716-446655440007"
  },
  "options": {
    "lookback_days": 1,
    "max_items": 10
  }
}
```

**Response:**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "run_id": "880e8400-e29b-41d4-a716-446655440003",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "started_at": "2025-12-15T10:00:00Z",
  "completed_at": null,
  "n8n_execution_id": null,
  "error_message": null
}
```

#### Get Run Status

```http
GET /api/publisher/runs/{run_id}
Authorization: Bearer {token}
```

**Response:**

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "run_id": "880e8400-e29b-41d4-a716-446655440003",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "partial",
  "started_at": "2025-12-15T10:00:00Z",
  "completed_at": "2025-12-15T10:15:00Z",
  "n8n_execution_id": "990e8400-e29b-41d4-a716-446655440004",
  "error_message": null
}
```

#### Complete Run (from n8n)

```http
POST /api/publisher/runs/{run_id}/complete
Content-Type: application/json

{
  "run_id": "880e8400-e29b-41d4-a716-446655440003",
  "status": "success",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "n8n_execution_id": "990e8400-e29b-41d4-a716-446655440004",
  "error": null,
  "published_items": [
    {
      "draft_id": "aa0e8400-e29b-41d4-a716-446655440005",
      "channel": "telegram",
      "channel_item_id": "12345",
      "channel_url": "https://t.me/channel/12345",
      "status": "success",
      "metrics": {
        "views": 100,
        "reactions": 10,
        "shares": 5
      }
    }
  ]
}
```

---

### Publish Record (Proxy)

Dashboard transforms and forwards publish records to MPIS.

```http
POST /api/publisher/publish/record
Content-Type: application/json
Authorization: Bearer {token}

{
  "draft_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "channel": "telegram",
  "channel_item_id": "12345",
  "channel_url": "https://t.me/channel/12345"
}
```

**Note**: Dashboard stores `run_id`, `project_id`, and `published_at` locally but does NOT forward them to MPIS.

**Response:**

```json
{
  "published_item_id": "bb0e8400-e29b-41d4-a716-446655440006",
  "status": "recorded"
}
```

---

### Dashboard Layouts

#### List Layouts

```http
GET /api/dashboards/layouts?user_id={user_id}
Authorization: Bearer {token}
```

#### Create Layout

```http
POST /api/dashboards/layouts
Content-Type: application/json
Authorization: Bearer {token}

{
  "name": "My Dashboard",
  "user_id": null,
  "is_default": true,
  "layout_config": {
    "widgets": [
      {
        "widget_id": "persona-overview",
        "position": { "x": 0, "y": 0, "w": 4, "h": 2 },
        "config": {
          "persona_id": "550e8400-e29b-41d4-a716-446655440000"
        }
      }
    ]
  }
}
```

---

### Widgets

#### List Widgets

```http
GET /api/widgets
Authorization: Bearer {token}
```

#### Register Widget

```http
POST /api/widgets/register
Content-Type: application/json
Authorization: Bearer {token}

{
  "widget_id": "custom-sentiment",
  "name": "Sentiment Analysis",
  "description": "Display sentiment trends",
  "widget_type": "custom",
  "schema": {
    "data_source": {
      "type": "api",
      "endpoint": "/api/analytics/sentiment"
    }
  },
  "renderer_url": "https://cdn.example.com/widgets/sentiment-v1.js"
}
```

---

### Red Flags

#### Get Red Flags Summary

```http
GET /api/red-flags
Authorization: Bearer {token}
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
    "alert": true
  },
  "missing_publish_records": {
    "count": 2,
    "alert": true
  }
}
```

---

### Metrics Ingestion

#### Create Ingestion Job

Create a periodic job to fetch metrics from external APIs.

```http
POST /api/metrics/jobs
Content-Type: application/json
Authorization: Bearer {token}

{
  "job_name": "telegram_metrics_hourly",
  "channel": "telegram",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_cron": "0 * * * *",
  "config": {
    "lookback_hours": 24,
    "bot_token": "TELEGRAM_BOT_TOKEN"
  }
}
```

**Response:**

```json
{
  "id": "cc0e8400-e29b-41d4-a716-446655440007",
  "job_name": "telegram_metrics_hourly",
  "channel": "telegram",
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "schedule_cron": "0 * * * *",
  "last_run_at": null,
  "next_run_at": "2025-12-15T11:00:00Z",
  "enabled": true
}
```

---

### AI Analyst

#### Query AI Analyst

```http
POST /api/ai-analyst/query
Content-Type: application/json
Authorization: Bearer {token}

{
  "persona_id": "550e8400-e29b-41d4-a716-446655440000",
  "time_range": "30d",
  "question": "What are the best performing content topics?"
}
```

**Response:**

```json
{
  "answer": "Based on the data from the last 30 days, your best performing content topics are: 1) AI ethics (avg engagement: 12.3%), 2) Technology philosophy (avg engagement: 10.8%), and 3) Innovation trends (avg engagement: 9.5%).",
  "citations": [
    {
      "published_item_id": "dd0e8400-e29b-41d4-a716-446655440008",
      "channel": "telegram",
      "published_at": "2025-12-10T10:00:00Z",
      "metrics": {
        "views": 1200,
        "engagement_rate": 0.123
      }
    }
  ],
  "suggested_actions": [
    "Create more content about AI ethics",
    "Experiment with posting times for philosophy topics"
  ],
  "confidence": 0.85
}
```

---

### Persona Flow (Proxy to Genesis)

#### Start Persona Creation

```http
POST /api/genesis/start
Content-Type: application/json
Authorization: Bearer {token}

{
  "persona_name": "Tech Philosopher",
  "language": "en",
  "inspiration_source": "Tim Keller",
  "public_persona": true,
  "public_name": "Tim Keller",
  "gdrive_folder_id": "1ABC123...",
  "sources": [
    "https://youtube.com/watch?v=xyz",
    "https://example.com/article"
  ],
  "notes": "Focus on technology ethics and philosophy"
}
```

#### Get Persona Status

```http
GET /api/genesis/status/{job_id}
Authorization: Bearer {token}
```

#### Approve Persona

```http
POST /api/genesis/approve
Content-Type: application/json
Authorization: Bearer {token}

{
  "job_id": "ee0e8400-e29b-41d4-a716-446655440009",
  "draft_no": 1,
  "confirm": true
}
```

#### Get Persona Export Path

```http
GET /api/genesis/export/{persona_id}
Authorization: Bearer {token}
```

---

## Examples

### Complete Workflow: Create Project and Run Content Generation

#### Step 1: Create Project

```bash
curl -X POST "http://localhost:8080/api/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Tech Blog",
    "persona_id": "550e8400-e29b-41d4-a716-446655440000",
    "channels": ["telegram", "instagram"]
  }'
```

#### Step 2: Start Run

```bash
curl -X POST "http://localhost:8080/api/publisher/runs" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "660e8400-e29b-41d4-a716-446655440001",
    "persona_id": "550e8400-e29b-41d4-a716-446655440000",
    "channels": ["telegram"],
    "date_from": "2025-12-14",
    "date_to": "2025-12-15"
  }'
```

#### Step 3: Check Run Status

```bash
curl -X GET "http://localhost:8080/api/publisher/runs/$RUN_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### Step 4: Query AI Analyst

```bash
curl -X POST "http://localhost:8080/api/ai-analyst/query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "550e8400-e29b-41d4-a716-446655440000",
    "time_range": "30d",
    "question": "What are my best performing posts?"
  }'
```

---

## Integration Guide

### Integrating with n8n Workflows

Dashboard expects n8n workflows to call completion endpoints:

```javascript
// n8n HTTP Request Node
{
  "method": "POST",
  "url": "http://dashboard:8080/api/publisher/runs/{{$json.run_id}}/complete",
  "body": {
    "run_id": "{{$json.run_id}}",
    "status": "success",
    "persona_id": "{{$json.persona_id}}",
    "project_id": "{{$json.project_id}}",
    "n8n_execution_id": "{{$workflow.executionId}}",
    "published_items": "{{$json.published_items}}"
  }
}
```

### Integrating with Telegram Bot API

To fetch metrics from Telegram:

```python
import requests

def fetch_telegram_metrics(bot_token, channel_name, message_id):
    """Fetch metrics for a Telegram post."""
    url = f"https://api.telegram.org/bot{bot_token}/getChat"
    response = requests.get(url, params={"chat_id": channel_name})
    
    # Get post views/reactions
    # Note: Telegram Bot API has limitations for channel stats
    # Consider using MTProto for full channel analytics
    
    return {
        "views": response.json().get("views", 0),
        "reactions": response.json().get("reactions", {}),
        "forwards": response.json().get("forwards", 0)
    }
```

### Integrating with Instagram Graph API

To fetch metrics from Instagram (requires Business Account):

```python
import requests

def fetch_instagram_metrics(access_token, media_id):
    """Fetch metrics for an Instagram post."""
    url = f"https://graph.facebook.com/v18.0/{media_id}/insights"
    params = {
        "metric": "impressions,reach,likes,comments,shares,saves",
        "access_token": access_token
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    metrics = {}
    for item in data.get("data", []):
        metrics[item["name"]] = item["values"][0]["value"]
    
    return metrics
```

### Metric Normalization

Dashboard automatically normalizes metrics from different channels:

| Channel   | Source Field  | Normalized Key |
|-----------|---------------|----------------|
| Telegram  | `views`       | `views`        |
| Telegram  | `reactions`   | `reactions`    |
| Telegram  | `forwards`    | `shares`       |
| Instagram | `impressions` | `impressions`  |
| Instagram | `reach`       | `reach`        |
| Instagram | `likes`       | `reactions`    |
| Instagram | `comments`    | `comments`     |
| Instagram | `shares`      | `shares`       |
| Instagram | `saves`       | `saves`        |

Engagement rate is calculated as:

```
engagement_rate = (reactions + comments + shares) / max(reach, views, 1)
```

---

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:

- `400`: Bad Request (validation error)
- `401`: Unauthorized (missing or invalid token)
- `404`: Not Found (resource doesn't exist)
- `500`: Internal Server Error

---

## Rate Limiting

MVP does not include rate limiting, but it's recommended for production:

```
10 requests per second per IP
100 requests per minute per user
```

---

## Changelog

### Version 1.0 (2025-12-15)

- Initial release
- Dashboard projects and runs
- Metrics normalization
- Dashboard layouts and widgets
- AI Analyst queries
- Persona flow proxy
- Red flags monitoring

---

*For questions or support, please contact the MPIS development team.*
