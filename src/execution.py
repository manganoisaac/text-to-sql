"""Execute read-only SQL and always roll back its transaction."""

from __future__ import annotations

import json
import logging
from time import perf_counter
from typing import TYPE_CHECKING

import pandas as pd
import sqlparse
from sqlalchemy import text
from sqlalchemy.engine import Engine

if TYPE_CHECKING:
    from .types import SQLExecutionResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def execute_readonly_sql(
    sql: str,
    readonly_engine: Engine,
    row_limit: int = 1000,
) -> SQLExecutionResult:
    """Run one SELECT, return capped results and its EXPLAIN plan, then roll back."""
    if row_limit < 1:
        raise ValueError("row_limit must be at least 1")
    statements = sqlparse.parse(sql)
    if len(statements) != 1 or statements[0].get_type() != "SELECT":
        raise ValueError("Only one SELECT statement is allowed")

    with readonly_engine.connect() as connection:
        transaction = connection.begin()
        try:
            connection.execute(text("SET TRANSACTION READ ONLY"))
            explain_data = connection.execute(
                text(f"EXPLAIN (FORMAT JSON) {sql}")
            ).scalar_one()
            if isinstance(explain_data, str):
                explain_data = json.loads(explain_data)
            explain_plan = explain_data[0]

            start_time = perf_counter()
            result = connection.execution_options(stream_results=True).execute(
                text(sql)
            )
            columns = list(result.keys())
            raw_results = [
                dict(row._mapping) for row in result.fetchmany(row_limit)
            ]
            execution_time = perf_counter() - start_time
        except Exception:
            logger.exception("Read-only SQL execution failed: %s", sql)
            raise
        finally:
            transaction.rollback()

    dataframe = pd.DataFrame(raw_results, columns=columns)
    response: SQLExecutionResult = {
        "sql": sql,
        "dataframe": dataframe,
        "raw_results": raw_results,
        "execution_time_seconds": execution_time,
        "rows_returned": len(raw_results),
        "row_limit": row_limit,
        "explain_plan": explain_plan,
    }
    audit_record = {
        "sql": sql,
        "dataframe": dataframe.to_dict(orient="records"),
        "raw_results": raw_results,
        "execution_time_seconds": execution_time,
        "rows_returned": len(raw_results),
        "row_limit": row_limit,
        "explain_plan": explain_plan,
    }
    logger.info("SQL execution audit: %s", json.dumps(audit_record, default=str))
    return response
