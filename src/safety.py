"""Small SQL safety checks."""

import json

import sqlparse
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlparse.sql import Parenthesis, Token, TokenList
from sqlparse.tokens import Comment, Keyword, Punctuation


def is_valid_sql(sql: str) -> bool:
    """Return whether sqlparse recognizes every non-empty statement as SQL."""
    statements = sqlparse.parse(sql)
    return bool(statements) and all(
        statement.get_type() != "UNKNOWN" for statement in statements
    )


def contains_blocked_ddl(sql: str) -> bool:
    """Return True if any statement is CREATE, ALTER, or DROP."""
    blocked = {"CREATE", "ALTER", "DROP"}
    return any(statement.get_type() in blocked for statement in sqlparse.parse(sql))


def contains_blocked_dml(sql: str) -> bool:
    """Return True if any statement is INSERT, UPDATE, or DELETE."""
    blocked = {"INSERT", "UPDATE", "DELETE"}
    return any(statement.get_type() in blocked for statement in sqlparse.parse(sql))


def add_row_limit(sql: str, limit: int = 1000) -> str:
    """Add LIMIT to one SELECT if it does not already have a top-level LIMIT."""
    if limit < 0:
        raise ValueError("limit must be zero or greater")

    statements = sqlparse.parse(sql)
    if len(statements) != 1 or statements[0].get_type() != "SELECT":
        raise ValueError("Expected one SELECT statement")

    statement = statements[0]
    if any(
        token.ttype in Keyword and token.normalized == "LIMIT"
        for token in statement.tokens
    ):
        return sql

    tokens = statement.tokens
    insert_at = next(
        (
            index
            for index, token in enumerate(tokens)
            if token.ttype in Punctuation and token.value == ";"
        ),
        len(tokens),
    )
    if insert_at == len(tokens):
        while insert_at and (
            tokens[insert_at - 1].is_whitespace
            or tokens[insert_at - 1].ttype in Comment
        ):
            insert_at -= 1

    tokens.insert(insert_at, Token(None, f" LIMIT {limit}"))
    return str(statement)


def subquery_depth_within_limit(sql: str, max_depth: int = 3) -> bool:
    """Return True if a single SELECT has no more than max_depth subqueries."""
    statements = sqlparse.parse(sql)
    if max_depth < 0 or len(statements) != 1 or statements[0].get_type() != "SELECT":
        return False

    def starts_query(parenthesis: Parenthesis) -> bool:
        for token in parenthesis.tokens:
            if token.is_whitespace or token.ttype in Comment:
                continue
            if token.ttype in Punctuation and token.value == "(":
                continue
            return token.ttype in Keyword and token.normalized in {"SELECT", "WITH"}
        return False

    def deepest_depth(token_list: TokenList, depth: int = 0) -> int:
        deepest = depth
        for token in token_list.tokens:
            if token.is_group:
                child_depth = depth
                if isinstance(token, Parenthesis) and starts_query(token):
                    child_depth += 1
                deepest = max(deepest, deepest_depth(token, child_depth))
        return deepest

    return deepest_depth(statements[0]) <= max_depth


def exceeds_estimated_scan_rows(
    sql: str,
    engine: Engine,
    max_rows: int = 100_000,
) -> bool:
    """Return True if PostgreSQL EXPLAIN estimates over max_rows at scan nodes."""
    if max_rows < 0:
        raise ValueError("max_rows must be zero or greater")

    statements = sqlparse.parse(sql)
    if len(statements) != 1 or statements[0].get_type() != "SELECT":
        raise ValueError("Expected one SELECT statement")

    # EXPLAIN (without ANALYZE) plans the query without running it.
    with engine.begin() as connection:
        connection.execute(text("SET TRANSACTION READ ONLY"))
        plan_data = connection.execute(
            text(f"EXPLAIN (FORMAT JSON) {sql}")
        ).scalar_one()

    if isinstance(plan_data, str):
        plan_data = json.loads(plan_data)
    root = plan_data[0]["Plan"] if isinstance(plan_data, list) else plan_data["Plan"]

    scan_nodes = {
        "Seq Scan",
        "Parallel Seq Scan",
        "Index Scan",
        "Index Only Scan",
        "Bitmap Heap Scan",
        "Tid Scan",
        "Tid Range Scan",
        "Foreign Scan",
        "Function Scan",
        "Table Function Scan",
        "Values Scan",
        "CTE Scan",
        "WorkTable Scan",
        "Named Tuplestore Scan",
        "Sample Scan",
        "Custom Scan",
    }
    estimated_rows = 0
    pending = [root]
    while pending:
        node = pending.pop()
        if node.get("Node Type") in scan_nodes:
            estimated_rows += int(node.get("Plan Rows", 0))
        pending.extend(node.get("Plans", []))

    return estimated_rows > max_rows
