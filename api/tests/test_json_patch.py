"""
MPIS Genesis API - Unit Tests for JSON Patch Utilities

Tests for JSON Patch operations.
"""
import pytest
from app.utils.json_patch import (
    parse_path,
    apply_json_patch,
    JsonPatchError
)
from app.schemas.genesis import EditOperation


class TestParsePath:
    """Tests for the parse_path function."""
    
    def test_simple_path(self):
        """Test simple dot-notation path."""
        assert parse_path("credo") == ["credo"]
        assert parse_path("credo.summary") == ["credo", "summary"]
    
    def test_array_index(self):
        """Test path with array index."""
        assert parse_path("credo.statements[0]") == ["credo", "statements", 0]
        assert parse_path("credo.statements[1]") == ["credo", "statements", 1]
    
    def test_nested_path(self):
        """Test deeply nested path."""
        path = "ethos.virtues"
        assert parse_path(path) == ["ethos", "virtues"]
    
    def test_multiple_arrays(self):
        """Test path with multiple array indices."""
        path = "items[0].values[1]"
        result = parse_path(path)
        assert result == ["items", 0, "values", 1]
    
    def test_empty_path(self):
        """Test empty path."""
        assert parse_path("") == []


class TestApplyJsonPatch:
    """Tests for the apply_json_patch function."""
    
    def test_replace_simple_value(self):
        """Test replacing a simple value."""
        obj = {"credo": {"summary": "old"}}
        edits = [EditOperation(path="credo.summary", op="replace", value="new")]
        
        result = apply_json_patch(obj, edits)
        
        assert result["credo"]["summary"] == "new"
        # Original should be unchanged
        assert obj["credo"]["summary"] == "old"
    
    def test_replace_array_element(self):
        """Test replacing an array element."""
        obj = {"credo": {"statements": ["a", "b", "c"]}}
        edits = [EditOperation(path="credo.statements[1]", op="replace", value="B")]
        
        result = apply_json_patch(obj, edits)
        
        assert result["credo"]["statements"] == ["a", "B", "c"]
    
    def test_add_to_array(self):
        """Test adding to an array."""
        obj = {"ethos": {"virtues": ["wisdom", "humility"]}}
        edits = [EditOperation(path="ethos.virtues", op="add", value="compassion")]
        
        result = apply_json_patch(obj, edits)
        
        assert "compassion" in result["ethos"]["virtues"]
        assert len(result["ethos"]["virtues"]) == 3
    
    def test_add_new_field(self):
        """Test adding a new field to an object."""
        obj = {"credo": {}}
        edits = [EditOperation(path="credo.summary", op="add", value="new summary")]
        
        result = apply_json_patch(obj, edits)
        
        assert result["credo"]["summary"] == "new summary"
    
    def test_remove_from_array(self):
        """Test removing an element from an array."""
        obj = {"credo": {"statements": ["a", "b", "c"]}}
        edits = [EditOperation(path="credo.statements[1]", op="remove")]
        
        result = apply_json_patch(obj, edits)
        
        assert result["credo"]["statements"] == ["a", "c"]
    
    def test_remove_field(self):
        """Test removing a field from an object."""
        obj = {"credo": {"summary": "text", "extra": "remove me"}}
        edits = [EditOperation(path="credo.extra", op="remove")]
        
        result = apply_json_patch(obj, edits)
        
        assert "extra" not in result["credo"]
        assert "summary" in result["credo"]
    
    def test_multiple_edits(self):
        """Test applying multiple edits."""
        obj = {
            "credo": {"statements": ["a", "b"]},
            "ethos": {"virtues": ["v1"]}
        }
        edits = [
            EditOperation(path="credo.statements[0]", op="replace", value="A"),
            EditOperation(path="ethos.virtues", op="add", value="v2")
        ]
        
        result = apply_json_patch(obj, edits)
        
        assert result["credo"]["statements"][0] == "A"
        assert "v2" in result["ethos"]["virtues"]
    
    def test_invalid_path_raises_error(self):
        """Test that invalid path raises error."""
        obj = {"credo": {"summary": "text"}}
        edits = [EditOperation(path="invalid.path", op="replace", value="new")]
        
        with pytest.raises(JsonPatchError):
            apply_json_patch(obj, edits)
    
    def test_replace_without_value_raises_error(self):
        """Test that replace without value raises error."""
        obj = {"credo": {"summary": "text"}}
        edits = [EditOperation(path="credo.summary", op="replace", value=None)]
        
        with pytest.raises(JsonPatchError):
            apply_json_patch(obj, edits)
    
    def test_array_index_out_of_bounds(self):
        """Test that out of bounds index raises error."""
        obj = {"items": ["a", "b"]}
        edits = [EditOperation(path="items[10]", op="replace", value="x")]
        
        with pytest.raises(JsonPatchError):
            apply_json_patch(obj, edits)
    
    def test_unknown_operation_raises_error(self):
        """Test that unknown operation raises error."""
        obj = {"key": "value"}
        # Force an invalid operation
        edit = EditOperation(path="key", op="replace", value="new")
        edit.op = "invalid"  # type: ignore
        
        with pytest.raises(JsonPatchError):
            apply_json_patch(obj, [edit])


class TestIntegrationScenarios:
    """Integration tests for realistic edit scenarios."""
    
    def test_edit_persona_credo(self):
        """Test editing a full persona credo section."""
        persona = {
            "credo": {
                "summary": "Original summary",
                "statements": [
                    "Statement 1",
                    "Statement 2",
                    "Statement 3"
                ]
            },
            "ethos": {
                "virtues": ["wisdom"]
            }
        }
        
        edits = [
            EditOperation(
                path="credo.summary",
                op="replace",
                value="Updated summary with more depth"
            ),
            EditOperation(
                path="credo.statements[1]",
                op="replace",
                value="Revised statement 2"
            ),
            EditOperation(
                path="ethos.virtues",
                op="add",
                value="humility"
            )
        ]
        
        result = apply_json_patch(persona, edits)
        
        assert result["credo"]["summary"] == "Updated summary with more depth"
        assert result["credo"]["statements"][1] == "Revised statement 2"
        assert "humility" in result["ethos"]["virtues"]
        
        # Other fields unchanged
        assert result["credo"]["statements"][0] == "Statement 1"
        assert result["credo"]["statements"][2] == "Statement 3"
