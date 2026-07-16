"""Company Research Agent (system-architecture.md Section 10.1's "Company Insight" slot —
knowledge_base.category already reserved 'company_insight' since the table's first migration, never
written until now). Unlike industry_brief.py's industry/competitor Briefs (deal-agnostic,
source_deal_id=null), this is per-deal: one research row per deal, about that deal's own target
company (deals.name), refreshed on backend/app/scheduler.py's `company_research_refresh` job (every
24h, real APScheduler interval, same as industry/competitor) or on demand via the admin route.

Researches recent news, financial results/filings, and other relevant articles about the company —
due-diligence-relevant background for analysts working this specific deal. Uses Claude's real
web_search + web_fetch server tools (same pairing as agents/industry_brief.py/agents/learning_agent.py).
Citations are parsed from the response's real `citations` array, never fabricated.

Stored three ways: (1) a knowledge_base row (category='company_insight', source_deal_id=<deal_id>,
versioned via agents/knowledge.py's supersede_and_insert — the "RAG" destination, embedded + pgvector
searchable), (2) injected into agents/nodes/concierge_qa.py's system prompt alongside the Industry
Brief — the "memory" a per-deal agent reads back, and (3) a real Document via
backend/app/services/documents.py::create_document_from_research (the "source" destination, wired by
backend/app/services/company_research.py's thin wrapper — this module stays free of any backend/app
import, matching every other agents/ module's independence from backend/).

From the second refresh onward, the prompt asks the model to focus on what's changed since the prior
version's `created_at` (agents/knowledge.py::since_clause) — a request, not a guaranteed filter, since
neither web_search nor web_fetch has a server-side date-restriction parameter in the installed SDK.
"""

from typing import Any

from agents.adapters.model_adapter import call_model
from agents.db import get_client
from agents.embeddings import embed_text
from agents.knowledge import get_current_knowledge_row, since_clause, supersede_and_insert
from agents.retry import with_retry

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
WEB_FETCH_TOOL = {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 5}
WEB_FETCH_BETAS = ["web-fetch-2025-09-10"]

COMPANY_RESEARCH_PROMPT = """You are the Knowledge Agent's company research analyst, writing a
due-diligence-relevant research note for an M&A deal team about {company}{industry_clause}. Research
using web search, and fetch full articles where useful: (1) recent news and developments, (2)
financial results, filings, or other notable financial data, (3) other articles or commentary
materially relevant to this deal's evaluation. Write a compact note (3-5 paragraphs), citing what you
actually find — no generic filler. This will be cached and reused as background context for analysts
working this specific deal."""


def _synthesize(agent_name: str, prompt: str) -> dict[str, Any]:
    def _call() -> dict[str, Any]:
        response = call_model(
            agent_name,
            messages=[{"role": "user", "content": prompt}],
            tools=[WEB_SEARCH_TOOL, WEB_FETCH_TOOL],
            betas=WEB_FETCH_BETAS,
            max_tokens=2048,
        )
        text_parts: list[str] = []
        citations: list[dict[str, Any]] = []
        for block in response.content:
            if block.type != "text":
                continue
            text_parts.append(block.text)
            for citation in getattr(block, "citations", None) or []:
                citations.append(
                    {
                        "url": getattr(citation, "url", None),
                        "title": getattr(citation, "title", None),
                        "cited_text": getattr(citation, "cited_text", None),
                    }
                )
        if not text_parts:
            raise ValueError(f"model returned no text block (stop_reason={response.stop_reason!r})")
        return {"brief": "".join(text_parts), "citations": citations}

    return with_retry(agent_name, _call)


def refresh_company_research(deal_id: str) -> dict[str, Any]:
    client = get_client()
    deal_rows = client.table("deals").select("name, industries").eq("id", deal_id).execute().data
    if not deal_rows:
        raise ValueError(f"No deal with id {deal_id}")
    deal = deal_rows[0]
    company_name = deal["name"]
    industry = deal["industries"][0] if deal["industries"] else None
    industry_clause = f" (the target company in an active deal, industry: {industry})" if industry else " (the target company in an active deal)"

    current = get_current_knowledge_row("company_insight", source_deal_id=deal_id)
    since = current["created_at"] if current else None
    prompt = COMPANY_RESEARCH_PROMPT.format(company=company_name, industry_clause=industry_clause) + since_clause(since)

    result = _synthesize("company_research", prompt)

    try:
        embedding = embed_text(result["brief"], input_type="document")
    except Exception:
        embedding = None

    row = supersede_and_insert(
        client,
        "company_insight",
        {"source_deal_id": deal_id},
        {
            "source_deal_id": deal_id,
            "company_name": company_name,
            "industry": industry,
            "content": {"brief": result["brief"], "citations": result["citations"]},
            "summary": result["brief"],
            "embedding": embedding,
        },
    )

    return {
        "knowledge_row": row,
        "brief": result["brief"],
        "citations": result["citations"],
        "deal": {"id": deal_id, "name": company_name},
    }


def get_current_company_research(deal_id: str) -> dict[str, Any] | None:
    """The read side of the per-deal research cache — what concierge_qa calls
    to inject the current, non-superseded company research into its own
    context, instead of re-researching it."""
    return get_current_knowledge_row("company_insight", source_deal_id=deal_id)
