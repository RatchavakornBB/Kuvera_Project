import sys
from pathlib import Path

# agents/ lives at the repo root, a sibling of backend/ (AGENT.md's repo
# layout), not a subpackage of this app — make it importable regardless of
# the directory uvicorn was launched from (D-007), rather than requiring
# every invocation to remember `--app-dir backend` from the repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import analyze, concierge, contracts, deals, documents

app = FastAPI(title="Kuvera Capital API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(deals.router)
app.include_router(documents.router)
app.include_router(analyze.router)
app.include_router(contracts.router)
app.include_router(concierge.router)


@app.get("/health")
def health():
    return {"status": "ok", "supabase_url": settings.supabase_url}
