-- Real scheduled background jobs (system-architecture.md Section 8's "scheduled background
-- check" for 4.3 Key-date notifier, and the same infrastructure retrofitted onto
-- agents/industry_brief.py's Briefs and agents/learning_agent.py's research cycles per the notes
-- left in phase6-002/003's reports). A real in-process APScheduler (backend/app/scheduler.py)
-- fires these on a real interval, not client-side polling — this table is the real, checkable
-- proof a job actually ran on schedule, not just whenever a user happened to load a page.

create table public.scheduled_run_log (
  id uuid primary key default gen_random_uuid(),
  job_name text not null,
  status text not null check (status in ('success', 'error')),
  detail text,
  started_at timestamptz not null default now()
);

create index scheduled_run_log_job_name_idx on public.scheduled_run_log(job_name);

grant select, insert, update, delete on public.scheduled_run_log to service_role;
