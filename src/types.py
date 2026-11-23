"""Typed shapes shared by schema discovery, retrieval, and enrichment."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal, TypeAlias, TypedDict

from pydantic import BaseModel

if TYPE_CHECKING:
    import pandas as pd


JSONScalar: TypeAlias = str | int | float | bool | None
JSONValue: TypeAlias = JSONScalar | list["JSONValue"] | dict[str, "JSONValue"]
SampleRow: TypeAlias = dict[str, JSONValue]
SchemaObjectKind: TypeAlias = Literal["table", "view", "materialized_view"]


class IdentityInfo(TypedDict, total=False):
    always: bool
    start: int | None
    increment: int | None


class ColumnInfo(TypedDict, total=False):
    name: str
    type: str
    description: str | None
    nullable: bool
    server_default: str | None
    identity: IdentityInfo | None
    primary_key: bool
    foreign_keys: list[dict[str, str | None]]
    is_categorical: bool
    sample_values: list[JSONValue] | None


class ForeignKeyInfo(TypedDict, total=False):
    name: str | None
    columns: list[str]
    referred_schema: str | None
    referred_table: str | None
    referred_columns: list[str]


class UniqueConstraintInfo(TypedDict, total=False):
    name: str | None
    columns: list[str]


class SchemaObject(TypedDict, total=False):
    schema: str
    name: str
    kind: SchemaObjectKind
    description: str | None
    definition: str | None
    primary_key: list[str]
    foreign_keys: list[ForeignKeyInfo]
    unique_constraints: list[UniqueConstraintInfo]
    columns: list[ColumnInfo]


class RetrievedSchemaObject(SchemaObject, total=False):
    similarity: float


class EnrichedSchemaObject(RetrievedSchemaObject, total=False):
    sample_rows: list[SampleRow]


class SchemaGroup(TypedDict, total=False):
    name: str
    tables: list[SchemaObject]
    views: list[SchemaObject]


class SchemaContext(TypedDict, total=False):
    database: str | None
    dialect: str
    schemas: list[SchemaGroup]


EnrichedContext: TypeAlias = list[EnrichedSchemaObject]


class SQLExecutionResult(TypedDict):
    sql: str
    dataframe: pd.DataFrame
    raw_results: list[dict[str, Any]]
    execution_time_seconds: float
    rows_returned: int
    row_limit: int
    explain_plan: dict[str, Any]


# FastAPI request and history models
class HistoryItem(BaseModel):
    conversation_id: str
    query: str
    result: list[dict[str, Any]]
    sql: str
    sanity_violations: list[dict[str, str | float]]
    confidence: float


class QueryInput(BaseModel):
    query: str


class AnswerInput(BaseModel):
    answer: str
