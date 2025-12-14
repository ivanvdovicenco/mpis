# MPIS Genesis API - Environment Variables Reference

This document describes all environment variables used by the Genesis API.

## Application Settings

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `APP_NAME` | `MPIS Genesis API` | No | Application name |
| `APP_VERSION` | `1.0.0` | No | Application version |
| `DEBUG` | `false` | No | Enable debug mode |
| `DRY_RUN` | `false` | No | Mock LLM calls for testing |

## Database Configuration

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `DATABASE_URL` | See below | **Yes** | PostgreSQL connection string |
| `DATABASE_POOL_SIZE` | `10` | No | Connection pool size |
| `DATABASE_MAX_OVERFLOW` | `20` | No | Max overflow connections |

**Default DATABASE_URL:** `postgresql+asyncpg://mpis:mpis@mpis-postgres:5432/mpis`

## Qdrant Vector Store

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `QDRANT_URL` | `http://mpis-qdrant:6333` | No | Qdrant server URL |
| `QDRANT_API_KEY` | None | No | Qdrant API key (if secured) |
| `QDRANT_COLLECTION_SOURCES` | `persona_sources_embeddings` | No | Sources collection name |
| `QDRANT_COLLECTION_CORE` | `persona_core_embeddings` | No | Core collection name |
| `EMBEDDING_DIMENSION` | `1536` | No | Embedding vector dimension |

## LLM Configuration

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `LLM_PROVIDER` | `openai` | No | LLM provider: `openai` or `anthropic` |
| `OPENAI_API_KEY` | None | Conditional | OpenAI API key (required if provider is openai) |
| `ANTHROPIC_API_KEY` | None | Conditional | Anthropic API key (required if provider is anthropic) |
| `LLM_MODEL` | `gpt-4-turbo-preview` | No | Model name for generation |
| `LLM_MAX_TOKENS` | `4096` | No | Max tokens in LLM response |
| `LLM_TEMPERATURE` | `0.7` | No | Generation temperature |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | No | OpenAI embedding model |

## File Paths

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `YOUTUBE_LINKS_DIR` | `/opt/mpis/input` | No | Directory for youtube_links.txt |
| `YOUTUBE_LINKS_FILENAME` | `youtube_links.txt` | No | YouTube links filename |
| `PERSONAS_BASE_DIR` | `/opt/mpis/personas` | No | Base directory for persona exports |
| `SOURCES_BASE_DIR` | `/opt/mpis/sources` | No | Base directory for source files |
| `SECRETS_DIR` | `/opt/mpis/secrets` | No | Directory for secrets |

## Google Drive Integration

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `GDRIVE_SERVICE_ACCOUNT_JSON_PATH` | `/opt/mpis/secrets/gdrive_sa.json` | Conditional | Path to service account JSON |

**Note:** Required only if using Google Drive source channel.

### Setting Up Google Drive

1. Create a Google Cloud project
2. Enable Google Drive API
3. Create a service account
4. Download the JSON key file
5. Save to `/opt/mpis/secrets/gdrive_sa.json`
6. Share the target folder with the service account email

## Public Persona Web Enrichment

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `PUBLIC_WEB_MAX_SOURCES` | `20` | No | Maximum web sources to fetch |
| `PUBLIC_WEB_ALLOWED_DOMAINS` | None | No | Comma-separated allowed domains |
| `PUBLIC_WEB_DENIED_DOMAINS` | None | No | Comma-separated denied domains |
| `SERPAPI_API_KEY` | None | No | SerpAPI key for web search |
| `WEB_REQUEST_TIMEOUT` | `30` | No | Request timeout in seconds |
| `WEB_REQUEST_DELAY` | `1.0` | No | Delay between requests (rate limit) |

**Example domain lists:**
```
PUBLIC_WEB_ALLOWED_DOMAINS=wikipedia.org,britannica.com,nytimes.com
PUBLIC_WEB_DENIED_DOMAINS=reddit.com,twitter.com,facebook.com
```

## Text Chunking

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `CHUNK_MIN_TOKENS` | `500` | No | Minimum tokens per chunk |
| `CHUNK_MAX_TOKENS` | `1200` | No | Maximum tokens per chunk |
| `CHUNK_OVERLAP_TOKENS` | `100` | No | Overlap between chunks |

## API Server

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `API_HOST` | `0.0.0.0` | No | Server bind address |
| `API_PORT` | `8080` | No | Server port |

## Example .env File

```env
# Core settings
DATABASE_URL=postgresql+asyncpg://mpis:secretpassword@mpis-postgres:5432/mpis
QDRANT_URL=http://mpis-qdrant:6333

# LLM
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here

# Paths (default for Docker)
YOUTUBE_LINKS_DIR=/opt/mpis/input
PERSONAS_BASE_DIR=/opt/mpis/personas
SOURCES_BASE_DIR=/opt/mpis/sources

# Optional
DEBUG=false
DRY_RUN=false
PUBLIC_WEB_MAX_SOURCES=20
```

## Docker Environment

When running in Docker, paths should match the container's filesystem. The docker-compose.genesis.yml mounts:

- `/opt/mpis/input` (read-only)
- `/opt/mpis/personas` (read-write)
- `/opt/mpis/sources` (read-write)
- `/opt/mpis/secrets` (read-only)

Ensure these directories exist on the host:

```bash
mkdir -p /opt/mpis/{input,personas,sources,secrets}
```
