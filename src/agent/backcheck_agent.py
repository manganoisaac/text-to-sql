"""Checks whether generated SQL matches the user's intended question."""

from .llm import get_llm
from .prompts import BACKCHECK_PROMPT


def backcheck_sql(sql_query: str) -> str:
    response = get_llm().invoke(BACKCHECK_PROMPT.format(sql_query=sql_query))
    return response.text
