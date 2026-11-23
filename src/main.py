"""FastAPI application for the Text-to-SQL service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException

from query import (
    ConversationNotFoundError,
    answer_handler,
    query_handler,
)
from src.types import AnswerInput, HistoryItem, QueryInput


history: list[HistoryItem] = []

app = FastAPI()


@app.get("/")
def test():
    return {"Hello": "World"}


def record_result(conversation_id: str, result: dict[str, Any]) -> None:
    if result["type"] == "result":
        history.append(
            HistoryItem(
                conversation_id=conversation_id,
                query=result["query"],
                result=result["result"],
                sql=result["sql"],
                sanity_violations=result["sanity_violations"],
                confidence=result["confidence"],
            )
        )


@app.post("/v1/query")
def query(input: QueryInput):
    conversation_id = str(uuid4())
    query_result = query_handler(input.query, conversation_id)
    record_result(conversation_id, query_result)
    return {**query_result, "conversation_id": conversation_id, "status_code": 200}


@app.post("/v1/query/{conversation_id}/answer")
def answer(conversation_id: str, input: AnswerInput):
    if not input.answer.strip():
        raise HTTPException(status_code=422, detail="Please provide an answer")
    try:
        query_result = answer_handler(conversation_id, input.answer)
    except ConversationNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    record_result(conversation_id, query_result)
    return {**query_result, "conversation_id": conversation_id, "status_code": 200}


@app.get("/v1/schema")
def schema():
    return json.loads(
        (Path(__file__).resolve().parent.parent / "schema_context.json").read_text(
            encoding="utf-8"
        )
    )


@app.get("/v1/history")
def history_fn():
    return history
