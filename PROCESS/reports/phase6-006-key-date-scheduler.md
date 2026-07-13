## Result: ✅ DoD met — a genuinely real scheduler, verified at the mechanism level

Gate: real FastAPI startup verification ✅ · isolated real timer-mechanism proof ✅ · real job
execution + logging verification ✅ · real browser verification ✅.

Closes the explicit deviation logged in phase4-004 ("on-demand/polled, not a true server cron") and
phase6-002's matching note for Industry Briefs. `backend/app/scheduler.py` wires a real
`BackgroundScheduler` (a real OS thread, not asyncio — deliberate, since every `agents/` function
uses synchronous supabase-py/httpx/anthropic clients throughout this codebase, and forcing async
here would mean wrapping all of them for no real benefit) into FastAPI's actual `startup`/
`shutdown` events. Key-date checks run every 5 minutes (cheap — a plain DB query); Industry Brief
refreshes run every 24 hours, deliberately not more often, since those are real paid Claude +
web_search calls and firing them too aggressively risks unexpected cost or an unwanted live call
mid-demo.

**Verification went past "the endpoint works" to the actual scheduling mechanism**, because that's
the part that was never real before: (1) confirmed via `GET /admin/scheduler/status` against a
freshly-started real backend that both jobs registered with correct, real `next_run_time` values
computed from the real current time — not stubbed; (2) ran a fully isolated `BackgroundScheduler`
with a 2-second interval for 9 seconds and confirmed 4 real fires, proving APScheduler's timer
mechanism itself works correctly in this Windows/Python environment, independent of any of this
codebase's own job logic; (3) called `run_key_date_check()` directly and confirmed a real row
landed in `scheduled_run_log` with the correct real content ("1 upcoming key date(s) found",
matching Deal A's real contract deadline set back in phase4-004).

**Found and fixed two stale demo-script.md entries while updating it for this task** — the Agent
Hub row and its Q&A answer still described the pre-phase6-005 "static log only" state, and the
Learning Agent Q&A still said "isn't built," both now wrong after phase6-003/005. Caught by
re-reading the whole Live vs. Design-only table rather than only touching the one row this task was
nominally about.

Frontend: `SchedulerStatusPanel` in the Knowledge Base tab shows the real job list with real next-
run times and real recent-run history, replacing the now-inaccurate "on-demand for now" copy.

Deviation, stated plainly: Learning Agent's research cycles remain on-demand — deliberately, not an
oversight. They need a specific topic to be meaningful; a timer firing real paid research calls
without one would be guessing at what to research, not a genuine scheduled check.
