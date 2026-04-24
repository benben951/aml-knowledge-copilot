"""
LLM Client

Provides interface for:
- Text generation (chat/completion)
- Text embedding
"""

from typing import List, Optional, Dict, Any
from loguru import logger
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from app.core.config import settings


class LLMClient:
    """LLM client wrapper using LangChain OpenAI"""
    
    _instance: Optional["LLMClient"] = None
    _chat_model: Optional[ChatOpenAI] = None
    _embeddings_model: Optional[OpenAIEmbeddings] = None
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern to reuse models"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize LLM clients"""
        if hasattr(self, "_initialized"):
            return
        
        if not settings.OPENAI_API_KEY:
            logger.error("OPENAI_API_KEY not configured")
            raise ValueError("OPENAI_API_KEY is required")
        
        # Initialize chat model for text generation
        self._chat_model = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            temperature=0.3,  # Lower temperature for factual accuracy
            streaming=False,
        )
        
        # Initialize embeddings model
        self._embeddings_model = OpenAIEmbeddings(
            model=settings.OPENAI_EMBEDDING_MODEL,
        )
        
        self._initialized = True
        logger.info(f"LLMClient initialized with model: {settings.OPENAI_MODEL}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate text response from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Override default temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text response
        """
        try:
            chat_model = self._chat_model
            if temperature is not None:
                chat_model = chat_model.bind(temperature=temperature)
            if max_tokens is not None:
                chat_model = chat_model.bind(max_tokens=max_tokens)
            
            messages = []
            if system_prompt:
                messages.append(("system", system_prompt))
            messages.append(("human", prompt))
            
            response = chat_model.invoke(messages)
            
            # Handle different response types
            if hasattr(response, "content"):
                result = response.content
            else:
                result = str(response)
            
            logger.debug(f"LLM generated response ({len(result)} chars)")
            return result
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise
    
    def generate_with_context(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate response with conversation history.
        
        Args:
            system_prompt: System prompt
            messages: List of message dicts with 'role' and 'content'
            temperature: Override default temperature
            
        Returns:
            Generated text response
        """
        try:
            chat_model = self._chat_model
            if temperature is not None:
                chat_model = chat_model.bind(temperature=temperature)
            
            formatted_messages = [("system", system_prompt)]
            for msg in messages:
                role = msg.get("role", "human")
                if role == "assistant":
                    role = "ai"
                formatted_messages.append((role, msg["content"]))
            
            response = chat_model.invoke(formatted_messages)
            
            if hasattr(response, "content"):
                result = response.content
            else:
                result = str(response)
            
            return result
        except Exception as e:
            logger.error(f"LLM context generation failed: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        try:
            embedding = self._embeddings_model.embed_query(text)
            logger.debug(f"Generated embedding for {len(text)} chars")
            return embedding
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self._embeddings_model.embed_documents(texts)
            logger.debug(f"Generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """
        Check LLM connection health.
        
        Returns:
            True if connection is healthy
        """
        try:
            # Simple test generation
            test_response = self.generate("Say 'OK' if you can hear me.")
            return "OK" in test_response
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False

def get_llm_client() -> "LLMClient":
    """Factory function to get an LLMClient instance (singleton)."""
    return LLMClient()
