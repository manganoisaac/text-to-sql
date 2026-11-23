"""Schema shapes used by embedding and retrieval."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class ColumnInfo(TypedDict, total=False):
    name: str
    type: str
    description: str | None
    nullable: bool
    primary_key: bool
    sample_values: list[Any] | None


class ForeignKeyInfo(TypedDict, total=False):
    columns: list[str]
    referred_schema: str | None
    referred_table: str | None
    referred_columns: list[str]


class UniqueConstraintInfo(TypedDict, total=False):
    columns: list[str]


class SchemaObject(TypedDict, total=False):
    schema: str
    name: str
    kind: Literal["table", "view", "materialized_view"]
    description: str | None
    definition: str | None
    primary_key: list[str]
    foreign_keys: list[ForeignKeyInfo]
    unique_constraints: list[UniqueConstraintInfo]
    columns: list[ColumnInfo]


class RetrievedSchemaObject(SchemaObject, total=False):
    similarity: float


class SchemaGroup(TypedDict, total=False):
    name: str
    tables: list[SchemaObject]
    views: list[SchemaObject]


class SchemaContext(TypedDict, total=False):
    database: str | None
    dialect: str
    schemas: list[SchemaGroup]
