"""LangGraph agent for generating SQL and asking clarification questions."""

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from .llm import get_llm
from .types import SQLAgentState, SQLResult


def call_llm(state: SQLAgentState) -> dict:
    structured_llm = get_llm().with_structured_output(
        SQLResult,
        method="function_calling",
    )
    return {"sql_result": structured_llm.invoke(state["messages"]).model_dump()}


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
