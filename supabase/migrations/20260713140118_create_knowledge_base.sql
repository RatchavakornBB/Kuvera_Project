-- Knowledge Agent (system-architecture.md Section 10.1/10.2) — full spec including real
-- pgvector semantic search, built at the user's explicit request after this was previously
-- deferred. One row per promoted knowledge category per deal, embedded via Voyage AI
-- (agents/embeddings.py) so risk_flagger/pricing_advisor can retrieve genuine historical
-- precedent via cosine-distance search, not lightweight context-stuffing.

create extension if not exists vector;

create table public.knowledge_base (
  id uuid primary key default gen_random_uuid(),
  source_deal_id uuid references public.deals(id) on delete set null,
  category text not null check (category in (
    'deal_profile', 'industry_insight', 'company_insight', 'competitor_insight',
    'evaluation_approach', 'analysis_approach', 'strategy_planning_approach',
    'outcome', 'risk_signals_resolution', 'prompt_engineering', 'loop_engineering'
  )),
  company_name text,
  industry text,
  -- Structured, category-specific fields (see system-architecture.md's Knowledge
  -- schema table for what belongs in each category).
  content jsonb not null default '{}',
  -- The real Claude-written narrative this record's embedding is generated from —
  -- also what's shown in the Admin Knowledge Base tab and injected into a
  -- retrieving node's prompt as historical precedent.
  summary text not null,
  -- voyage-3 produces 1024-dim embeddings (agents/embeddings.py).
  embedding vector(1024),
  created_at timestamptz not null default now()
);

create index knowledge_base_industry_idx on public.knowledge_base(industry);
create index knowledge_base_category_idx on public.knowledge_base(category);
create index knowledge_base_embedding_idx
  on public.knowledge_base using hnsw (embedding vector_cosine_ops);

grant select, insert, update, delete on public.knowledge_base to service_role;
