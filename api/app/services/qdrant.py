"""
MPIS Genesis API - Qdrant Service

Handles vector store operations for persona embeddings.
"""
import logging
from typing import Optional, List, Dict, Any
from uuid import UUID

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class QdrantService:
    """
    Service for Qdrant vector store operations.
    
    Manages collections and embeddings for persona sources and core.
    """
    
    def __init__(self):
        """Initialize Qdrant client."""
        self.client = None
        self.available = False
        
        try:
            self.client = QdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=10
            )
            # Test connection
            self.client.get_collections()
            self.available = True
            logger.info("Qdrant connection established")
        except Exception as e:
            logger.warning(f"Qdrant not available: {e}")
            self.available = False
    
    async def ensure_collections(self) -> bool:
        """
        Ensure required collections exist.
        
        Creates:
        - persona_sources_embeddings
        - persona_core_embeddings
        
        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False
        
        try:
            collections = {c.name for c in self.client.get_collections().collections}
            
            # Create sources collection
            if settings.QDRANT_COLLECTION_SOURCES not in collections:
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_SOURCES,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {settings.QDRANT_COLLECTION_SOURCES}")
            
            # Create core collection
            if settings.QDRANT_COLLECTION_CORE not in collections:
                self.client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION_CORE,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {settings.QDRANT_COLLECTION_CORE}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ensuring collections: {e}")
            return False
    
    async def upsert_source_embeddings(
        self,
        job_id: UUID,
        persona_slug: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Upsert source chunk embeddings.
        
        Args:
            job_id: Genesis job ID
            persona_slug: Persona slug
            chunks: List of chunk dicts with text and metadata
            embeddings: Corresponding embedding vectors
            
        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            logger.warning("Qdrant not available, skipping embeddings")
            return False
        
        if len(chunks) != len(embeddings):
            logger.error("Chunks and embeddings count mismatch")
            return False
        
        try:
            points = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                point = PointStruct(
                    id=str(chunk.get("chunk_id", f"{job_id}_{i}")),
                    vector=embedding,
                    payload={
                        "job_id": str(job_id),
                        "persona_slug": persona_slug,
                        "source_id": str(chunk.get("source_id", "")),
                        "chunk_index": i,
                        "text_preview": chunk.get("text", "")[:200],
                        "timestamp": chunk.get("timestamp", "")
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION_SOURCES,
                points=points
            )
            
            logger.info(f"Upserted {len(points)} source embeddings for job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting source embeddings: {e}")
            return False
    
    async def upsert_core_embeddings(
        self,
        persona_id: UUID,
        persona_slug: str,
        core_sections: List[Dict[str, Any]],
        embeddings: List[List[float]]
    ) -> bool:
        """
        Upsert persona core embeddings.
        
        Args:
            persona_id: Persona ID
            persona_slug: Persona slug
            core_sections: List of core section dicts
            embeddings: Corresponding embedding vectors
            
        Returns:
            True if successful, False otherwise
        """
        if not self.available:
            return False
        
        try:
            points = []
            for i, (section, embedding) in enumerate(zip(core_sections, embeddings)):
                point = PointStruct(
                    id=f"{persona_id}_{section.get('section', i)}",
                    vector=embedding,
                    payload={
                        "persona_id": str(persona_id),
                        "persona_slug": persona_slug,
                        "section": section.get("section", ""),
                        "text_preview": section.get("text", "")[:200]
                    }
                )
                points.append(point)
            
            self.client.upsert(
                collection_name=settings.QDRANT_COLLECTION_CORE,
                points=points
            )
            
            logger.info(f"Upserted {len(points)} core embeddings for persona {persona_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error upserting core embeddings: {e}")
            return False
    
    async def search_similar(
        self,
        collection: str,
        query_vector: List[float],
        limit: int = 10,
        persona_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            collection: Collection name
            query_vector: Query embedding
            limit: Maximum results
            persona_slug: Optional filter by persona
            
        Returns:
            List of similar items with scores
        """
        if not self.available:
            return []
        
        try:
            filter_conditions = None
            if persona_slug:
                filter_conditions = Filter(
                    must=[
                        FieldCondition(
                            key="persona_slug",
                            match=MatchValue(value=persona_slug)
                        )
                    ]
                )
            
            results = self.client.search(
                collection_name=collection,
                query_vector=query_vector,
                limit=limit,
                query_filter=filter_conditions
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "payload": r.payload
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Qdrant is available."""
        return self.available
