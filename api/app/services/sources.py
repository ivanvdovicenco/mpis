"""
MPIS Genesis API - Source Collector Service

Handles collecting source materials from all three channels:
- Channel A: YouTube Links File
- Channel B: Google Drive Folder
- Channel C: Public Persona Auto-Enrichment
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import UUID
import hashlib
import time
import json

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.persona import Source
from app.utils.text import normalize_text, compute_content_hash, slugify
from app.utils.youtube import parse_youtube_links_file, extract_video_id

logger = logging.getLogger(__name__)
settings = get_settings()


class SourceCollector:
    """
    Collects and processes source materials for persona generation.
    
    Implements all three source channels with idempotency checking.
    """
    
    def __init__(self, db: AsyncSession, job_id: UUID, slug: str):
        """
        Initialize source collector.
        
        Args:
            db: Database session
            job_id: Genesis job ID
            slug: Persona slug for file paths
        """
        self.db = db
        self.job_id = job_id
        self.slug = slug
        self.sources_dir = Path(settings.SOURCES_BASE_DIR) / slug
        self.sources_dir.mkdir(parents=True, exist_ok=True)
    
    async def collect_all(
        self,
        gdrive_folder_id: Optional[str] = None,
        public_persona: bool = False,
        public_name: Optional[str] = None,
        additional_sources: List[dict] = None
    ) -> Dict[str, Any]:
        """
        Collect from all applicable source channels.
        
        Args:
            gdrive_folder_id: Google Drive folder ID for Channel B
            public_persona: Enable Channel C web enrichment
            public_name: Public name for web search
            additional_sources: Additional sources from request
            
        Returns:
            Summary of collected sources
        """
        results = {
            "youtube": {"count": 0, "success": 0, "failed": 0, "skipped": 0},
            "gdrive": {"count": 0, "success": 0, "failed": 0, "skipped": 0},
            "web": {"count": 0, "success": 0, "failed": 0, "skipped": 0},
            "text": {"count": 0, "success": 0, "failed": 0, "skipped": 0},
            "total_sources": 0,
            "total_text_length": 0
        }
        
        # Channel A: YouTube Links
        youtube_results = await self.collect_youtube_sources()
        results["youtube"] = youtube_results
        
        # Channel B: Google Drive
        if gdrive_folder_id:
            gdrive_results = await self.collect_gdrive_sources(gdrive_folder_id)
            results["gdrive"] = gdrive_results
        
        # Channel C: Public Persona Web Enrichment
        if public_persona and public_name:
            web_results = await self.collect_web_sources(public_name)
            results["web"] = web_results
        
        # Additional text sources
        if additional_sources:
            text_results = await self.collect_text_sources(additional_sources)
            results["text"] = text_results
        
        # Calculate totals
        for key in ["youtube", "gdrive", "web", "text"]:
            results["total_sources"] += results[key].get("success", 0)
        
        return results
    
    async def check_content_exists(self, content_hash: str) -> bool:
        """Check if content with this hash already exists for this job."""
        result = await self.db.execute(
            select(Source)
            .where(Source.job_id == self.job_id)
            .where(Source.content_hash == content_hash)
        )
        return result.scalars().first() is not None
    
    async def save_source(
        self,
        source_type: str,
        source_ref: str,
        content: str,
        metadata: dict,
        file_path: Optional[str] = None
    ) -> Optional[Source]:
        """
        Save a source to the database with idempotency check.
        
        Args:
            source_type: Type of source (youtube, file, url, text)
            source_ref: Reference identifier
            content: Extracted text content
            metadata: Additional metadata
            file_path: Path where text was saved (if applicable)
            
        Returns:
            Created Source or None if duplicate
        """
        content_hash = compute_content_hash(content)
        
        # Idempotency check
        if await self.check_content_exists(content_hash):
            logger.info(f"Skipping duplicate source: {source_ref}")
            return None
        
        source = Source(
            job_id=self.job_id,
            source_type=source_type,
            source_ref=source_ref,
            content_hash=content_hash,
            metadata=metadata,
            extracted_text_path=file_path
        )
        
        self.db.add(source)
        await self.db.flush()
        
        return source
    
    async def collect_youtube_sources(self) -> Dict[str, int]:
        """
        Channel A: Collect YouTube sources from youtube_links.txt
        
        Returns:
            Collection summary
        """
        results = {"count": 0, "success": 0, "failed": 0, "skipped": 0}
        
        youtube_links_path = Path(settings.youtube_links_path)
        
        if not youtube_links_path.exists():
            logger.info(f"YouTube links file not found: {youtube_links_path}")
            return results
        
        try:
            content = youtube_links_path.read_text(encoding='utf-8')
            links = parse_youtube_links_file(content)
        except Exception as e:
            logger.error(f"Error reading YouTube links file: {e}")
            return results
        
        results["count"] = len(links)
        
        # Create youtube subdirectory
        youtube_dir = self.sources_dir / "youtube"
        youtube_dir.mkdir(exist_ok=True)
        
        for link_info in links:
            if not link_info["valid"]:
                results["failed"] += 1
                continue
            
            video_id = link_info["video_id"]
            url = link_info["url"]
            
            try:
                # Try to fetch transcript
                transcript_text = await self._fetch_youtube_transcript(video_id)
                
                if not transcript_text:
                    # Mark as failed_transcript
                    await self.save_source(
                        source_type="youtube",
                        source_ref=url,
                        content="",
                        metadata={
                            "provider": "youtube",
                            "videoId": video_id,
                            "status": "failed_transcript"
                        }
                    )
                    results["failed"] += 1
                    continue
                
                # Save transcript to file
                file_path = youtube_dir / f"{video_id}.txt"
                file_path.write_text(transcript_text, encoding='utf-8')
                
                # Save to database
                source = await self.save_source(
                    source_type="youtube",
                    source_ref=url,
                    content=transcript_text,
                    metadata={
                        "provider": "youtube",
                        "videoId": video_id,
                        "status": "ok"
                    },
                    file_path=str(file_path)
                )
                
                if source:
                    results["success"] += 1
                else:
                    results["skipped"] += 1
                    
            except Exception as e:
                logger.error(f"Error processing YouTube video {video_id}: {e}")
                results["failed"] += 1
        
        return results
    
    async def _fetch_youtube_transcript(self, video_id: str) -> Optional[str]:
        """
        Fetch transcript for a YouTube video.
        
        Uses youtube-transcript-api library.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Transcript text or None if failed
        """
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            transcript_list = await loop.run_in_executor(
                None,
                lambda: YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'ru', 'de', 'fr', 'es'])
            )
            
            # Combine transcript segments
            text_parts = [entry['text'] for entry in transcript_list]
            return ' '.join(text_parts)
            
        except Exception as e:
            logger.warning(f"Failed to fetch transcript for {video_id}: {e}")
            return None
    
    async def collect_gdrive_sources(self, folder_id: str) -> Dict[str, int]:
        """
        Channel B: Collect documents from Google Drive folder.
        
        Supports:
        - Google Docs (exported to text)
        - PDF (text extraction)
        - DOCX (text extraction)
        - DOC (optional, marks as failed if can't convert)
        
        Args:
            folder_id: Google Drive folder ID
            
        Returns:
            Collection summary
        """
        results = {"count": 0, "success": 0, "failed": 0, "skipped": 0}
        
        # Check for service account file
        sa_path = Path(settings.GDRIVE_SERVICE_ACCOUNT_JSON_PATH)
        if not sa_path.exists():
            logger.warning(f"Google Drive service account file not found: {sa_path}")
            return results
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaIoBaseDownload
            import io
            
            # Authenticate
            credentials = service_account.Credentials.from_service_account_file(
                str(sa_path),
                scopes=['https://www.googleapis.com/auth/drive.readonly']
            )
            service = build('drive', 'v3', credentials=credentials)
            
            # List files in folder
            query = f"'{folder_id}' in parents and trashed=false"
            response = service.files().list(
                q=query,
                fields="files(id, name, mimeType)"
            ).execute()
            
            files = response.get('files', [])
            results["count"] = len(files)
            
            # Create drive subdirectory
            drive_dir = self.sources_dir / "drive"
            drive_dir.mkdir(exist_ok=True)
            
            for file_info in files:
                file_id = file_info['id']
                file_name = file_info['name']
                mime_type = file_info['mimeType']
                
                try:
                    text_content = await self._extract_gdrive_file(
                        service, file_id, file_name, mime_type, drive_dir
                    )
                    
                    if not text_content:
                        results["failed"] += 1
                        continue
                    
                    # Safe filename
                    safe_name = slugify(file_name, max_length=40)
                    file_path = drive_dir / f"{file_id}_{safe_name}.txt"
                    file_path.write_text(text_content, encoding='utf-8')
                    
                    source = await self.save_source(
                        source_type="file",
                        source_ref=f"{file_id}:{file_name}",
                        content=text_content,
                        metadata={
                            "provider": "gdrive",
                            "mimeType": mime_type,
                            "title": file_name,
                            "status": "ok"
                        },
                        file_path=str(file_path)
                    )
                    
                    if source:
                        results["success"] += 1
                    else:
                        results["skipped"] += 1
                        
                except Exception as e:
                    logger.error(f"Error processing GDrive file {file_name}: {e}")
                    results["failed"] += 1
                    
        except Exception as e:
            logger.error(f"Error accessing Google Drive: {e}")
        
        return results
    
    async def _extract_gdrive_file(
        self,
        service,
        file_id: str,
        file_name: str,
        mime_type: str,
        output_dir: Path
    ) -> Optional[str]:
        """
        Extract text from a Google Drive file.
        
        Args:
            service: Google Drive service instance
            file_id: File ID
            file_name: File name
            mime_type: MIME type
            output_dir: Directory to save downloaded files
            
        Returns:
            Extracted text or None
        """
        import io
        from googleapiclient.http import MediaIoBaseDownload
        
        loop = asyncio.get_event_loop()
        
        try:
            # Google Docs - export as plain text
            if mime_type == 'application/vnd.google-apps.document':
                request = service.files().export_media(
                    fileId=file_id,
                    mimeType='text/plain'
                )
                content = await loop.run_in_executor(None, request.execute)
                return content.decode('utf-8') if isinstance(content, bytes) else content
            
            # PDF
            elif mime_type == 'application/pdf':
                request = service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = await loop.run_in_executor(None, downloader.next_chunk)
                
                fh.seek(0)
                return await self._extract_pdf_text(fh)
            
            # DOCX
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                request = service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                while not done:
                    status, done = await loop.run_in_executor(None, downloader.next_chunk)
                
                fh.seek(0)
                return await self._extract_docx_text(fh)
            
            # DOC (legacy) - mark as failed_parse
            elif mime_type == 'application/msword':
                logger.warning(f"DOC format not supported: {file_name}")
                return None
            
            # Plain text
            elif mime_type.startswith('text/'):
                request = service.files().get_media(fileId=file_id)
                content = await loop.run_in_executor(None, request.execute)
                return content.decode('utf-8') if isinstance(content, bytes) else content
            
            else:
                logger.warning(f"Unsupported MIME type: {mime_type} for {file_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting file {file_name}: {e}")
            return None
    
    async def _extract_pdf_text(self, file_obj) -> str:
        """Extract text from PDF file object."""
        from pypdf import PdfReader
        
        loop = asyncio.get_event_loop()
        
        def extract():
            reader = PdfReader(file_obj)
            text_parts = []
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
            return '\n\n'.join(text_parts)
        
        return await loop.run_in_executor(None, extract)
    
    async def _extract_docx_text(self, file_obj) -> str:
        """Extract text from DOCX file object."""
        from docx import Document
        
        loop = asyncio.get_event_loop()
        
        def extract():
            doc = Document(file_obj)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            return '\n\n'.join(text_parts)
        
        return await loop.run_in_executor(None, extract)
    
    async def collect_web_sources(self, public_name: str) -> Dict[str, int]:
        """
        Channel C: Collect web sources for public persona enrichment.
        
        Discovery approach:
        - If SERPAPI_API_KEY exists: use SerpAPI for search
        - Else: Wikipedia API + limited direct sources
        
        Args:
            public_name: Name to search for
            
        Returns:
            Collection summary
        """
        results = {"count": 0, "success": 0, "failed": 0, "skipped": 0}
        
        urls_to_fetch = []
        
        # Discover URLs
        if settings.SERPAPI_API_KEY:
            urls_to_fetch = await self._discover_via_serpapi(public_name)
        else:
            urls_to_fetch = await self._discover_via_wikipedia(public_name)
        
        results["count"] = len(urls_to_fetch)
        
        # Create web subdirectory
        web_dir = self.sources_dir / "web"
        web_dir.mkdir(exist_ok=True)
        
        for url_info in urls_to_fetch[:settings.PUBLIC_WEB_MAX_SOURCES]:
            url = url_info.get("url", "")
            title = url_info.get("title", "")
            
            # Check domain allowlist/denylist
            if not self._is_domain_allowed(url):
                results["skipped"] += 1
                continue
            
            try:
                # Fetch and extract content (with rate limiting)
                summary = await self._fetch_web_summary(url)
                
                if not summary:
                    results["failed"] += 1
                    continue
                
                # Store as source (do NOT store full articles, just summary)
                source = await self.save_source(
                    source_type="url",
                    source_ref=url,
                    content=summary,
                    metadata={
                        "provider": "web",
                        "title": title,
                        "publisher": self._extract_domain(url),
                        "status": "ok"
                    }
                )
                
                if source:
                    results["success"] += 1
                else:
                    results["skipped"] += 1
                
                # Rate limiting delay
                await asyncio.sleep(settings.WEB_REQUEST_DELAY)
                
            except Exception as e:
                logger.error(f"Error fetching web source {url}: {e}")
                results["failed"] += 1
        
        # Internal knowledge enrichment from Qdrant
        try:
            internal_results = await self._collect_internal_sources(public_name)
            results["success"] += internal_results.get("success", 0)
        except Exception as e:
            logger.warning(f"Error collecting internal sources: {e}")
        
        return results
    
    async def _discover_via_serpapi(self, query: str) -> List[dict]:
        """Discover URLs using SerpAPI."""
        import requests
        
        try:
            response = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "api_key": settings.SERPAPI_API_KEY,
                    "num": settings.PUBLIC_WEB_MAX_SOURCES
                },
                timeout=settings.WEB_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            results = []
            
            for item in data.get("organic_results", []):
                results.append({
                    "url": item.get("link", ""),
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "")
                })
            
            return results
            
        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            return []
    
    async def _discover_via_wikipedia(self, query: str) -> List[dict]:
        """Discover URLs using Wikipedia API as fallback."""
        import requests
        
        results = []
        
        try:
            # Search Wikipedia
            response = requests.get(
                "https://en.wikipedia.org/w/api.php",
                params={
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json",
                    "srlimit": 5
                },
                timeout=settings.WEB_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "").replace(" ", "_")
                results.append({
                    "url": f"https://en.wikipedia.org/wiki/{title}",
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", "")
                })
                
        except Exception as e:
            logger.error(f"Wikipedia API error: {e}")
        
        return results
    
    async def _fetch_web_summary(self, url: str) -> Optional[str]:
        """
        Fetch web page and extract semantic summary.
        
        Uses trafilatura for clean text extraction.
        Does NOT store full articles - returns summarized notes.
        """
        import requests
        
        try:
            import trafilatura
            
            response = requests.get(
                url,
                timeout=settings.WEB_REQUEST_TIMEOUT,
                headers={"User-Agent": "MPIS Genesis Bot/1.0"}
            )
            response.raise_for_status()
            
            # Extract main content
            text = trafilatura.extract(response.text)
            
            if not text:
                return None
            
            # Limit to configured max chars as summary (don't store full copyrighted content)
            max_chars = settings.WEB_SUMMARY_MAX_CHARS
            if len(text) > max_chars:
                text = text[:max_chars] + "..."
            
            return text
            
        except Exception as e:
            logger.warning(f"Error fetching {url}: {e}")
            return None
    
    def _is_domain_allowed(self, url: str) -> bool:
        """Check if domain is allowed by allowlist/denylist."""
        domain = self._extract_domain(url)
        
        # Check denylist
        if domain in settings.denied_domains_list:
            return False
        
        # Check allowlist (if defined, only allow those)
        if settings.allowed_domains_list:
            return domain in settings.allowed_domains_list
        
        return True
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            return parsed.netloc.lower()
        except Exception:
            return ""
    
    async def _collect_internal_sources(self, public_name: str) -> Dict[str, int]:
        """
        Collect internal knowledge from Qdrant if available.
        
        Does similarity lookup by public_name.
        """
        results = {"success": 0, "failed": 0}
        
        # This will be implemented when QdrantService is available
        # For now, return empty results
        return results
    
    async def collect_text_sources(self, sources: List[dict]) -> Dict[str, int]:
        """
        Collect additional text sources from request.
        
        Args:
            sources: List of source dicts with type, ref, metadata
            
        Returns:
            Collection summary
        """
        results = {"count": len(sources), "success": 0, "failed": 0, "skipped": 0}
        
        for source_info in sources:
            source_type = source_info.get("type", "text")
            ref = source_info.get("ref", "")
            metadata = source_info.get("metadata", {})
            
            if source_type == "text" and ref:
                source = await self.save_source(
                    source_type="text",
                    source_ref=ref[:100],  # First 100 chars as ref
                    content=ref,
                    metadata={
                        **metadata,
                        "provider": "user_input",
                        "status": "ok"
                    }
                )
                
                if source:
                    results["success"] += 1
                else:
                    results["skipped"] += 1
            else:
                results["failed"] += 1
        
        return results
    
    async def get_all_source_texts(self) -> List[str]:
        """
        Get all extracted text from sources for this job.
        
        Returns:
            List of text contents
        """
        result = await self.db.execute(
            select(Source)
            .where(Source.job_id == self.job_id)
            .where(Source.metadata['status'].astext == 'ok')
        )
        sources = result.scalars().all()
        
        texts = []
        for source in sources:
            if source.extracted_text_path:
                try:
                    path = Path(source.extracted_text_path)
                    if path.exists():
                        texts.append(path.read_text(encoding='utf-8'))
                except Exception as e:
                    logger.warning(f"Error reading source file: {e}")
            elif source.source_type == "text":
                # For text sources, the content is in source_ref
                texts.append(source.source_ref)
        
        return texts
