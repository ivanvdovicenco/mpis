# MPIS Deployment Guide

Complete guide for deploying MPIS from GitHub to production servers with zero manual edits.

## Prerequisites

### Infrastructure
- Ubuntu 24.04 LTS server (ARM64 supported)
- Docker and Docker Compose v2+
- External Postgres container (`mpis-postgres`) running on `mpis_net` network
- External Qdrant container (`mpis-qdrant`) running on `mpis_net` network
- Docker network `mpis_net` must exist

### Access
- SSH access to the server
- Git repository access (GitHub)
- OpenAI or Anthropic API key

## Initial Server Setup

### 1. Create Directory Structure

```bash
# Create required directories
sudo mkdir -p /opt/mpis/{input,personas,sources,secrets,infra,tmp,exports}
sudo chown -R 1000:1000 /opt/mpis

# Clone repository
cd /opt/mpis
git clone https://github.com/ivanvdovicenco/mpis.git repo
cd repo
```

### 2. Configure Environment

```bash
# Copy environment template
cp api/.env.example /opt/mpis/infra/.env

# Edit configuration (add your API keys and passwords)
nano /opt/mpis/infra/.env
```

**Important:** Never commit real secrets to the repository. The `.env` file should exist only on the server.

Required environment variables:
```env
DATABASE_URL=postgresql+asyncpg://mpis:PASSWORD@mpis-postgres:5432/mpis
QDRANT_URL=http://mpis-qdrant:6333
OPENAI_API_KEY=sk-...
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview
```

See [docs/ENV.md](docs/ENV.md) for complete configuration reference.

### 3. Run Database Migrations

```bash
# Ensure Postgres is running
docker ps | grep mpis-postgres

# Run all migrations
docker exec -i mpis-postgres psql -U mpis -d mpis < /opt/mpis/repo/scripts/002_genesis.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < /opt/mpis/repo/scripts/003_life.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < /opt/mpis/repo/scripts/004_publisher.sql
docker exec -i mpis-postgres psql -U mpis -d mpis < /opt/mpis/repo/scripts/005_analytics.sql
```

### 4. Create Docker Network (if not exists)

```bash
# Create mpis_net network
docker network create mpis_net

# Verify network exists
docker network ls | grep mpis_net
```

### 5. Initial Deployment

```bash
cd /opt/mpis/repo/infra

# Deploy full stack (all modules)
./deploy.sh

# Or deploy specific module
./deploy.sh docker-compose.genesis.yml
```

### 6. Verify Deployment

```bash
cd /opt/mpis/repo/infra

# Run verification script
./verify.sh

# Check API health manually
curl http://127.0.0.1:8080/health

# View API documentation
# If on server: curl http://127.0.0.1:8080/docs
# Via tunnel: http://localhost:8080/docs
```

## Regular Deployment (Updates)

### Tag-Based Deployment (Recommended)

```bash
cd /opt/mpis/repo

# View available tags
git fetch --tags
git tag -l

# Deploy specific release
git checkout v1.2.3
cd infra
./deploy.sh
./verify.sh
```

### Branch-Based Deployment

```bash
cd /opt/mpis/repo

# Pull latest from current branch
git pull origin main
cd infra
./deploy.sh
./verify.sh
```

### Complete Deployment Workflow

```bash
# 1. Navigate to repository
cd /opt/mpis/repo

# 2. Check current status
git status
git log -1 --oneline

# 3. Create snapshot tag (optional, for rollback)
SNAPSHOT_TAG="snapshot-$(date +%Y%m%d-%H%M%S)"
git tag "$SNAPSHOT_TAG"
echo "Created snapshot: $SNAPSHOT_TAG"

# 4. Pull latest changes
git pull origin main

# 5. Show what changed
git log --oneline HEAD@{1}..HEAD

# 6. Deploy
cd infra
./deploy.sh docker-compose.full.yml

# 7. Verify
./verify.sh

# 8. Check logs for issues
docker compose -f docker-compose.full.yml logs -f --tail=50
```

## Deployment Options

### Full Stack (All Modules)
```bash
./deploy.sh docker-compose.full.yml
```
Deploys all MPIS modules (Genesis, Life, Publisher, Analytics) in a single container.
- Port: `127.0.0.1:8080`
- Service: `genesis-api`

### Individual Modules
```bash
# Genesis only
./deploy.sh docker-compose.genesis.yml

# Life only  
./deploy.sh docker-compose.life.yml

# Publisher only
./deploy.sh docker-compose.publisher.yml

# Analytics only
./deploy.sh docker-compose.analytics.yml
```

## Rollback Procedures

### Rollback to Previous Tag

```bash
cd /opt/mpis/repo

# List recent tags
git tag -l | tail -10

# Checkout previous stable version
git checkout v1.2.2

# Re-deploy
cd infra
./deploy.sh
./verify.sh
```

### Rollback to Snapshot

If you created a snapshot tag before deployment:

```bash
cd /opt/mpis/repo

# Find your snapshot
git tag -l | grep snapshot

# Rollback
git checkout snapshot-20231214-153045
cd infra
./deploy.sh
./verify.sh
```

### Emergency Rollback

If deployment fails catastrophically:

```bash
cd /opt/mpis/repo

# Go back one commit
git reset --hard HEAD~1

# Or go back to specific commit
git reset --hard <commit-hash>

# Re-deploy
cd infra
./deploy.sh
./verify.sh
```

**Note:** Use `git reset` with caution. If you need to return to latest, use `git pull --force`.

## Verification and Troubleshooting

### Health Checks

```bash
# Quick health check
curl http://127.0.0.1:8080/health

# Full verification
cd /opt/mpis/repo/infra
./verify.sh
```

### View Logs

