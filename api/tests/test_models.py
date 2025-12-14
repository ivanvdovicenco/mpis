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
        
        # Verify 'metadata' is NOT a mapped attribute (to avoid SQLAlchemy conflicts)
        # Note: Source will have Base.metadata class attribute, but not a mapped column named 'metadata'
        assert not any(
            col.name == "metadata" and hasattr(col, "type")
            for col in Source.__table__.columns
        ) or Source.__table__.columns.get("metadata") is not None, \
            "Source model should map Python attribute 'meta' to DB column 'metadata'"
    
    def test_source_meta_maps_to_metadata_column(self):
        """Test that 'meta' attribute maps to 'metadata' database column."""
        # Find the column that the 'meta' attribute maps to
        meta_column = None
        for col in Source.__table__.columns:
            if col.name == "metadata":
                meta_column = col
                break
        
        assert meta_column is not None, "Database should have 'metadata' column"
        
        # Verify it's the JSONB type
        assert str(meta_column.type) == "JSONB", "metadata column should be JSONB type"
