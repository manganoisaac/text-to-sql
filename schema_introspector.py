"""Reflect a database schema into JSON for use as Text-to-SQL context."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import (
    Boolean,
    Enum,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
    inspect,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


SYSTEM_SCHEMAS = {"information_schema", "pg_catalog", "pg_toast"}

# Avoid putting personal or unstructured text into the LLM's schema context.
NON_CATEGORICAL_NAME = re.compile(
    r"(?:^|_)(?:id|name|email|phone|body|description|title|address|sku|"
    r"reference|tracking|number|postal|line|note|comment|message|content)(?:_|$)",
    re.IGNORECASE,
)
INTEGER_CATEGORY_NAME = re.compile(r"(?:^|_)(?:rating|priority)(?:_|$)", re.IGNORECASE)


def _json_value(value: Any) -> Any:
    """Convert common DBAPI values to JSON-safe values without losing precision."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _is_categorical_candidate(column_name: str, column_type: Any) -> bool:
    if isinstance(column_type, (Boolean, Enum)):
        return True
    if isinstance(column_type, Integer):
        return bool(INTEGER_CATEGORY_NAME.search(column_name))
    if isinstance(column_type, String):
        return NON_CATEGORICAL_NAME.search(column_name) is None
    return False


def _sample_categorical_values(
    connection: Any,
    column: Any,
    max_distinct_values: int,
) -> list[Any] | None:
    """Return distinct values if the column is low-cardinality, otherwise None."""
    statement = (
        select(column)
        .where(column.is_not(None))
        .distinct()
        .order_by(column)
        .limit(max_distinct_values + 1)
    )
    values = connection.execute(statement).scalars().all()
    if len(values) > max_distinct_values:
        return None
    return [_json_value(value) for value in values]


def _column_foreign_keys(
    column_name: str, foreign_keys: list[dict[str, Any]], schema: str
) -> list[dict[str, Any]]:
    references = []
    for foreign_key in foreign_keys:
        constrained_columns = foreign_key.get("constrained_columns") or []
        if column_name not in constrained_columns:
            continue
        referred_columns = foreign_key.get("referred_columns") or []
        column_index = constrained_columns.index(column_name)
        references.append(
            {
                "schema": foreign_key.get("referred_schema") or schema,
                "table": foreign_key.get("referred_table"),
                "column": referred_columns[column_index]
                if column_index < len(referred_columns)
                else None,
            }
        )
    return references


def _reflect_table(
    connection: Any,
    inspector: Any,
    schema: str,
    table_name: str,
    kind: str,
    max_distinct_values: int,
) -> dict[str, Any]:
    reflected = Table(
        table_name,
        MetaData(),
        schema=schema,
        autoload_with=connection,
    )
    primary_key = inspector.get_pk_constraint(table_name, schema=schema).get(
        "constrained_columns", []
    )
    foreign_keys = inspector.get_foreign_keys(table_name, schema=schema)
    unique_constraints = [
        {
            "name": constraint.get("name"),
            "columns": constraint.get("column_names", []),
        }
        for constraint in inspector.get_unique_constraints(table_name, schema=schema)
    ]

    columns = []
    for column in reflected.columns:
        categorical = _is_categorical_candidate(column.name, column.type)
        samples = (
            _sample_categorical_values(
                connection, column, max_distinct_values
            )
            if categorical
            else None
        )
        # A high-cardinality candidate is not useful as a categorical example.
        is_categorical = categorical and samples is not None
        columns.append(
            {
                "name": column.name,
                "type": str(column.type),
                "description": column.comment,
                "nullable": column.nullable,
                "server_default": str(column.server_default.arg)
                if column.server_default is not None
                and hasattr(column.server_default, "arg")
                else None,
                "identity": {
                    "always": column.identity.always,
                    "start": column.identity.start,
                    "increment": column.identity.increment,
                }
                if column.identity is not None
                else None,
                "primary_key": column.name in primary_key,
                "foreign_keys": _column_foreign_keys(
                    column.name, foreign_keys, schema
                ),
                "is_categorical": is_categorical,
                "sample_values": samples if is_categorical else None,
            }
        )

    try:
        description = inspector.get_table_comment(table_name, schema=schema).get("text")
    except NotImplementedError:
        description = None

    result: dict[str, Any] = {
        "name": table_name,
        "kind": kind,
        "description": description,
        "primary_key": primary_key,
        "foreign_keys": [
            {
                "name": foreign_key.get("name"),
                "columns": foreign_key.get("constrained_columns", []),
                "referred_schema": foreign_key.get("referred_schema") or schema,
                "referred_table": foreign_key.get("referred_table"),
                "referred_columns": foreign_key.get("referred_columns", []),
            }
            for foreign_key in foreign_keys
        ],
        "unique_constraints": unique_constraints,
        "columns": columns,
    }
    if kind == "view":
        try:
            result["definition"] = inspector.get_view_definition(
                table_name, schema=schema
            )
        except NotImplementedError:
            result["definition"] = None
    return result


