Scope: backend/requirements.txt, supabase/migrations/<new>_create_scheduled_run_log.sql,
backend/app/scheduler.py, backend/app/routes/scheduler.py, backend/app/main.py,
frontend/src/lib/api.ts, frontend/src/components/admin/SchedulerStatusPanel.tsx,
frontend/src/components/admin/KnowledgeBaseTab.tsx, docs/demo-script.md
Depends on: phase4-004 (key-date notifier, on-demand version), phase6-002 (Industry Brief refresh,
on-demand version)

Scope: closes the "on-demand, not true cron" deviation logged in phase4-004 and phase6-002's
reports. A real in-process APScheduler (BackgroundScheduler, a real thread — not asyncio, since
agents/ uses synchronous clients throughout) fires jobs on a real interval independent of any
client having the app open: key-date checks every 5 minutes (cheap, a DB query), Industry Brief
refresh every 24h (real Claude + web_search calls, deliberately not more frequent to avoid firing
costly real API calls during a live session). Learning Agent's research cycles stay on-demand —
they need a specific topic to be meaningful, and auto-firing real paid research calls on a timer
without one would be guessing, not a real scheduled check.

DoD:
  - [x] `apscheduler` installed, added to requirements.txt
  - [x] `scheduled_run_log` table — real, checkable proof a job ran on schedule, not fabricated
  - [x] `backend/app/scheduler.py`: real jobs wired to FastAPI's actual startup/shutdown events
  - [x] `GET /admin/scheduler/status` (real registered jobs + real next_run_time),
        `GET /admin/scheduler/runs` (real run history)
  - [x] Frontend: `SchedulerStatusPanel` in the Knowledge Base tab, replacing the stale
        "on-demand for now" language
  - [x] docs/demo-script.md updated — Key-date notifier's Live vs Design-only row, plus two stale
        entries found and fixed while doing this (Agent Hub and Learning Agent rows/Q&A still
        described their pre-phase6-003/005 state)
  - [x] Verified at three levels, not just "the endpoint returns 200": (1) confirmed the real
        FastAPI startup event actually registered both jobs with correct real `next_run_time`
        values; (2) an isolated APScheduler instance with a 2-second interval fired 4 real times in
        9 seconds, proving the timer mechanism itself works in this Windows environment; (3) called
        the real job function directly and confirmed it wrote a real, correct row to
        `scheduled_run_log` ("1 upcoming key date(s) found", matching known real data)
