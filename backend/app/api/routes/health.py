"""
Health Check Router

Provides health check endpoints for monitoring and load balancers.
"""

from fastapi import APIRouter
from loguru import logger

from app.infra.vector.qdrant_client import QdrantClient
from app.infra.llm.llm_client import LLMClient

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Comprehensive health check endpoint.
    
    Checks:
    - Qdrant connection
    - LLM connection
    """
    health_status = {
        "status": "healthy",
        "service": "aml-knowledge-copilot",
        "checks": {},
    }
    
    # Check Qdrant
    try:
        qdrant = QdrantClient()
        qdrant_healthy = qdrant.health_check()
        health_status["checks"]["qdrant"] = {
            "status": "healthy" if qdrant_healthy else "unhealthy",
        }
    except Exception as e:
        logger.error(f"Qdrant health check failed: {e}")
        health_status["checks"]["qdrant"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"
    
    # Check LLM
    try:
        llm = LLMClient()
        llm_healthy = llm.health_check()
        health_status["checks"]["llm"] = {
            "status": "healthy" if llm_healthy else "unhealthy",
        }
    except Exception as e:
        logger.error(f"LLM health check failed: {e}")
        health_status["checks"]["llm"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns ready only if all critical services are available.
    """
    try:
        # Check Qdrant
        qdrant = QdrantClient()
        qdrant_ready = qdrant.health_check() and qdrant.collection_exists()
        
        # Check LLM
        llm = LLMClient()
        llm_ready = llm.health_check()
        
        if qdrant_ready and llm_ready:
            return {"status": "ready", "message": "Service is ready to accept requests"}
        else:
            return {
                "status": "not_ready",
                "message": "Service is not ready",
                "details": {
                    "qdrant": "ready" if qdrant_ready else "not_ready",
                    "llm": "ready" if llm_ready else "not_ready",
                }
            }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "status": "not_ready",
            "message": f"Readiness check failed: {str(e)}",
        }