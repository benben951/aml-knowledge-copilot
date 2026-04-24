"""
Qdrant Vector Database Client

Provides a clean interface for vector operations:
- Initialize connection
- Create collections
- Upsert vectors
- Search similar vectors
"""

from typing import List, Dict, Any, Optional
from qdrant_client import QdrantVectorStore as QdrantClientNative
from qdrant_client.http.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    SearchParams,
    ScalarQuantile,
    ScalarQuantization,
)
from loguru import logger

from app.core.config import settings


class QdrantVectorStore:
    """Qdrant vector database client wrapper"""
    
    _instance: Optional["QdrantVectorStore"] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to reuse connection"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Qdrant client connection"""
        if hasattr(self, "_initialized"):
            return
            
        self._client = QdrantClientNative(
            url=settings.QDRANT_URL,
            prefer_grpc=False,  # Use REST for simplicity
        )
        self._collection_name = settings.QDRANT_COLLECTION_NAME
        self._vector_size = settings.QDRANT_VECTOR_SIZE
        self._initialized = True
        
        logger.info(f"QdrantClient initialized with collection: {self._collection_name}")
    
    def create_collection(self) -> bool:
        """
        Create collection if it doesn't exist.
        
        Returns:
            True if collection was created or already exists
        """
        try:
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            
            if self._collection_name not in collection_names:
                logger.info(f"Creating collection: {self._collection_name}")
                self._client.create_collection(
                    collection_name=self._collection_name,
                    vectors_config=VectorParams(
                        size=self._vector_size,
                        distance=Distance.COSINE,
                    ),
                    # Enable quantization for memory efficiency
                    quantization_config=ScalarQuantization(
                        scalar=ScalarQuantile(
                            quantile=0.99,
                            always_ram=True,
                        )
                    ),
                )
                logger.info(f"Collection {self._collection_name} created successfully")
            else:
                logger.debug(f"Collection {self._collection_name} already exists")
            
            return True
        except Exception as e:
            logger.error(f"Failed to create collection: {e}")
            return False
    
    def collection_exists(self) -> bool:
        """Check if collection exists"""
        try:
            collections = self._client.get_collections().collections
            collection_names = [c.name for c in collections]
            return self._collection_name in collection_names
        except Exception as e:
            logger.error(f"Failed to check collection existence: {e}")
            return False
    
    def upsert(
        self,
        vectors: List[List[float]],
        payloads: List[Dict[str, Any]],
        ids: Optional[List[str]] = None,
    ) -> bool:
        """
        Upsert vectors into the collection.
        
        Args:
            vectors: List of vector embeddings
            payloads: List of metadata dictionaries
            ids: Optional list of point IDs (auto-generated if not provided)
            
        Returns:
            True if upsert was successful
        """
        try:
            if ids is None:
                import uuid
                ids = [str(uuid.uuid4()) for _ in vectors]
            
            points = []
            for vid, vector, payload in zip(ids, vectors, payloads):
                points.append(
                    PointStruct(
                        id=vid,
                        vector=vector,
                        payload=payload,
                    )
                )
            
            result = self._client.upsert(
                collection_name=self._collection_name,
                points=points,
            )
            
            logger.info(f"Upserted {len(vectors)} vectors to Qdrant")
            return result.status == "completed"
        except Exception as e:
            logger.error(f"Failed to upsert vectors: {e}")
            return False
    
    def search(
        self,
        query_vector: List[float],
        limit: int = 5,
        min_score: float = 0.7,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for similar vectors.
        
        Args:
            query_vector: The query embedding
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold
            metadata_filters: Optional metadata filters
            
        Returns:
            List of search results with payload and score
        """
        try:
            # Build filter if provided
            qdrant_filter = None
            if metadata_filters:
                conditions = []
                for key, value in metadata_filters.items():
                    conditions.append(
                        FieldCondition(
                            key=key,
                            match=MatchValue(value=value),
                        )
                    )
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            results = self._client.search(
                collection_name=self._collection_name,
                query_vector=query_vector,
                query_filter=qdrant_filter,
                limit=limit,
                score_threshold=min_score,
                search_params=SearchParams(
                    hnsw_ef=128,
                    exact=False,
                ),
            )
            
            # Convert to dict format
            search_results = []
            for result in results:
                search_results.append({
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload,
                })
            
            logger.debug(f"Search returned {len(search_results)} results")
            return search_results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
    
    def delete_points(self, point_ids: List[str]) -> bool:
        """
        Delete points by ID.
        
        Args:
            point_ids: List of point IDs to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            result = self._client.delete(
                collection_name=self._collection_name,
                points_selector={"points": point_ids},
            )
            logger.info(f"Deleted {len(point_ids)} points from Qdrant")
            return result.status == "completed"
        except Exception as e:
            logger.error(f"Failed to delete points: {e}")
            return False
    
    def get_collection_info(self) -> Optional[Dict[str, Any]]:
        """
        Get collection information.
        
        Returns:
            Collection info dict or None if not found
        """
        try:
            info = self._client.get_collection(self._collection_name)
            return {
                "vectors_count": info.vectors_count,
                "points_count": info.points_count,
                "status": info.status,
                "vectors_count": info.vectors_count,
            }
        except Exception as e:
            logger.error(f"Failed to get collection info: {e}")
            return None
    
    def health_check(self) -> bool:
        """
        Check Qdrant connection health.
        
        Returns:
            True if connection is healthy
        """
        try:
            self._client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

def get_qdrant_client() -> "QdrantVectorStore":
    """Factory function to get a QdrantClient instance (singleton)."""
    return QdrantVectorStore()
