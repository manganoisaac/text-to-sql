"""Vector normalization and text similarity calculations."""

import math
from collections.abc import Sequence

from .providers import EmbeddingProvider, OpenAIEmbedder


def text_cosine_similarity(
    text_a: str,
    text_b: str,
    embedder: EmbeddingProvider | None = None,
) -> float:
    """Return cosine similarity for two texts embedded by the same provider."""
    if not text_a.strip() or not text_b.strip():
        raise ValueError("Texts must not be empty")

    provider = embedder if embedder is not None else OpenAIEmbedder()
    vectors = provider.embed_documents([text_a, text_b])
    if len(vectors) != 2:
        raise ValueError("Embedder must return exactly two vectors")

    vector_a = _normalize(vectors[0])
    vector_b = _normalize(vectors[1])
    if len(vector_a) != len(vector_b):
        raise ValueError("Text embeddings must have the same dimensions")

    return sum(value_a * value_b for value_a, value_b in zip(vector_a, vector_b))


def _normalize(values: Sequence[float]) -> tuple[float, ...]:
    vector = tuple(float(value) for value in values)
    if not vector:
        raise ValueError("Embedding vector must not be empty")
    if not all(math.isfinite(value) for value in vector):
        raise ValueError("Embedding vector contains a non-finite value")
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0:
        raise ValueError("Embedding vector must have non-zero magnitude")
    return tuple(value / norm for value in vector)
