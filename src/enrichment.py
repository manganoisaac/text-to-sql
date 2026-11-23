"""Add a small, safe sample of live rows to retrieved schema context."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from copy import deepcopy
from datetime import date, datetime, time
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import MetaData, Table, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import NoSuchTableError

if TYPE_CHECKING:
    from .types import EnrichedContext, EnrichedSchemaObject, SampleRow, SchemaObject


MAX_SAMPLE_ROWS = 5
REDACTED_VALUE = "[REDACTED]"
SENSITIVE_COLUMN_NAME = re.compile(
    r"(?:^|_)(?:email|phone|first_name|last_name|full_name|address|line_1|"
    r"postal_code|tracking_number|provider_reference|review_title|review_body|"
    r"description|note|resolution)(?:_|$)",
    re.IGNORECASE,
)


def enrich_context(
    context: Sequence[SchemaObject],
    engine: Engine,
    max_rows_per_object: int = MAX_SAMPLE_ROWS,
    redact_sensitive: bool = True,
) -> EnrichedContext:
    """Return retrieved tables/views with up to five example rows each.

    Tables with primary keys are sampled in primary-key order. Views and tables
    without primary keys use the database's returned order. Queries are read-only.
    Common personal and free-text columns are redacted by default before returning
    rows to the caller.
    """
    if not 0 <= max_rows_per_object <= MAX_SAMPLE_ROWS:
        raise ValueError(f"max_rows_per_object must be between 0 and {MAX_SAMPLE_ROWS}")

    enriched: EnrichedContext = []
    with engine.connect() as connection:
        for schema_object in context:
            schema_name = schema_object.get("schema")
            object_name = schema_object.get("name")
            if not schema_name or not object_name:
                raise ValueError("Each context object must include schema and name")

            item: EnrichedSchemaObject = deepcopy(schema_object)
            item["sample_rows"] = _sample_rows(
                connection,
                schema_name,
                object_name,
                max_rows_per_object,
                redact_sensitive,
            )
            enriched.append(item)
    return enriched


def _sample_rows(
    connection: Any,
    schema_name: str,
    object_name: str,
    max_rows: int,
    redact_sensitive: bool,
) -> list[SampleRow]:
    if max_rows == 0:
        return []
    try:
        reflected = Table(
            object_name,
            MetaData(),
            schema=schema_name,
            autoload_with=connection,
        )
    except NoSuchTableError as error:
        raise ValueError(
            f"Schema context refers to missing object {schema_name}.{object_name}"
        ) from error

    statement = select(reflected)
    primary_key_columns = list(reflected.primary_key.columns)
    if primary_key_columns:
        statement = statement.order_by(*primary_key_columns)
    statement = statement.limit(max_rows)

    rows = connection.execute(statement).mappings().all()
    return [
        {
            column_name: REDACTED_VALUE
            if redact_sensitive and SENSITIVE_COLUMN_NAME.search(column_name)
            else _json_safe(value)
            for column_name, value in row.items()
        }
        for row in rows
    ]


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else str(value)
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return str(value)
