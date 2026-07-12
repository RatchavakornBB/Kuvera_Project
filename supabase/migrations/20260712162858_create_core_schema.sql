-- Core deal-management schema — 8 models per docs/system-architecture.md Section 3.1.
-- RLS intentionally left disabled: full RBAC/deal-level confidentiality is Phase 3
-- scope (system-architecture.md Section 1.4 / 14), not this MVP week. Every table
-- below is scoped to `public` and reachable by the single seeded demo user
-- (system-architecture.md Section 4.4).

create extension if not exists "pgcrypto";

-- USER --------------------------------------------------------------------
-- 1:1 profile row for each Supabase Auth user, carrying the app-level role.
create table public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  full_name text not null,
  initials text not null,
  role text not null check (role in ('Partner', 'Deal Lead', 'Analyst', 'Admin', 'Viewer')),
  created_at timestamptz not null default now()
);

-- DEAL ----------------------------------------------------------------------
create table public.deals (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  client text not null,
  industries text[] not null default '{}',
  stage text not null check (stage in (
    'Lead', 'NDA', 'Sourcing & Screening', 'Valuation & Bidding',
    'Strategy & Preparation', 'Due Diligence', 'Negotiation & Closing'
  )),
  stage_entered_at timestamptz not null default now(),
  status text not null default 'On track' check (status in (
    'On track', 'Needs attention', 'Stalled', 'Closed'
  )),
  owner_id uuid references public.users(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- CONTACT ---------------------------------------------------------------------
create table public.contacts (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  name text not null,
  role text,
  company text,
  last_contacted_at timestamptz,
  created_at timestamptz not null default now()
);

-- DOCUMENT --------------------------------------------------------------------
create table public.documents (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  name text not null,
  type text not null,
  storage_path text,
  status text not null default 'requested' check (status in (
    'requested', 'received', 'pending', 'under_review', 'approved', 'rejected'
  )),
  summary text,
  key_date date,
  uploaded_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

-- TASK --------------------------------------------------------------------
create table public.tasks (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  text text not null,
  owner_id uuid references public.users(id),
  due_date date,
  done boolean not null default false,
  created_at timestamptz not null default now()
);

-- MEETING NOTE ----------------------------------------------------------------
create table public.meeting_notes (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  occurred_at timestamptz not null default now(),
  author_id uuid references public.users(id),
  attendees text[] not null default '{}',
  summary text,
  action_items text[] not null default '{}',
  created_at timestamptz not null default now()
);

-- DD ITEM (due diligence checklist) --------------------------------------------
create table public.dd_items (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  item text not null,
  status text not null default 'pending' check (status in ('pending', 'received', 'reviewed')),
  owner_id uuid references public.users(id),
  created_at timestamptz not null default now()
);

-- MILESTONE -----------------------------------------------------------------
create table public.milestones (
  id uuid primary key default gen_random_uuid(),
  deal_id uuid not null references public.deals(id) on delete cascade,
  label text not null,
  occurred_at timestamptz,
  sort_order int not null default 0,
  created_at timestamptz not null default now()
);

-- Indexes on the foreign key every child table shares.
create index deals_owner_id_idx on public.deals(owner_id);
create index contacts_deal_id_idx on public.contacts(deal_id);
create index documents_deal_id_idx on public.documents(deal_id);
create index tasks_deal_id_idx on public.tasks(deal_id);
create index meeting_notes_deal_id_idx on public.meeting_notes(deal_id);
create index dd_items_deal_id_idx on public.dd_items(deal_id);
create index milestones_deal_id_idx on public.milestones(deal_id);

-- New tables are no longer auto-exposed to the Data API roles by default on
-- current Supabase CLI versions (see the commented-out `auto_expose_new_tables`
-- note in supabase/config.toml) — without this, PostgREST returns
-- "permission denied for table X" even with the service_role key. RLS stays
-- disabled per this migration's top comment, so service_role is granted full
-- access; anon/authenticated are intentionally NOT granted anything yet since
-- there's no direct-from-frontend Supabase usage in Phase 1 (backend-only,
-- via service_role). Repeat this grant block in any future migration that
-- adds a new public table.
grant usage on schema public to service_role;
grant select, insert, update, delete on
  public.users,
  public.deals,
  public.contacts,
  public.documents,
  public.tasks,
  public.meeting_notes,
  public.dd_items,
  public.milestones
to service_role;
