"""Document listing and retrieval endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from nyayasetu.api.deps import StoreDep

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("")
def list_documents(
    store: StoreDep,
    q: str = "",
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    results = store.search(q)
    total = len(results)
    items = results[offset : offset + limit]

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    store: StoreDep,
) -> dict[str, Any]:
    record = store.get(doc_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{doc_id}' was not found.",
        )

    return record
