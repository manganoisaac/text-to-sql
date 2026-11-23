"""In-memory schema indexing and semantic retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .providers import EmbeddingProvider, OpenAIEmbedder
from .similarity import _normalize
from .types import RetrievedSchemaObject, SchemaContext, SchemaObject


DEFAULT_SIMILARITY_THRESHOLD = 0.35


@dataclass(frozen=True)
class _IndexedObject:
    metadata: SchemaObject
    embedding: tuple[float, ...]


class InMemorySchemaIndex:
    """Embed schema objects once, then retrieve them by cosine similarity.

    Pass an ``EmbeddingProvider`` implementation to use a different model or a
    deterministic test embedder. By default, vectors are produced by OpenAI's
    ``text-embedding-3-small`` model and kept only in process memory.
    """

    def __init__(
        self,
        schema_context: SchemaContext,
        embedder: EmbeddingProvider | None = None,
    ) -> None:
        self._embedder = embedder if embedder is not None else OpenAIEmbedder()
        objects = _schema_objects(schema_context)
        documents = [_object_document(metadata) for metadata in objects]
        vectors = self._embedder.embed_documents(documents)
        if len(vectors) != len(objects):
            raise ValueError(
                f"Embedder returned {len(vectors)} vectors for "
                f"{len(objects)} schema objects"
            )

        normalized_vectors = [_normalize(vector) for vector in vectors]
        dimensions = {len(vector) for vector in normalized_vectors}
        if len(dimensions) > 1:
            raise ValueError("All schema embeddings must have the same dimensions")

        self._objects = [
            _IndexedObject(metadata=metadata, embedding=vector)
            for metadata, vector in zip(objects, normalized_vectors)
        ]

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        embedder: EmbeddingProvider | None = None,
    ) -> InMemorySchemaIndex:
        """Load the JSON emitted by ``schema_introspector.py`` and embed it."""
        with Path(path).open(encoding="utf-8") as schema_file:
            schema_context = json.load(schema_file)
        return cls(schema_context, embedder=embedder)

    def search(
        self,
        question: str,
        similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
        top_k: int | None = None,
    ) -> list[RetrievedSchemaObject]:
        """Return tables/views scoring at least ``similarity_threshold``.

        Results are ranked by cosine similarity. No below-threshold fallback is
        added; an empty list means no schema object met the configured cutoff.
        """
        if not question.strip():
            raise ValueError("Question must not be empty")
        if not -1.0 <= similarity_threshold <= 1.0:
            raise ValueError("similarity_threshold must be between -1 and 1")
        if top_k is not None and top_k < 1:
            raise ValueError("top_k must be at least 1 when specified")

        query_vector = _normalize(self._embedder.embed_query(question))
        matches: list[RetrievedSchemaObject] = []
        for indexed_object in self._objects:
            if len(indexed_object.embedding) != len(query_vector):
                raise ValueError(
                    "Query and schema embeddings have different dimensions"
                )
            similarity = sum(
                query_value * document_value
                for query_value, document_value in zip(
                    query_vector, indexed_object.embedding
                )
            )
            if similarity >= similarity_threshold:
                match: RetrievedSchemaObject = {
                    **indexed_object.metadata,
                    "similarity": similarity,
                }
                matches.append(match)

        matches.sort(key=lambda item: item["similarity"], reverse=True)
        return matches[:top_k] if top_k is not None else matches


def _schema_objects(schema_context: SchemaContext) -> list[SchemaObject]:
    schemas = schema_context.get("schemas")
    if not isinstance(schemas, list):
        raise ValueError("Schema context must contain a 'schemas' list")

    objects: list[SchemaObject] = []
    for schema_entry in schemas:
        schema_name = schema_entry.get("name")
        if not schema_name:
            continue
        for collection_name in ("tables", "views"):
            for schema_object in schema_entry.get(collection_name, []):
                metadata = {**schema_object, "schema": schema_name}
                metadata.setdefault(
                    "kind", "view" if collection_name == "views" else "table"
                )
                objects.append(metadata)
    if not objects:
        raise ValueError("Schema context contains no tables or views to embed")
    return objects


def _object_document(metadata: SchemaObject) -> str:
    schema = metadata["schema"]
    name = metadata.get("name", "unknown")
    kind = metadata.get("kind", "table")
    lines = [
        f"{kind.title()}: {schema}.{name}",
        f"Description: {metadata.get('description') or 'No description provided.'}",
        "Columns:",
    ]
    for column in metadata.get("columns", []):
        nullability = "nullable" if column.get("nullable", True) else "not nullable"
        detail = (
            f"- {column.get('name')} ({column.get('type', 'unknown type')}, "
            f"{nullability})"
        )
        if column.get("primary_key"):
            detail += "; primary key"
        if column.get("description"):
            detail += f"; {column['description']}"
        if column.get("sample_values"):
            detail += f"; sample values: {column['sample_values']}"
        lines.append(detail)

    primary_key = metadata.get("primary_key") or []
    if primary_key:
        lines.append(f"Primary key columns: {', '.join(primary_key)}")
    for constraint in metadata.get("unique_constraints", []):
        columns = ", ".join(constraint.get("columns", []))
        lines.append(f"Unique columns: {columns}")
    for foreign_key in metadata.get("foreign_keys", []):
        local_columns = ", ".join(foreign_key.get("columns", []))
        remote_columns = ", ".join(foreign_key.get("referred_columns", []))
        lines.append(
            "Foreign key: "
            f"{local_columns} -> "
            f"{foreign_key.get('referred_schema') or schema}."
            f"{foreign_key.get('referred_table')}({remote_columns})"
        )
    if metadata.get("definition"):
        lines.append(f"View definition: {metadata['definition']}")
    return "\n".join(lines)
