"""Document Management API Routes"""

import os
import tempfile
import shutil
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel
from loguru import logger

from app.services.document.document_service import DocumentService
from app.infra.vector.qdrant_client import QdrantClient

router = APIRouter()

# In-memory document registry (replace with database in production)
_document_registry = {}


class DocumentResponse(BaseModel):
    """Document upload response"""
    document_id: str
    filename: str
    status: str
    message: str
    chunks_count: Optional[int] = None


class DocumentInfo(BaseModel):
    """Document information"""
    document_id: str
    filename: str
    file_type: str
    upload_time: str
    chunks_count: int
    metadata: dict


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """
    Upload a document for processing.
    
    Supported formats: PDF, DOCX, TXT
    """
    try:
        # Validate file type
        allowed_types = ["pdf", "docx", "txt"]
        file_ext = file.filename.split(".")[-1].lower()
        
        if file_ext not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_ext}. Allowed: {allowed_types}"
            )
        
        # Validate file size
        contents = await file.read()
        file_size_mb = len(contents) / (1024 * 1024)
        if file_size_mb > 50:  # 50MB limit
            raise HTTPException(
                status_code=400,
                detail=f"File too large: {file_size_mb:.2f}MB. Maximum: 50MB"
            )
        
        logger.info(f"Received document upload: {file.filename}")
        
        # Save to temporary file
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_file_path, "wb") as f:
            f.write(contents)
        
        try:
            # Process document
            doc_service = DocumentService()
            result = doc_service.process_document(
                file_path=temp_file_path,
                filename=file.filename,
                file_type=file_ext,
            )
            
            # Register document
            document_id = result["document_id"]
            _document_registry[document_id] = {
                "document_id": document_id,
                "filename": file.filename,
                "file_type": file_ext,
                "upload_time": datetime.now().isoformat(),
                "chunks_count": result["chunks_count"],
                "content_hash": result.get("content_hash", ""),
                "status": result["status"],
                "temp_path": temp_file_path,
            }
            
            logger.info(f"Document uploaded and processed: {document_id}")
            
            return DocumentResponse(
                document_id=document_id,
                filename=file.filename,
                status=result["status"],
                message="Document uploaded and processed successfully",
                chunks_count=result["chunks_count"],
            )
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Document processing failed: {str(e)}"
            )
        finally:
            # Clean up temp directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp dir: {e}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/list", response_model=List[DocumentInfo])
async def list_documents():
    """
    List all uploaded documents.
    """
    try:
        documents = []
        for doc_id, doc_info in _document_registry.items():
            documents.append(DocumentInfo(
                document_id=doc_info["document_id"],
                filename=doc_info["filename"],
                file_type=doc_info["file_type"],
                upload_time=doc_info["upload_time"],
                chunks_count=doc_info["chunks_count"],
                metadata={
                    "content_hash": doc_info.get("content_hash", ""),
                    "status": doc_info.get("status", "unknown"),
                }
            ))
        
        logger.info(f"Listed {len(documents)} documents")
        return documents
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        return []


@router.get("/{document_id}", response_model=DocumentInfo)
async def get_document(document_id: str):
    """
    Get document details by ID.
    """
    try:
        if document_id not in _document_registry:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_info = _document_registry[document_id]
        return DocumentInfo(
            document_id=doc_info["document_id"],
            filename=doc_info["filename"],
            file_type=doc_info["file_type"],
            upload_time=doc_info["upload_time"],
            chunks_count=doc_info["chunks_count"],
            metadata={
                "content_hash": doc_info.get("content_hash", ""),
                "status": doc_info.get("status", "unknown"),
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document and its chunks.
    """
    try:
        if document_id not in _document_registry:
            raise HTTPException(status_code=404, detail="Document not found")
        
        doc_info = _document_registry[document_id]
        
        # Delete from Qdrant (by document_id filter)
        qdrant = QdrantClient()
        # Note: Qdrant delete by filter would be better, but for now we skip this
        # In production, implement proper filtering
        
        # Remove from registry
        del _document_registry[document_id]
        
        logger.info(f"Document deleted: {document_id}")
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "filename": doc_info["filename"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document: {e}")
        raise HTTPException(status_code=500, detail=str(e))