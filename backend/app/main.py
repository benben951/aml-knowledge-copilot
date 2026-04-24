"""FastAPI Main Application Entry Point"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.infra.vector.qdrant_client import QdrantVectorStore
from app.api.routes import documents, health, query

# Configure logging
logger.add(
    "logs/app.log",
    rotation="10 MB",
    retention="7 days",
    level=settings.LOG_LEVEL,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Handle application startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME}...")
    
    # Initialize Qdrant collection
    try:
        qdrant = QdrantVectorStore()
        collection_created = qdrant.create_collection()
        
        if collection_created:
            logger.info("Qdrant collection initialized successfully")
        else:
            logger.warning("Failed to initialize Qdrant collection")
    except Exception as e:
        logger.error(f"Failed to initialize Qdrant: {e}")
    
    logger.info("Application startup complete")
    
    try:
        yield
    finally:
        logger.info("Shutting down application...")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="AML/DD Compliance Knowledge Q&A Agent with RAG",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(query.router, prefix="/api/query", tags=["Query"])
app.include_router(health.router, prefix="/api", tags=["Health"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"{settings.APP_NAME} API",
        "version": "0.1.0",
        "docs": "/api/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )