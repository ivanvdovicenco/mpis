# MPIS - Multi-Persona Intelligence System

A self-hosted ecosystem for creating, developing, and analyzing AI-powered digital personas.

## Modules

### Module 1: Persona Genesis Engine
Create AI personas from various source materials through automated, human-supervised workflows.

### Module 2: Persona Life
Continuous persona evolution through interactions, reflection cycles, and memory updates.

### Module 3: Social Publisher
Plan, generate, approve, and publish content under persona voice with metrics tracking.

### Module 4: Analytics Dashboard + EIDOS
Performance analytics and AI-powered actionable recommendations.

## Features

- **Multi-Channel Source Collection**: YouTube, Google Drive, web enrichment
- **AI-Powered Generation**: Concept extraction, persona_core.json generation
- **Human Approval Loop**: Review, edit, and approve all outputs
- **Reflection Cycles**: Daily/weekly persona evolution
- **Content Publishing**: RAG-powered content generation
- **EIDOS Recommendations**: AI-driven content strategy insights
- **Full Provenance Tracking**: Trace all outputs to sources
- **n8n Integration**: Ready-to-use workflow templates

## Quick Start

### Prerequisites

- Docker and Docker Compose v2+
- Ubuntu 24.04 LTS (ARM64 supported)
- OpenAI or Anthropic API key

### Installation

```bash
# Create required directories
sudo mkdir -p /opt/mpis/{input,personas,sources,secrets,infra,tmp,exports}
sudo chown -R 1000:1000 /opt/mpis

# Clone the repository
cd /opt/mpis
git clone https://github.com/ivanvdovicenco/mpis.git repo
cd repo

# Copy and configure environment
cp api/.env.example /opt/mpis/infra/.env
nano /opt/mpis/infra/.env  # Add your API keys and passwords

# Run all database migrations
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/002_genesis.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/003_life.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/004_publisher.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/005_analytics.sql

# Build and start MPIS API
cd /opt/mpis/repo/infra
docker compose -f docker-compose.full.yml up -d --build
```

### Verify Installation

```bash
# Check health
curl http://localhost:8080/health

# View API docs
open http://localhost:8080/docs
```

### Create a Persona

```bash
# Start generation
curl -X POST http://localhost:8080/genesis/start \
  -H "Content-Type: application/json" \
  -d '{
    "persona_name": "Alexey",
    "inspiration_source": "Tim Keller",
    "language": "en",
    "public_persona": true,
    "public_name": "Tim Keller"
  }'

# Check status (use job_id from response)
curl http://localhost:8080/genesis/status/{job_id}

# Approve and commit
curl -X POST http://localhost:8080/genesis/approve \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "...",
    "draft_no": 1,
    "confirm": true
  }'
```

### YouTube Links

Create `/opt/mpis/input/youtube_links.txt`:

```
# Tim Keller sermons
https://youtube.com/watch?v=VIDEO_ID_1
https://youtu.be/VIDEO_ID_2
https://youtube.com/shorts/VIDEO_ID_3
```

### Google Drive Setup

1. Create a Google Cloud service account
2. Download JSON key to `/opt/mpis/secrets/gdrive_sa.json`
3. Share your folder with the service account email
4. Include `gdrive_folder_id` in your request

## Project Structure

```
/opt/mpis/
├── api/                    # FastAPI application
│   ├── app/
│   │   ├── main.py        # Application entry
│   │   ├── config.py      # Configuration
│   │   ├── routers/       # API endpoints (genesis, life, publisher, analytics)
│   │   ├── services/      # Business logic
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── utils/         # Utilities
│   ├── tests/             # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/
│   ├── 002_genesis.sql    # Genesis tables
│   ├── 003_life.sql       # Life tables
│   ├── 004_publisher.sql  # Publisher tables
│   └── 005_analytics.sql  # Analytics tables
├── infra/
│   ├── docker-compose.genesis.yml
│   ├── docker-compose.life.yml
│   ├── docker-compose.publisher.yml
│   ├── docker-compose.analytics.yml
│   └── docker-compose.full.yml
├── n8n/
│   └── workflows/         # n8n workflow templates
├── docs/
│   ├── SETUP_GUIDE.md
│   ├── MODULE1_GENESIS_SPEC.md
│   ├── MODULE2_LIFE_SPEC.md
│   ├── MODULE3_PUBLISHER_SPEC.md
│   ├── MODULE4_ANALYTICS_SPEC.md
│   └── ENV.md
├── personas/              # Generated persona files
├── sources/               # Extracted source materials
└── input/                 # Input files (youtube_links.txt)
```

