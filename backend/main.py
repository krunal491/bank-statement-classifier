"""
REST API for the bank statement pipeline, served to the React frontend.

Stateless by design: every endpoint takes whatever data it needs in the request
and returns the full result - the frontend holds the current table in memory,
nothing about a processed statement is stored server-side.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # so `import src...` resolves regardless of cwd

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.routers import statements

app = FastAPI(title="Bank Statement Classifier API")
app.add_middleware(
    CORSMiddleware,
    # Frontend (Vercel) and backend (Render) are different origins in production, and there's
    # no session/auth to protect - every request is independently authorized by its own
    # content - so a wildcard is the pragmatic choice here, not an oversight.
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(statements.router)

# Serve the built React app (one-process local convenience only - in the deployed
# split, Vercel serves the frontend and this backend is API-only, so frontend/dist
# won't exist here and this mount is simply skipped).
FRONTEND_DIST = ROOT / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
