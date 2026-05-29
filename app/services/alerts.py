from __future__ import annotations

import sqlite3
from typing import Any

from app.db import ensure_user, rows_to_dicts



def subscribe(conn: sqlite3.Connection, user_id: int, barcode: str) -> dict[str, Any]:
    ensure_user(conn, user_id)
    conn.execute(
        "INSERT OR IGNORE INTO alerts (user_id, product_barcode) VALUES (?, ?)",
        (user_id, barcode),
    )
    return dict(
        conn.execute(
            "SELECT * FROM alerts WHERE user_id = ? AND product_barcode = ?",
            (user_id, barcode),
        ).fetchone()
    )



def list_alerts(conn: sqlite3.Connection, user_id: int) -> list[dict[str, Any]]:
    ensure_user(conn, user_id)
    rows = conn.execute(
        "SELECT * FROM alerts WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return rows_to_dicts(rows)



def unsubscribe(conn: sqlite3.Connection, alert_id: int, user_id: int) -> bool:
    ensure_user(conn, user_id)
    cursor = conn.execute("DELETE FROM alerts WHERE id = ? AND user_id = ?", (alert_id, user_id))
    return cursor.rowcount > 0
