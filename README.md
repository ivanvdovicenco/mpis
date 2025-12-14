# MPIS - Multi-Persona Intelligence System

A self-hosted ecosystem for creating, developing, and analyzing AI-powered digital personas.

## Module 1: Persona Genesis Engine

The Genesis Engine creates AI personas from various source materials through an automated, human-supervised workflow.

### Features

- **Multi-Channel Source Collection**
  - YouTube video transcripts
  - Google Drive documents (PDF, DOCX, Google Docs)
  - Public web enrichment (Wikipedia, search results)

- **AI-Powered Generation**
  - Concept extraction (themes, virtues, tone)
  - Complete persona_core.json generation
  - Human approval loop with edit support

- **Production-Ready**
  - PostgreSQL for persistence
  - Qdrant for vector embeddings
  - Docker deployment
  - Full API documentation

## Quick Start

### Prerequisites

- Docker and Docker Compose
- PostgreSQL container running on `mpis_net`
- Qdrant container running on `mpis_net`
- OpenAI or Anthropic API key

### Server Setup (Ubuntu 24.04, ARM64)

```bash
# Create required directories
sudo mkdir -p /opt/mpis/{input,personas,sources,secrets,infra}
sudo chown -R $USER:$USER /opt/mpis

# Clone the repository
cd /opt/mpis
git clone https://github.com/ivanvdovicenco/mpis.git repo
cd repo

# Copy and configure environment
cp api/.env.example /opt/mpis/infra/.env
nano /opt/mpis/infra/.env  # Add your API keys and passwords

# Run database migrations
docker exec -i mpis-postgres psql -U mpis -d mpis < scripts/002_genesis.sql

# Build and start genesis-api
cd /opt/mpis/infra
docker compose -f docker-compose.genesis.yml up -d --build
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
│   │   ├── routers/       # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── utils/         # Utilities
│   ├── tests/             # Test suite
│   ├── Dockerfile
│   └── requirements.txt
├── scripts/
│   └── 002_genesis.sql    # Database migration
├── infra/
│   └── docker-compose.genesis.yml
├── n8n/
│   └── workflows/         # n8n workflow templates
├── docs/
│   ├── MODULE1_GENESIS_SPEC.md
│   └── ENV.md
├── personas/              # Generated persona files
├── sources/               # Extracted source materials
└── input/                 # Input files (youtube_links.txt)
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/genesis/start` | Start persona generation |
| GET | `/genesis/status/{job_id}` | Check job status |
| POST | `/genesis/approve` | Approve or edit draft |
| GET | `/genesis/export/{persona_id}` | Get export paths |
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

## Defaults & Assumptions

- **LLM Provider:** OpenAI (gpt-4-turbo-preview)
- **Embedding Model:** text-embedding-3-small (1536 dimensions)
- **Chunk Size:** 500-1200 tokens
- **Web Sources Limit:** 20
- **API Port:** 8080 (internal)

## Future Modules

- **Module 2:** Persona Life (metrics, reflection cycles)
- **Module 3:** Social Publisher (content creation)
- **Module 4:** Analytics Dashboard + EIDOS

## License

MIT

## Architecture

See [docs/MODULE1_GENESIS_SPEC.md](docs/MODULE1_GENESIS_SPEC.md) for detailed technical specification.