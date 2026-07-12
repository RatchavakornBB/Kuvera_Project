from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import deals, documents

app = FastAPI(title="Kuvera Capital API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals.router)
app.include_router(documents.router)


@app.get("/health")
def health():
    return {"status": "ok", "supabase_url": settings.supabase_url}
