"""
Retrieval Service

Handles question embedding and similarity search.
"""

from typing import List, Dict, Any, Optional
from loguru import logger

from app.infra.vector.qdrant_client import QdrantVectorStore
from app.infra.llm.llm_client import LLMClient
from app.core.config import settings


class RetrievalService:
    """Retrieval service for finding relevant document chunks"""
    
    def __init__(self):
        """Initialize retrieval service"""
        self.qdrant = QdrantVectorStore()
        self.llm = LLMClient()
        
        logger.info("RetrievalService initialized")
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant document chunks for a query.
        
        Args:
            query: User query/question
            top_k: Number of results to return (defaults to TOP_K_RESULTS)
            min_score: Minimum similarity score (defaults to MIN_SIMILARITY_SCORE)
            metadata_filters: Optional metadata filters
            
        Returns:
            List of search results sorted by relevance
        """
        try:
            top_k = top_k or settings.TOP_K_RESULTS
            min_score = min_score or settings.MIN_SIMILARITY_SCORE
            
            logger.info(f"Retrieving for query: {query[:100]}...")
            
            # Generate query embedding
            query_embedding = self.llm.embed_text(query)
            
            # Search in Qdrant
            results = self.qdrant.search(
                query_vector=query_embedding,
                limit=top_k,
                min_score=min_score,
                metadata_filters=metadata_filters,
            )
            
            logger.info(f"Retrieved {len(results)} relevant chunks")
            
            return results
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            raise
    
    def retrieve_with_explanation(
        self,
        query: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve results with additional analysis.
        
        Args:
            query: User query/question
            top_k: Number of results
            min_score: Minimum similarity score
            
        Returns:
            Dict with results and analysis
        """
        try:
            results = self.retrieve(query, top_k, min_score)
            
            # Analyze result quality
            avg_score = sum(r["score"] for r in results) / len(results) if results else 0.0
            has_strong_match = any(r["score"] >= 0.85 for r in results)
            
            return {
                "results": results,
                "total_found": len(results),
                "average_score": avg_score,
                "has_strong_match": has_strong_match,
                "quality": "high" if has_strong_match else ("medium" if avg_score > 0.75 else "low"),
            }
        except Exception as e:
            logger.error(f"Retrieval with explanation failed: {e}")
            raise