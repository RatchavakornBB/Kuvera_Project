from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import governance as governance_service

router = APIRouter(prefix="/admin", tags=["governance"])


class ProposeChange(BaseModel):
    change_type: str
    new_value: str


class CreateAgent(BaseModel):
    agent_name: str
    model_id: str
    skill_content: str = ""


class AddSkill(BaseModel):
    instruction: str


class CreateEvalCase(BaseModel):
    agent_name: str
    prompt: str
    criteria: str
    expected_tool_sequence: list[str] | None = None
    trajectory_rubric: str | None = None
    max_iterations: int | None = None


@router.get("/agents")
def list_agents():
    return governance_service.list_agents()


@router.post("/agents")
def create_agent(body: CreateAgent):
    try:
        return governance_service.create_agent(body.agent_name, body.model_id, body.skill_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/agents/{agent_name}/add-skill")
def add_skill(agent_name: str, body: AddSkill):
    try:
        return governance_service.propose_skill_addition(agent_name, body.instruction)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


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


@router.get("/eval-cases")
def list_eval_cases(agent_name: str | None = None):
    return governance_service.list_eval_cases(agent_name)


@router.get("/eval-cases/built-in-counts")
def builtin_eval_case_counts():
    return governance_service.builtin_eval_case_counts()


@router.post("/eval-cases")
def create_eval_case(body: CreateEvalCase):
    try:
        return governance_service.create_eval_case(
            body.agent_name,
            body.prompt,
            body.criteria,
            expected_tool_sequence=body.expected_tool_sequence,
            trajectory_rubric=body.trajectory_rubric,
            max_iterations=body.max_iterations,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/eval-cases/{case_id}")
def delete_eval_case(case_id: str):
    governance_service.delete_eval_case(case_id)
    return {"status": "deleted"}
