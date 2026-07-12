from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="Kuvera Capital API")


@app.get("/health")
def health():
    return {"status": "ok", "supabase_url": settings.supabase_url}
