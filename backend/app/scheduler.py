"""Real in-process scheduler (system-architecture.md Section 8's "scheduled background check"
for 4.3 Key-date notifier). A BackgroundScheduler thread, not client-side polling — jobs fire on a
real interval whether or not anyone has the app open. Also runs three real research-refresh jobs —
agents/industry_brief.py's Industry Brief (fixed 3-industry roster) and Competitor Brief, and
agents/company_research.py's per-deal Company Research (both of the latter loop every active deal,
via `_active_deal_roster()`) — per the retrofit note left in phase6-002's report (Learning Agent
itself stays on-demand here — it needs a specific research topic to be meaningful, and auto-firing
real paid web-search calls on a timer without one would be guessing at what to research, not a real
scheduled check).

Intervals are demo-safe on purpose: key-date/stalled-deal checks are cheap (a DB query) so 5 minutes
is fine; the three research-refresh jobs are real Claude + web_search/web_fetch calls, so those run
daily, not every few minutes — and are staggered a few minutes apart from each other (via
`next_run_time`) so a server restart doesn't fire all three real-money job batches in the same
instant."""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler

logger = logging.getLogger("scheduler")

_scheduler = BackgroundScheduler()

INDUSTRIES = ["Healthcare", "Logistics", "Fintech"]


def _active_deal_roster() -> list[dict]:
    """The roster for competitor_brief_refresh and company_research_refresh —
    every deal not yet Closed (deliberately NOT also excluding Stalled, unlike
    flag_stalled_deals's filter: a stalled deal's target company still needs
    fresh research, arguably more so)."""
    from app.db import get_client

    return get_client().table("deals").select("id, name, industries").neq("status", "Closed").execute().data


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


def run_competitor_brief_refresh() -> None:
    from agents.industry_brief import refresh_competitor_brief

    for deal in _active_deal_roster():
        industry = deal["industries"][0] if deal["industries"] else "unspecified"
        try:
            refresh_competitor_brief(deal["name"], industry)
            _log_run("competitor_brief_refresh", "success", deal["name"])
        except Exception as e:
            logger.exception("competitor_brief_refresh failed for %s", deal["name"])
            _log_run("competitor_brief_refresh", "error", f"{deal['name']}: {e}")


def run_company_research_refresh() -> None:
    from app.services.company_research import refresh_company_research

    for deal in _active_deal_roster():
        try:
            refresh_company_research(deal["id"])
            _log_run("company_research_refresh", "success", deal["name"])
        except Exception as e:
            logger.exception("company_research_refresh failed for %s", deal["name"])
            _log_run("company_research_refresh", "error", f"{deal['name']}: {e}")


def start() -> None:
    if _scheduler.running:
        return
    now = datetime.now(timezone.utc)
    _scheduler.add_job(run_key_date_check, "interval", minutes=5, id="key_date_check", replace_existing=True)
    _scheduler.add_job(
        run_stalled_deal_check, "interval", minutes=5, id="stalled_deal_check", replace_existing=True
    )
    _scheduler.add_job(
        run_industry_brief_refresh, "interval", hours=24, id="industry_brief_refresh", replace_existing=True
    )
    _scheduler.add_job(
        run_company_research_refresh,
        "interval",
        hours=24,
        id="company_research_refresh",
        replace_existing=True,
        next_run_time=now + timedelta(minutes=10),
    )
    _scheduler.add_job(
        run_competitor_brief_refresh,
        "interval",
        hours=24,
        id="competitor_brief_refresh",
        replace_existing=True,
        next_run_time=now + timedelta(minutes=20),
    )
    _scheduler.start()
    logger.info(
        "Scheduler started: key_date_check every 5min, stalled_deal_check every 5min, "
        "industry_brief_refresh/company_research_refresh/competitor_brief_refresh every 24h (staggered)"
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
