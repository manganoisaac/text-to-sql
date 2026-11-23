import unittest

from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table, create_engine

from schema_introspector import extract_schema


class SchemaIntrospectorTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        metadata = MetaData()
        self.customers = Table(
            "customers",
            metadata,
            Column("customer_id", Integer, primary_key=True),
            Column("segment", String(32), nullable=False),
            Column("email", String(128), nullable=False),
        )
        self.orders = Table(
            "orders",
            metadata,
            Column("order_id", Integer, primary_key=True),
            Column("customer_id", ForeignKey("customers.customer_id"), nullable=False),
            Column("status", String(24), nullable=False),
            Column("rating", Integer),
        )
        metadata.create_all(self.engine)
        with self.engine.begin() as connection:
            connection.execute(
                self.customers.insert(),
                [
                    {"customer_id": 1, "segment": "consumer", "email": "a@example.test"},
                    {"customer_id": 2, "segment": "business", "email": "b@example.test"},
                ],
            )
            connection.execute(
                self.orders.insert(),
                [
                    {"order_id": 10, "customer_id": 1, "status": "paid", "rating": 5},
                    {"order_id": 11, "customer_id": 2, "status": "pending", "rating": 4},
                ],
            )

    def tearDown(self):
        self.engine.dispose()

    def test_extracts_columns_keys_and_categorical_samples(self):
        result = extract_schema(self.engine)
        main_schema = next(item for item in result["schemas"] if item["name"] == "main")
        tables = {table["name"]: table for table in main_schema["tables"]}

        customer_columns = {column["name"]: column for column in tables["customers"]["columns"]}
        self.assertEqual(tables["customers"]["primary_key"], ["customer_id"])
        self.assertEqual(customer_columns["segment"]["sample_values"], ["business", "consumer"])
        self.assertFalse(customer_columns["email"]["is_categorical"])

        order_table = tables["orders"]
        self.assertEqual(order_table["foreign_keys"][0]["referred_table"], "customers")
        order_columns = {column["name"]: column for column in order_table["columns"]}
        self.assertEqual(order_columns["status"]["sample_values"], ["paid", "pending"])
        self.assertEqual(order_columns["rating"]["sample_values"], [4, 5])

    def test_rejects_unknown_schema(self):
        with self.assertRaisesRegex(ValueError, "was not found"):
            extract_schema(self.engine, schema="missing")

    def test_rejects_invalid_distinct_value_limit(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            extract_schema(self.engine, max_distinct_values=0)

    def test_omits_columns_above_the_distinct_value_limit(self):
        result = extract_schema(self.engine, max_distinct_values=1)
        main_schema = next(item for item in result["schemas"] if item["name"] == "main")
        customers = next(table for table in main_schema["tables"] if table["name"] == "customers")
        segment = next(column for column in customers["columns"] if column["name"] == "segment")
        self.assertFalse(segment["is_categorical"])
        self.assertIsNone(segment["sample_values"])


if __name__ == "__main__":
    unittest.main()
