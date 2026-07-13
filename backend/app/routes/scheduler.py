from fastapi import APIRouter

from app import scheduler
from app.db import get_client

router = APIRouter(prefix="/admin/scheduler", tags=["scheduler"])


@router.get("/status")
def get_status():
    return {"jobs": scheduler.status()}


@router.get("/runs")
def get_runs(limit: int = 20):
    client = get_client()
    return (
        client.table("scheduled_run_log")
        .select("*")
        .order("started_at", desc=True)
        .limit(limit)
        .execute()
        .data
    )
