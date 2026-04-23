"""
Query Router

Handles question-answering operations using RAG.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger

from app.services.answer.answer_service import AnswerService

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for asking questions."""
    question: str
    top_k: Optional[int] = 5
    min_score: Optional[float] = 0.7
    filters: Optional[dict] = None  # Metadata filters


class SourceReference(BaseModel):
    """Source reference model for citations."""
    document_name: str
    page_number: Optional[int] = None
    section: Optional[str] = None
    content_snippet: str
    similarity_score: float


class QueryResponse(BaseModel):
    """Response model for answers."""
    question: str
    answer: str
    sources: List[SourceReference]
    confidence: float
    needs_review: bool  # True if confidence is low


@router.post("/ask", response_model=QueryResponse)
async def ask_question(request: QueryRequest):
    """
    Ask a question and get an answer using RAG.
    
    The system will:
    1. Embed the question
    2. Search for relevant chunks in Qdrant
    3. Generate an answer using LLM
    4. Return answer with source citations
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Generate answer using RAG
        answer_service = AnswerService()
        result = answer_service.generate_answer(
            question=request.question,
            top_k=request.top_k,
            min_score=request.min_score,
            metadata_filters=request.filters,
        )
        
        # Convert sources to Pydantic model
        sources = []
        for src in result["sources"]:
            sources.append(SourceReference(
                document_name=src["document_name"],
                page_number=src["page_number"],
                section=src["section"],
                content_snippet=src["content_snippet"],
                similarity_score=src["similarity_score"],
            ))
        
        logger.info(
            f"Answer generated: confidence={result['confidence']:.2f}, "
            f"needs_review={result['needs_review']}"
        )
        
        return QueryResponse(
            question=result["question"],
            answer=result["answer"],
            sources=sources,
            confidence=result["confidence"],
            needs_review=result["needs_review"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Question processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process question: {str(e)}"
        )


@router.post("/search")
async def search_documents(request: QueryRequest):
    """
    Search for relevant document chunks without generating an answer.
    
    Useful for previewing what sources would be used.
    """
    try:
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        logger.info(f"Search query: {request.question[:100]}...")
        
        # Use answer service for search preview
        answer_service = AnswerService()
        result = answer_service.generate_search_preview(
            query=request.question,
            top_k=request.top_k,
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/history")
async def get_query_history(limit: int = 10):
    """
    Get recent query history.
    
    Note: This is a placeholder - implement proper audit logging in production.
    """
    return {
        "queries": [],
        "total": 0,
        "message": "Query history not yet implemented"
    }