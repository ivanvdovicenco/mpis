"""
MPIS Genesis API - YouTube Utilities

Utilities for parsing YouTube URLs and extracting video IDs.
"""
import re
from typing import Optional, Tuple


# Patterns for YouTube URL formats
# Note: YouTube video IDs are currently 11 characters, but we use {10,12}
# for future resilience in case the format changes slightly
YOUTUBE_PATTERNS = [
    # Standard watch URL: youtube.com/watch?v=VIDEO_ID
    re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/watch\?(?:.*&)?v=([a-zA-Z0-9_-]{10,12})'),
    # Short URL: youtu.be/VIDEO_ID
    re.compile(r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{10,12})'),
    # Shorts URL: youtube.com/shorts/VIDEO_ID
    re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]{10,12})'),
    # Embed URL: youtube.com/embed/VIDEO_ID
    re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{10,12})'),
    # Video URL: youtube.com/v/VIDEO_ID
    re.compile(r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]{10,12})'),
]


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various URL formats.
    
    Supports:
    - youtube.com/watch?v=...
    - youtu.be/...
    - youtube.com/shorts/...
    - youtube.com/embed/...
    - youtube.com/v/...
    
    Args:
        url: YouTube URL string
        
    Returns:
        Video ID string or None if not found
        
    Examples:
        >>> extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id("https://youtu.be/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id("https://youtube.com/shorts/dQw4w9WgXcQ")
        'dQw4w9WgXcQ'
        >>> extract_video_id("invalid-url")
        None
    """
    if not url:
        return None
    
    url = url.strip()
    
    for pattern in YOUTUBE_PATTERNS:
        match = pattern.search(url)
        if match:
            return match.group(1)
    
    return None


def parse_youtube_url(url: str) -> Tuple[Optional[str], str]:
    """
    Parse YouTube URL and extract video ID with URL type.
    
    Args:
        url: YouTube URL string
        
    Returns:
        Tuple of (video_id, url_type) where url_type is 'watch', 'short',
        'youtu.be', 'embed', 'v', or 'unknown'
        
    Examples:
        >>> parse_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        ('dQw4w9WgXcQ', 'watch')
        >>> parse_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        ('dQw4w9WgXcQ', 'youtu.be')
        >>> parse_youtube_url("https://youtube.com/shorts/dQw4w9WgXcQ")
        ('dQw4w9WgXcQ', 'shorts')
    """
    if not url:
        return None, 'unknown'
    
    url = url.strip()
    
    # Check each pattern and identify type
    patterns_with_types = [
        (YOUTUBE_PATTERNS[0], 'watch'),
        (YOUTUBE_PATTERNS[1], 'youtu.be'),
        (YOUTUBE_PATTERNS[2], 'shorts'),
        (YOUTUBE_PATTERNS[3], 'embed'),
        (YOUTUBE_PATTERNS[4], 'v'),
    ]
    
    for pattern, url_type in patterns_with_types:
        match = pattern.search(url)
        if match:
            return match.group(1), url_type
    
    return None, 'unknown'


def parse_youtube_links_file(content: str) -> list[dict]:
    """
    Parse a youtube_links.txt file content.
    
    Format rules:
    - Each non-empty non-comment line is one URL
    - Lines starting with # are ignored
    
    Args:
        content: File content string
        
    Returns:
        List of dicts with 'url', 'video_id', and 'line_number' keys
    """
    results = []
    
    for line_no, line in enumerate(content.split('\n'), start=1):
        line = line.strip()
        
        # Skip empty lines and comments
        if not line or line.startswith('#'):
            continue
        
        video_id = extract_video_id(line)
        
        results.append({
            'url': line,
            'video_id': video_id,
            'line_number': line_no,
            'valid': video_id is not None
        })
    
    return results


def get_youtube_thumbnail_url(video_id: str, quality: str = 'maxresdefault') -> str:
    """
    Get YouTube video thumbnail URL.
    
    Args:
        video_id: YouTube video ID
        quality: Thumbnail quality (maxresdefault, hqdefault, mqdefault, sddefault)
        
    Returns:
        Thumbnail URL
    """
    return f"https://img.youtube.com/vi/{video_id}/{quality}.jpg"
