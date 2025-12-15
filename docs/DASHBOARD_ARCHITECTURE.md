# MPIS Dashboard - Architecture Documentation

**Version:** 1.0  
**Date:** 2025-12-15

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Principles](#architecture-principles)
3. [Component Architecture](#component-architecture)
4. [Data Flow](#data-flow)
5. [Integration Model](#integration-model)
6. [Security Architecture](#security-architecture)
7. [Scalability Considerations](#scalability-considerations)

---

## System Overview

The MPIS Dashboard is designed as an **independent service** that acts as both a user interface and a proxy/aggregator for the MPIS API ecosystem.

### Core Responsibilities

1. **User Interface Layer**: Next.js-based frontend for persona management and analytics
2. **API Gateway**: Proxy and transform requests to MPIS modules
3. **Data Aggregation**: Collect and normalize metrics from multiple channels
4. **Analytics Engine**: AI-powered insights and recommendations
5. **Observability Hub**: Correlation IDs, logging, and red flags monitoring

### Design Philosophy

- **Separation of Concerns**: Dashboard and MPIS API are independent services
- **No Changes to MPIS**: Dashboard adapts to MPIS, not the other way around
- **Transformation Layer**: Dashboard handles field mapping and status aggregation
- **Single Source of Truth**: Dashboard DB stores only Dashboard-specific data

---

## Architecture Principles

### 1. Independent Service Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Dashboard Service                  │
│                                                     │
│  ┌──────────────┐  ┌──────────────┐               │
│  │   Frontend   │  │   Backend    │               │
│  │   (Next.js)  │→ │   (FastAPI)  │               │
│  └──────────────┘  └──────┬───────┘               │
│                            │                        │
│                            ↓                        │
│                   ┌──────────────┐                 │
│                   │  Dashboard   │                 │
│                   │  Database    │                 │
│                   │ (PostgreSQL) │                 │
│                   └──────────────┘                 │
└─────────────────────────────────────────────────────┘
                           │
                           │ HTTP/REST
                           ↓
┌─────────────────────────────────────────────────────┐
│                    MPIS API Service                 │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Genesis  │  │   Life   │  │Publisher │        │
│  │  Module  │  │  Module  │  │  Module  │        │
│  └──────────┘  └──────────┘  └──────────┘        │
│                                                     │
│                   ┌──────────────┐                 │
│                   │  MPIS        │                 │
│                   │  Database    │                 │
│                   │ (PostgreSQL) │                 │
│                   └──────────────┘                 │
└─────────────────────────────────────────────────────┘
```

### 2. Proxy/Aggregator Pattern

Dashboard acts as a **smart proxy** that:

- **Transforms**: Removes Dashboard-specific fields before forwarding
- **Enriches**: Adds correlation IDs and metadata
- **Aggregates**: Combines status from multiple publish attempts
- **Normalizes**: Converts channel-specific metrics to standard schema

### 3. Database Separation

#### Dashboard Database Tables

- `dashboard_projects`: Project metadata
- `dashboard_runs`: Run tracking with correlation to MPIS
- `dashboard_layouts`: User dashboard configurations
- `widget_registry`: Widget definitions
- `red_flags`: System health monitoring
- `metrics_ingestion_jobs`: Scheduled metrics collection
- `normalized_metrics`: Normalized metrics from all channels

#### MPIS Database Tables (unchanged)

- `personas`: Persona definitions
- `content_plans`: Content planning
- `content_drafts`: Generated drafts
- `published_items`: Published content records
- `item_metrics`: Raw metrics from MPIS

---

## Component Architecture

### Frontend (Next.js + shadcn/ui + Tailwind CSS)

```
pages/
├── index.tsx                 # Dashboard home
├── projects/
│   ├── [id].tsx             # Project details
│   └── new.tsx              # Create project
├── personas/
│   ├── [id].tsx             # Persona details
│   └── create.tsx           # Persona creation flow
├── runs/
│   └── [id].tsx             # Run details and logs
└── analytics/
    └── [personaId].tsx      # Analytics dashboard

components/
├── widgets/
│   ├── PersonaOverview.tsx
│   ├── RecentPosts.tsx
│   ├── EngagementChart.tsx
│   ├── RedFlags.tsx
│   └── EidosRecommendations.tsx
├── layouts/
│   └── DashboardLayout.tsx
└── common/
    ├── Header.tsx
    ├── Sidebar.tsx
    └── StatusBadge.tsx
```

### Backend (FastAPI)

```
app/
├── routers/
│   └── dashboard.py         # Dashboard API endpoints
├── services/
│   ├── dashboard.py         # Business logic
│   ├── metric_normalizer.py # Metric normalization
│   └── ai_analyst.py        # AI analytics (future)
├── models/
│   └── dashboard.py         # SQLAlchemy models
└── schemas/
    └── dashboard.py         # Pydantic schemas
```

### Database Schema

```sql
-- Dashboard-specific tables
CREATE TABLE dashboard_projects (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    persona_id UUID REFERENCES personas(id),
    channels TEXT[] NOT NULL,
    created_at TIMESTAMPTZ NOT NULL,
    meta JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE dashboard_runs (
    id UUID PRIMARY KEY,
    run_id UUID NOT NULL UNIQUE,
    project_id UUID REFERENCES dashboard_projects(id),
    persona_id UUID REFERENCES personas(id),
    status TEXT NOT NULL, -- pending/running/success/failed/partial
    started_at TIMESTAMPTZ NOT NULL,
    completed_at TIMESTAMPTZ,
    n8n_execution_id UUID,
    error_message TEXT,
    meta JSONB NOT NULL DEFAULT '{}'
);

CREATE TABLE normalized_metrics (
    id UUID PRIMARY KEY,
    published_item_id UUID REFERENCES published_items(id),
    channel TEXT NOT NULL,
    views INTEGER,
    impressions INTEGER,
    reach INTEGER,
    reactions INTEGER,
    comments INTEGER,
    shares INTEGER,
    saves INTEGER,
    clicks INTEGER,
    engagement_rate NUMERIC(5, 4),
    raw_metrics JSONB NOT NULL,
    measured_at TIMESTAMPTZ NOT NULL,
    source TEXT NOT NULL
);
```

---

## Data Flow

### 1. Content Publishing Flow

```
User → Dashboard Frontend → Dashboard API → n8n → MPIS API
                                ↓
                          Dashboard DB
                         (store run_id,
                          project_id)
                                ↓
                                │
                    ┌───────────┴────────────┐
                    ↓                        ↓
              Transform Request      Track Run Status
           (remove Dashboard fields)  (pending → running)
                    ↓                        ↓
               Forward to n8n          Update Dashboard DB
```

#### Detailed Steps:

1. **User initiates run** via Dashboard UI
2. **Dashboard API creates run record** in `dashboard_runs` table
3. **Dashboard generates `run_id`** and `project_id`
4. **Dashboard forwards request to n8n** with all fields
5. **n8n executes workflow** and calls MPIS API
6. **n8n calls back Dashboard** with completion status
7. **Dashboard calculates final status** (success/failed/partial)
8. **Dashboard updates run record** with final status

### 2. Publish Record Transformation Flow

```
n8n Workflow
     ↓
     │ POST /api/publisher/publish/record
     │ {
     │   draft_id,
     │   channel,
     │   channel_item_id,
     │   channel_url,
     │   run_id,            ← Dashboard-specific
     │   project_id,        ← Dashboard-specific
     │   published_at       ← Dashboard-specific
     │ }
     ↓
Dashboard API (Proxy)
     ↓
     │ 1. Store run_id, project_id, published_at
     │    in Dashboard DB
     │
     │ 2. Transform request (remove Dashboard fields)
     │
     │ 3. Forward to MPIS API
     │    POST /publisher/publish/record
     │    {
     │      draft_id,
     │      channel,
     │      channel_item_id,
     │      channel_url
     │    }
     ↓
MPIS API
     ↓
     │ Store in published_items table
     │ (without Dashboard-specific fields)
     ↓
Response to Dashboard
```

### 3. Status Aggregation Flow

```
n8n completes workflow
     ↓
     │ Calls: POST /api/publisher/runs/{run_id}/complete
     │ {
     │   status: "success",
     │   published_items: [
     │     { channel: "telegram", status: "success" },
     │     { channel: "instagram", status: "failed" }
     │   ]
     │ }
     ↓
Dashboard Status Calculator
     ↓
     │ Rules:
     │ - All success → "success"
     │ - All failed → "failed"
     │ - Mix of success/failed → "partial"
     ↓
Dashboard DB Update
     ↓
     │ UPDATE dashboard_runs
     │ SET status = "partial",
     │     completed_at = NOW()
     │ WHERE run_id = ...
```

### 4. Metrics Ingestion Flow

```
Scheduled Job (Cron)
     ↓
Dashboard Metrics Ingestion Service
     ↓
     ├─→ Telegram Bot API
     │   └─→ Get views, reactions, forwards
     │
     ├─→ Instagram Graph API
     │   └─→ Get impressions, reach, likes, comments, shares
     │
     └─→ TikTok API (future)
         └─→ Get views, likes, comments, shares
     ↓
Metric Normalizer Service
     ↓
     │ Transform channel-specific metrics
     │ to standard schema:
     │ {
     │   views, impressions, reach,
     │   reactions, comments, shares,
     │   saves, clicks, engagement_rate
     │ }
     ↓
Store in normalized_metrics table
```

---

## Integration Model

### Dashboard ↔ MPIS Modules

#### /genesis Integration

**Dashboard proxies Genesis endpoints without transformation:**

```
Dashboard → MPIS Genesis
POST /api/genesis/start        → POST /genesis/start
GET  /api/genesis/status/{id}  → GET  /genesis/status/{id}
POST /api/genesis/approve      → POST /genesis/approve
GET  /api/genesis/export/{id}  → GET  /genesis/export/{id}
```

#### /publisher Integration

**Dashboard transforms Publisher endpoints:**

```
Dashboard → MPIS Publisher

POST /api/publisher/publish/record → POST /publisher/publish/record
(transforms: removes run_id, project_id, published_at)

POST /api/publisher/metrics/ingest → POST /publisher/metrics/ingest
(normalizes metrics before forwarding)
```

#### /analytics Integration

**Dashboard enhances Analytics endpoints:**

```
Dashboard → MPIS Analytics

GET /api/analytics/persona/{id}/summary → GET /analytics/persona/{id}/summary
(adds normalized metrics data)

POST /api/ai-analyst/query (Dashboard-only endpoint)
(uses normalized_metrics + MPIS data)
```

### Dashboard ↔ n8n Workflows

**n8n calls Dashboard endpoints:**

1. **At start of workflow**: n8n receives run metadata from Dashboard
2. **During workflow**: n8n calls MPIS API directly (bypasses Dashboard)
3. **At end of workflow**: n8n calls Dashboard completion endpoint

```javascript
// n8n workflow structure
1. Receive webhook from Dashboard
   → Contains: run_id, project_id, persona_id, channels, etc.

2. Generate content (call MPIS directly)
   → POST /publisher/generate

3. Publish to channels (external APIs)
   → Telegram Bot API, Instagram Graph API, etc.

4. Record publish (call Dashboard proxy)
   → POST /api/publisher/publish/record

5. Complete run (call Dashboard)
   → POST /api/publisher/runs/{run_id}/complete
```

### Dashboard ↔ External APIs

#### Telegram Bot API

```python
# Get message views
GET https://api.telegram.org/bot{token}/getChat?chat_id={channel}

# Get message reactions (Telegram Premium feature)
# Note: Limited access via Bot API, consider MTProto for full stats
```

#### Instagram Graph API

```python
# Requires Facebook Business Account
GET https://graph.facebook.com/v18.0/{media_id}/insights
?metric=impressions,reach,likes,comments,shares,saves
&access_token={token}
```

---

## Security Architecture

### MVP Security Model

```
┌─────────────────────────────────────┐
│  User                               │
└─────────┬───────────────────────────┘
          │
          │ Password
          ↓
┌─────────────────────────────────────┐
│  Dashboard Login                    │
│  POST /api/auth/login               │
└─────────┬───────────────────────────┘
          │
          │ JWT Token (24h expiration)
          ↓
┌─────────────────────────────────────┐
│  Dashboard API                      │
│  (validates token on every request) │
└─────────┬───────────────────────────┘
          │
          │ Internal call (no auth)
          ↓
┌─────────────────────────────────────┐
│  MPIS API                           │
│  (localhost only, not exposed)      │
└─────────────────────────────────────┘
```

### Future: Multi-User Security

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    password_hash VARCHAR(255),
    role VARCHAR(50) -- admin, editor, viewer
);

CREATE TABLE api_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    token_hash VARCHAR(255),
    expires_at TIMESTAMP
);
```

### Security Checklist

- [x] HTTPS only (TLS 1.2+)
- [x] Password hashing (bcrypt)
- [x] JWT tokens with expiration
- [x] CORS configuration
- [x] Input validation (Pydantic)
- [x] SQL injection protection (parameterized queries)
- [ ] Rate limiting (future)
- [ ] API key rotation (future)
- [ ] Audit logging (future)

---

## Scalability Considerations

### Horizontal Scaling

Dashboard API can be scaled horizontally:

```
                    ┌──────────────┐
                    │ Load Balancer│
                    └───────┬──────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
          ↓                 ↓                 ↓
    ┌──────────┐      ┌──────────┐    ┌──────────┐
    │Dashboard │      │Dashboard │    │Dashboard │
    │  API 1   │      │  API 2   │    │  API 3   │
    └────┬─────┘      └────┬─────┘    └────┬─────┘
         │                 │                │
         └─────────────────┼────────────────┘
                           │
                           ↓
                    ┌──────────────┐
                    │  PostgreSQL  │
                    │  (Primary)   │
                    └──────────────┘
```

### Caching Strategy

```
┌──────────────┐
│   Redis      │  ← Cache layer for:
│   Cache      │    - Dashboard layouts
└──────┬───────┘    - Widget definitions
       │            - Red flags summary
       │            - Normalized metrics (recent)
       ↓
┌──────────────┐
│  Dashboard   │
│  API         │
└──────┬───────┘
       │
       ↓
┌──────────────┐
│  PostgreSQL  │
│  Database    │
└──────────────┘
```

### Database Optimization

- **Indexes**: All foreign keys and frequently queried columns
- **Partitioning**: Consider partitioning `normalized_metrics` by date
- **Archiving**: Move old runs (>90 days) to archive table

### Async Processing

For expensive operations, use background tasks:

```python
from fastapi import BackgroundTasks

@router.post("/metrics/ingest-batch")
async def ingest_batch(
    items: List[dict],
    background_tasks: BackgroundTasks
):
    # Queue for background processing
    background_tasks.add_task(process_metrics_batch, items)
    return {"status": "queued", "count": len(items)}
```

---

## Deployment Architecture

### Docker Compose Setup

```yaml
version: '3.8'

services:
  dashboard-frontend:
    build: ./dashboard-ui
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://dashboard-api:8080
  
  dashboard-api:
    build: ./api
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/mpis
      - MPIS_API_URL=http://mpis-api:8080
    depends_on:
      - postgres
  
  mpis-api:
    build: ./api
    ports:
      - "8081:8080"  # Different port, localhost only
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres:5432/mpis
  
  postgres:
    image: postgres:15
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=mpis
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## Monitoring and Observability

### Correlation IDs

Every request includes correlation IDs in headers:

```
X-Run-ID: 550e8400-e29b-41d4-a716-446655440000
X-Project-ID: 660e8400-e29b-41d4-a716-446655440001
X-N8N-Execution-ID: 770e8400-e29b-41d4-a716-446655440002
```

### Logging Format

```json
{
  "timestamp": "2025-12-15T10:00:00Z",
  "level": "INFO",
  "service": "dashboard-api",
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "message": "Run completed successfully",
  "duration_ms": 15234
}
```

### Health Checks

```
GET /health        # Basic health check
GET /health/db     # Database connectivity
GET /health/mpis   # MPIS API connectivity
```

---

## Conclusion

The MPIS Dashboard architecture is designed for:

- **Independence**: Dashboard is a standalone service
- **Flexibility**: Easy to add new channels and widgets
- **Observability**: Full tracing with correlation IDs
- **Scalability**: Horizontal scaling and caching support
- **Security**: Token-based auth with future multi-user support

---

*For questions or clarifications, please contact the MPIS development team.*
