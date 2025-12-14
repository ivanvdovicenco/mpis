"""
MPIS Genesis API - Integration Tests

Minimal integration tests for the genesis workflow.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
import os

# Set DRY_RUN before importing app
os.environ["DRY_RUN"] = "true"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test:test@localhost:5432/test"

from app.main import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    """Create test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    @pytest.mark.anyio
    async def test_health_check(self, client):
        """Test basic health check."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    @pytest.mark.anyio
    async def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert "genesis" in data["modules"]


class TestGenesisEndpoints:
    """Tests for genesis workflow endpoints."""
    
    @pytest.mark.anyio
    async def test_start_genesis_validation(self, client):
        """Test genesis start request validation."""
        # Missing required field
        response = await client.post("/genesis/start", json={})
        assert response.status_code == 422
        
        # Valid minimal request (will fail on DB, but validates request)
        response = await client.post("/genesis/start", json={
            "persona_name": "Test Persona"
        })
        # May fail due to DB not being available, but should not be 422
        assert response.status_code != 422
    
    @pytest.mark.anyio
    async def test_status_not_found(self, client):
        """Test status endpoint with invalid job ID."""
        response = await client.get("/genesis/status/00000000-0000-0000-0000-000000000000")
        # Should return 404 or 500 (DB not available)
        assert response.status_code in [404, 500]
    
    @pytest.mark.anyio
    async def test_approve_validation(self, client):
        """Test approve endpoint validation."""
        # Invalid request
        response = await client.post("/genesis/approve", json={})
        assert response.status_code == 422
        
        # Valid structure but invalid job
        response = await client.post("/genesis/approve", json={
            "job_id": "00000000-0000-0000-0000-000000000000",
            "draft_no": 1,
            "confirm": True
        })
        # Should return 400 or 500
        assert response.status_code in [400, 404, 500]


class TestOpenAPI:
    """Tests for OpenAPI documentation."""
    
    @pytest.mark.anyio
    async def test_openapi_schema(self, client):
        """Test OpenAPI schema is accessible."""
        response = await client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
        assert "/genesis/start" in data["paths"]
        assert "/genesis/approve" in data["paths"]
    
    @pytest.mark.anyio
    async def test_docs_endpoint(self, client):
        """Test docs endpoint is accessible."""
        response = await client.get("/docs")
        assert response.status_code == 200
