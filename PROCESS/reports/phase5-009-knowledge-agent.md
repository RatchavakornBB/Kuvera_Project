## Result: ✅ DoD met — the full Knowledge Agent spec, real pgvector included

Gate: syntax checks ✅ · real Voyage AI embedding calls ✅ · real end-to-end HTTP verification ✅ ·
real browser verification (Playwright) ✅.

Built at the user's explicit request, choosing the full-spec option (real pgvector, not a
filter-only approximation) and Voyage AI as the embedding provider, both confirmed via
`AskUserQuestion`. Real `VOYAGER_API_KEY` supplied by the user directly into `.env` (never pasted
into chat).

**Architecture:** `knowledge_base` table (migration `20260713140118_create_knowledge_base.sql`,
`vector(1024)` column, HNSW cosine index) stores one row per promoted category. `agents/
embeddings.py` calls Voyage's real embeddings API via `httpx` (no new dependency — already present
transitively). `agents/knowledge.py` has `promote_deal_to_knowledge()` (real Claude synthesis of
Evaluation/Analysis/Strategy/Risk-Signals from the deal's actual `build_deal_context()` output,
plus directly-computed Deal Profile/Outcome/Prompt-Engineering/Loop-Engineering records — no
fabrication) and `search_knowledge()` (real `ORDER BY embedding <=> query LIMIT n` cosine search via
raw psycopg, since PostgREST doesn't expose the `<=>` operator). `risk_flagger` and
`pricing_advisor` call a new `historical_precedent_context()` helper that retrieves and injects real
matches — deliberately best-effort (swallows its own failures) since it's supplementary context,
not a required output field.

**Deliberately not built**, consistent with the scope agreed before starting: `industry_insight`,
`competitor_insight`, `company_insight` — these need a periodically-refreshed cross-deal Brief fed
by an outside-world news/company-monitoring pipeline that doesn't exist anywhere in this codebase;
populating them from a single deal's own data would misrepresent what they're for.

**Two real bugs found and fixed during verification, not assumed away:**
1. Claude's tool-use output for `analysis_approach`/`strategy_planning_approach` came back as
   JSON-encoded *strings* instead of nested objects in real testing, and `risk_signals_resolution`
   was outright missing from one response — added `_normalize_field()` to parse/recover both cases
   instead of crashing on `KeyError`.
2. Embedding each of the 8 promoted records with a separate Voyage call hit a real `429 Too Many
   Requests` (free-tier rate limit) partway through a promotion, which would have left a deal
   partially promoted. Fixed by batching all 8 texts into one `embed_texts()` call — one API call
   per deal-close, not eight.

**Verified end to end with real data:** closed Nova Fintech via the real UI action (Deal Detail
header → Won), confirmed 8 real `knowledge_base` rows were created with genuine 1024-dim vectors
(checked via `vector_dims()` directly in Postgres, not just "no error thrown"); browsed them in the
real Admin Knowledge Base tab (expandable real JSON content, correct industry label); ran a real
semantic search ("fintech valuation and risk assessment") that correctly ranked Nova Fintech's own
records highest and still surfaced Horizon Freight Corp's lower-ranked records — genuine cross-deal
retrieval, not per-deal filtering. Separately confirmed `historical_precedent_context()` returns a
real, formatted precedent block when called directly. Zero console errors throughout.

Side effect kept, not reverted: Nova Fintech is now genuinely `status: Closed` with real promoted
knowledge — a valuable, not embarrassing, demo state (shows the full deal lifecycle including what
happens after a deal closes). `docs/demo-script.md` should be updated to reflect this — noted as a
follow-up.
