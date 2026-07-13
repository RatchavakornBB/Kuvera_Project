from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import governance as governance_service

router = APIRouter(prefix="/admin", tags=["governance"])


class ProposeChange(BaseModel):
    change_type: str
    new_value: str


@router.get("/agents")
def list_agents():
    return governance_service.list_agents()


@router.post("/agents/{agent_name}/propose")
def propose_change(agent_name: str, body: ProposeChange):
    try:
        return governance_service.propose_change(agent_name, body.change_type, body.new_value)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/pending-approvals")
def list_pending_approvals(status: str = "pending"):
    return governance_service.list_pending_changes(status=status)


@router.post("/pending-approvals/{change_id}/approve")
def approve_change(change_id: str):
    try:
        return governance_service.approve_change(change_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/pending-approvals/{change_id}/reject")
def reject_change(change_id: str):
    try:
        return governance_service.reject_change(change_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/pending-approvals/{change_id}/run-eval")
def run_eval_for_change(change_id: str):
    try:
        return governance_service.run_eval_for_change(change_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/audit-log")
def list_audit_log():
    return governance_service.list_audit_log()
