from fastapi import APIRouter

from app.services import agent_hub as agent_hub_service

router = APIRouter(prefix="/agent-hub", tags=["agent-hub"])


@router.get("/activity")
def get_activity(limit: int = 50):
    return agent_hub_service.get_activity(limit=limit)


@router.get("/grid")
def get_agent_grid():
    return agent_hub_service.get_agent_grid()


@router.get("/agents/{agent_name}")
def get_agent_detail(agent_name: str):
    return agent_hub_service.get_agent_detail(agent_name)


@router.get("/graph/analyst-lead")
def get_analyst_lead_graph():
    return agent_hub_service.get_analyst_lead_graph()
