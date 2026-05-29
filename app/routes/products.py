from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, Query, status

from app.db import get_db, rebuild_fts, row_to_dict, rows_to_dicts
from app.models import ProductCreate
from app.services.ai_explainer import explain_ingredients
from app.services.ingredient_parser import parse_ingredients

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("/search")
def search_products(q: str = Query(..., min_length=1), status_filter: str | None = Query(default=None, alias="status")):
    sql = """
        SELECT p.* FROM products p
        LEFT JOIN products_fts fts ON p.id = fts.rowid
        WHERE (
            p.name LIKE ? OR p.brand LIKE ? OR p.ingredients LIKE ? OR fts.products_fts MATCH ?
        )
    """
    params = [f"%{q}%", f"%{q}%", f"%{q}%", q.replace(" ", " OR ")]
    if status_filter:
        sql += " AND p.halal_status = ?"
        params.append(status_filter)
    sql += " ORDER BY p.updated_at DESC LIMIT 25"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
        return {"items": rows_to_dicts(rows), "count": len(rows)}


@router.get("/{barcode}")
def get_product(barcode: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return row_to_dict(row)


@router.post("", status_code=status.HTTP_201_CREATED)
def submit_product(product: ProductCreate):
    payload = product.model_dump(mode="json")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO pending_contributions (type, payload, user_id) VALUES (?, ?, ?)",
            ("product", json.dumps(payload), product.user_id),
        )
        return {"status": "pending_review", "barcode": product.barcode}


@router.get("/{barcode}/analyze")
def analyze_product(barcode: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM products WHERE barcode = ?", (barcode,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        product = row_to_dict(row)

    ingredients = parse_ingredients(product.get("ingredients", ""))
    explanation = explain_ingredients(ingredients)
    return {
        "product": product,
        "ingredients": ingredients,
        "explanation": explanation,
        "mode": "ai-assisted" if "unavailable" not in explanation else "local-fallback",
    }
