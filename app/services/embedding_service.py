from functools import lru_cache

import numpy as np

from fastembed import TextEmbedding


class EmbeddingService:
    """Stateless embedding wrapper"""

    def __init__(self):
        # ~22MB ONNX model, downloaded on first use and cached
        self.model = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")

    def embed(self, text: str) -> np.ndarray:
        """Return a normalized embedding vector for the given text."""
        return next(self.model.embed([text]))

    def similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity via dot product (vectors are already L2-normalized)."""
        return float(np.dot(a, b))


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
