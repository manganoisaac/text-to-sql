import unittest
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from embedding import (
    InMemorySchemaIndex,
    OpenAIEmbedder,
    format_schema_context,
    text_cosine_similarity,
)


class FakeEmbedder:
    def embed_documents(self, texts):
        return [
            [1.0, 0.0] if text.startswith("Table: retail.customers") else [0.0, 1.0]
            for text in texts
        ]

    def embed_query(self, text):
        return [1.0, 0.0]


class PairEmbedder:
    def __init__(self, vectors):
        self.vectors = vectors
        self.texts = None

    def embed_documents(self, texts):
        self.texts = list(texts)
        return self.vectors

    def embed_query(self, text):
        raise NotImplementedError


class FakeOpenAIClient:
    def __init__(self):
        self.embeddings = self
        self.request = None

    def create(self, **kwargs):
        self.request = kwargs
        return SimpleNamespace(
            data=[
                SimpleNamespace(index=1, embedding=[0.0, 1.0]),
                SimpleNamespace(index=0, embedding=[1.0, 0.0]),
            ]
        )


class InMemorySchemaIndexTests(unittest.TestCase):
    def setUp(self):
        self.schema_context = {
            "schemas": [
                {
                    "name": "retail",
                    "tables": [
                        {
                            "name": "customers",
                            "kind": "table",
                            "description": "Customer accounts.",
                            "columns": [
                                {
                                    "name": "segment",
                                    "type": "TEXT",
                                    "nullable": False,
                                    "description": "Customer business grouping.",
                                    "sample_values": ["consumer", "business"],
                                }
                            ],
                            "primary_key": ["customer_id"],
                            "foreign_keys": [],
                        },
                        {
                            "name": "orders",
                            "kind": "table",
                            "description": "Orders placed by customers.",
                            "columns": [],
                            "primary_key": ["order_id"],
                            "foreign_keys": [],
                        },
                    ],
                    "views": [],
                }
            ]
        }

    def test_search_returns_only_objects_above_threshold(self):
        index = InMemorySchemaIndex(self.schema_context, embedder=FakeEmbedder())

        matches = index.search("Which customer segment has the most orders?", 0.8)

        self.assertEqual([match["name"] for match in matches], ["customers"])
        self.assertGreaterEqual(matches[0]["similarity"], 0.8)
        self.assertEqual(
            matches[0]["columns"][0]["sample_values"], ["consumer", "business"]
        )

    def test_search_serializes_retrieved_context(self):
        index = InMemorySchemaIndex(self.schema_context, embedder=FakeEmbedder())
        context = format_schema_context(index.search("customers", 0.8))

        self.assertIn('"description": "Customer accounts."', context)
        self.assertIn('"similarity":', context)

    def test_invalid_threshold_is_rejected(self):
        index = InMemorySchemaIndex(self.schema_context, embedder=FakeEmbedder())

        with self.assertRaisesRegex(ValueError, "between -1 and 1"):
            index.search("customers", 1.1)

    def test_openai_adapter_batches_and_preserves_input_order(self):
        client = FakeOpenAIClient()
        embedder = OpenAIEmbedder(client=client)

        vectors = embedder.embed_documents([" first\ntext ", "second text"])

        self.assertEqual(vectors, [[1.0, 0.0], [0.0, 1.0]])
        self.assertEqual(client.request["model"], "text-embedding-3-small")
        self.assertEqual(client.request["input"], ["first text", "second text"])

    def test_text_cosine_similarity_uses_one_batch_for_both_texts(self):
        embedder = PairEmbedder([[3.0, 0.0], [0.0, 2.0]])

        similarity = text_cosine_similarity("question", "backcheck", embedder)

        self.assertEqual(similarity, 0.0)
        self.assertEqual(embedder.texts, ["question", "backcheck"])

    def test_text_cosine_similarity_returns_one_for_matching_vectors(self):
        embedder = PairEmbedder([[1.0, 2.0], [2.0, 4.0]])

        similarity = text_cosine_similarity("same", "same meaning", embedder)

        self.assertAlmostEqual(similarity, 1.0)

    def test_text_cosine_similarity_rejects_empty_text(self):
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            text_cosine_similarity("question", "  ", PairEmbedder([]))


if __name__ == "__main__":
    unittest.main()
