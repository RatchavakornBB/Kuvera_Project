from fastapi import APIRouter

from app.services import knowledge as knowledge_service

router = APIRouter(prefix="/admin/knowledge-base", tags=["knowledge"])


@router.get("")
def list_knowledge(industry: str | None = None, category: str | None = None):
    return knowledge_service.list_records(industry=industry, category=category)


@router.get("/search")
def search_knowledge(q: str, industry: str | None = None, category: str | None = None, limit: int = 10):
    return knowledge_service.search_records(q, industry=industry, category=category, limit=limit)
