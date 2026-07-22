-- Project-plan / Gantt support (phase7-011).
-- Each deal gets a set of ordered "phases" (the PM analogue of the 7 pipeline
-- stages), and tasks gain scheduling fields so they can be drawn as bars on a
-- timeline. The 7 stages are seeded as default phases per deal (source='stage'),
-- but phases live in their own table so a user can add/rename/reorder custom
-- phases and drag tasks between them — mirroring the flexible phase list in a
-- typical project-management timeline. RLS stays disabled per the core-schema
-- migration; service_role gets full access, anon/authenticated get nothing.

create table public.deal_phases (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  name text not null,
  sort_order int not null default 0,
  color text,
  source text not null default 'custom' check (source in ('stage', 'custom')),
  collapsed boolean not null default false,
  created_at timestamptz not null default now()
);
create index deal_phases_deal_id_idx on public.deal_phases(deal_id);

-- Scheduling fields on tasks. `due_date` is kept for back-compat with the flat
-- Tasks & Notes list; the timeline uses start_date/end_date for bar geometry
-- and phase_id to group under a phase. Nulls mean "not scheduled yet" — such a
-- task shows in the phase's unscheduled tray rather than on the time grid.
alter table public.tasks
  add column phase_id uuid references public.deal_phases(id) on delete set null,
  add column start_date date,
  add column end_date date,
  add column sort_order int not null default 0;
create index tasks_phase_id_idx on public.tasks(phase_id);

-- Backfill: give every existing deal the 7 stage phases in pipeline order.
insert into public.deal_phases (deal_id, name, sort_order, source)
select d.id, s.name, s.ord, 'stage'
from public.deals d
cross join (values
  ('Lead', 0),
  ('NDA', 1),
  ('Sourcing & Screening', 2),
  ('Valuation & Bidding', 3),
  ('Strategy & Preparation', 4),
  ('Due Diligence', 5),
  ('Negotiation & Closing', 6)
) as s(name, ord);

-- Repeat the grant block for every new public table (core-schema migration note).
grant usage on schema public to service_role;
grant select, insert, update, delete on public.deal_phases to service_role;
