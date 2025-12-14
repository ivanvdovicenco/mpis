"""
MPIS API - Module Tests

Tests for Life, Publisher, and Analytics modules.
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.schemas.life import (
    LifeEventCreate,
    LifeEventResponse,
    CycleStartRequest,
    ReflectionSummary,
)
from app.schemas.publisher import (
    ContentPlanCreate,
    ContentGenerateRequest,
    ContentVariant,
    DraftApproveRequest,
    MetricsIngestRequest,
)
from app.schemas.analytics import (
    AnalyticsSummaryResponse,
    MetricsSummary,
    EidosRecommendationItem,
    ContentBrief,
    ExperimentSuggestion,
)


class TestLifeSchemas:
    """Tests for Life module schemas."""
    
    def test_life_event_create_valid(self):
        """Test valid LifeEventCreate."""
        event = LifeEventCreate(
            persona_id=uuid4(),
            event_type="conversation",
            content="User asked about meaning",
            tags=["meaning", "pastoral"],
            meta={"source": "telegram"}
        )
        assert event.event_type == "conversation"
        assert len(event.tags) == 2
    
    def test_life_event_create_minimal(self):
        """Test minimal LifeEventCreate."""
        event = LifeEventCreate(
            persona_id=uuid4(),
            event_type="note",
            content="Simple note"
        )
        assert event.tags == []
        assert event.meta == {}
    
    def test_cycle_start_request(self):
        """Test CycleStartRequest."""
        request = CycleStartRequest(
            persona_id=uuid4(),
            cycle_type="daily",
            options={"lookback_days": 1}
        )
        assert request.cycle_type == "daily"
        assert request.options["lookback_days"] == 1
    
    def test_reflection_summary(self):
        """Test ReflectionSummary schema."""
        summary = ReflectionSummary(
            summary="Processed 10 events",
            key_insights=["Insight 1", "Insight 2"],
            suggested_adjustments=[],
            next_actions=["Action 1"],
            staleness_alerts=[]
        )
        assert summary.summary == "Processed 10 events"
        assert len(summary.key_insights) == 2


class TestPublisherSchemas:
    """Tests for Publisher module schemas."""
    
    def test_content_plan_create(self):
        """Test ContentPlanCreate."""
        plan = ContentPlanCreate(
            persona_id=uuid4(),
            title="Finding Hope",
            topic="faith",
            channel="telegram",
            language="en"
        )
        assert plan.title == "Finding Hope"
        assert plan.max_length == 1000  # default
    
    def test_content_plan_with_constraints(self):
        """Test ContentPlanCreate with constraints."""
        plan = ContentPlanCreate(
            persona_id=uuid4(),
            title="Test",
            topic="test",
            channel="telegram",
            constraints={
                "tone": ["hopeful"],
                "forbidden_topics": ["politics"]
            }
        )
        assert "tone" in plan.constraints
        assert plan.constraints["forbidden_topics"] == ["politics"]
    
    def test_content_variant(self):
        """Test ContentVariant."""
        variant = ContentVariant(
            variant_no=1,
            text="Main content here",
            title="Hook title",
            cta="Share your thoughts!"
        )
        assert variant.variant_no == 1
        assert variant.cta == "Share your thoughts!"
    
    def test_metrics_ingest_request(self):
        """Test MetricsIngestRequest."""
        request = MetricsIngestRequest(
            published_item_id=uuid4(),
            metrics=[
                {"type": "views", "value": 1000},
                {"type": "reactions", "value": 50}
            ],
            source="telegram_api"
        )
        assert len(request.metrics) == 2
        assert request.source == "telegram_api"


class TestAnalyticsSchemas:
    """Tests for Analytics module schemas."""
    
    def test_metrics_summary(self):
        """Test MetricsSummary."""
        summary = MetricsSummary(
            total_published=25,
            total_views=15000,
            total_reactions=450,
            total_shares=120,
            engagement_rate=3.8,
            best_performing_topics=["faith", "hope"],
            best_performing_times=["9:00 AM"]
        )
        assert summary.engagement_rate == 3.8
        assert summary.total_published == 25
    
    def test_eidos_recommendation_item(self):
        """Test EidosRecommendationItem."""
        rec = EidosRecommendationItem(
            id=1,
            title="Increase frequency",
            description="Post more often for better engagement",
            priority="high",
            category="content",
            evidence=["Data shows higher engagement with frequent posts"],
            measurable_outcome="Track weekly engagement"
        )
        assert rec.priority == "high"
        assert len(rec.evidence) == 1
    
    def test_content_brief(self):
        """Test ContentBrief."""
        brief = ContentBrief(
            topic="Community",
            hook="What brings you hope?",
            key_points=["Invite discussion", "Be authentic"],
            target_channel="telegram",
            suggested_length=500,
            rationale="Interactive content works"
        )
        assert brief.suggested_length == 500
        assert len(brief.key_points) == 2
    
    def test_experiment_suggestion(self):
        """Test ExperimentSuggestion."""
        exp = ExperimentSuggestion(
            name="CTA Test",
            hypothesis="Questions work better",
            variants=["Control", "Treatment"],
            success_metric="Reaction rate",
            duration_days=14
        )
        assert exp.duration_days == 14
        assert len(exp.variants) == 2


class TestSchemaValidation:
    """Tests for schema validation."""
    
    def test_life_event_requires_content(self):
        """Test that LifeEventCreate requires non-empty content."""
        with pytest.raises(ValueError):
            LifeEventCreate(
                persona_id=uuid4(),
                event_type="note",
                content=""  # Empty not allowed
            )
    
    def test_content_plan_max_length_bounds(self):
        """Test ContentPlanCreate max_length bounds."""
        # Valid within bounds
        plan = ContentPlanCreate(
            persona_id=uuid4(),
            title="Test",
            topic="test",
            channel="telegram",
            max_length=5000
        )
        assert plan.max_length == 5000
        
        # Invalid - too large
        with pytest.raises(ValueError):
            ContentPlanCreate(
                persona_id=uuid4(),
                title="Test",
                topic="test",
                channel="telegram",
                max_length=20000  # Exceeds 10000 limit
            )
    
    def test_metrics_ingest_allows_empty_list(self):
        """Test MetricsIngestRequest allows empty metrics list (validation at service level)."""
        # Empty list is allowed at schema level; validation happens in service
        request = MetricsIngestRequest(
            published_item_id=uuid4(),
            metrics=[],
            source="manual"
        )
        assert request.metrics == []
