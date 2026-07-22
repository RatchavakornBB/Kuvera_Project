from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import contradictions as contradictions_service
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
    phase_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class TaskUpdate(BaseModel):
    text: str | None = None
    owner_id: str | None = None
    due_date: str | None = None
    done: bool | None = None
    phase_id: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class PhaseCreate(BaseModel):
    name: str
    sort_order: int | None = None
    color: str | None = None


class PhaseUpdate(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    color: str | None = None
    collapsed: bool | None = None


class CloseDealRequest(BaseModel):
    outcome: str


class StageUpdate(BaseModel):
    stage: str


class ResolveContradiction(BaseModel):
    resolution: str
    note: str = ""


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
    return deals_service.create_task(
        deal_id,
        text=body.text,
        owner_id=body.owner_id,
        due_date=body.due_date,
        phase_id=body.phase_id,
        start_date=body.start_date,
        end_date=body.end_date,
    )


@router.patch("/{deal_id}/tasks/{task_id}")
def update_task(deal_id: str, task_id: str, body: TaskUpdate):
    # exclude_unset (not "is not None") so the client can explicitly clear a
    # field — e.g. drag a task off the grid by sending start_date=null, or move
    # it to the unscheduled tray with phase_id=null.
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    task = deals_service.update_task(deal_id, task_id, fields)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/{deal_id}/phases")
def create_phase(deal_id: str, body: PhaseCreate):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deals_service.create_phase(deal_id, name=body.name, sort_order=body.sort_order, color=body.color)


@router.patch("/{deal_id}/phases/{phase_id}")
def update_phase(deal_id: str, phase_id: str, body: PhaseUpdate):
    fields = body.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    phase = deals_service.update_phase(deal_id, phase_id, fields)
    if phase is None:
        raise HTTPException(status_code=404, detail="Phase not found")
    return phase


@router.delete("/{deal_id}/phases/{phase_id}")
def delete_phase(deal_id: str, phase_id: str):
    if not deals_service.delete_phase(deal_id, phase_id):
        raise HTTPException(status_code=404, detail="Phase not found")
    return {"deleted": phase_id}


@router.patch("/{deal_id}/stage")
def update_deal_stage(deal_id: str, body: StageUpdate):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    if body.stage not in deals_service.STAGES:
        raise HTTPException(status_code=400, detail=f"stage must be one of {deals_service.STAGES}")
    return deals_service.update_deal_stage(deal_id, body.stage)


@router.post("/{deal_id}/close")
def close_deal(deal_id: str, body: CloseDealRequest):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    if body.outcome not in ("won", "lost"):
        raise HTTPException(status_code=400, detail="outcome must be 'won' or 'lost'")
    return deals_service.close_deal(deal_id, body.outcome)


@router.get("/{deal_id}/contradictions")
def list_contradictions(deal_id: str):
    if deals_service.get_deal(deal_id) is None:
        raise HTTPException(status_code=404, detail="Deal not found")
    return contradictions_service.list_for_deal(deal_id)


@router.post("/{deal_id}/contradictions/{contradiction_id}/resolve")
def resolve_contradiction(deal_id: str, contradiction_id: str, body: ResolveContradiction):
    try:
        return contradictions_service.resolve(contradiction_id, body.resolution, body.note)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
