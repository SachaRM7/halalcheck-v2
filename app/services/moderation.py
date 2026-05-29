from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.db import ensure_user, rebuild_fts



def list_pending(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM pending_contributions WHERE rejected = 0 ORDER BY submitted_at ASC"
    ).fetchall()
    items = []
    for row in rows:
        item = dict(row)
        item["payload"] = json.loads(item["payload"])
        items.append(item)
    return items



def approve_contribution(conn: sqlite3.Connection, contribution_id: int, user_id: int) -> dict[str, Any]:
    user = ensure_user(conn, user_id)
    if not user["is_editor"]:
        raise PermissionError("Editor access required.")

    row = conn.execute(
        "SELECT * FROM pending_contributions WHERE id = ? AND rejected = 0",
        (contribution_id,),
    ).fetchone()
    if row is None:
        raise LookupError("Contribution not found.")

    payload = json.loads(row["payload"])
    contribution_type = row["type"]
    approvals = row["approvals"] + 1
    conn.execute(
        "UPDATE pending_contributions SET approvals = ? WHERE id = ?",
        (approvals, contribution_id),
    )

    if contribution_type == "product":
        conn.execute(
            """
            INSERT OR REPLACE INTO products (
                barcode, name, brand, ingredients, halal_status, certification_body,
                cert_number, source_url, contributor_id, editor_approvals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["barcode"],
                payload["name"],
                payload.get("brand"),
                payload.get("ingredients", ""),
                payload["halal_status"],
                payload.get("certification_body"),
                payload.get("cert_number"),
                payload.get("source_url"),
                row["user_id"],
                approvals,
            ),
        )
        rebuild_fts(conn)
    elif contribution_type == "restaurant":
        conn.execute(
            """
            INSERT INTO restaurants (
                name, address, lat, lng, cuisine_type, halal_status, contributor_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload["name"],
                payload.get("address"),
                payload.get("lat"),
                payload.get("lng"),
                payload.get("cuisine_type"),
                payload.get("halal_status", "unknown"),
                row["user_id"],
            ),
        )
    elif contribution_type == "review":
        conn.execute(
            """
            INSERT INTO reviews (restaurant_id, user_id, rating, comment, photo_url)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload["restaurant_id"],
                row["user_id"],
                payload["rating"],
                payload.get("comment"),
                payload.get("photo_url"),
            ),
        )
        conn.execute(
            """
            UPDATE restaurants
            SET avg_rating = (
                SELECT COALESCE(AVG(rating), 0) FROM reviews WHERE restaurant_id = ?
            ),
                review_count = (
                SELECT COUNT(*) FROM reviews WHERE restaurant_id = ?
            )
            WHERE id = ?
            """,
            (payload["restaurant_id"], payload["restaurant_id"], payload["restaurant_id"]),
        )

    conn.execute("DELETE FROM pending_contributions WHERE id = ?", (contribution_id,))
    return {"status": "approved", "id": contribution_id, "approvals": approvals}



def reject_contribution(conn: sqlite3.Connection, contribution_id: int, user_id: int) -> dict[str, Any]:
    user = ensure_user(conn, user_id)
    if not user["is_editor"]:
        raise PermissionError("Editor access required.")
    cursor = conn.execute(
        "UPDATE pending_contributions SET rejected = 1 WHERE id = ?",
        (contribution_id,),
    )
    if cursor.rowcount == 0:
        raise LookupError("Contribution not found.")
    return {"status": "rejected", "id": contribution_id}
