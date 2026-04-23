"""
Gemma LLM Client - Local/Offline LLM backend alternative.

Supports Kaggle, Ollama, and HuggingFace backends.
Used as an alternative to OpenAI for offline deployment scenarios.
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

logger = logging.getLogger(__name__)


class GemmaBackendType(Enum):
    KAGGLE = "kaggle"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"


class GemmaLLMClient:
    """Gemma LLM Client for offline AML compliance assistance.

    Provides Thinking Mode for explainable AI - critical for compliance scenarios
    where audit trails are required.
    """

    DEFAULT_MODEL = "gemma-4-26b-a4b"

    def __init__(
        self,
        backend: str = "ollama",
        model: Optional[str] = None,
        **kwargs,
    ):
        self.backend = GemmaBackendType(backend.lower())
        self.model = model or self.DEFAULT_MODEL
        self._model_instance = None
        self._processor = None
        self._initialized = False

    def initialize(self) -> bool:
        """Initialize the LLM backend. Returns True on success."""
        try:
            if self.backend == GemmaBackendType.OLLAMA:
                return self._init_ollama()
            elif self.backend == GemmaBackendType.KAGGLE:
                return self._init_kaggle()
            elif self.backend == GemmaBackendType.HUGGINGFACE:
                return self._init_huggingface()
        except Exception as e:
            logger.error(f"Failed to initialize Gemma backend {self.backend.value}: {e}")
            return False
        return False

    def _init_ollama(self) -> bool:
        try:
            import ollama
            self._ollama = ollama
            models = ollama.list()
            model_names = [m.get("name", "") for m in models.get("models", [])]
            if self.model not in model_names:
                logger.info(f"Pulling model {self.model}...")
                ollama.pull(self.model)
            self._initialized = True
            return True
        except ImportError:
            logger.error("ollama package not installed. Run: pip install ollama")
            return False

    def _init_kaggle(self) -> bool:
        try:
            import kagglehub
            import torch
            from transformers import AutoProcessor, AutoModelForCausalLM, BitsAndBytesConfig

            model_path = kagglehub.model_download(
                f"google/{self.model}/transformers/{self.model}"
            )
            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            self._processor = AutoProcessor.from_pretrained(model_path)
            self._model_instance = AutoModelForCausalLM.from_pretrained(
                model_path, quantization_config=bnb_config, device_map="auto"
            )
            self._initialized = True
            return True
        except ImportError:
            logger.error("Kaggle dependencies not installed")
            return False

    def _init_huggingface(self) -> bool:
        try:
            import torch
            from transformers import AutoProcessor, AutoModelForCausalLM, BitsAndBytesConfig

            bnb_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
                bnb_4bit_use_double_quant=True,
            )
            self._processor = AutoProcessor.from_pretrained(f"google/{self.model}")
            self._model_instance = AutoModelForCausalLM.from_pretrained(
                f"google/{self.model}", quantization_config=bnb_config, device_map="auto"
            )
            self._initialized = True
            return True
        except ImportError:
            logger.error("HuggingFace dependencies not installed")
            return False

    def generate(
        self,
        prompt: str,
        system_prompt: str = "You are an AML compliance expert.",
        context: Optional[str] = None,
        enable_thinking: bool = False,
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Generate a response with optional thinking mode.

        Returns:
            Dict with keys: content, thinking, raw_response, sources
        """
        if not self._initialized:
            return {
                "content": "Error: Gemma client not initialized",
                "thinking": None,
                "raw_response": "",
                "sources": [],
            }

        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "system", "content": f"Context:\n{context}"})
        messages.append({"role": "user", "content": prompt})

        if self.backend == GemmaBackendType.OLLAMA:
            return self._generate_ollama(messages, enable_thinking, temperature, max_tokens)
        else:
            return self._generate_transformers(messages, enable_thinking, temperature, max_tokens)

    def _generate_ollama(
        self,
        messages: List[Dict],
        enable_thinking: bool,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        try:
            import ollama
            response = self._ollama.chat(
                model=self.model,
                messages=messages,
                options={"num_predict": max_tokens, "temperature": temperature},
            )
            content = response.get("message", {}).get("content", "")
            return {
                "content": content,
                "thinking": None,
                "raw_response": content,
                "sources": [],
            }
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return {
                "content": f"Error: {str(e)}",
                "thinking": None,
                "raw_response": "",
                "sources": [],
            }

    def _generate_transformers(
        self,
        messages: List[Dict],
        enable_thinking: bool,
        temperature: float,
        max_tokens: int,
    ) -> Dict[str, Any]:
        try:
            import torch

            text = self._processor.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True,
                enable_thinking=enable_thinking,
            )
            inputs = self._processor(text=text, return_tensors="pt").to(
                self._model_instance.device
            )
            input_len = inputs["input_ids"].shape[-1]

            with torch.no_grad():
                outputs = self._model_instance.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature,
                    do_sample=True,
                )

            raw = self._processor.decode(outputs[0][input_len:], skip_special_tokens=False)
            thinking = None
            content = raw

            if enable_thinking and "<|think|>" in raw:
                think_start = raw.find("<|think|>") + len("<|think|>")
                think_end = raw.find("<|/think|>")
                if think_end > think_start:
                    thinking = raw[think_start:think_end].strip()
                    content = raw[think_end + len("<|/think|>"):].strip()

            content = content.replace("<|end|>", "").strip()

            return {
                "content": content,
                "thinking": thinking,
                "raw_response": raw,
                "sources": [],
            }
        except Exception as e:
            logger.error(f"Transformers generation failed: {e}")
            return {
                "content": f"Error: {str(e)}",
                "thinking": None,
                "raw_response": "",
                "sources": [],
            }

    def health_check(self) -> bool:
        """Check if the Gemma backend is healthy."""
        return self._initialized

    @property
    def backend_name(self) -> str:
        return f"gemma-{self.backend.value}"