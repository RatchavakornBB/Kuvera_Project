from fastapi import APIRouter

from app.services import agent_hub as agent_hub_service

router = APIRouter(prefix="/agent-hub", tags=["agent-hub"])


@router.get("/activity")
def get_activity(limit: int = 50):
    return agent_hub_service.get_activity(limit=limit)
