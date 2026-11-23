"""Checks query results for semantic sanity violations."""

from typing import Any

from .llm import get_llm
from .prompts import SANITY_CHECKER_PROMPT
from .types import CriticResult, SanityViolationType, Violation


def sanity_checker(user_query: str, sql_query: str, result: Any) -> CriticResult:
    return (
        get_llm()
        .with_structured_output(CriticResult)
        .invoke(
            SANITY_CHECKER_PROMPT.format(
                user_query=user_query, sql_query=sql_query, result=result
            )
        )
    )


def score_violations(violations: list[Violation]) -> float:
    """Return the proportion of sanity criteria with no reported violation."""
    violated_categories = {violation.category for violation in violations}
    return 1 - len(violated_categories) / len(SanityViolationType)
