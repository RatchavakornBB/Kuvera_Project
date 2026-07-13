Scope: agents/industry_brief.py, agents/adapters/model_adapter.py, supabase/migrations/<new>,
backend/app/services/knowledge.py, backend/app/routes/knowledge.py, frontend/src/lib/api.ts,
frontend/src/components/admin/KnowledgeBaseTab.tsx
Depends on: phase5-009 (Knowledge Agent core + pgvector infra), reuses knowledge_base directly —
no new table.

Scope: extends the Knowledge Agent (phase5-009) to cover Industry Insight and Competitor Insight,
the two categories deliberately left unpopulated in phase5-009 because they need real current
outside-world information, not deal data. Uses Claude's real `web_search` server tool (same as
agents/nodes/web_research.py) — genuine research, not fabricated commentary. On-demand for now
(admin-triggered); a true periodic schedule needs the same scheduler infrastructure phase6's
Key-date notifier task will build, and should be retrofitted to call these once that exists.

Company Insight (the third previously-unpopulated category) is not a new deliverable here — per
system-architecture.md, it's meant to be "retrieved fresh via RAG on every query," which is already
what agents/knowledge.py's historical_precedent_context() + deal_context.py's context-stuffing do;
there's no separate stored-Brief form of it to build.

DoD:
  - [x] `agents/industry_brief.py`: `refresh_industry_brief()` / `refresh_competitor_brief()`, real
        Claude + web_search synthesis, real Voyage embedding, inserted into the existing
        `knowledge_base` table (source_deal_id null — these aren't deal-specific)
  - [x] `industry_brief` / `competitor_brief` added to `AGENT_MODELS` + seeded `agent_configs` rows
        so they're governable from Admin like every other real agent
  - [x] Backend: `POST /admin/knowledge-base/refresh-industry-brief`,
        `POST /admin/knowledge-base/refresh-competitor-brief`
  - [x] Frontend: a "Refresh a Brief" form in the Knowledge Base tab
  - [x] Verified end to end with real web search: refreshed a real Logistics industry brief (real
        current market-size/CAGR figures came back) and a real DHL Supply Chain competitor brief
        (real, verifiable market-share figures), both stored with real embeddings, both visible and
        correctly labeled in a real browser session with zero console errors