## API Endpoints

### Module 1: Genesis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/genesis/start` | Start persona generation |
| GET | `/genesis/status/{job_id}` | Check job status |
| POST | `/genesis/approve` | Approve or edit draft |
| GET | `/genesis/export/{persona_id}` | Get export paths |

### Module 2: Life
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/life/event` | Ingest life event |
| POST | `/life/cycle/start` | Start reflection cycle |
| GET | `/life/cycle/status/{cycle_id}` | Check cycle status |
| POST | `/life/cycle/approve` | Approve cycle |

### Module 3: Publisher
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/publisher/plan` | Create content plan |
| POST | `/publisher/generate` | Generate draft |
| GET | `/publisher/draft/{draft_id}` | Get draft |
| POST | `/publisher/approve` | Approve draft |
| POST | `/publisher/publish/record` | Record publish |
| POST | `/publisher/metrics/ingest` | Ingest metrics |

### Module 4: Analytics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/analytics/persona/{id}/summary` | Get analytics summary |
| POST | `/analytics/recompute` | Trigger recomputation |
| GET | `/analytics/recommendations/{id}` | Get EIDOS recommendations |
| POST | `/analytics/experiments` | Create experiment |

### Common
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | OpenAPI documentation |

## Configuration

See [docs/ENV.md](docs/ENV.md) for complete environment variable reference.

Key settings:

```env
DATABASE_URL=postgresql+asyncpg://mpis:PASSWORD@mpis-postgres:5432/mpis
QDRANT_URL=http://mpis-qdrant:6333
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
```

## Optional: Caddy Reverse Proxy

To expose Genesis API via HTTPS at `genesis.46.62.174.134.nip.io`:

Add to `/var/n8n/Caddyfile`:

```
genesis.46.62.174.134.nip.io {
    reverse_proxy genesis-api:8080
}
```

Then:

```bash
# Ensure genesis-api is on the same network as Caddy
docker network connect n8n_default genesis-api

# Reload Caddy
docker exec n8n-caddy-1 caddy reload --config /etc/caddy/Caddyfile
```

## Testing

```bash
cd api
pip install -r requirements.txt
DRY_RUN=true pytest tests/ -v
```

## n8n Workflow Templates

Import ready-to-use workflows from `n8n/workflows/`:

- `content-publishing.json` - Full content publishing workflow
- `daily-reflection.json` - Daily reflection cycle automation

## Defaults & Assumptions

- **LLM Provider:** OpenAI (gpt-4-turbo-preview)
- **Embedding Model:** text-embedding-3-small (1536 dimensions)
- **Chunk Size:** 500-1200 tokens
- **Web Sources Limit:** 20
- **API Port:** 8080 (internal, localhost only)

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) - Complete installation instructions
- [Module 1 Spec](docs/MODULE1_GENESIS_SPEC.md) - Genesis technical specification
- [Module 2 Spec](docs/MODULE2_LIFE_SPEC.md) - Life technical specification
- [Module 3 Spec](docs/MODULE3_PUBLISHER_SPEC.md) - Publisher technical specification
- [Module 4 Spec](docs/MODULE4_ANALYTICS_SPEC.md) - Analytics technical specification
- [Environment Variables](docs/ENV.md) - Configuration reference

## License

MIT

## Architecture

See the technical specification docs for detailed architecture information.