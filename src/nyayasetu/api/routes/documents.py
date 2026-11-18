"""Document listing and retrieval endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from nyayasetu.api.deps import RepositoryDep
from nyayasetu.db.repository import FILTER_KEY

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
async def list_documents(
    request: Request,
    repository: RepositoryDep,
    q: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    reserved = {"q", "limit", "offset"}
    filters = {key: value for key, value in request.query_params.items() if key not in reserved}

    for key in filters:
        if not FILTER_KEY.fullmatch(key):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid filter name: {key}",
            )

    total, items = await repository.list(
        q=q,
        filters=filters,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": filters,
    }


@router.get("/{doc_id}")
async def get_document(
    doc_id: str,
    repository: RepositoryDep,
) -> dict[str, Any]:
    record = await repository.get(doc_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' was not found.",
        )

    return record
