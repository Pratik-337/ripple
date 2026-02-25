from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.storage import ensure_bucket_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    ensure_bucket_exists()
    yield
    # Shutdown (add cleanup here if needed)


app = FastAPI(
    title="Ripple API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers (uncomment as they are built) ─────────────────────────────────────
from app.api.v1.routers import auth  # noqa: E402
app.include_router(auth.router, prefix="/api/v1")

# from app.api.v1.routers import projects, components, files, changes, notifications, invites, users
# app.include_router(projects.router, prefix="/api/v1")
# ... etc.


@app.get("/health")
async def health():
    return {"status": "ok"}
