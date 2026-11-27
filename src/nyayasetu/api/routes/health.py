"""Health and readiness endpoints."""

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from nyayasetu.api.deps import DbCheckDep, SettingsDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health(settings: SettingsDep) -> dict[str, str]:
    return {"status": "ok", "git_sha": settings.git_sha}


@router.get("/ready")
async def ready(database_available: DbCheckDep) -> Any:
    if not database_available:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "checks": {"database": False}},
        )
    return {"status": "ready", "checks": {"database": True}}
