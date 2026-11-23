"""Embedding provider interfaces and implementations."""

import re
from collections.abc import Sequence
from typing import Protocol

from openai import OpenAI


DEFAULT_MODEL = "text-embedding-3-small"


class EmbeddingProvider(Protocol):
    """Interface implemented by any text embedding service or local model."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        """Embed a batch of schema documents in input order."""

    def embed_query(self, text: str) -> list[float]:
        """Embed one user question in the same vector space as documents."""


class OpenAIEmbedder:
    """OpenAI embeddings API adapter; requires a separate OpenAI API credential."""

    def __init__(self, model: str = DEFAULT_MODEL, client: OpenAI | None = None):
        self.model = model
        self._client = client if client is not None else OpenAI()

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        cleaned = [_clean_text(text) for text in texts]
        if not cleaned:
            return []
        if any(not text for text in cleaned):
            raise ValueError("Embedding input text must not be empty")

        response = self._client.embeddings.create(
            model=self.model,
            input=cleaned,
            encoding_format="float",
        )
        ordered = sorted(response.data, key=lambda item: item.index)
        if len(ordered) != len(cleaned):
            raise RuntimeError(
                "Embedding API returned "
                f"{len(ordered)} vectors for {len(cleaned)} texts"
            )
        return [list(item.embedding) for item in ordered]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_documents([text])[0]


class FakeEmbedder:
    """Deterministic keyword-based embedder for tests and local wiring checks."""

    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]:
        return [self._vector(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)

    @staticmethod
    def _vector(text: str) -> list[float]:
        return [1.0, 0.0] if "customer" in text.lower() else [0.0, 1.0]


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()
