from __future__ import annotations

from fastapi import APIRouter

from app.db import get_db, row_to_dict

router = APIRouter(prefix="/api/scan", tags=["scan"])


@router.get("/{barcode}")
def scan_barcode(barcode: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
        if row is None:
            return {
                "barcode": barcode,
                "status": "unknown",
                "message": "Product not found. Help the community by submitting a verification.",
            }
        product = row_to_dict(row)
        return {"barcode": barcode, "status": product["halal_status"], "product": product}
