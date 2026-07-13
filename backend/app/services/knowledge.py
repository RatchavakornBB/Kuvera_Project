from typing import Any

from agents.knowledge import list_knowledge as _list_knowledge
from agents.knowledge import search_knowledge as _search_knowledge


def list_records(industry: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    return _list_knowledge(industry=industry, category=category)


def search_records(q: str, industry: str | None = None, category: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    return _search_knowledge(q, industry=industry, category=category, limit=limit)
