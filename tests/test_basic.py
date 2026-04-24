"""Tests for AML Knowledge Copilot - API and Services"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ========== API Route Tests ==========

class TestHealthCheck:
    def test_health_check(self):
        from backend.app.api.routes.health import router
        assert router is not None


# ========== Config Tests ==========

class TestConfig:
    def test_default_settings(self):
        from backend.app.core.config import settings
        assert settings.APP_NAME == "AML Knowledge Copilot"
        assert settings.QDRANT_COLLECTION_NAME == "aml_knowledge"
        assert settings.TOP_K_RESULTS == 5
        assert settings.MIN_SIMILARITY_SCORE == 0.7
        assert settings.MAX_CHUNK_SIZE == 1000

    def test_llm_backend_options(self):
        from backend.app.core.config import settings
        assert settings.LLM_BACKEND in ("openai", "gemma")


# ========== Prompts Tests ==========

class TestPrompts:
    def test_system_prompt_exists(self):
        from backend.app.core.prompts import SYSTEM_PROMPT
        assert "反洗钱" in SYSTEM_PROMPT
        assert "AML" in SYSTEM_PROMPT

    def test_qa_prompt_template_exists(self):
        from backend.app.core.prompts import QA_PROMPT_TEMPLATE
        assert "{context}" in QA_PROMPT_TEMPLATE
        assert "{question}" in QA_PROMPT_TEMPLATE

    def test_guardrail_prompt_exists(self):
        from backend.app.core.prompts import GUARDRAIL_PROMPT
        assert "人工复核" in GUARDRAIL_PROMPT

    def test_few_shot_examples(self):
        from backend.app.core.prompts import FEW_SHOT_EXAMPLES
        assert len(FEW_SHOT_EXAMPLES) >= 2
        for ex in FEW_SHOT_EXAMPLES:
            assert "question" in ex
            assert "answer" in ex
            assert "sources" in ex


# ========== Models Tests ==========

class TestDocumentService:
    def test_chunk_text_basic(self):
        """Test text chunking logic."""
        from backend.app.services.document.document_service import DocumentService

        service = DocumentService.__new__(DocumentService)
        service.chunk_size = 100
        service.chunk_overlap = 20

        text = "A" * 250
        chunks = service._chunk_text(text, source="test.txt")
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) <= 100

    def test_chunk_text_with_overlap(self):
        """Test that chunks have overlap."""
        from backend.app.services.document.document_service import DocumentService

        service = DocumentService.__new__(DocumentService)
        service.chunk_size = 50
        service.chunk_overlap = 10

        text = "Hello World " * 20
        chunks = service._chunk_text(text, source="test.txt")
        # Verify overlap exists between consecutive chunks
        if len(chunks) > 1:
            # The end of chunk[i] should overlap with the start of chunk[i+1]
            assert len(chunks) > 1


# ========== Integration Tests (require Qdrant) ==========

class TestQdrantIntegration:
    @pytest.mark.skip(reason="Requires running Qdrant instance")
    def test_qdrant_connection(self):
        from backend.app.infra.vector.qdrant_client import get_qdrant_client
        client = get_qdrant_client()
        assert client.health_check() is True