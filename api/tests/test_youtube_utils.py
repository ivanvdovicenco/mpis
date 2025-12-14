"""
MPIS Genesis API - Unit Tests for YouTube Utilities

Tests for YouTube URL parsing and video ID extraction.
"""
import pytest
from app.utils.youtube import (
    extract_video_id,
    parse_youtube_url,
    parse_youtube_links_file
)


class TestExtractVideoId:
    """Tests for the extract_video_id function."""
    
    def test_standard_watch_url(self):
        """Test standard youtube.com/watch?v= URLs."""
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("http://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_watch_url_with_extra_params(self):
        """Test watch URLs with additional parameters."""
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=120") == "dQw4w9WgXcQ"
        assert extract_video_id("https://www.youtube.com/watch?list=abc&v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_short_url(self):
        """Test youtu.be short URLs."""
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("http://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_shorts_url(self):
        """Test youtube.com/shorts/ URLs."""
        assert extract_video_id("https://youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_embed_url(self):
        """Test youtube.com/embed/ URLs."""
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_v_url(self):
        """Test youtube.com/v/ URLs."""
        assert extract_video_id("https://www.youtube.com/v/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_invalid_url(self):
        """Test invalid URLs return None."""
        assert extract_video_id("invalid-url") is None
        assert extract_video_id("https://example.com/watch?v=abc123") is None
        assert extract_video_id("") is None
        assert extract_video_id(None) is None
    
    def test_whitespace_handling(self):
        """Test URL with whitespace is handled."""
        assert extract_video_id("  https://youtube.com/watch?v=dQw4w9WgXcQ  ") == "dQw4w9WgXcQ"


class TestParseYoutubeUrl:
    """Tests for the parse_youtube_url function."""
    
    def test_identifies_watch_type(self):
        """Test identification of watch URL type."""
        video_id, url_type = parse_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
        assert url_type == "watch"
    
    def test_identifies_short_type(self):
        """Test identification of youtu.be URL type."""
        video_id, url_type = parse_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
        assert url_type == "youtu.be"
    
    def test_identifies_shorts_type(self):
        """Test identification of shorts URL type."""
        video_id, url_type = parse_youtube_url("https://youtube.com/shorts/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
        assert url_type == "shorts"
    
    def test_identifies_embed_type(self):
        """Test identification of embed URL type."""
        video_id, url_type = parse_youtube_url("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert video_id == "dQw4w9WgXcQ"
        assert url_type == "embed"
    
    def test_unknown_type(self):
        """Test unknown URL returns unknown type."""
        video_id, url_type = parse_youtube_url("invalid-url")
        assert video_id is None
        assert url_type == "unknown"


class TestParseYoutubeLinksFile:
    """Tests for the parse_youtube_links_file function."""
    
    def test_basic_parsing(self):
        """Test basic file content parsing."""
        content = """https://youtube.com/watch?v=video1
https://youtu.be/video2
https://youtube.com/shorts/video3"""
        
        results = parse_youtube_links_file(content)
        
        assert len(results) == 3
        assert results[0]["video_id"] == "video1xxxxx"[:11].ljust(11, 'x') or results[0]["video_id"] is None
    
    def test_comments_ignored(self):
        """Test that comment lines are ignored."""
        content = """# This is a comment
https://youtube.com/watch?v=dQw4w9WgXcQ
# Another comment"""
        
        results = parse_youtube_links_file(content)
        
        assert len(results) == 1
        assert results[0]["video_id"] == "dQw4w9WgXcQ"
    
    def test_empty_lines_ignored(self):
        """Test that empty lines are ignored."""
        content = """https://youtube.com/watch?v=dQw4w9WgXcQ

https://youtu.be/abcdefghijk"""
        
        results = parse_youtube_links_file(content)
        
        assert len(results) == 2
    
    def test_invalid_urls_marked(self):
        """Test that invalid URLs are marked as invalid."""
        content = """https://youtube.com/watch?v=dQw4w9WgXcQ
invalid-url
https://example.com"""
        
        results = parse_youtube_links_file(content)
        
        assert len(results) == 3
        assert results[0]["valid"] is True
        assert results[1]["valid"] is False
        assert results[2]["valid"] is False
    
    def test_line_numbers(self):
        """Test that line numbers are tracked."""
        content = """# Comment
https://youtube.com/watch?v=dQw4w9WgXcQ

https://youtu.be/abcdefghijk"""
        
        results = parse_youtube_links_file(content)
        
        assert results[0]["line_number"] == 2
        assert results[1]["line_number"] == 4
    
    def test_empty_file(self):
        """Test empty file handling."""
        assert parse_youtube_links_file("") == []
        assert parse_youtube_links_file("   \n\n   ") == []
