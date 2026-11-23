# Text-to-SQL sample database

This project contains a PostgreSQL retail/e-commerce database with customers, addresses, a product catalog, suppliers, inventory, promotions, orders, payments, shipments, returns, and product reviews. It includes relational constraints, useful indexes, reporting views, and deterministic seed data (90 orders and related records across 2024–2025).

## Load with `psql`

Run from this directory against a fresh local PostgreSQL database:

```bash
createdb text2sql_sample
psql -v ON_ERROR_STOP=1 -d text2sql_sample -f sample_ecommerce.sql
```

The script creates a `retail` schema and does not drop existing data. To inspect it:

```bash
psql -d text2sql_sample
```

Then, for example:

```sql
SET search_path TO retail, public;
SELECT * FROM order_totals ORDER BY total DESC LIMIT 10;
SELECT * FROM monthly_sales ORDER BY sales_month, category_name;
```

## Example Text-to-SQL questions

- Which five customers have the highest fulfilled order value?
- What is the monthly net sales by product category and sales channel?
- Which products are below their reorder point in each warehouse?
- Which suppliers provide each product, and which one is preferred?
- What percentage of orders from each channel were cancelled?
- Which promotions generated the most orders and net sales?
- What is the average rating and review count for each product?
- Which returned items have been refunded, and how much was refunded?
- What is the average time between order placement and delivery by carrier?
- Which customer segments have the highest average order value?

## Auto-extract schema context with SQLAlchemy

The introspector reflects tables and views with SQLAlchemy's Inspector and emits a JSON description with table and column descriptions, column types, nullability, primary keys, foreign keys, unique constraints, view definitions, and bounded sample values for low-cardinality columns. It excludes obvious personal/free-text fields (such as emails and review bodies) from value sampling. PostgreSQL comments are maintained in `column_descriptions.sql` and `table_descriptions.sql`; the main seed script includes both files automatically.

Install the Python dependencies:

```bash
python -m pip install -r requirements.txt
```

Point it at the sample database and write the extracted context to a file:

```bash
export DATABASE_URL='postgresql+psycopg://isaac@/text2sql_sample'
python schema_introspector.py --schema retail --output schema_context.json
```

Omit `--schema retail` to inspect all non-system schemas. `--max-distinct-values` controls the maximum number of unique values included for each categorical column (default: `20`). Use the resulting JSON as structured schema context for the LLM. The Python API is also available as `extract_schema(engine, schema="retail")` from `schema_introspector.py`.

The checked-in `schema_context.json` is an example snapshot generated from the sample database; regenerate it after changing the database or seed data.

To add the descriptions to an already-created sample database without rebuilding it:

```bash
psql -v ON_ERROR_STOP=1 -d text2sql_sample -f column_descriptions.sql
psql -v ON_ERROR_STOP=1 -d text2sql_sample -f table_descriptions.sql
```

In `psql`, inspect a table and its descriptions with `\d+ retail.orders`; inspect views with `\dv+ retail.*`.

Run the tests with:

```bash
uv run python -m unittest discover -s tests
```

## In-memory schema retrieval

The semantic retriever in `src/embedding.py` embeds table and view descriptions, columns, sample values, and foreign-key relationships once when the index is created. It then embeds each user question and returns only schema objects at or above the configured cosine-similarity threshold.

The OpenAI adapter uses `text-embedding-3-small` and needs an OpenAI API key (separate from an OpenCode subscription):

```bash
export OPENAI_API_KEY='your-openai-api-key'
uv run python - <<'PY'
import sys

sys.path.insert(0, "src")
from embedding import InMemorySchemaIndex, format_schema_context

index = InMemorySchemaIndex.from_file("schema_context.json")
matches = index.search(
    "Which product categories have the highest sales?",
    similarity_threshold=0.35,
)
print(format_schema_context(matches))
PY
```

Vectors are held in memory and recomputed at startup. The threshold is model- and data-dependent; tune it with representative questions. Pass a different implementation of the `EmbeddingProvider` protocol to use a local model or another embedding service.

`src/enrichment.py` adds up to five live example rows per retrieved table or view. Table rows are ordered by primary key when available; common personal and free-text columns are redacted by default. The shared JSON context and enrichment shapes are typed in `src/types.py`. To build and print the prompt:

```bash
export DATABASE_URL='postgresql+psycopg:///text2sql_sample'
uv run src/main.py
```

`src/main.py` uses `FakeEmbedder` for local wiring/testing, so it does not require an OpenAI API key. The fake is keyword-based and is not suitable for semantic retrieval. Replace it with `OpenAIEmbedder()` when using real embeddings. The prompt builder keeps retrieval results structured while enrichment runs, then serializes them for the prompt only at the end.

Before SQL generation, an LLM classifies the question's complexity. Simple questions use one SQL generation call. Complex questions are sent concurrently to two generation strategies (direct SQL and stepwise/CTE-oriented); normalized SQL agreement is included as an additional score in the returned confidence. Disagreement lowers confidence but does not by itself block the query.

## Notes

- Monetary amounts use `NUMERIC`, and order-item tax defaults to 10% (GST-style example data).
- `order_totals`, `monthly_sales`, and `customer_summary` are reporting views.
- The data is synthetic and intended for development, demos, and SQL practice.
