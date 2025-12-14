"""
MPIS Genesis API - Text Utilities

Text processing utilities including slugification, normalization,
and content hashing.
"""
import re
import hashlib
from typing import Optional
from unidecode import unidecode


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert text to a URL-safe slug.
    
    Handles transliteration from Cyrillic and other scripts to ASCII.
    
    Args:
        text: Input text to slugify
        max_length: Maximum length of the slug
        
    Returns:
        URL-safe slug string
        
    Examples:
        >>> slugify("Tim Keller")
        'tim-keller'
        >>> slugify("Тим Келлер")
        'tim-keller'
        >>> slugify("Алексей 123")
        'aleksei-123'
    """
    if not text:
        return ""
    
    # Transliterate to ASCII
    text = unidecode(text)
    
    # Convert to lowercase
    text = text.lower()
    
    # Replace spaces and underscores with hyphens
    text = re.sub(r'[\s_]+', '-', text)
    
    # Remove non-alphanumeric characters except hyphens
    text = re.sub(r'[^a-z0-9-]', '', text)
    
    # Remove multiple consecutive hyphens
    text = re.sub(r'-+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Truncate to max length
    if len(text) > max_length:
        text = text[:max_length].rstrip('-')
    
    return text or "persona"


def normalize_text(text: str) -> str:
    """
    Normalize text for processing and hashing.
    
    Strips noise, normalizes whitespace, and removes excessive formatting.
    
    Args:
        text: Input text to normalize
        
    Returns:
        Normalized text string
    """
    if not text:
        return ""
    
    # Replace various unicode spaces with regular spaces
    text = re.sub(r'[\u00a0\u2000-\u200b\u2028\u2029\u3000]', ' ', text)
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove excessive blank lines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Normalize spaces within lines
    text = re.sub(r'[ \t]+', ' ', text)
    
    # Strip leading/trailing whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Strip overall
    text = text.strip()
    
    return text


def compute_content_hash(text: str) -> str:
    """
    Compute SHA-256 hash of normalized text content.
    
    Used for idempotency checking to avoid re-importing identical content.
    
    Args:
        text: Text content to hash
        
    Returns:
        SHA-256 hex digest string
    """
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def chunk_text(
    text: str,
    min_tokens: int = 500,
    max_tokens: int = 1200,
    overlap_tokens: int = 100
) -> list[str]:
    """
    Split text into chunks of approximately the specified token range.
    
    Uses a simple word-based approximation (1 token ≈ 0.75 words on average).
    Chunks at paragraph boundaries when possible.
    
    Args:
        text: Text to chunk
        min_tokens: Minimum tokens per chunk
        max_tokens: Maximum tokens per chunk
        overlap_tokens: Token overlap between chunks
        
    Returns:
        List of text chunks
    """
    if not text:
        return []
    
    # Approximate tokens to words (1 token ≈ 0.75 words)
    tokens_to_words = 0.75
    min_words = int(min_tokens * tokens_to_words)
    max_words = int(max_tokens * tokens_to_words)
    overlap_words = int(overlap_tokens * tokens_to_words)
    
    # Split into paragraphs
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    
    chunks = []
    current_chunk_words = []
    current_word_count = 0
    
    for para in paragraphs:
        para_words = para.split()
        para_word_count = len(para_words)
        
        # If single paragraph is too long, split it
        if para_word_count > max_words:
            # Flush current chunk first
            if current_chunk_words:
                chunks.append(' '.join(current_chunk_words))
                # Keep overlap
                overlap_start = max(0, len(current_chunk_words) - overlap_words)
                current_chunk_words = current_chunk_words[overlap_start:]
                current_word_count = len(current_chunk_words)
            
            # Split long paragraph into sentences
            sentences = re.split(r'(?<=[.!?])\s+', para)
            for sentence in sentences:
                sentence_words = sentence.split()
                sentence_word_count = len(sentence_words)
                
                if current_word_count + sentence_word_count > max_words:
                    if current_chunk_words:
                        chunks.append(' '.join(current_chunk_words))
                        overlap_start = max(0, len(current_chunk_words) - overlap_words)
                        current_chunk_words = current_chunk_words[overlap_start:]
                        current_word_count = len(current_chunk_words)
                
                current_chunk_words.extend(sentence_words)
                current_word_count += sentence_word_count
        else:
            # Check if adding paragraph exceeds max
            if current_word_count + para_word_count > max_words:
                if current_chunk_words:
                    chunks.append(' '.join(current_chunk_words))
                    # Keep overlap
                    overlap_start = max(0, len(current_chunk_words) - overlap_words)
                    current_chunk_words = current_chunk_words[overlap_start:]
                    current_word_count = len(current_chunk_words)
            
            current_chunk_words.extend(para_words)
            current_word_count += para_word_count
    
    # Flush remaining
    if current_chunk_words:
        chunks.append(' '.join(current_chunk_words))
    
    # Filter out chunks that are too small (unless it's the only chunk)
    if len(chunks) > 1:
        chunks = [c for c in chunks if len(c.split()) >= min_words // 2]
    
    return chunks


def extract_text_preview(text: str, max_chars: int = 200) -> str:
    """
    Extract a preview of text for display.
    
    Args:
        text: Full text
        max_chars: Maximum characters to include
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if not text:
        return ""
    
    text = normalize_text(text)
    
    if len(text) <= max_chars:
        return text
    
    # Try to cut at a word boundary
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    
    if last_space > max_chars * 0.7:
        truncated = truncated[:last_space]
    
    return truncated.rstrip() + "..."
