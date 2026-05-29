from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException, status

from app.db import get_db, row_to_dict, rows_to_dicts
from app.models import RestaurantCreate, ReviewCreate

router = APIRouter(prefix="/api/restaurants", tags=["restaurants"])


@router.get("")
def list_restaurants(q: str | None = None):
    with get_db() as conn:
        if q:
            rows = conn.execute(
                "SELECT * FROM restaurants WHERE name LIKE ? OR address LIKE ? ORDER BY avg_rating DESC",
                (f"%{q}%", f"%{q}%"),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM restaurants ORDER BY avg_rating DESC").fetchall()
        return {"items": rows_to_dicts(rows), "count": len(rows)}


@router.get("/{restaurant_id}")
def get_restaurant(restaurant_id: int):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return row_to_dict(row)


@router.post("", status_code=status.HTTP_201_CREATED)
def create_restaurant(restaurant: RestaurantCreate):
    payload = restaurant.model_dump(mode="json")
    with get_db() as conn:
        conn.execute(
            "INSERT INTO pending_contributions (type, payload, user_id) VALUES (?, ?, ?)",
            ("restaurant", json.dumps(payload), restaurant.user_id),
        )
        return {"status": "pending_review", "name": restaurant.name}


@router.get("/{restaurant_id}/reviews")
def list_reviews(restaurant_id: int):
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM reviews WHERE restaurant_id = ? ORDER BY created_at DESC",
            (restaurant_id,),
        ).fetchall()
        return {"items": rows_to_dicts(rows), "count": len(rows)}


@router.post("/{restaurant_id}/reviews", status_code=status.HTTP_201_CREATED)
def create_review(restaurant_id: int, review: ReviewCreate):
    payload = review.model_dump(mode="json")
    payload["restaurant_id"] = restaurant_id
    with get_db() as conn:
        if conn.execute("SELECT 1 FROM restaurants WHERE id = ?", (restaurant_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        conn.execute(
            "INSERT INTO pending_contributions (type, payload, user_id) VALUES (?, ?, ?)",
            ("review", json.dumps(payload), review.user_id),
        )
        return {"status": "pending_review", "restaurant_id": restaurant_id}
