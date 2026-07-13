"""Knowledge Agent (system-architecture.md Section 10.1) — real promotion pipeline + real
pgvector retrieval. On deal close, synthesizes structured patterns from that deal's ACTUAL data
(via agents/deal_context.py's existing real data-gathering + a real Claude call) into firm-wide
knowledge; risk_flagger and pricing_advisor retrieve genuine historical precedent from it via
cosine-distance search over real Voyage embeddings.

Categories populated per deal close: deal_profile, evaluation_approach, analysis_approach,
strategy_planning_approach, outcome, risk_signals_resolution, prompt_engineering,
loop_engineering — all grounded in this deal's real rows or the system's real current
configuration. NOT populated: industry_insight, competitor_insight, company_insight — these are
meant to be periodically-refreshed cross-deal Briefs (system-architecture.md's own framing), which
needs an outside-world news/company-monitoring pipeline that doesn't exist in this build; nothing
here fabricates them just to fill the category out.
"""

import json
from datetime import date, datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

from agents.adapters.model_adapter import call_model
from agents.config import settings
from agents.db import get_client
from agents.deal_context import build_deal_context
from agents.embeddings import embed_text, embed_texts
from agents.retry import with_retry

SYNTHESIS_TOOL = {
    "name": "report_knowledge_records",
    "description": "Report the structured knowledge records synthesized from this closed deal, grounded only in the real deal data provided.",
    "input_schema": {
        "type": "object",
        "properties": {
            "evaluation_approach": {
                "type": "object",
                "properties": {
                    "user_decisions": {"type": "string", "description": "Key decisions made during evaluation, drawn from tasks/notes/analysis"},
                    "evaluation_methodology": {"type": "string", "description": "How this deal was evaluated"},
                    "outcome_comments": {"type": "string", "description": "Any user commentary on how the evaluation played out"},
                },
                "required": ["user_decisions", "evaluation_methodology", "outcome_comments"],
            },
            "analysis_approach": {
                "type": "object",
                "properties": {
                    "data_weighted": {"type": "string", "description": "What data the analysis weighted most heavily"},
                    "what_was_flagged": {"type": "string", "description": "What the analysis flagged as risks or notable"},
                },
                "required": ["data_weighted", "what_was_flagged"],
            },
            "strategy_planning_approach": {
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "How the deal strategy was built, combining agent output and user input"},
                },
                "required": ["description"],
            },
            "risk_signals_resolution": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "risk": {"type": "string"},
                        "materialized": {"type": "string", "enum": ["yes", "no", "unknown"]},
                        "resolution": {"type": "string"},
                    },
                    "required": ["risk", "materialized", "resolution"],
                },
                "description": "Risks identified during evaluation and whether each one materialized, grounded in the real risk_flags provided",
            },
        },
        "required": ["evaluation_approach", "analysis_approach", "strategy_planning_approach", "risk_signals_resolution"],
    },
}

SYNTHESIS_PROMPT = """You are the Knowledge Agent, promoting a closed deal's real history into
firm-wide knowledge for future deals. Everything below is real data from this one deal — do not
invent facts not present in it. If a field has no real basis in the data, say so plainly (e.g.
"not enough data to determine") rather than guessing. Call report_knowledge_records.

DEAL DATA:
{deal_context}

OUTCOME: {outcome}
"""


def _normalize_field(value: Any, fallback_key: str) -> Any:
    """Claude's tool_use output is usually schema-conformant but not always —
    an object-typed field occasionally comes back as a JSON-encoded string
    instead of a nested object (seen in real testing here). Parse it back to
    a real object rather than storing an unreadable string blob; if it isn't
    valid JSON either, wrap the raw string so nothing is silently dropped."""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return {fallback_key: value}
    return value


def _record_summary(category: str, content: dict[str, Any]) -> str:
    """A deterministic, non-fabricated text rendering of a record's structured
    content — what gets embedded and what an Admin reads in the Knowledge Base
    tab. No extra LLM call needed; this is just a formatter."""
    parts = [f"[{category}]"]
    for key, value in content.items():
        parts.append(f"{key}: {value}")
    return "\n".join(parts)


