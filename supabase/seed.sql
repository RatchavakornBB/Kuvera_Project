-- Phase 1 demo data — runs automatically on `supabase db reset` (see
-- supabase/config.toml [db.seed] sql_paths). Always starts from an empty
-- database, so this is safe to re-run as often as needed.

-- Single seeded demo user (system-architecture.md Section 4.4).
-- auth.users + auth.identities inserted directly since this runs before any
-- app code exists to call the Auth Admin API.
-- GoTrue's Go model scans every *_token / email_change column into a plain
-- (non-nullable) string — any of them left NULL fails sign-in with
-- "converting NULL to string is unsupported" (found by reading the auth
-- container's logs, one column at a time). Set all of them to '' explicitly
-- rather than trusting column defaults.
insert into auth.users (
  instance_id, id, aud, role, email, encrypted_password,
  email_confirmed_at, raw_app_meta_data, raw_user_meta_data,
  confirmation_token, recovery_token, email_change_token_new, email_change,
  email_change_token_current, phone_change, phone_change_token, reauthentication_token,
  created_at, updated_at
) values (
  '00000000-0000-0000-0000-000000000000',
  'a0000000-0000-0000-0000-000000000001',
  'authenticated', 'authenticated', 'demo@kuvera.capital',
  crypt('kuvera-demo', gen_salt('bf')),
  now(), '{"provider":"email","providers":["email"]}', '{}',
  '', '', '', '',
  '', '', '', '',
  now(), now()
);

insert into auth.identities (
  id, provider_id, user_id, identity_data, provider, created_at, updated_at
) values (
  gen_random_uuid(), 'a0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001',
  '{"sub":"a0000000-0000-0000-0000-000000000001","email":"demo@kuvera.capital"}', 'email', now(), now()
);

insert into public.users (id, full_name, initials, role) values
  ('a0000000-0000-0000-0000-000000000001', 'Priya Sharma', 'PS', 'Partner');

-- Deal A — worked example, system-architecture.md Section 3.3, exactly.
insert into public.deals (id, name, client, industries, stage, status, owner_id) values
  ('d0000000-0000-0000-0000-00000000000a', 'Deal A', 'Khun A', '{Healthcare}', 'Due Diligence', 'On track', 'a0000000-0000-0000-0000-000000000001');

insert into public.contacts (deal_id, name, role, company, last_contacted_at) values
  ('d0000000-0000-0000-0000-00000000000a', 'Khun A', 'CEO', 'Deal A', now() - interval '3 days');

insert into public.documents (deal_id, name, type, status) values
  ('d0000000-0000-0000-0000-00000000000a', 'FY2025 audited financial statements', 'Financial', 'requested');

insert into public.milestones (deal_id, label, occurred_at, sort_order) values
  ('d0000000-0000-0000-0000-00000000000a', 'Lead identified', now() - interval '90 days', 0),
  ('d0000000-0000-0000-0000-00000000000a', 'NDA signed', now() - interval '75 days', 1),
  ('d0000000-0000-0000-0000-00000000000a', 'Due diligence started', now() - interval '20 days', 2),
  ('d0000000-0000-0000-0000-00000000000a', 'Negotiation & closing', null, 3);

insert into public.tasks (deal_id, text, owner_id, due_date, done) values
  ('d0000000-0000-0000-0000-00000000000a', 'Financial model', null, current_date + 10, false);

insert into public.dd_items (deal_id, item, status, owner_id) values
  ('d0000000-0000-0000-0000-00000000000a', 'Cap table', 'received', 'a0000000-0000-0000-0000-000000000001'),
  ('d0000000-0000-0000-0000-00000000000a', 'FY2025 audited financial statements', 'pending', null);

insert into public.meeting_notes (deal_id, occurred_at, author_id, attendees, summary) values
  ('d0000000-0000-0000-0000-00000000000a', now() - interval '3 days', 'a0000000-0000-0000-0000-000000000001', '{"Khun A","Priya Sharma"}', 'Walked through the FY2025 audit timeline with Khun A; statements expected within two weeks.');

-- Two additional demo deals for dashboard variety (Section 6 Phase 1: "2-3
-- example deals").
insert into public.deals (id, name, client, industries, stage, status, owner_id) values
  ('d0000000-0000-0000-0000-00000000000b', 'Horizon Freight Corp', 'Somsak L.', '{Logistics}', 'Sourcing & Screening', 'Needs attention', 'a0000000-0000-0000-0000-000000000001'),
  ('d0000000-0000-0000-0000-00000000000c', 'Nova Fintech', 'Ariya P.', '{Fintech}', 'Negotiation & Closing', 'On track', 'a0000000-0000-0000-0000-000000000001');
