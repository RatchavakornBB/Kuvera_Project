"""Industry & Competitor Insight Briefs (system-architecture.md Section 10.1) — the "fine-tuning-
style" storage the doc describes: a compact reference document refreshed periodically and reused
as background context, rather than retrieved fresh via RAG on every query (that's what Company
Insight is for, and it's already covered by agents/knowledge.py's deal-scoped retrieval).

Scheduled via backend/app/scheduler.py's `industry_brief_refresh` job (every 24h, real APScheduler
interval) for industry Briefs; competitor Briefs stay admin-triggered via the knowledge-base route
since there's no fixed company roster to loop over the way there is a fixed industry list. Reuses
knowledge_base (phase5-009) rather than a new table — industry/competitor briefs are just
knowledge_base rows with no source_deal_id, marked current via `superseded_at is null` rather than
deleted when refreshed, so a prior Brief stays queryable for audit ("the Brief said X as of date
Y") instead of being silently overwritten.

Uses Claude's real web_search and web_fetch server tools (same tools as agents/nodes/web_research.py
for web_search; web_fetch is still beta-only in the installed SDK, hence `betas=WEB_FETCH_BETAS`)
for current, real information — not fabricated industry commentary. Citations are parsed from the
response's real `citations` array (AGENT.md's non-negotiable invariant on this — never fabricated
or inferred) and stored alongside the brief text so every factual claim has a traceable source."""

from datetime import datetime, timezone
from typing import Any

from agents.adapters.model_adapter import call_model
from agents.db import get_client
from agents.embeddings import embed_text
from agents.retry import with_retry

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}
WEB_FETCH_TOOL = {"type": "web_fetch_20250910", "name": "web_fetch", "max_uses": 5}
WEB_FETCH_BETAS = ["web-fetch-2025-09-10"]

INDUSTRY_BRIEF_PROMPT = """You are the Knowledge Agent's industry analyst, writing a reference
brief for M&A analysts. Research the {industry} industry using web search for current, real
information: recent news and notable company actions, trends, financial data (market cap movement,
expansion/contraction signals), internal and external factors affecting the sector, and your own
assessment of investment-worthiness and market growth. Write a compact brief (3-5 paragraphs),
citing what you actually find — no generic filler. This will be cached and reused as background
context for analysts working deals in this industry."""

COMPETITOR_BRIEF_PROMPT = """You are the Knowledge Agent's competitor analyst, writing a reference
brief for M&A analysts. Research {company} (a real company in the {industry} industry, if it
exists — say so plainly if you can't find real information rather than inventing any) using web
search: recent news and actions, trends, financial data, and how it might affect a deal involving
a competitor. Write a compact brief (3-5 paragraphs), citing what you actually find."""


def _synthesize(agent_name: str, prompt: str) -> dict[str, Any]:
    def _call() -> dict[str, Any]:
        response = call_model(
            agent_name,
            messages=[{"role": "user", "content": prompt}],
            tools=[WEB_SEARCH_TOOL, WEB_FETCH_TOOL],
            betas=WEB_FETCH_BETAS,
            max_tokens=2048,
        )
        fetched_at = datetime.now(timezone.utc).isoformat()
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
                        "fetched_at": fetched_at,
                    }
                )
        if not text_parts:
            raise ValueError(f"model returned no text block (stop_reason={response.stop_reason!r})")
        return {"brief": "".join(text_parts), "citations": citations}

    return with_retry(agent_name, _call)


def _supersede_and_insert(client: Any, category: str, match: dict[str, str], row: dict[str, Any]) -> dict[str, Any]:
    """Marks the current row(s) for this scope superseded rather than deleting
    them — old Briefs stay queryable (`superseded_at is null` selects only the
    live one) so a downstream disagreement can be traced back to "the Brief
    said X as of date Y" instead of the prior version being silently gone."""
    now = datetime.now(timezone.utc).isoformat()
    query = client.table("knowledge_base").update({"superseded_at": now}).eq("category", category).is_("superseded_at", "null")
    for column, value in match.items():
        query = query.eq(column, value)
    query.execute()

    res = client.table("knowledge_base").insert({"category": category, "superseded_at": None, **row}).execute()
    return res.data[0]


def refresh_industry_brief(industry: str) -> dict[str, Any]:
    result = _synthesize("industry_brief", INDUSTRY_BRIEF_PROMPT.format(industry=industry))
    embedding = embed_text(result["brief"], input_type="document")

    client = get_client()
    return _supersede_and_insert(
        client,
        "industry_insight",
        {"industry": industry},
        {
            "industry": industry,
            "company_name": None,
            "content": {"brief": result["brief"], "citations": result["citations"]},
            "summary": result["brief"],
            "embedding": embedding,
        },
    )


def refresh_competitor_brief(company_name: str, industry: str) -> dict[str, Any]:
    result = _synthesize("competitor_brief", COMPETITOR_BRIEF_PROMPT.format(company=company_name, industry=industry))
    embedding = embed_text(result["brief"], input_type="document")

    client = get_client()
    return _supersede_and_insert(
        client,
        "competitor_insight",
        {"company_name": company_name},
        {
            "industry": industry,
            "company_name": company_name,
            "content": {"brief": result["brief"], "citations": result["citations"]},
            "summary": result["brief"],
            "embedding": embedding,
        },
    )


def get_current_industry_brief(industry: str) -> dict[str, Any] | None:
    """The read side of the Brief cache — what a per-deal agent (e.g.
    concierge_qa) calls to inject the current, non-superseded Brief for a
    deal's industry into its own context, instead of re-researching it."""
    client = get_client()
    rows = (
        client.table("knowledge_base")
        .select("industry, summary, created_at")
        .eq("category", "industry_insight")
        .eq("industry", industry)
        .is_("superseded_at", "null")
        .limit(1)
        .execute()
        .data
    )
    return rows[0] if rows else None
