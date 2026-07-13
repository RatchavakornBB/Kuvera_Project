from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import deals as deals_service

router = APIRouter(prefix="/deals", tags=["deals"])


class DealCreate(BaseModel):
    name: str
    client: str
    industries: list[str] = []
    owner_id: str | None = None


class TaskCreate(BaseModel):
    text: str
    owner_id: str | None = None
    due_date: str | None = None


class TaskUpdate(BaseModel):
    text: str | None = None
    owner_id: str | None = None
    due_date: str | None = None
    done: bool | None = None


class CloseDealRequest(BaseModel):
    outcome: str


@router.get("")
def list_deals(stage: str | None = None, industry: str | None = None, owner: str | None = None):
    return deals_service.list_deals(stage=stage, industry=industry, owner=owner)


@router.post("")
def create_deal(body: DealCreate):
    return deals_service.create_deal(
        name=body.name, client_name=body.client, industries=body.industries, owner_id=body.owner_id
    )


@router.get("/{deal_id}")
def get_deal(deal_id: str):
    deal = deals_service.get_deal(deal_id)
    if deal is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.post("/{deal_id}/tasks")
def create_task(deal_id: str, body: TaskCreate):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deals_service.create_task(deal_id, text=body.text, owner_id=body.owner_id, due_date=body.due_date)


@router.patch("/{deal_id}/tasks/{task_id}")
def update_task(deal_id: str, task_id: str, body: TaskUpdate):
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    task = deals_service.update_task(deal_id, task_id, fields)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{deal_id}/close")
def close_deal(deal_id: str, body: CloseDealRequest):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    if body.outcome not in ("won", "lost"):
        raise HTTPException(status_code=400, detail="outcome must be 'won' or 'lost'")
    return deals_service.close_deal(deal_id, body.outcome)
