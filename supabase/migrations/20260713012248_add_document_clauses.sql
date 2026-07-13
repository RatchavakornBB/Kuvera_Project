-- Contracts Lead's 4.2 Clause Extractor output — a contract is just a
-- Document with type='Contract' (system-architecture.md Section 3.1's
-- Document model already covers contracts; no separate Contract model).
alter table public.documents add column clauses jsonb not null default '[]';
