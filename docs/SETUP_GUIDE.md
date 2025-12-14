# MPIS Setup Guide

Complete installation and operation guide for the Multi-Persona Intelligence System.

## Prerequisites

- Ubuntu 24.04 LTS (ARM64)
- Docker and Docker Compose v2+
- At least 4GB RAM, 20GB disk space
- OpenAI or Anthropic API key

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Caddy (ports 80/443)                    │
│                      HTTPS + Reverse Proxy                      │
└─────────────────────────────────────────────────────────────────┘
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐   ┌─────────────────────┐   ┌─────────────────┐
│   n8n (:5678)   │   │  MPIS API (:8080)   │   │  Other Services │
│   Localhost     │   │   Genesis/Life/     │   │                 │
│                 │   │   Publisher/Analytics│   │                 │
└─────────────────┘   └─────────────────────┘   └─────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                    ▼                           ▼
          ┌─────────────────┐         ┌─────────────────┐
          │  PostgreSQL     │         │     Qdrant      │
          │  (:5432)        │         │    (:6333)      │
          │  mpis-postgres  │         │   mpis-qdrant   │
          └─────────────────┘         └─────────────────┘
```

## Step 1: Create Directory Structure

```bash
# Create base directory
sudo mkdir -p /opt/mpis/{api,scripts,docs,n8n,personas,sources,input,infra,secrets,tmp,exports}

# Set ownership (Docker containers run as UID 1000)
sudo chown -R 1000:1000 /opt/mpis
```

## Step 2: Install Prerequisites (if not already installed)

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose v2
sudo apt-get update
sudo apt-get install docker-compose-plugin
```

## Step 3: Create Docker Network

```bash
docker network create mpis_net
```

## Step 4: Start PostgreSQL

```bash
docker run -d \
  --name mpis-postgres \
  --network mpis_net \
  -e POSTGRES_USER=mpis \
  -e POSTGRES_PASSWORD=YOUR_SECURE_PASSWORD \
  -e POSTGRES_DB=mpis \
  -v /opt/mpis/postgres_data:/var/lib/postgresql/data \
  --restart unless-stopped \
  postgres:16-alpine
```

## Step 5: Start Qdrant

```bash
docker run -d \
  --name mpis-qdrant \
  --network mpis_net \
  -v /opt/mpis/qdrant_data:/qdrant/storage \
  --restart unless-stopped \
  qdrant/qdrant:latest
```

## Step 6: Run Database Migrations

```bash
# Clone the repository
cd /opt/mpis
git clone https://github.com/ivanvdovicenco/mpis.git repo
cd repo

# Run migrations in order
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/002_genesis.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/003_life.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/004_publisher.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/005_analytics.sql
```

## Step 7: Configure Environment

```bash
# Copy example environment file
cp /opt/mpis/repo/api/.env.example /opt/mpis/infra/.env

# Edit with your values
nano /opt/mpis/infra/.env

# IMPORTANT: Update these values:
# - DATABASE_URL with your postgres password
# - OPENAI_API_KEY or ANTHROPIC_API_KEY
```

## Step 8: Start MPIS API

```bash
cd /opt/mpis/repo/infra

# Build and start
docker compose -f docker-compose.full.yml up -d --build

# Or use the genesis-only compose if you don't need all modules
# docker compose -f docker-compose.genesis.yml up -d --build
```

## Step 9: Verify Installation

```bash
# Check health
curl http://localhost:8080/health

# Expected response:
# {"status":"healthy","service":"MPIS API","version":"1.0.0"}

# Check API docs
curl http://localhost:8080/docs

# Check all modules are available
curl http://localhost:8080/ | jq
```

## Step 10: (Optional) Configure Caddy for HTTPS

If you want to expose MPIS API via HTTPS:

```bash
# Add to your Caddyfile (e.g., /var/n8n/Caddyfile)
genesis.YOUR_IP.nip.io {
    reverse_proxy genesis-api:8080
}

# Connect to Caddy network if needed
docker network connect n8n_default genesis-api

# Reload Caddy
docker exec n8n-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

## Usage Examples

### Create a Persona (Genesis)

```bash
curl -X POST http://localhost:8080/genesis/start \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Wisdom Guide",
    "inspiration_source": "Tim Keller",
    "language": "en",
    "public_persona": true,
    "public_name": "Tim Keller"
  }'
```

### Ingest a Life Event

```bash
curl -X POST http://localhost:8080/life/event \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "YOUR_PERSONA_ID",
    "event_type": "conversation",
    "content": "User asked about finding meaning in difficult times",
    "tags": ["meaning", "suffering", "pastoral"]
  }'
