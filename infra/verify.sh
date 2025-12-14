#!/bin/bash
# MPIS Verification Script
#
# Checks API health and examines logs for issues.
# Specifically looks for SQLAlchemy metadata errors.
#
# Usage:
#   ./verify.sh [compose-file]
#
# Examples:
#   ./verify.sh                          # Uses docker-compose.full.yml
#   ./verify.sh docker-compose.full.yml  # Explicit full stack

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

log_section() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}\n"
}

# Determine repository root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Determine which compose file to use
COMPOSE_FILE="${1:-docker-compose.full.yml}"

# Check if compose file exists
if [ ! -f "$SCRIPT_DIR/$COMPOSE_FILE" ]; then
    log_error "Compose file not found: $SCRIPT_DIR/$COMPOSE_FILE"
    exit 1
fi

log_info "Verifying MPIS deployment using: $COMPOSE_FILE"

# Navigate to infra directory
cd "$SCRIPT_DIR"

# Check if containers are running
log_section "Container Status"
if ! docker compose -f "$COMPOSE_FILE" ps; then
    log_error "Failed to get container status"
    exit 1
fi

# Check API health
log_section "API Health Check"
if curl -f -s http://127.0.0.1:8080/health; then
    echo ""
    log_info "✓ API health check PASSED"
else
    echo ""
    log_error "✗ API health check FAILED"
    log_info "The API is not responding at http://127.0.0.1:8080/health"
fi

# Show last 80 lines of API logs
log_section "Recent API Logs (last 80 lines)"
SERVICE_NAME=$(docker compose -f "$COMPOSE_FILE" ps --services | head -1)
if [ -n "$SERVICE_NAME" ]; then
    docker compose -f "$COMPOSE_FILE" logs --tail=80 "$SERVICE_NAME" || log_warn "Failed to retrieve logs"
else
    log_warn "No service found in compose file"
fi

# Check for SQLAlchemy metadata errors
log_section "Checking for SQLAlchemy Metadata Errors"
ERROR_PATTERNS=(
    "reserved word"
    "metadata.*reserved"
    "AttributeError.*metadata"
    "Column.*metadata.*conflicts"
    "InstrumentedAttribute.*metadata"
)

ERRORS_FOUND=false
for pattern in "${ERROR_PATTERNS[@]}"; do
    if docker compose -f "$COMPOSE_FILE" logs "$SERVICE_NAME" 2>/dev/null | grep -i -E "$pattern"; then
        log_error "Found potential SQLAlchemy metadata error with pattern: $pattern"
        ERRORS_FOUND=true
    fi
done

if [ "$ERRORS_FOUND" = false ]; then
    log_info "✓ No SQLAlchemy metadata errors detected"
else
    log_warn "✗ SQLAlchemy metadata errors detected in logs"
    log_info "This may indicate that the 'metadata' reserved word issue is not fully resolved."
fi

# Check for common error patterns
log_section "Checking for Common Error Patterns"
COMMON_ERRORS=(
    "ERROR"
    "CRITICAL"
    "Exception"
    "Traceback"
)

CRITICAL_ERRORS=false
for error in "${COMMON_ERRORS[@]}"; do
    COUNT=$(docker compose -f "$COMPOSE_FILE" logs --tail=80 "$SERVICE_NAME" 2>/dev/null | grep -c "$error" || echo 0)
    if [ "$COUNT" -gt 0 ]; then
        log_warn "Found $COUNT occurrences of '$error' in recent logs"
        CRITICAL_ERRORS=true
    fi
done

if [ "$CRITICAL_ERRORS" = false ]; then
    log_info "✓ No critical errors in recent logs"
fi

# Network connectivity check
log_section "Network Connectivity"
log_info "Checking connectivity to external services..."

# Check if containers can reach postgres
if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" sh -c "command -v nc" &>/dev/null; then
    if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" nc -zv mpis-postgres 5432 2>&1 | grep -q "open"; then
        log_info "✓ Can reach mpis-postgres:5432"
    else
        log_warn "✗ Cannot reach mpis-postgres:5432"
    fi
    
    if docker compose -f "$COMPOSE_FILE" exec -T "$SERVICE_NAME" nc -zv mpis-qdrant 6333 2>&1 | grep -q "open"; then
        log_info "✓ Can reach mpis-qdrant:6333"
    else
        log_warn "✗ Cannot reach mpis-qdrant:6333"
    fi
else
    log_info "Skipping network checks (nc not available in container)"
fi

# Summary
log_section "Verification Summary"
log_info "Deployment verification complete."
log_info ""
log_info "Useful commands:"
log_info "  - View live logs: docker compose -f $COMPOSE_FILE logs -f"
log_info "  - Restart service: docker compose -f $COMPOSE_FILE restart"
log_info "  - Shell into container: docker compose -f $COMPOSE_FILE exec $SERVICE_NAME sh"
log_info "  - API documentation: http://localhost:8080/docs"
