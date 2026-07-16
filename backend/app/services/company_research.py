"""Thin wrapper adding the one backend/app-only side effect
agents/company_research.py can't do itself (agents/ stays independent of
backend/app/, per D-007): writing the research note as a real Document
("source") via the existing create_document_from_research write path,
alongside the knowledge_base row agents/company_research.py already wrote
("RAG"/"memory")."""

from typing import Any

from agents.company_research import refresh_company_research as _refresh_company_research

from app.services import documents as documents_service


def refresh_company_research(deal_id: str) -> dict[str, Any]:
    result = _refresh_company_research(deal_id)
    company_name = result["deal"]["name"]
    refreshed_date = result["knowledge_row"]["created_at"][:10]
    question = f"Company research update — {company_name} ({refreshed_date})"
    documents_service.create_document_from_research(deal_id, question, result["brief"], result["citations"])
    return result["knowledge_row"]
