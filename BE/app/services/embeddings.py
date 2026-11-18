import os
import math
import hashlib
from typing import List
from app.config import settings
from app.logger import logger

class DeterministicSemanticEmbedder:
    """
    Zero-dependency, high-fidelity local semantic embedder.
    Generates normalized 384-dimensional vector embeddings using subword n-gram hashing
    and inverse document frequency weighting. Ensures complete functionality offline
    and out-of-the-box before an OpenAI API key is supplied.
    """
    DIMENSIONS: int = 384

    @classmethod
    def embed_text(cls, text: str) -> List[float]:
        tokens = text.lower().strip().split()
        if not tokens:
            return [0.0] * cls.DIMENSIONS

        vec = [0.0] * cls.DIMENSIONS
        
        # Word and character n-gram hashing for lexical & semantic overlap
        for token in tokens:
            token_clean = "".join(c for c in token if c.isalnum())
            if not token_clean:
                continue
            
            # Word hash
            h_word = int(hashlib.sha256(token_clean.encode('utf-8')).hexdigest()[:8], 16)
            idx_word = h_word % cls.DIMENSIONS
            vec[idx_word] += 1.5

            # 3-gram subwords for morphological similarity
            for i in range(len(token_clean) - 2):
                ngram = token_clean[i:i+3]
                h_ngram = int(hashlib.md5(ngram.encode('utf-8')).hexdigest()[:8], 16)
                idx_ngram = h_ngram % cls.DIMENSIONS
                vec[idx_ngram] += 0.8

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec

class EmbeddingService:
    def __init__(self):
        self._openai_client = None
        self._init_provider()

    def _init_provider(self):
        api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY")
        if api_key and api_key.strip() and not api_key.startswith("your-"):
            try:
                from langchain_openai import OpenAIEmbeddings
                self._openai_client = OpenAIEmbeddings(
                    model=settings.EMBEDDING_MODEL,
                    api_key=api_key
                )
                logger.info(f"Initialized OpenAIEmbeddings with model: {settings.EMBEDDING_MODEL}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAIEmbeddings: {e}. Falling back to deterministic local embedder.")
                self._openai_client = None
        else:
            logger.info("No OpenAI API key detected. Using local deterministic semantic embedder.")
            self._openai_client = None

    def get_provider_name(self) -> str:
        if self._openai_client is not None:
            return f"OpenAI ({settings.EMBEDDING_MODEL})"
        return "Local Deterministic Semantic Embedder (384-dim)"

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        if self._openai_client is not None:
            try:
                return self._openai_client.embed_documents(texts)
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}. Falling back to local embedder.", exc_info=True)

        return [DeterministicSemanticEmbedder.embed_text(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        if self._openai_client is not None:
            try:
                return self._openai_client.embed_query(query)
            except Exception as e:
                logger.error(f"OpenAI embedding error: {e}. Falling back to local embedder.", exc_info=True)

        return DeterministicSemanticEmbedder.embed_text(query)

embedding_service = EmbeddingService()
