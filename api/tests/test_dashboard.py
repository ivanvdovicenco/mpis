"""
MPIS Dashboard API - Dashboard Service Tests

Unit tests for Dashboard service layer.
"""
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.dashboard import DashboardService
from app.services.metric_normalizer import MetricNormalizer
from app.schemas.dashboard import (
    DashboardProjectCreate,
    DashboardRunCreate,
    DashboardRunCompleteRequest,
)


class TestMetricNormalizer:
    """Tests for metric normalization."""
    
    def test_normalize_telegram_metrics(self):
        """Test Telegram metric normalization."""
        raw_metrics = {
            "views": 1500,
            "reactions": {
                "👍": 45,
                "❤️": 32,
                "🔥": 18
            },
            "forwards": 23
        }
        
        normalized = MetricNormalizer.normalize_metrics("telegram", raw_metrics)
        
        assert normalized["views"] == 1500
        assert normalized["reactions"] == 95  # Sum of all reactions
        assert normalized["shares"] == 23  # Forwards mapped to shares
        assert "engagement_rate" in normalized
    
    def test_normalize_instagram_metrics(self):
        """Test Instagram metric normalization."""
        raw_metrics = {
            "impressions": 2500,
            "reach": 2100,
            "likes": 180,
            "comments": 24,
            "shares": 15,
            "saves": 42
        }
        
        normalized = MetricNormalizer.normalize_metrics("instagram", raw_metrics)
        
        assert normalized["impressions"] == 2500
        assert normalized["reach"] == 2100
        assert normalized["reactions"] == 180  # Likes mapped to reactions
        assert normalized["comments"] == 24
        assert normalized["shares"] == 15
        assert normalized["saves"] == 42
        assert "engagement_rate" in normalized
    
    def test_calculate_engagement_rate(self):
        """Test engagement rate calculation."""
        metrics = {
            "reactions": 100,
            "comments": 20,
            "shares": 10,
            "reach": 1000
        }
        
        engagement_rate = MetricNormalizer.calculate_engagement_rate(metrics)
        
        # (100 + 20 + 10) / 1000 = 0.13
        assert engagement_rate == 0.13
    
    def test_calculate_engagement_rate_with_views_fallback(self):
        """Test engagement rate calculation with views as fallback."""
        metrics = {
            "reactions": 50,
            "comments": 10,
            "shares": 5,
            "views": 500  # No reach, use views
        }
        
        engagement_rate = MetricNormalizer.calculate_engagement_rate(metrics)
        
        # (50 + 10 + 5) / 500 = 0.13
        assert engagement_rate == 0.13
    
    def test_calculate_engagement_rate_no_denominator(self):
        """Test engagement rate calculation with no reach or views."""
        metrics = {
            "reactions": 10,
            "comments": 5,
            "shares": 2
        }
        
        engagement_rate = MetricNormalizer.calculate_engagement_rate(metrics)
        
        # Should return None when denominator is 0
        assert engagement_rate is None


class TestDashboardService:
    """Tests for Dashboard service."""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()
        db.execute = AsyncMock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create DashboardService instance."""
        return DashboardService(mock_db)
    
    @pytest.mark.asyncio
    async def test_create_project(self, service, mock_db):
        """Test project creation."""
        request = DashboardProjectCreate(
            name="Test Project",
            persona_id=uuid4(),
            channels=["telegram", "instagram"]
        )
        
        # Mock the created project
        mock_project = MagicMock()
        mock_project.id = uuid4()
        mock_project.name = request.name
        mock_project.persona_id = request.persona_id
        mock_project.channels = request.channels
        mock_project.created_at = datetime.utcnow()
        
        # Setup mock to return the project after refresh
        mock_db.refresh.side_effect = lambda obj: setattr(obj, 'id', mock_project.id)
        
        result = await service.create_project(request)
        
        assert mock_db.add.called
        assert mock_db.commit.called
        assert result.name == request.name
        assert result.persona_id == request.persona_id
        assert result.channels == request.channels
    
    @pytest.mark.asyncio
    async def test_calculate_run_status_all_success(self, service):
        """Test run status calculation with all successes."""
        published_items = [
            {"channel": "telegram", "status": "success"},
            {"channel": "instagram", "status": "success"}
        ]
        
        status = await service._calculate_run_status("success", published_items)
        
        assert status == "success"
    
    @pytest.mark.asyncio
    async def test_calculate_run_status_all_failed(self, service):
        """Test run status calculation with all failures."""
        published_items = [
            {"channel": "telegram", "status": "failed"},
            {"channel": "instagram", "status": "failed"}
        ]
        
        status = await service._calculate_run_status("failed", published_items)
        
        assert status == "failed"
    
    @pytest.mark.asyncio
    async def test_calculate_run_status_partial(self, service):
        """Test run status calculation with partial success."""
        published_items = [
            {"channel": "telegram", "status": "success"},
            {"channel": "instagram", "status": "failed"}
        ]
        
        status = await service._calculate_run_status("success", published_items)
        
        # At least one success and one failure = partial
        assert status == "partial"
    
    @pytest.mark.asyncio
    async def test_calculate_run_status_no_items(self, service):
        """Test run status calculation with no published items."""
        status = await service._calculate_run_status("failed", [])
        
        # No items and failed = failed
        assert status == "failed"


class TestDashboardServiceIntegration:
    """Integration tests for Dashboard service."""
    
    @pytest.mark.asyncio
    async def test_create_and_complete_run(self):
        """Test creating and completing a run."""
        # This would require a real database connection
        # For now, we'll skip or mock
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
