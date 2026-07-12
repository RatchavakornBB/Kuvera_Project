from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services import deals as deals_service

router = APIRouter(prefix="/deals", tags=["deals"])


class DealCreate(BaseModel):
    name: str
    client: str
    industries: list[str] = []
    owner_id: str | None = None


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
