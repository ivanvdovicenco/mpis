#!/bin/bash
# MPIS Deployment Script
# 
# Pulls latest code and rebuilds the MPIS API stack.
# Safe for production use - includes guards and logging.
#
# Prerequisites:
# - External network 'mpis_net' must exist
# - mpis-postgres and mpis-qdrant must be running on mpis_net
# - Environment file at /opt/mpis/infra/.env must be configured
#
# Usage:
#   ./deploy.sh [compose-file]
#
# Examples:
#   ./deploy.sh                          # Uses docker-compose.full.yml
#   ./deploy.sh docker-compose.full.yml  # Explicit full stack
#   ./deploy.sh docker-compose.genesis.yml  # Genesis module only

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Determine repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info "MPIS Deployment starting..."
log_info "Repository root: $REPO_ROOT"

# Determine which compose file to use
COMPOSE_FILE="${1:-docker-compose.full.yml}"

# Check if compose file exists
if [ ! -f "$SCRIPT_DIR/$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $SCRIPT_DIR/$COMPOSE_FILE"
    log_info "Available compose files:"
    ls -1 "$SCRIPT_DIR"/docker-compose*.yml 2>/dev/null || log_warn "No compose files found in $SCRIPT_DIR"
    exit 1
fi

log_info "Using compose file: $COMPOSE_FILE"

# Pull latest code
log_info "Pulling latest code from current branch..."
cd "$REPO_ROOT"

# Check for uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
    log_warn "Uncommitted changes detected. These will NOT be deployed."
    git status --short
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
log_info "Current branch: $CURRENT_BRANCH"

# Pull latest
if ! git pull origin "$CURRENT_BRANCH"; then
    log_error "Failed to pull latest code. Check for merge conflicts."
    exit 1
fi

# Show latest commit
log_info "Latest commit:"
git log -1 --oneline

# Check for required environment file
ENV_FILE="/opt/mpis/infra/.env"
if [ ! -f "$ENV_FILE" ]; then
    log_warn "Environment file not found at $ENV_FILE"
    log_info "You may need to create it from api/.env.example"
fi

# Check for external dependencies
log_info "Checking external dependencies..."

# Check if mpis_net network exists
if ! docker network inspect mpis_net &>/dev/null; then
    log_error "Docker network 'mpis_net' does not exist."
    log_info "Create it with: docker network create mpis_net"
    exit 1
fi

# Check if mpis-postgres is running
if ! docker ps --format '{{.Names}}' | grep -q "mpis-postgres"; then
    log_warn "Container 'mpis-postgres' is not running."
    log_info "Ensure Postgres is running before deploying."
fi

# Check if mpis-qdrant is running
if ! docker ps --format '{{.Names}}' | grep -q "mpis-qdrant"; then
    log_warn "Container 'mpis-qdrant' is not running."
    log_info "Ensure Qdrant is running before deploying."
fi

# Navigate to infra directory
cd "$SCRIPT_DIR"

# Stop existing containers (if any)
log_info "Stopping existing containers..."
docker compose -f "$COMPOSE_FILE" down || log_warn "No existing containers to stop"

# Build and start services
log_info "Building and starting services..."
if ! docker compose -f "$COMPOSE_FILE" up -d --build; then
    log_error "Failed to build and start services."
    exit 1
fi

# Wait for services to be healthy
log_info "Waiting for services to start..."
sleep 10

# Show running containers
log_info "Running containers:"
docker compose -f "$COMPOSE_FILE" ps

# Check API health (assuming genesis-api on 127.0.0.1:8080)
log_info "Checking API health..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s http://127.0.0.1:8080/health > /dev/null 2>&1; then
        log_info "API is healthy! ✓"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        log_error "API health check failed after $MAX_RETRIES attempts."
        log_info "Check logs with: docker compose -f $COMPOSE_FILE logs genesis-api"
        exit 1
    fi
    echo -n "."
    sleep 2
done

log_info ""
log_info "Deployment completed successfully! ✓"
log_info ""
log_info "Next steps:"
log_info "  - Verify deployment: ./verify.sh"
log_info "  - View logs: docker compose -f $COMPOSE_FILE logs -f"
log_info "  - Check API docs: http://localhost:8080/docs"
log_info ""
log_info "To rollback:"
log_info "  1. git checkout <previous-tag>"
log_info "  2. ./deploy.sh"
