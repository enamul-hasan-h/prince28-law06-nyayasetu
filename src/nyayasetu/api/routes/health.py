"""Health and readiness endpoints."""

from fastapi import APIRouter, HTTPException

from nyayasetu.api.deps import StoreDep

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
def ready(store: StoreDep) -> dict[str, str]:
    if not store.ready:
        raise HTTPException(
            status_code=503,
            detail="Document store is not ready.",
        )

    return {"status": "ready"}
