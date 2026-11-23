"""Schema embedding and semantic retrieval utilities."""

from .formatting import format_schema_context
from .providers import DEFAULT_MODEL, EmbeddingProvider, FakeEmbedder, OpenAIEmbedder
from .schema_index import DEFAULT_SIMILARITY_THRESHOLD, InMemorySchemaIndex
from .similarity import text_cosine_similarity
from .types import RetrievedSchemaObject, SchemaContext, SchemaObject

__all__ = [
    "DEFAULT_MODEL",
    "DEFAULT_SIMILARITY_THRESHOLD",
    "EmbeddingProvider",
    "FakeEmbedder",
    "InMemorySchemaIndex",
    "OpenAIEmbedder",
    "RetrievedSchemaObject",
    "SchemaContext",
    "SchemaObject",
    "format_schema_context",
    "text_cosine_similarity",
]
