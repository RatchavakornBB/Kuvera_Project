"""Contracts Lead: reuses the phase2-001 upload path (Storage object +
Document row together), then runs the Contracts Lead agentic loop
(agents/contracts_graph.py) — a real multi-step decide/act cycle that can
call search_knowledge for comparable-deal precedent before reporting its
final summary and clauses, replacing the old forced pair of single-shot
contract_summarizer + clause_extractor calls."""

from typing import Any

from agents.contracts_graph import compiled_contracts_graph
from agents.retry import with_retry

from app.services import documents as documents_service


def process_contract(deal_id: str, filename: str, content: bytes, content_type: str) -> dict[str, Any]:
    doc = documents_service.upload_document(
        deal_id=deal_id, filename=filename, content=content, content_type=content_type
    )
    return reanalyze_contract(doc["id"])


def _run_once(document_id: str) -> dict[str, Any]:
    with compiled_contracts_graph() as graph:
        return graph.invoke(
            {"document_id": document_id},
            config={"configurable": {"thread_id": f"contracts:{document_id}"}},
        )


def reanalyze_contract(document_id: str) -> dict[str, Any]:
    """Re-runs the Contracts Lead loop on an already-uploaded contract
    document — same work process_contract runs on ingest, factored out so a
    chat-driven 'contracts_lead' request (agents/nodes/orchestrator.py) can
    re-analyze an existing document without re-uploading it.

    Wrapped in with_retry so a truncated or otherwise-failed loop run (raised
    as LoopTruncated from agents/contracts_graph.py's finalize node) gets one
    full fresh retry — re-invoking the whole graph from init is cheap here
    (just a document re-fetch) — before failing loud as NodeFailure, same
    AGENT.md Section 10 contract every other node in this codebase follows."""
    result = with_retry("contracts_lead", lambda: _run_once(document_id))

    summary = result["summary"]
    clauses = result["clauses"]

    documents_service.update_document_summary(
        document_id, {"summary": summary, "clauses": clauses, "type": "Contract"}
    )

    return {"document_id": document_id, "summary": summary, "clauses": clauses}
