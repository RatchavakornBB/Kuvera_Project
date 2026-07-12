"""Wires the Analyst Lead subgraph (agents/graph.py) into the backend.
Triggers the graph synchronously for the demo (timeline Section 4.1 —
no background queue needed at this scale), persists the result, and keeps
the document's own summary column current for the Documents tab."""

from typing import Any

from agents.analyses import save_analysis
from agents.graph import compiled_analyst_graph

from app.db import get_client


def run_analysis(deal_id: str, document_id: str) -> dict[str, Any]:
    initial_state = {"deal_id": deal_id, "document_id": document_id}

    with compiled_analyst_graph() as graph:
        result = graph.invoke(
            initial_state,
            config={"configurable": {"thread_id": f"{deal_id}:{document_id}"}},
        )

    save_analysis(
        deal_id=deal_id,
        document_id=document_id,
        summary=result["summary"],
        risk_flags=result.get("risk_flags", []),
        ic_memo_draft=result.get("ic_memo_draft"),
        pricing_note=result.get("pricing_note"),
    )

    get_client().table("documents").update({"summary": result["summary"]}).eq("id", document_id).execute()

    return {
        "summary": result["summary"],
        "risk_flags": result.get("risk_flags", []),
        "ic_memo_draft": result.get("ic_memo_draft"),
        "pricing_note": result.get("pricing_note"),
        "pricing_error": result.get("pricing_error"),
    }
