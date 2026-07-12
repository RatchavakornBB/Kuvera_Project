-- Analyst Lead run history — not one of the 8 deal-management models in
-- system-architecture.md Section 3.1, but required infrastructure for the
-- /deals/{id}/analyze endpoint's response (Section 4.1) and the lightweight
-- contradiction check on re-upload (Section 6 Phase 2 / Section 10.5,
-- scoped down): "last stored version" means the most recent row here for a
-- deal, ordered by created_at.
create table public.analyses (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  document_id uuid references public.documents(id),
  summary text not null,
  risk_flags jsonb not null default '[]',
  ic_memo_draft text,
  pricing_note text,
  created_at timestamptz not null default now()
);

create index analyses_deal_id_idx on public.analyses(deal_id);

grant select, insert, update, delete on public.analyses to service_role;
