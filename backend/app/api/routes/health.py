"""
Health Check Router

Provides health check endpoints for monitoring and load balancers.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "aml-knowledge-copilot"}


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint."""
    # TODO: Check database and Qdrant connections
    return {"status": "ready"}