from agents.errors import NodeFailure
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import learning as learning_service

router = APIRouter(prefix="/admin/learning", tags=["learning"])


class RunCycle(BaseModel):
    category: str
    topic: str


@router.post("/run")
def run_cycle(body: RunCycle):
    try:
        return learning_service.run_cycle(body.category, body.topic)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except NodeFailure as e:
        raise HTTPException(status_code=500, detail=e.to_dict()) from e


@router.get("/digests")
def list_digests():
    return learning_service.list_digests()
