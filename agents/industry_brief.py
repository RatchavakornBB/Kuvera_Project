"""Industry & Competitor Insight Briefs (system-architecture.md Section 10.1) — the "fine-tuning-
style" storage the doc describes: a compact reference document refreshed periodically and reused
as background context, rather than retrieved fresh via RAG on every query (that's what Company
Insight is for, and it's already covered by agents/knowledge.py's deal-scoped retrieval).

Scheduled via backend/app/scheduler.py's `industry_brief_refresh` and `competitor_brief_refresh` jobs
(each every 24h, real APScheduler interval) — competitor Briefs are no longer admin-trigger-only:
the scheduler loops every active deal's own company name as the roster (agents/company_research.py
covers the same roster from the deal's-own-company angle; there's no separate "competitors" data
source in this schema, so the overlap is accepted). Reuses knowledge_base (phase5-009) rather than a
new table — industry/competitor briefs are just knowledge_base rows with no source_deal_id, marked
current via `superseded_at is null` rather than deleted when refreshed, so a prior Brief stays
queryable for audit ("the Brief said X as of date Y") instead of being silently overwritten. From the
second refresh onward, the prompt also asks the model to focus on what's changed since the prior
version's `created_at` (agents/knowledge.py::since_clause) — a request, not a guaranteed filter,
since neither web_search nor web_fetch has a server-side date-restriction parameter.

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
from agents.knowledge import get_current_knowledge_row, since_clause, supersede_and_insert
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


def refresh_industry_brief(industry: str) -> dict[str, Any]:
    current = get_current_knowledge_row("industry_insight", industry=industry)
    since = current["created_at"] if current else None
    prompt = INDUSTRY_BRIEF_PROMPT.format(industry=industry) + since_clause(since)
    result = _synthesize("industry_brief", prompt)
    embedding = embed_text(result["brief"], input_type="document")

    client = get_client()
    return supersede_and_insert(
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
    current = get_current_knowledge_row("competitor_insight", company_name=company_name)
    since = current["created_at"] if current else None
    prompt = COMPETITOR_BRIEF_PROMPT.format(company=company_name, industry=industry) + since_clause(since)
    result = _synthesize("competitor_brief", prompt)
    embedding = embed_text(result["brief"], input_type="document")

    client = get_client()
    return supersede_and_insert(
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
    return get_current_knowledge_row("industry_insight", industry=industry)