def extract_schema(
    engine: Engine,
    schema: str | None = None,
    max_distinct_values: int = 20,
) -> dict[str, Any]:
    """Return tables, columns, keys, and low-cardinality values as a JSON-ready dict.

    If ``schema`` is omitted, all non-system schemas are inspected. Distinct
    values are sampled only for boolean, enum, string, and explicitly categorical
    integer columns, with a strict limit to avoid unbounded context or data reads.
    """
    if max_distinct_values < 1:
        raise ValueError("max_distinct_values must be at least 1")

    with engine.connect() as connection:
        inspector = inspect(connection)
        available_schemas = inspector.get_schema_names()
        if schema is not None:
            if schema not in available_schemas:
                raise ValueError(
                    f"Schema {schema!r} was not found. Available schemas: "
                    f"{', '.join(sorted(available_schemas))}"
                )
            schemas = [schema]
        else:
            schemas = sorted(
                name
                for name in available_schemas
                if name not in SYSTEM_SCHEMAS and not name.startswith("pg_")
            )

        schema_results: list[dict[str, Any]] = []
        for schema_name in schemas:
            table_names = inspector.get_table_names(schema=schema_name)
            view_names = inspector.get_view_names(schema=schema_name)
            try:
                materialized_view_names = inspector.get_materialized_view_names(
                    schema=schema_name
                )
            except (NotImplementedError, AttributeError):
                materialized_view_names = []

            tables = [
                _reflect_table(
                    connection,
                    inspector,
                    schema_name,
                    name,
                    "table",
                    max_distinct_values,
                )
                for name in sorted(table_names)
            ]
            views = [
                _reflect_table(
                    connection,
                    inspector,
                    schema_name,
                    name,
                    "view",
                    max_distinct_values,
                )
                for name in sorted(view_names)
            ]
            views.extend(
                _reflect_table(
                    connection,
                    inspector,
                    schema_name,
                    name,
                    "materialized_view",
                    max_distinct_values,
                )
                for name in sorted(materialized_view_names)
            )
            if tables or views:
                schema_results.append(
                    {"name": schema_name, "tables": tables, "views": views}
                )

        return {
            "database": engine.url.database,
            "dialect": engine.dialect.name,
            "schemas": schema_results,
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract database schema metadata and categorical samples as JSON."
    )
    parser.add_argument(
        "--database-url",
        default=os.environ.get("DATABASE_URL"),
        help="SQLAlchemy URL (defaults to DATABASE_URL).",
    )
    parser.add_argument(
        "--schema",
        help="Only inspect this schema; omit to inspect all non-system schemas.",
    )
    parser.add_argument(
        "--max-distinct-values",
        type=int,
        default=20,
        help="Maximum distinct values for a column to be included as categorical (default: 20).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Write JSON to this path instead of stdout.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.database_url:
        parser.error("provide --database-url or set DATABASE_URL")

    engine = create_engine(args.database_url, pool_pre_ping=True)
    try:
        result = extract_schema(
            engine,
            schema=args.schema,
            max_distinct_values=args.max_distinct_values,
        )
    except (SQLAlchemyError, ValueError) as error:
        parser.error(f"schema extraction failed: {error}")
    finally:
        engine.dispose()

    rendered = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    else:
        print(rendered)
    return 0


if __name__ == "__main__":
    sys.exit(main())
