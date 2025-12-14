"""
MPIS Genesis API - Unit Tests for Text Utilities

Tests for slugification, normalization, and content hashing.
"""
import pytest
from app.utils.text import slugify, normalize_text, compute_content_hash, chunk_text


class TestSlugify:
    """Tests for the slugify function."""
    
    def test_basic_english(self):
        """Test basic English text slugification."""
        assert slugify("Tim Keller") == "tim-keller"
        assert slugify("Hello World") == "hello-world"
    
    def test_cyrillic_transliteration(self):
        """Test Cyrillic to ASCII transliteration."""
        assert slugify("Тим Келлер") == "tim-keller"
        assert slugify("Алексей") == "aleksei"
        assert slugify("Привет Мир") == "privet-mir"
    
    def test_numbers(self):
        """Test that numbers are preserved."""
        assert slugify("Test 123") == "test-123"
        assert slugify("Алексей 123") == "aleksei-123"
    
    def test_special_characters(self):
        """Test removal of special characters."""
        assert slugify("Hello! World?") == "hello-world"
        assert slugify("Test@#$%^&*()") == "test"
    
    def test_multiple_spaces(self):
        """Test handling of multiple spaces."""
        assert slugify("Hello   World") == "hello-world"
        assert slugify("  Tim   Keller  ") == "tim-keller"
    
    def test_underscores(self):
        """Test underscore handling."""
        assert slugify("hello_world") == "hello-world"
    
    def test_max_length(self):
        """Test max length truncation."""
        long_text = "This is a very long text that should be truncated"
        result = slugify(long_text, max_length=20)
        assert len(result) <= 20
        assert not result.endswith('-')
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert slugify("") == ""
        # Whitespace-only returns "persona" as fallback
        assert slugify("   ") == "persona"
    
    def test_only_special_chars(self):
        """Test string with only special characters."""
        assert slugify("@#$%^&*()") == "persona"


class TestNormalizeText:
    """Tests for the normalize_text function."""
    
    def test_whitespace_normalization(self):
        """Test whitespace normalization."""
        text = "Hello    World"
        assert normalize_text(text) == "Hello World"
    
    def test_line_ending_normalization(self):
        """Test line ending normalization."""
        text = "Line1\r\nLine2\rLine3"
        result = normalize_text(text)
        assert "\r" not in result
        assert "Line1\nLine2\nLine3" == result
    
    def test_excessive_blank_lines(self):
        """Test removal of excessive blank lines."""
        text = "Para1\n\n\n\n\nPara2"
        result = normalize_text(text)
        assert result == "Para1\n\nPara2"
    
    def test_unicode_spaces(self):
        """Test unicode space normalization."""
        text = "Hello\u00a0World"  # Non-breaking space
        result = normalize_text(text)
        assert result == "Hello World"
    
    def test_empty_string(self):
        """Test empty string handling."""
        assert normalize_text("") == ""
        assert normalize_text("   ") == ""


class TestComputeContentHash:
    """Tests for the compute_content_hash function."""
    
    def test_deterministic(self):
        """Test that hash is deterministic."""
        text = "Hello World"
        hash1 = compute_content_hash(text)
        hash2 = compute_content_hash(text)
        assert hash1 == hash2
    
    def test_different_content(self):
        """Test that different content produces different hashes."""
        hash1 = compute_content_hash("Hello")
        hash2 = compute_content_hash("World")
        assert hash1 != hash2
    
    def test_normalization_applied(self):
        """Test that normalization is applied before hashing."""
        text1 = "Hello    World"
        text2 = "Hello World"
        # After normalization, these should produce the same hash
        hash1 = compute_content_hash(text1)
        hash2 = compute_content_hash(text2)
        assert hash1 == hash2
    
    def test_hash_format(self):
        """Test that hash is a valid SHA-256 hex digest."""
        hash_value = compute_content_hash("test")
        assert len(hash_value) == 64
        assert all(c in '0123456789abcdef' for c in hash_value)


class TestChunkText:
    """Tests for the chunk_text function."""
    
    def test_short_text(self):
        """Test that short text returns single chunk."""
        text = "Short text."
        chunks = chunk_text(text, min_tokens=10, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0] == "Short text."
    
    def test_long_text_splits(self):
        """Test that long text is split into chunks."""
        # Create long text with paragraphs (chunk_text splits on paragraphs)
        paragraphs = ["This is paragraph number " + str(i) + ". " * 50 for i in range(20)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_text(text, min_tokens=50, max_tokens=100)
        assert len(chunks) > 1
    
    def test_empty_text(self):
        """Test empty text handling."""
        assert chunk_text("") == []
        assert chunk_text("   ") == []
    
    def test_preserves_content(self):
        """Test that chunking preserves all content."""
        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = chunk_text(text, min_tokens=1, max_tokens=5)
        # All words should be present (with some possible overlap)
        combined = " ".join(chunks)
        assert "First" in combined
        assert "Second" in combined
        assert "Third" in combined
