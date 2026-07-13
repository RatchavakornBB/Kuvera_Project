Scope: supabase/migrations/<new>_create_knowledge_base.sql, agents/config.py,
agents/embeddings.py, agents/knowledge.py, agents/nodes/risk_flagger.py,
agents/nodes/pricing_advisor.py, backend/app/services/deals.py, backend/app/routes/deals.py,
backend/app/services/knowledge.py, backend/app/routes/knowledge.py, backend/app/main.py,
frontend/src/lib/api.ts, frontend/src/components/admin/KnowledgeBaseTab.tsx,
frontend/src/pages/AdminGovernance.tsx, frontend/src/components/dealDetail/DealDetailHeader.tsx
Depends on: phase5-008 (done). User explicitly asked for the full system-architecture.md Section
10.1 spec including real pgvector semantic search (confirmed via AskUserQuestion), and chose
Voyage AI as the embedding provider (also confirmed via AskUserQuestion). Requires a real
VOYAGE_API_KEY in .env, supplied directly by the user (never pasted into chat).

Scope (system-architecture.md Section 10.1 / 10.2):
  - Real `knowledge_base` table: one row per promoted category
    (deal_profile/industry_insight/company_insight/competitor_insight/evaluation_approach/
    analysis_approach/strategy_planning_approach/outcome/risk_signals_resolution/
    prompt_engineering/loop_engineering), JSONB `content` + a real Claude-written `summary` +
    a real Voyage embedding of that summary (`vector(1024)`, model `voyage-3`)
  - Real promotion pipeline: a "Close Deal" action (real API, real UI) that synthesizes the
    Evaluation/Analysis/Strategy/Risk-Signals/Outcome records from that deal's ACTUAL data
    (agents/deal_context.py's existing real data-gathering, not fabricated) via a real Claude call,
    embeds each with Voyage, and inserts them
  - Real retrieval: risk_flagger and pricing_advisor query knowledge_base via real pgvector
    cosine-distance search (embed the current deal's summary, `ORDER BY embedding <=> query LIMIT
    N`) and inject the top historical-precedent matches into their prompts — genuine RAG, not the
    lightweight context-stuffing pattern used elsewhere in this codebase
  - Admin's Knowledge Base tab (previously explicitly skipped in phase5-006) is now real:
    browsable, filterable by industry/category, click a record to see its full JSONB content
  - Explicitly NOT built: periodic Industry/Competitor Brief regeneration (no task-queue infra,
    same reasoning as the key-date notifier — an on-demand "Refresh Brief" action instead if time
    allows), Apache AGE graph traversal (JSONB + pgvector only, per the doc's own fallback note)

DoD:
  - [x] Migration creates the `vector` extension + `knowledge_base` table, real GRANTs
  - [x] `agents/embeddings.py`: real Voyage AI HTTP call (httpx, no new dependency), fails loudly
        (not silently) if VOYAGER_API_KEY is missing or the API call errors
  - [x] `agents/knowledge.py`: `promote_deal_to_knowledge()` (real Claude synthesis + real
        embeddings + insert) and `search_knowledge()` (real pgvector cosine search, optionally
        filtered by industry)
  - [x] risk_flagger and pricing_advisor inject real retrieved historical precedent into their
        prompts when knowledge_base has relevant rows
  - [x] `POST /deals/{id}/close` (real endpoint) + a real "Close Deal" UI action
  - [x] `GET /admin/knowledge-base` + real Admin Knowledge Base tab
  - [x] Verified end to end with REAL data, not fabricated: close a real deal, confirm real rows
        appear in `knowledge_base` with real non-null embeddings, confirm a real pgvector query
        against those embeddings returns them ranked correctly, and confirm risk_flagger/
        pricing_advisor's prompts actually include the retrieved precedent on a subsequent run
