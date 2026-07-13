"""Industry & Competitor Insight Briefs (system-architecture.md Section 10.1) — the "fine-tuning-
style" storage the doc describes: a compact reference document refreshed periodically and reused
as background context, rather than retrieved fresh via RAG on every query (that's what Company
Insight is for, and it's already covered by agents/knowledge.py's deal-scoped retrieval).

On-demand for now — no scheduler exists yet in this codebase. phase6's Key-date notifier task will
build a real in-process scheduler (APScheduler); once that exists, it should also call
refresh_industry_brief()/refresh_competitor_brief() on a real interval, making this genuinely
periodic rather than admin-triggered. Reuses knowledge_base (phase5-009) rather than a new table —
industry/competitor briefs are just knowledge_base rows with no source_deal_id.

Uses Claude's real web_search server tool (same as agents/nodes/web_research.py) for current,
real information — not fabricated industry commentary."""

from typing import Any

from agents.adapters.model_adapter import call_model
from agents.db import get_client
from agents.embeddings import embed_text
from agents.retry import with_retry

WEB_SEARCH_TOOL = {"type": "web_search_20250305", "name": "web_search", "max_uses": 5}

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


def _synthesize(agent_name: str, prompt: str) -> str:
    def _call() -> str:
        response = call_model(agent_name, messages=[{"role": "user", "content": prompt}], tools=[WEB_SEARCH_TOOL], max_tokens=2048)
        text_parts = [block.text for block in response.content if block.type == "text"]
        if not text_parts:
            raise ValueError(f"model returned no text block (stop_reason={response.stop_reason!r})")
        return "".join(text_parts)

    return with_retry(agent_name, _call)


def refresh_industry_brief(industry: str) -> dict[str, Any]:
    brief_text = _synthesize("industry_brief", INDUSTRY_BRIEF_PROMPT.format(industry=industry))
    embedding = embed_text(brief_text, input_type="document")

    client = get_client()
    # A Brief is a current snapshot, not an accumulating history — replace any
    # existing one for this industry rather than piling up stale duplicates.
    client.table("knowledge_base").delete().eq("category", "industry_insight").eq("industry", industry).execute()
    res = (
        client.table("knowledge_base")
        .insert(
            {
                "category": "industry_insight",
                "industry": industry,
                "company_name": None,
                "content": {"brief": brief_text},
                "summary": brief_text,
                "embedding": embedding,
            }
        )
        .execute()
    )
    return res.data[0]


def refresh_competitor_brief(company_name: str, industry: str) -> dict[str, Any]:
    brief_text = _synthesize("competitor_brief", COMPETITOR_BRIEF_PROMPT.format(company=company_name, industry=industry))
    embedding = embed_text(brief_text, input_type="document")

    client = get_client()
    client.table("knowledge_base").delete().eq("category", "competitor_insight").eq("company_name", company_name).execute()
    res = (
        client.table("knowledge_base")
        .insert(
            {
                "category": "competitor_insight",
                "industry": industry,
                "company_name": company_name,
                "content": {"brief": brief_text},
                "summary": brief_text,
                "embedding": embedding,
            }
        )
        .execute()
    )
    return res.data[0]