def promote_deal_to_knowledge(deal_id: str, outcome: str) -> list[dict[str, Any]]:
    client = get_client()
    deal_rows = client.table("deals").select("*").eq("id", deal_id).execute().data
    if not deal_rows:
        raise ValueError(f"No deal with id {deal_id}")
    deal = deal_rows[0]

    context = build_deal_context(deal_id)

    def _call_and_parse() -> dict[str, Any]:
        response = call_model(
            "knowledge_promoter",
            messages=[{"role": "user", "content": SYNTHESIS_PROMPT.format(deal_context=context, outcome=outcome)}],
            tools=[SYNTHESIS_TOOL],
            max_tokens=2048,
        )
        for block in response.content:
            if block.type == "tool_use" and block.name == "report_knowledge_records":
                return block.input
        raise ValueError(f"model did not call report_knowledge_records (stop_reason={response.stop_reason!r})")

    synthesized = with_retry("knowledge_promoter", _call_and_parse)
    for key in ("evaluation_approach", "analysis_approach", "strategy_planning_approach"):
        synthesized[key] = _normalize_field(synthesized.get(key, {}), fallback_key="description")
    risk_signals = synthesized.get("risk_signals_resolution", [])
    if isinstance(risk_signals, str):
        risk_signals = _normalize_field(risk_signals, fallback_key="signals")
        risk_signals = risk_signals if isinstance(risk_signals, list) else [risk_signals]
    synthesized["risk_signals_resolution"] = risk_signals

    days_to_close = (datetime.now(timezone.utc).date() - date.fromisoformat(deal["created_at"][:10])).days

    contacts = client.table("contacts").select("*").eq("deal_id", deal_id).execute().data
    agent_configs = client.table("agent_configs").select("agent_name, model_id, skill_content").execute().data
    analyst_configs = {
        c["agent_name"]: c
        for c in agent_configs
        if c["agent_name"] in ("doc_summarizer", "risk_flagger", "ic_memo_drafter", "pricing_advisor")
    }

    records: list[dict[str, Any]] = [
        {
            "category": "deal_profile",
            "content": {
                "company_name": deal["name"],
                "client": deal["client"],
                "industries": deal["industries"],
                "poc": [c["name"] for c in contacts],
            },
        },
        {"category": "evaluation_approach", "content": synthesized["evaluation_approach"]},
        {"category": "analysis_approach", "content": synthesized["analysis_approach"]},
        {"category": "strategy_planning_approach", "content": synthesized["strategy_planning_approach"]},
        {
            "category": "risk_signals_resolution",
            "content": {"signals": synthesized["risk_signals_resolution"]},
        },
        {
            "category": "outcome",
            "content": {"result": outcome, "days_to_close": days_to_close, "rounds_to_close": "not tracked in this schema"},
        },
        {
            "category": "prompt_engineering",
            "content": {
                name: {"model_id": cfg["model_id"], "skill_content": cfg["skill_content"] or "(base prompt only)"}
                for name, cfg in analyst_configs.items()
            },
        },
        {
            "category": "loop_engineering",
            "content": {
                "pattern": "gate (doc_summarizer -> risk_flagger) then Send() fan-out (ic_memo_drafter, pricing_advisor)",
                "checkpointer": "Postgres (langgraph-checkpoint-postgres)",
                "retry": "bounded, max 2 attempts per node",
                "note": "this orchestration pattern is currently uniform across all deals, not deal-specific",
            },
        },
    ]

    summaries = [_record_summary(r["category"], r["content"]) for r in records]
    embeddings = embed_texts(summaries, input_type="document")

    inserted = []
    for record, summary, embedding in zip(records, summaries, embeddings):
        res = (
            client.table("knowledge_base")
            .insert(
                {
                    "source_deal_id": deal_id,
                    "category": record["category"],
                    "company_name": deal["name"],
                    "industry": deal["industries"][0] if deal["industries"] else None,
                    "content": record["content"],
                    "summary": summary,
                    "embedding": embedding,
                }
            )
            .execute()
        )
        inserted.append(res.data[0])

    return inserted


def search_knowledge(
    query_text: str, industry: str | None = None, category: str | None = None, limit: int = 5
) -> list[dict[str, Any]]:
    query_embedding = embed_text(query_text, input_type="query")
    embedding_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"

    conditions = []
    params: list[Any] = [embedding_literal]
    if industry:
        conditions.append("industry = %s")
        params.append(industry)
    if category:
        conditions.append("category = %s")
        params.append(category)
    where_clause = f"where {' and '.join(conditions)}" if conditions else ""

    sql = f"""
        select id, source_deal_id, category, company_name, industry, content, summary,
               1 - (embedding <=> %s::vector) as similarity
        from knowledge_base
        {where_clause}
        order by embedding <=> %s::vector
        limit %s
    """
    params.append(embedding_literal)
    params.append(limit)

    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def get_deal_industry(deal_id: str) -> str | None:
    client = get_client()
    rows = client.table("deals").select("industries").eq("id", deal_id).execute().data
    if not rows or not rows[0]["industries"]:
        return None
    return rows[0]["industries"][0]


def historical_precedent_context(deal_id: str, query_text: str, limit: int = 3) -> str:
    """Best-effort real retrieval for risk_flagger/pricing_advisor to inject as
    extra context. Returns "" if nothing relevant exists OR if retrieval itself
    fails (e.g. an embeddings-provider rate limit, a real failure mode hit
    during development). This is supplementary context, not a required output
    field — unlike risk_flags itself, a retrieval failure here must not break
    the node's core output, so it is deliberately swallowed, not propagated as
    a NodeFailure."""
    if not query_text:
        return ""
    try:
        industry = get_deal_industry(deal_id)
        results = search_knowledge(query_text, industry=industry, limit=limit)
    except Exception:
        return ""
    if not results:
        return ""

    lines = ["\n\nHISTORICAL PRECEDENT FROM PAST CLOSED DEALS (real, retrieved by semantic search — context only, not a fact about THIS deal):"]
    for r in results:
        lines.append(f"- [{r['category']}, {r['company_name']}] {r['summary'][:300]}")
    return "\n".join(lines)


def list_knowledge(industry: str | None = None, category: str | None = None) -> list[dict[str, Any]]:
    client = get_client()
    query = client.table("knowledge_base").select("id, source_deal_id, category, company_name, industry, content, summary, created_at")
    if industry:
        query = query.eq("industry", industry)
    if category:
        query = query.eq("category", category)
    return query.order("created_at", desc=True).execute().data
