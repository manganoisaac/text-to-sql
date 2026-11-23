"""Build an LLM prompt from retrieved and row-enriched schema context."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Literal, TypedDict

from dotenv import load_dotenv
from langgraph.types import Command
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from agent import backcheck_sql, sanity_checker, score_violations, sql_agent
from agent.prompts import USER_PROMPT
from embedding import (
    FakeEmbedder,
    InMemorySchemaIndex,
    format_schema_context,
    text_cosine_similarity,
)
from enrichment import enrich_context
from execution import execute_readonly_sql
from safety import (
    contains_blocked_ddl,
    contains_blocked_dml,
    exceeds_estimated_scan_rows,
    is_valid_sql,
    subquery_depth_within_limit,
)


class QueryResult(TypedDict):
    type: Literal["result"]
    query: str
    result: list[dict[str, Any]]
    sql: str
    sanity_violations: list[dict[str, str | float]]
    confidence: float


class ClarificationQuestion(TypedDict):
    type: Literal["question"]
    question: str


QueryResponse = QueryResult | ClarificationQuestion


class ConversationNotFoundError(ValueError):
    pass


def _average_scores(scores: list[float]) -> float:
    if not scores:
        raise ValueError("At least one confidence score is required")
    if any(not 0 <= score <= 1 for score in scores):
        raise ValueError("Confidence scores must be between 0 and 1")
    return sum(scores) / len(scores)


def build_user_prompt(
    user_query: str,
    index: InMemorySchemaIndex,
    engine: Engine,
    few_shot_examples: str = "No examples configured",
) -> str:
    """Retrieve relevant schema, enrich it with sample rows, and format a prompt."""
    matches = index.search(user_query, similarity_threshold=0.35)
    print("Retrieved tables:", [item["name"] for item in matches])
    context = enrich_context(matches, engine)
    return USER_PROMPT.format(
        user_query=user_query,
        few_shot_examples=few_shot_examples,
        relevant_schemas_with_sample_values=format_schema_context(context),
    )


def _database_engine():
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError(
            "Set DATABASE_URL before running the Text-to-SQL prompt builder"
        )
    return project_root, create_engine(database_url, pool_pre_ping=True)


def _interrupted_question(result: dict[str, Any]) -> str | None:
    interrupts = result.get("__interrupt__", ())
    return interrupts[0].value if interrupts else None


def _finish_query(
    user_query: str, result: dict[str, Any], engine: Engine
) -> QueryResult:
    sql_query = result["sql_result"]["sql_query"]
    print(f"sql query: {sql_query}")
    if not is_valid_sql(sql_query):
        raise ValueError("The generated SQL was not recognized as SQL")
    if contains_blocked_ddl(sql_query):
        raise ValueError("The generated SQL contains a blocked DDL command")
    if contains_blocked_dml(sql_query):
        raise ValueError("The generated SQL contains a blocked data-modifying command")
    if not subquery_depth_within_limit(sql_query):
        raise ValueError("The generated SQL exceeds the maximum subquery depth of 3")
    if exceeds_estimated_scan_rows(sql_query, engine):
        raise ValueError(
            "The generated SQL exceeds the estimated 100,000-row scan limit"
        )

    # TODO: account for follow up questions (patch the question)
    backcheck_question = backcheck_sql(sql_query)
    similarity = text_cosine_similarity(user_query, backcheck_question, FakeEmbedder())
    print(f"Backcheck similarity: {similarity:.3f}")
    # if similarity < 0.7:
    #     raise ValueError("The generated SQL may not answer the user's question")

    rows = execute_readonly_sql(sql_query, engine)
    critic_result = sanity_checker(user_query, sql_query, rows["dataframe"])
    confidence_scores = [
        similarity,
        score_violations(critic_result.sanity_violations),
    ]
    sql_agreement = result.get("sql_agreement")
    if sql_agreement is not None:
        confidence_scores.append(sql_agreement)
    confidence = _average_scores(confidence_scores)

    return {
        "type": "result",
        "query": user_query,
        "result": rows["raw_results"],
        "sql": sql_query,
        "sanity_violations": [
            violation.model_dump(mode="json")
            for violation in critic_result.sanity_violations
        ],
        "confidence": confidence,
    }


def query_handler(user_query: str, conversation_id: str) -> QueryResponse:
    project_root, engine = _database_engine()
    config = {"configurable": {"thread_id": conversation_id}}
    try:
        index = InMemorySchemaIndex.from_file(
            project_root / "schema_context.json",
            embedder=FakeEmbedder(),
        )
        prompt = build_user_prompt(user_query, index, engine)
        result = sql_agent.invoke(
            {
                "messages": [{"role": "user", "content": prompt}],
                "user_query": user_query,
            },
            config=config,
        )
        question = _interrupted_question(result)
        if question:
            return {"type": "question", "question": question}
        return _finish_query(user_query, result, engine)
    finally:
        engine.dispose()


def answer_handler(conversation_id: str, answer: str) -> QueryResponse:
    if not answer.strip():
        raise ValueError("Please provide an answer")

    config = {"configurable": {"thread_id": conversation_id}}
    state = sql_agent.get_state(config)
    if not state.values or not any(task.interrupts for task in state.tasks):
        raise ConversationNotFoundError(
            "No pending clarification for this conversation"
        )

    result = sql_agent.invoke(Command(resume=answer.strip()), config=config)
    question = _interrupted_question(result)
    if question:
        return {"type": "question", "question": question}

    user_query = result["user_query"]
    _, engine = _database_engine()
    try:
        return _finish_query(user_query, result, engine)
    finally:
        engine.dispose()
