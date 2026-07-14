"""Real in-process scheduler (system-architecture.md Section 8's "scheduled background check"
for 4.3 Key-date notifier). A BackgroundScheduler thread, not client-side polling — jobs fire on a
real interval whether or not anyone has the app open. Also runs agents/industry_brief.py's Brief
refresh, per the retrofit note left in phase6-002's report (both this and Learning Agent's
research cycles should move onto real scheduler infrastructure once it exists; Learning Agent
itself stays on-demand here — it needs a specific research topic to be meaningful, and auto-firing
real paid web-search calls on a timer without one would be guessing at what to research, not a
real scheduled check).

Intervals are demo-safe on purpose: key-date checks are cheap (a DB query) so 5 minutes is fine;
Industry Brief refreshes are real Claude + web_search calls, so those run daily, not every few
minutes, to avoid firing expensive real API calls unprompted during a live session."""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger("scheduler")

_scheduler = BackgroundScheduler()

INDUSTRIES = ["Healthcare", "Logistics", "Fintech"]


def _log_run(job_name: str, status: str, detail: str | None = None) -> None:
    try:
        from app.db import get_client

        get_client().table("scheduled_run_log").insert(
            {
                "job_name": job_name,
                "status": status,
                "detail": detail,
                "started_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
    except Exception:
        logger.exception("Failed to log scheduled run for %s", job_name)


def run_key_date_check() -> None:
    try:
        from app.services import notifications as notifications_service

        results = notifications_service.list_key_date_notifications(days=30)
        _log_run("key_date_check", "success", f"{len(results)} upcoming key date(s) found")
    except Exception as e:
        logger.exception("key_date_check failed")
        _log_run("key_date_check", "error", str(e))


def run_stalled_deal_check() -> None:
    """Automation path for deal status (system-architecture.md 3.2's "surfaces
    stalled deals automatically"). Flags status='Stalled' for deals sitting in
    the same stage too long — never moves `stage` itself, since stage is a
    judgment call made via the UI or chat, not a timer (see
    app.services.deals.flag_stalled_deals)."""
    try:
        from app.services import deals as deals_service

        flagged = deals_service.flag_stalled_deals()
        _log_run("stalled_deal_check", "success", f"{len(flagged)} deal(s) flagged stalled")
    except Exception as e:
        logger.exception("stalled_deal_check failed")
        _log_run("stalled_deal_check", "error", str(e))


def run_industry_brief_refresh() -> None:
    from agents.industry_brief import refresh_industry_brief

    for industry in INDUSTRIES:
        try:
            refresh_industry_brief(industry)
            _log_run("industry_brief_refresh", "success", industry)
        except Exception as e:
            logger.exception("industry_brief_refresh failed for %s", industry)
            _log_run("industry_brief_refresh", "error", f"{industry}: {e}")


def start() -> None:
    if _scheduler.running:
        return
    _scheduler.add_job(run_key_date_check, "interval", minutes=5, id="key_date_check", replace_existing=True)
    _scheduler.add_job(
        run_stalled_deal_check, "interval", minutes=5, id="stalled_deal_check", replace_existing=True
    )
    _scheduler.add_job(
        run_industry_brief_refresh, "interval", hours=24, id="industry_brief_refresh", replace_existing=True
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: key_date_check every 5min, stalled_deal_check every 5min, "
        "industry_brief_refresh every 24h"
    )


def shutdown() -> None:
    if _scheduler.running:
        _scheduler.shutdown(wait=False)


def status() -> list[dict]:
    return [
        {
            "id": job.id,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        }
        for job in _scheduler.get_jobs()
    ]