```bash
cd /opt/mpis/repo/infra

# Follow logs in real-time
docker compose -f docker-compose.full.yml logs -f

# View last 100 lines
docker compose -f docker-compose.full.yml logs --tail=100

# Specific service logs
docker compose -f docker-compose.full.yml logs -f genesis-api
```

### Check Container Status

```bash
cd /opt/mpis/repo/infra

# List running containers
docker compose -f docker-compose.full.yml ps

# Detailed container info
docker compose -f docker-compose.full.yml ps -a
```

### Shell Access

```bash
cd /opt/mpis/repo/infra

# Access container shell
docker compose -f docker-compose.full.yml exec genesis-api sh

# Run commands inside container
docker compose -f docker-compose.full.yml exec genesis-api python -c "from app.models.persona import Source; print('Source.meta:', hasattr(Source, 'meta'))"
```

### Common Issues

#### API not responding

```bash
# Check if container is running
docker ps | grep genesis-api

# Check container logs
docker logs genesis-api --tail=50

# Restart service
cd /opt/mpis/repo/infra
docker compose -f docker-compose.full.yml restart genesis-api
```

#### Database connection issues

```bash
# Verify Postgres is running
docker ps | grep mpis-postgres

# Check if API can reach Postgres
docker exec genesis-api nc -zv mpis-postgres 5432

# Check network connectivity
docker network inspect mpis_net
```

#### Port binding issues

The API binds to `127.0.0.1:8080` only. For external access, use a reverse proxy like Caddy:

```bash
# Check if port is already in use
sudo lsof -i :8080

# Verify API is bound to localhost only
docker port genesis-api
```

#### SQLAlchemy metadata errors

The deployment scripts automatically check for SQLAlchemy metadata errors in logs:

```bash
cd /opt/mpis/repo/infra
./verify.sh | grep -i metadata
```

If you see errors like "reserved word" or "metadata conflicts", check:
1. Ensure Source model uses `meta` attribute (not `metadata`)
2. Verify all code uses `Source.meta` not `Source.metadata`
3. Check recent code changes for regressions

## Public Access via Caddy

The API is bound to `127.0.0.1:8080` and should **not** be exposed directly to the internet.

For HTTPS access, configure Caddy reverse proxy:

### Option 1: Add to Existing Caddy

If you already have Caddy running (e.g., for n8n):

```bash
# Add to Caddyfile
cat >> /var/n8n/Caddyfile << 'EOF'

genesis.your-domain.com {
    reverse_proxy 127.0.0.1:8080
}
EOF

# Reload Caddy
docker exec caddy caddy reload --config /etc/caddy/Caddyfile
```

### Option 2: nip.io for Testing

For quick testing without DNS:

```bash
# Use nip.io wildcard DNS
# Replace with your server IP
genesis.46.62.174.134.nip.io {
    reverse_proxy 127.0.0.1:8080
}
```

## Security Best Practices

### Secrets Management

1. **Never commit secrets to Git**
   - `.env` files should be created on the server only
   - Use `.env.example` as a template with placeholder values
   - Add `.env` to `.gitignore`

2. **Protect sensitive files**
   ```bash
   # Service account keys
   chmod 600 /opt/mpis/secrets/gdrive_sa.json
   
   # Environment files
   chmod 600 /opt/mpis/infra/.env
   ```

3. **Rotate API keys regularly**
   ```bash
   # Update .env file
   nano /opt/mpis/infra/.env
   
   # Restart services
   cd /opt/mpis/repo/infra
   ./deploy.sh
   ```

### Network Security

1. **API bound to localhost only**
   - Direct API access: `127.0.0.1:8080`
   - Public access: Only via Caddy reverse proxy
   - No external port exposure

2. **Database and Qdrant**
   - Run on internal Docker network (`mpis_net`)
   - Not exposed to public internet
   - Access restricted to MPIS containers

### Update Management

1. **Use tags for production**
   ```bash
   git checkout v1.2.3  # Not main branch
   ```

2. **Test before deploying**
   - Deploy to staging environment first
   - Run verification scripts
   - Check logs for errors

3. **Keep dependencies updated**
   ```bash
   # Check for security updates
   cd /opt/mpis/repo/api
   pip list --outdated
   ```

## Monitoring and Maintenance

### Log Rotation

Docker handles log rotation automatically, but you can configure it:

```bash
# Edit docker daemon config
sudo nano /etc/docker/daemon.json
```

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

### Disk Space

```bash
# Check disk usage
df -h /opt/mpis

# Clean up Docker
docker system prune -a --volumes --force

# Clean old images
docker image prune -a --force
```

### Backup

```bash
# Backup personas and sources
cd /opt/mpis
tar -czf backup-$(date +%Y%m%d).tar.gz personas/ sources/

# Backup database (from Postgres container)
docker exec mpis-postgres pg_dump -U mpis mpis > backup-db-$(date +%Y%m%d).sql
```

## Development vs Production

### Production Dependencies

Production deployments use `api/requirements.txt` which excludes test dependencies.

### Development Dependencies

For local development with tests:

```bash
cd /opt/mpis/repo/api
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
DRY_RUN=true pytest tests/ -v
```

## Support

For issues or questions:
- Check logs: `./verify.sh`
- Review documentation: [docs/](docs/)
- Check API docs: http://localhost:8080/docs

## Quick Reference

```bash
# Deploy
cd /opt/mpis/repo/infra && ./deploy.sh

# Verify
./verify.sh

# View logs
docker compose -f docker-compose.full.yml logs -f

# Restart
docker compose -f docker-compose.full.yml restart

# Rollback
git checkout <previous-tag> && ./deploy.sh

# Health check
curl http://127.0.0.1:8080/health
```
