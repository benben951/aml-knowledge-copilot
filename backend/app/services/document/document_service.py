"""
Document Processing Service

Handles document upload, parsing, chunking, embedding, and storage.
"""

import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from langchain.text_splitter import RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
from docx import Document as DocxDocument

from app.infra.vector.qdrant_client import QdrantVectorStore
from app.infra.llm.llm_client import LLMClient
from app.core.config import settings


class DocumentService:
    """Document processing service for RAG pipeline"""
    
    def __init__(self):
        """Initialize document service"""
        self.qdrant = QdrantVectorStore()
        self.llm = LLMClient()
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.MAX_CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", "。", "！", "？", "；", " ", ""],
        )
        
        logger.info("DocumentService initialized")
    
    def _generate_document_id(self, filename: str, content_hash: str) -> str:
        """Generate unique document ID"""
        hash_input = f"{filename}:{content_hash}:{datetime.now().isoformat()}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    def _compute_content_hash(self, content: str) -> str:
        """Compute hash of document content"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def parse_pdf(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse PDF document.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Tuple of (full_text, metadata_list)
        """
        try:
            doc = fitz.open(file_path)
            full_text = ""
            page_metadatas = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                full_text += f"\n\n[第{page_num + 1}页]\n{text}"
                page_metadatas.append({
                    "page": page_num + 1,
                    "text": text,
                })
            
            doc.close()
            logger.info(f"Parsed PDF: {len(doc)} pages, {len(full_text)} chars")
            return full_text, page_metadatas
        except Exception as e:
            logger.error(f"PDF parsing failed: {e}")
            raise
    
    def parse_docx(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse DOCX document.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Tuple of (full_text, metadata_list)
        """
        try:
            doc = DocxDocument(file_path)
            full_text = ""
            paragraphs = []
            
            for i, para in enumerate(doc.paragraphs):
                text = para.text.strip()
                if text:
                    full_text += f"\n\n{text}"
                    paragraphs.append({
                        "paragraph_index": i,
                        "text": text,
                    })
            
            logger.info(f"Parsed DOCX: {len(paragraphs)} paragraphs, {len(full_text)} chars")
            return full_text, paragraphs
        except Exception as e:
            logger.error(f"DOCX parsing failed: {e}")
            raise
    
    def parse_txt(self, file_path: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse TXT document.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            Tuple of (full_text, metadata_list)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            logger.info(f"Parsed TXT: {len(content)} chars")
            return content, [{"text": content}]
        except Exception as e:
            logger.error(f"TXT parsing failed: {e}")
            raise
    
    def parse_document(self, file_path: str, file_type: str) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Parse document based on file type.
        
        Args:
            file_path: Path to document file
            file_type: File extension (pdf, docx, txt)
            
        Returns:
            Tuple of (full_text, metadata_list)
        """
        file_type = file_type.lower()
        
        if file_type == "pdf":
            return self.parse_pdf(file_path)
        elif file_type == "docx":
            return self.parse_docx(file_path)
        elif file_type == "txt":
            return self.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
    
    def chunk_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks.
        
        Args:
            text: Full text to split
            metadata: Optional metadata to attach to each chunk
            
        Returns:
            List of chunk dicts with 'text' and 'metadata'
        """
        try:
            chunks = self.text_splitter.split_text(text)
            
            chunk_dicts = []
            for i, chunk in enumerate(chunks):
                chunk_dict = {
                    "chunk_index": i,
                    "text": chunk,
                    "chunk_size": len(chunk),
                }
                if metadata:
                    chunk_dict.update(metadata)
                chunk_dicts.append(chunk_dict)
            
            logger.info(f"Split text into {len(chunks)} chunks")
            return chunk_dicts
        except Exception as e:
            logger.error(f"Text chunking failed: {e}")
            raise
    
    def process_document(
        self,
        file_path: str,
        filename: str,
        file_type: str,
        document_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process document: parse, chunk, embed, and store.
        
        Args:
            file_path: Path to document file
            filename: Original filename
            file_type: File extension
            document_id: Optional document ID (auto-generated if not provided)
            
        Returns:
            Processing result with document info
        """
        try:
            logger.info(f"Processing document: {filename}")
            
            # Parse document
            full_text, page_metadata = self.parse_document(file_path, file_type)
            content_hash = self._compute_content_hash(full_text)
            
            if not document_id:
                document_id = self._generate_document_id(filename, content_hash)
            
            # Chunk text
            chunks = self.chunk_text(
                full_text,
                metadata={
                    "document_id": document_id,
                    "filename": filename,
                    "file_type": file_type,
                    "content_hash": content_hash,
                }
            )
            
            # Generate embeddings
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = self.llm.embed_texts(chunk_texts)
            
            # Prepare payloads for Qdrant
            payloads = []
            for chunk, embedding in zip(chunks, embeddings):
                payload = {
                    "document_id": chunk["document_id"],
                    "filename": chunk["filename"],
                    "file_type": chunk["file_type"],
                    "content_hash": chunk["content_hash"],
                    "chunk_index": chunk["chunk_index"],
                    "chunk_size": chunk["chunk_size"],
                    "text": chunk["text"],
                    "embedding": embedding,  # Store embedding for reference
                }
                # Add page info if available
                if "page" in chunk:
                    payload["page"] = chunk["page"]
                if "paragraph_index" in chunk:
                    payload["paragraph_index"] = chunk["paragraph_index"]
                
                payloads.append(payload)
            
            # Upsert to Qdrant (without storing the embedding in payload)
            upsert_success = self.qdrant.upsert(
                vectors=embeddings,
                payloads=[{k: v for k, v in p.items() if k != "embedding"} for p in payloads],
            )
            
            if not upsert_success:
                raise Exception("Failed to upsert vectors to Qdrant")
            
            logger.info(f"Document processed successfully: {document_id}, {len(chunks)} chunks")
            
            return {
                "document_id": document_id,
                "filename": filename,
                "file_type": file_type,
                "chunks_count": len(chunks),
                "content_hash": content_hash,
                "status": "completed",
            }
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise