import unittest
import sys
from pathlib import Path

from sqlalchemy import Column, Integer, MetaData, String, Table, create_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from enrichment import enrich_context


class EnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        metadata = MetaData()
        self.customers = Table(
            "customers",
            metadata,
            Column("customer_id", Integer, primary_key=True),
            Column("email", String(120), nullable=False),
            Column("city", String(40), nullable=False),
        )
        metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.execute(
                self.customers.insert(),
                [
                    {
                        "customer_id": customer_id,
                        "email": f"customer{customer_id}@example.test",
                        "city": "Melbourne",
                    }
                    for customer_id in range(1, 8)
                ],
            )

        self.context: list[dict[str, object]] = [
            {
                "schema": "main",
                "name": "customers",
                "kind": "table",
                "similarity": 0.91,
                "primary_key": ["customer_id"],
                "foreign_keys": [],
                "columns": [],
            }
        ]

    def tearDown(self):
        self.engine.dispose()

    def test_samples_at_most_five_rows_in_primary_key_order_and_redacts_email(self):
        result = enrich_context(self.context, self.engine)

        rows = result[0]["sample_rows"]
        self.assertEqual([row["customer_id"] for row in rows], [1, 2, 3, 4, 5])
        self.assertTrue(all(row["email"] == "[REDACTED]" for row in rows))
        self.assertEqual(result[0]["similarity"], 0.91)
        self.assertNotIn("sample_rows", self.context[0])

    def test_can_request_fewer_sample_rows_or_disable_them(self):
        self.assertEqual(
            len(enrich_context(self.context, self.engine, max_rows_per_object=2)[0]["sample_rows"]),
            2,
        )
        self.assertEqual(
            enrich_context(self.context, self.engine, max_rows_per_object=0)[0]["sample_rows"],
            [],
        )

    def test_rejects_a_limit_over_five(self):
        with self.assertRaisesRegex(ValueError, "between 0 and 5"):
            enrich_context(self.context, self.engine, max_rows_per_object=6)


if __name__ == "__main__":
    unittest.main()
