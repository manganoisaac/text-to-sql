"""Formatting helpers for retrieved schema context."""

from __future__ import annotations

import json
from collections.abc import Sequence

from .types import SchemaObject


def format_schema_context(matches: Sequence[SchemaObject]) -> str:
    """Serialize retrieved metadata for the existing prompt template."""
    return json.dumps(matches, indent=2, ensure_ascii=False)
