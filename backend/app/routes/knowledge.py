from fastapi import APIRouter
from pydantic import BaseModel

from app.services import knowledge as knowledge_service

router = APIRouter(prefix="/admin/knowledge-base", tags=["knowledge"])


class RefreshIndustryBrief(BaseModel):
    industry: str


class RefreshCompetitorBrief(BaseModel):
    company_name: str
    industry: str


@router.get("")
def list_knowledge(industry: str | None = None, category: str | None = None):
    return knowledge_service.list_records(industry=industry, category=category)


@router.get("/search")
def search_knowledge(q: str, industry: str | None = None, category: str | None = None, limit: int = 10):
    return knowledge_service.search_records(q, industry=industry, category=category, limit=limit)


@router.post("/refresh-industry-brief")
def refresh_industry_brief(body: RefreshIndustryBrief):
    return knowledge_service.refresh_industry_brief(body.industry)


@router.post("/refresh-competitor-brief")
def refresh_competitor_brief(body: RefreshCompetitorBrief):
    return knowledge_service.refresh_competitor_brief(body.company_name, body.industry)


@router.post("/backfill-embeddings")
def backfill_embeddings():
    return {"embedded_count": knowledge_service.backfill_missing_embeddings()}
