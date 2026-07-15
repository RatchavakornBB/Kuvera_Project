"""Contracts Lead: reuses the phase2-001 upload path (Storage object +
Document row together), then runs 4.1 and 4.2 — an ingest-triggered pair,
no dependency between them, so plain sequential calls suffice (no
LangGraph needed for two independent nodes)."""

from typing import Any

from agents.nodes.clause_extractor import clause_extractor
from agents.nodes.contract_summarizer import contract_summarizer

from app.services import documents as documents_service


def process_contract(deal_id: str, filename: str, content: bytes, content_type: str) -> dict[str, Any]:
    doc = documents_service.upload_document(
        deal_id=deal_id, filename=filename, content=content, content_type=content_type
    )
    return reanalyze_contract(doc["id"])


def reanalyze_contract(document_id: str) -> dict[str, Any]:
    """Re-runs 4.1/4.2 on an already-uploaded contract document — same pair
    process_contract runs on ingest, factored out so a chat-driven
    'contracts_lead' request (agents/nodes/orchestrator.py) can re-analyze
    an existing document without re-uploading it."""
    summary = contract_summarizer(document_id)
    clauses = clause_extractor(document_id)

    documents_service.update_document_summary(
        document_id, {"summary": summary, "clauses": clauses, "type": "Contract"}
    )

    return {"document_id": document_id, "summary": summary, "clauses": clauses}
