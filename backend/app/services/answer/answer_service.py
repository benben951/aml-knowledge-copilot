"""
Answer Generation Service

Handles answer generation using RAG: retrieval + LLM + citation extraction.
"""

import re
from typing import List, Dict, Any, Optional
from loguru import logger

from app.infra.llm.llm_client import LLMClient
from app.services.retrieval.retrieval_service import RetrievalService
from app.core.prompts import SYSTEM_PROMPT, QA_PROMPT_TEMPLATE, GUARDRAIL_PROMPT
from app.core.config import settings


class AnswerService:
    """Answer generation service using RAG"""
    
    def __init__(self):
        """Initialize answer service"""
        self.llm = LLMClient()
        self.retrieval = RetrievalService()
        
        logger.info("AnswerService initialized")
    
    def _format_context(self, search_results: List[Dict[str, Any]]) -> str:
        """
        Format search results into context string for LLM.
        
        Args:
            search_results: List of search results
            
        Returns:
            Formatted context string
        """
        context_parts = []
        
        for i, result in enumerate(search_results, 1):
            payload = result.get("payload", {})
            text = payload.get("text", "")
            filename = payload.get("filename", "Unknown")
            page = payload.get("page", None)
            chunk_index = payload.get("chunk_index", 0)
            
            context_part = f"[文档{i}] {filename}"
            if page:
                context_part += f"，第{page}页"
            if chunk_index is not None:
                context_part += f" (片段{chunk_index + 1})"
            context_part += f":\n{text}\n"
            
            context_parts.append(context_part)
        
        return "\n\n".join(context_parts)
    
    def _extract_citations(
        self,
        answer: str,
        search_results: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Extract structured citations from search results.
        
        Args:
            answer: Generated answer text
            search_results: Original search results
            
        Returns:
            List of source references
        """
        citations = []
        
        for result in search_results:
            payload = result.get("payload", {})
            
            citation = {
                "document_name": payload.get("filename", "Unknown"),
                "page_number": payload.get("page", None),
                "section": None,  # Could be extracted from text structure
                "content_snippet": payload.get("text", "")[:200] + "..." if len(payload.get("text", "")) > 200 else payload.get("text", ""),
                "similarity_score": result.get("score", 0.0),
            }
            
            citations.append(citation)
        
        # Sort by similarity score
        citations.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return citations
    
    def _calculate_confidence(
        self,
        search_results: List[Dict[str, Any]],
        answer: str,
    ) -> float:
        """
        Calculate confidence score for the answer.
        
        Based on:
        - Retrieval quality (average similarity score)
        - Number of relevant sources
        - Answer length (too short might indicate uncertainty)
        
        Args:
            search_results: Search results used for generation
            answer: Generated answer
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not search_results:
            return 0.0
        
        # Base confidence from retrieval quality
        scores = [r["score"] for r in search_results]
        avg_score = sum(scores) / len(scores)
        max_score = max(scores) if scores else 0.0
        
        # Weight: 60% from retrieval, 20% from top result, 20% from count
        retrieval_confidence = avg_score * 0.6
        top_score_confidence = max_score * 0.2
        
        # More sources = more confidence (up to a point)
        count_factor = min(len(search_results) / settings.TOP_K_RESULTS, 1.0)
        count_confidence = count_factor * 0.2
        
        confidence = retrieval_confidence + top_score_confidence + count_confidence
        
        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, confidence))
    
    def generate_answer(
        self,
        question: str,
        top_k: Optional[int] = None,
        min_score: Optional[float] = None,
        metadata_filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate answer to question using RAG.
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve
            min_score: Minimum similarity score for retrieval
            metadata_filters: Optional metadata filters
            
        Returns:
            Answer dict with answer, sources, confidence, and flags
        """
        try:
            logger.info(f"Generating answer for: {question[:100]}...")
            
            # Step 1: Retrieve relevant chunks
            retrieval_result = self.retrieval.retrieve_with_explanation(
                query=question,
                top_k=top_k,
                min_score=min_score,
            )
            
            search_results = retrieval_result["results"]
            retrieval_quality = retrieval_result["quality"]
            
            # Step 2: Format context
            context = self._format_context(search_results) if search_results else "未找到相关文档内容。"
            
            # Step 3: Generate answer with LLM
            qa_prompt = QA_PROMPT_TEMPLATE.format(context=context, question=question)
            
            # Add guardrail warning if retrieval quality is low
            if retrieval_quality == "low" or not search_results:
                answer = GUARDRAIL_PROMPT + "\n\n" + self.llm.generate(
                    prompt=qa_prompt,
                    system_prompt=SYSTEM_PROMPT,
                )
            else:
                answer = self.llm.generate(
                    prompt=qa_prompt,
                    system_prompt=SYSTEM_PROMPT,
                )
            
            # Step 4: Extract citations
            sources = self._extract_citations(answer, search_results)
            
            # Step 5: Calculate confidence
            confidence = self._calculate_confidence(search_results, answer)
            
            # Step 6: Determine if review is needed
            needs_review = (
                confidence < 0.6 or
                retrieval_quality == "low" or
                len(search_results) < 2
            )
            
            logger.info(f"Answer generated (confidence: {confidence:.2f}, needs_review: {needs_review})")
            
            return {
                "question": question,
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "needs_review": needs_review,
                "retrieval_quality": retrieval_quality,
                "chunks_used": len(search_results),
            }
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            raise
    
    def generate_search_preview(
        self,
        query: str,
        top_k: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Generate search preview without full answer.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            Search results preview
        """
        try:
            results = self.retrieval.retrieve(query, top_k)
            
            # Simplified results for preview
            preview_results = []
            for result in results:
                payload = result.get("payload", {})
                preview_results.append({
                    "document_name": payload.get("filename", "Unknown"),
                    "page": payload.get("page", None),
                    "content_snippet": payload.get("text", "")[:300] + "..." if len(payload.get("text", "")) > 300 else payload.get("text", ""),
                    "score": result.get("score", 0.0),
                })
            
            return {
                "query": query,
                "results": preview_results,
                "total": len(preview_results),
            }
        except Exception as e:
            logger.error(f"Search preview failed: {e}")
            raise