```

### Start a Reflection Cycle

```bash
curl -X POST http://localhost:8080/life/cycle/start \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "YOUR_PERSONA_ID",
    "cycle_type": "daily",
    "options": {"lookback_days": 1}
  }'
```

### Create a Content Plan

```bash
curl -X POST http://localhost:8080/publisher/plan \
  -H "Content-Type: application/json" \
  -d '{
    "persona_id": "YOUR_PERSONA_ID",
    "title": "Finding Hope in Uncertainty",
    "topic": "faith during difficult times",
    "channel": "telegram",
    "language": "en"
  }'
```

### Generate Content Draft

```bash
curl -X POST http://localhost:8080/publisher/generate \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "YOUR_PLAN_ID",
    "variants": 2
  }'
```

### Get Analytics Summary

```bash
curl "http://localhost:8080/analytics/persona/YOUR_PERSONA_ID/summary?range=30d"
```

### Get EIDOS Recommendations

```bash
curl http://localhost:8080/analytics/recommendations/YOUR_PERSONA_ID
```

## n8n Workflow Integration

Import the workflow templates from `/n8n/workflows/`:

1. `content-publishing.json` - Full content publishing workflow
2. `daily-reflection.json` - Daily reflection cycle automation

### Required n8n Environment Variables

```
PERSONA_ID=your-default-persona-id
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_APPROVAL_CHAT_ID=your-approval-chat-id
TELEGRAM_PUBLISH_CHANNEL_ID=your-channel-id
TELEGRAM_CHANNEL_USERNAME=your-channel-username
```

## Troubleshooting

### API Container Won't Start

```bash
# Check logs
docker logs genesis-api

# Common issues:
# - Database connection failed: Check DATABASE_URL and postgres container
# - Qdrant connection failed: Check QDRANT_URL and qdrant container
```

### Database Migration Errors

```bash
# Connect to postgres and check
docker exec -it mpis-postgres psql -U mpis -d mpis

# List tables
\dt

# Check if tables exist
SELECT * FROM personas LIMIT 1;
```

### Qdrant Not Available

```bash
# Check Qdrant status
curl http://localhost:6333/collections

# The API works without Qdrant but embeddings won't be stored
```

### Permission Errors on /opt/mpis

```bash
# Reset permissions
sudo chown -R 1000:1000 /opt/mpis

# Check current ownership
ls -la /opt/mpis
```

## Security Checklist

- [ ] Database password changed from default
- [ ] API only accessible via localhost or Caddy
- [ ] UFW rules block direct access to ports 5678, 8080, 5432, 6333
- [ ] .env file is NOT in Git (use .env.example as template)
- [ ] Secrets stored in /opt/mpis/secrets only
- [ ] API key configured if exposing externally

## Service Ports

| Service | Internal Port | Binding |
|---------|--------------|---------|
| MPIS API | 8080 | 127.0.0.1:8080 |
| Life API | 8090 | 127.0.0.1:8090 (optional) |
| Publisher API | 8091 | 127.0.0.1:8091 (optional) |
| Analytics API | 8092 | 127.0.0.1:8092 (optional) |
| PostgreSQL | 5432 | Internal only |
| Qdrant | 6333 | Internal only |
| n8n | 5678 | 127.0.0.1:5678 |
| Caddy | 80, 443 | Public |

## Backup and Restore

### Backup

```bash
# Backup database
docker exec mpis-postgres pg_dump -U mpis mpis > /opt/mpis/backups/mpis_$(date +%Y%m%d).sql

# Backup Qdrant
tar -czf /opt/mpis/backups/qdrant_$(date +%Y%m%d).tar.gz /opt/mpis/qdrant_data

# Backup personas
tar -czf /opt/mpis/backups/personas_$(date +%Y%m%d).tar.gz /opt/mpis/personas
```

### Restore

```bash
# Restore database
docker exec -i mpis-postgres psql -U mpis -d mpis < /opt/mpis/backups/mpis_YYYYMMDD.sql

# Restore Qdrant
tar -xzf /opt/mpis/backups/qdrant_YYYYMMDD.tar.gz -C /

# Restore personas
tar -xzf /opt/mpis/backups/personas_YYYYMMDD.tar.gz -C /
```

## Support

- Documentation: `/docs/` directory
- API Reference: `http://localhost:8080/docs`
- Issues: GitHub Issues
