"""Shared types for the Text-to-SQL agents."""

from enum import Enum
from typing import Any

from langgraph.graph import MessagesState
from pydantic import BaseModel, Field


# Types used by sql_agent.py
class TableColumns(BaseModel):
    table_name: str = Field(
        description="Schema-qualified table name, such as retail.orders"
    )
    columns: list[str] = Field(description="Columns read from the table")


class SQLResult(BaseModel):
    sql_query: str = Field(description="SQL query answering the user's question")
    explanation: str = Field(description="Plain-language explanation of the query")
    confidence: float = Field(
        ge=0, le=1, description="Estimated confidence from 0 to 1"
    )
    tables_and_columns: list[TableColumns] = Field(
        description="Tables and columns referenced by the SQL query"
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask the user when clarification is needed; otherwise null",
    )


class SQLAgentState(MessagesState):
    sql_result: dict[str, Any]
    user_query: str


# Types used by sanity_checker_agent.py
class SanityViolationType(str, Enum):
    AGGREGATE_RANGE = "aggregate_range"
    COUNT_MAGNITUDE = "count_magnitude"
    DATE_RANGE = "date_range"
    NULL_HEAVY_JOIN = "null_heavy_join"


class Violation(BaseModel):
    category: SanityViolationType = Field(
        description="One of the four sanity check categories"
    )
    reason: str = Field(description="The sanity violation that has occured")
    severity: float = Field(
        description="A number between 0 and 1 for how bad the violation is"
    )


class CriticResult(BaseModel):
    sanity_violations: list[Violation] = Field(
        description="The reasons the SQL query was rejected"
    )
