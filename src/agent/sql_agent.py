"""LangGraph agent for generating SQL and asking clarification questions."""

from concurrent.futures import ThreadPoolExecutor

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
import sqlparse

from .llm import get_llm
from .prompts import COMPLEXITY_PROMPT, SQL_GENERATION_STRATEGIES
from .types import QueryComplexity, SQLAgentState, SQLResult


def _generate_sql(messages: list, strategy: str | None = None) -> SQLResult:
    structured_llm = get_llm().with_structured_output(
        SQLResult,
        method="function_calling",
    )
    prompt = messages
    if strategy:
        prompt = [{"role": "system", "content": strategy}, *messages]
    return structured_llm.invoke(prompt)


def _sql_matches(sql_a: str, sql_b: str) -> bool:
    """Compare generated SQL while ignoring formatting and keyword casing."""
    def normalize(sql: str) -> str:
        formatted = sqlparse.format(
            sql,
            strip_comments=True,
            keyword_case="upper",
            identifier_case="lower",
            function_case="lower",
            strip_whitespace=True,
            use_space_around_operators=True,
        )
        return " ".join(formatted.split()).rstrip(";").strip()

    return normalize(sql_a) == normalize(sql_b)


def call_llm(state: SQLAgentState) -> dict:
    classifier = get_llm().with_structured_output(
        QueryComplexity,
        method="function_calling",
    )
    complexity = classifier.invoke(
        [
            {"role": "system", "content": COMPLEXITY_PROMPT},
            {"role": "user", "content": state["user_query"]},
        ]
    )

    if not complexity.is_complex:
        return {
            "sql_result": _generate_sql(state["messages"]).model_dump(),
            "sql_agreement": None,
        }

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [
            executor.submit(_generate_sql, state["messages"], strategy)
            for strategy in SQL_GENERATION_STRATEGIES
        ]
        first, second = (future.result() for future in futures)

    agreement = None
    if not first.clarification_question:
        agreement = float(_sql_matches(first.sql_query, second.sql_query))

    return {
        "sql_result": first.model_dump(),
        "sql_agreement": agreement,
    }


def ask_question(state: SQLAgentState) -> dict:
    question = state["sql_result"].get("clarification_question")
    answer = interrupt(question)
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError("Please answer the clarification question")
    return {
        "messages": [
            AIMessage(content=question),
            HumanMessage(content=answer.strip()),
        ]
    }


def route_after_llm(state: SQLAgentState) -> str:
    return (
        "ask_question"
        if state["sql_result"].get("clarification_question")
        else END
    )


builder = StateGraph(SQLAgentState)
builder.add_node("call_llm", call_llm)
builder.add_node("ask_question", ask_question)
builder.add_edge(START, "call_llm")
builder.add_conditional_edges(
    "call_llm",
    route_after_llm,
    {"ask_question": "ask_question", END: END},
)
builder.add_edge("ask_question", "call_llm")

agent = builder.compile(checkpointer=InMemorySaver())
