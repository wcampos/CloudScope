"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from cache import get_redis
from database import SessionLocal, engine
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from models import AWSProfile, Base
from routers import profiles, resources
from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables (migrations preferred). Shutdown: nothing to do."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="CloudScope API",
    description="API for managing AWS profiles and resources",
    version="1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class NoCacheMiddleware(BaseHTTPMiddleware):
    """Set Cache-Control so browsers and proxies do not cache API responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response


app.add_middleware(NoCacheMiddleware)

app.include_router(profiles.router, prefix="/api")
app.include_router(resources.router, prefix="/api")


@app.get("/health")
def health_check() -> dict[str, Any]:
    """Health check endpoint with database status."""
    health_status: dict[str, Any] = {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "services": {},
    }

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "message": "Connected to PostgreSQL",
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "message": str(e),
        }

    try:
        db = SessionLocal()
        try:
            profile_count = db.query(AWSProfile).count()
            health_status["services"]["profiles"] = {
                "status": "healthy",
                "count": profile_count,
            }
            active_profile = db.query(AWSProfile).filter(AWSProfile.is_active.is_(True)).first()
            health_status["services"]["active_profile"] = {
                "name": active_profile.name if active_profile else None,
                "status": "healthy" if active_profile else "none",
            }
        finally:
            db.close()
    except Exception as e:
        health_status["services"]["profiles"] = {
            "status": "unhealthy",
            "message": str(e),
        }
        health_status["services"]["active_profile"] = {
            "status": "unhealthy",
            "message": str(e),
        }

    try:
        r = get_redis()
        if r is not None:
            r.ping()
            health_status["services"]["cache"] = {
                "status": "healthy",
                "message": "Redis connected",
            }
        else:
            health_status["services"]["cache"] = {
                "status": "unhealthy",
                "message": "Redis not configured or unavailable",
            }
    except Exception as e:
        health_status["services"]["cache"] = {
            "status": "unhealthy",
            "message": str(e),
        }

    return health_status
