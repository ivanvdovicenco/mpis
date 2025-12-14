"""
MPIS API - Model Tests

Tests for SQLAlchemy models.
"""
import pytest
from app.models.persona import Source


class TestSourceModel:
    """Tests for Source model."""
    
    def test_source_has_meta_attribute(self):
        """Test that Source model has 'meta' attribute, not 'metadata'."""
        # Verify the ORM attribute is named 'meta'
        assert hasattr(Source, "meta"), "Source model should have 'meta' attribute"
    
    def test_source_meta_maps_to_metadata_column(self):
        """Test that 'meta' attribute maps to 'metadata' database column."""
        # Verify the database column is named 'metadata'
        metadata_column = Source.__table__.columns.get("metadata")
        assert metadata_column is not None, "Database should have 'metadata' column"
        
        # Verify it's the JSONB type
        assert str(metadata_column.type) == "JSONB", "metadata column should be JSONB type"
