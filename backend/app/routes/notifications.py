from fastapi import APIRouter

from app.services import notifications as notifications_service

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/key-dates")
def get_key_date_notifications(days: int = 30):
    return notifications_service.list_key_date_notifications(days=days)
