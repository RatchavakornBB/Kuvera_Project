-- Full Contradiction & Hypothesis confidence-scoring engine (5day-build-timeline.md's cut-scope
-- table references "Section 10.5" for this, but no such section exists in system-architecture.md
-- — the only real spec is that one line: "status ranks, corroboration counting, versioned
-- promotion into Knowledge Agent." Designed here since nothing more detailed exists to follow.
--
-- Extends, not replaces, the lightweight contradiction check already live in risk_flagger.py
-- (a plain high-severity risk flag on re-analysis) — that stays exactly as-is. This table adds
-- real structured tracking behind it: each contradiction gets a status rank, and if the same
-- contradiction recurs across re-analyses (matched via real pgvector similarity, since the
-- description text is freshly LLM-generated each time, never identical), its corroboration count
-- increments instead of creating a duplicate row.

create table public.contradictions (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  description text not null,
  source_excerpt text,
  status text not null default 'unconfirmed' check (status in (
    'unconfirmed', 'corroborated', 'resolved', 'refuted'
  )),
  corroboration_count integer not null default 1,
  embedding vector(1024),
  first_flagged_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  resolved_at timestamptz,
  resolution_note text,
  promoted_to_knowledge_base boolean not null default false
);

create index contradictions_deal_id_idx on public.contradictions(deal_id);
create index contradictions_status_idx on public.contradictions(status);
create index contradictions_embedding_idx
  on public.contradictions using hnsw (embedding vector_cosine_ops);

grant select, insert, update, delete on public.contradictions to service_role;
