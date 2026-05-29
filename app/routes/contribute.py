from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.db import get_db
from app.services.moderation import approve_contribution, list_pending, reject_contribution

router = APIRouter(prefix="/api/contribute", tags=["contribute"])


@router.get("/pending")
def pending_contributions(user_id: int = Query(..., ge=1)):
    with get_db() as conn:
        items = list_pending(conn)
        return {"items": items, "count": len(items), "requested_by": user_id}


@router.post("/{contribution_id}/approve")
def approve(contribution_id: int, user_id: int = Query(..., ge=1)):
    with get_db() as conn:
        try:
            return approve_contribution(conn, contribution_id, user_id)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{contribution_id}/reject")
def reject(contribution_id: int, user_id: int = Query(..., ge=1)):
    with get_db() as conn:
        try:
            return reject_contribution(conn, contribution_id, user_id)
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except LookupError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
