from typing import Any

from agents.industry_brief import refresh_competitor_brief as _refresh_competitor_brief
from agents.industry_brief import refresh_industry_brief as _refresh_industry_brief
from agents.knowledge import backfill_missing_embeddings as _backfill_missing_embeddings
from agents.knowledge import list_knowledge as _list_knowledge
from agents.knowledge import search_knowledge as _search_knowledge


def list_records(industry: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    return _list_knowledge(industry=industry, category=category)


def search_records(q: str, industry: str | None = None, category: str | None = None, limit: int = 10) -> list[dict[str, Any]]:
    return _search_knowledge(q, industry=industry, category=category, limit=limit)


def refresh_industry_brief(industry: str) -> dict[str, Any]:
    return _refresh_industry_brief(industry)


def refresh_competitor_brief(company_name: str, industry: str) -> dict[str, Any]:
    return _refresh_competitor_brief(company_name, industry)


def backfill_missing_embeddings() -> int:
    return _backfill_missing_embeddings()
