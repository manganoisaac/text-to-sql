"""Shared LLM initialization."""

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv(Path(__file__).resolve().parents[2] / ".env")


@lru_cache
def get_llm() -> ChatOpenAI:
    api_key = os.getenv("OPENCODE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Add your OpenCode Console API key as OPENCODE_API_KEY in .env"
        )

    return ChatOpenAI(
        model=os.getenv("OPENCODE_MODEL", "kimi-k3"),
        api_key=api_key,
        base_url="https://opencode.ai/inference/go/openai/v1",
        default_headers={
            "x-opencode-session": os.getenv("OPENCODE_SESSION_ID", "text2sql-local")
        },
        use_responses_api=False,
    )
