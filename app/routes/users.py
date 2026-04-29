from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, status

from app.db import ensure_user, get_db, row_to_dict, rows_to_dicts
from app.models import AlertCreate, TrackerCreate
from app.services.alerts import list_alerts, subscribe, unsubscribe

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
def get_me(user_id: int = Query(1, ge=1)):
    with get_db() as conn:
        return ensure_user(conn, user_id)


@router.get("/me/tracker")
def list_tracker(user_id: int = Query(..., ge=1)):
    with get_db() as conn:
        ensure_user(conn, user_id)
        rows = conn.execute(
            "SELECT * FROM tracker WHERE user_id = ? ORDER BY consumed_at DESC",
            (user_id,),
        ).fetchall()
        return {"items": rows_to_dicts(rows), "count": len(rows)}


@router.post("/me/tracker", status_code=status.HTTP_201_CREATED)
def create_tracker_entry(entry: TrackerCreate):
    with get_db() as conn:
        ensure_user(conn, entry.user_id)
        product = conn.execute("SELECT halal_status FROM products WHERE barcode = ?", (entry.product_barcode,)).fetchone()
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        conn.execute(
            "INSERT INTO tracker (user_id, product_barcode, consumed_at, status_at_time) VALUES (?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?)",
            (entry.user_id, entry.product_barcode, entry.consumed_at.isoformat() if entry.consumed_at else None, product["halal_status"]),
        )
        created = conn.execute("SELECT * FROM tracker WHERE rowid = last_insert_rowid()").fetchone()
        return row_to_dict(created)


@router.get("/me/alerts")
def get_alerts(user_id: int = Query(..., ge=1)):
    with get_db() as conn:
        items = list_alerts(conn, user_id)
        return {"items": items, "count": len(items)}


@router.post("/me/alerts", status_code=status.HTTP_201_CREATED)
def create_alert(alert: AlertCreate):
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM products WHERE barcode = ?", (alert.product_barcode,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return subscribe(conn, alert.user_id, alert.product_barcode)


@router.delete("/me/alerts/{alert_id}")
def delete_alert(alert_id: int, user_id: int = Query(..., ge=1)):
    with get_db() as conn:
        deleted = unsubscribe(conn, alert_id, user_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Alert not found")
        return {"status": "deleted", "id": alert_id}
