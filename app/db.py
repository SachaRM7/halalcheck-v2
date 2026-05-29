from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = DATA_DIR / "static"
DB_PATH = DATA_DIR / "halalcheck.db"

SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      barcode TEXT UNIQUE NOT NULL,
      name TEXT NOT NULL,
      brand TEXT,
      ingredients TEXT,
      halal_status TEXT CHECK(halal_status IN ('halal','haram','dubious','unknown')),
      certification_body TEXT,
      cert_number TEXT,
      source_url TEXT,
      updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      contributor_id INTEGER,
      editor_approvals INTEGER DEFAULT 0
    )
    """,
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
      barcode, name, brand, ingredients, content='products', content_rowid='id'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS restaurants (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL,
      address TEXT,
      lat REAL,
      lng REAL,
      cuisine_type TEXT,
      halal_status TEXT CHECK(halal_status IN ('halal','haram','dubious','unknown')),
      avg_rating REAL DEFAULT 0,
      review_count INTEGER DEFAULT 0,
      last_verified DATETIME,
      contributor_id INTEGER
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reviews (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      restaurant_id INTEGER REFERENCES restaurants(id),
      user_id INTEGER NOT NULL,
      rating INTEGER CHECK(rating BETWEEN 1 AND 5),
      comment TEXT,
      photo_url TEXT,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      upvotes INTEGER DEFAULT 0,
      downvotes INTEGER DEFAULT 0,
      flagged BOOLEAN DEFAULT FALSE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS users (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      telegram_id INTEGER UNIQUE,
      display_name TEXT,
      reputation INTEGER DEFAULT 0,
      is_editor BOOLEAN DEFAULT FALSE,
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alerts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER REFERENCES users(id),
      product_barcode TEXT REFERENCES products(barcode),
      created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      UNIQUE(user_id, product_barcode)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS tracker (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER REFERENCES users(id),
      product_barcode TEXT REFERENCES products(barcode),
      consumed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      status_at_time TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pending_contributions (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      type TEXT CHECK(type IN ('product','restaurant','review')),
      payload TEXT,
      user_id INTEGER REFERENCES users(id),
      submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
      approvals INTEGER DEFAULT 0,
      rejected BOOLEAN DEFAULT FALSE
    )
    """,
]

SEED_USERS = [
    (1, 100001, "Halal Editor", 10, 1),
    (2, 100002, "Community Member", 2, 0),
]

SEED_PRODUCTS = [
    {
        "barcode": "8901234567890",
        "name": "Safa Turmeric Biscuits",
        "brand": "Safa Foods",
        "ingredients": "wheat flour, sugar, E100, vegetable oil",
        "halal_status": "halal",
        "certification_body": "MUI",
        "cert_number": "MUI-2026-01",
        "source_url": "https://example.org/safa-biscuits",
        "contributor_id": 1,
        "editor_approvals": 2,
    },
    {
        "barcode": "1112223334445",
        "name": "Gelatin Joy Marshmallows",
        "brand": "SweetCloud",
        "ingredients": "glucose syrup, gelatin, flavouring",
        "halal_status": "dubious",
        "certification_body": "Pending Review",
        "cert_number": "",
        "source_url": "https://example.org/marshmallow",
        "contributor_id": 1,
        "editor_approvals": 1,
    },
]

SEED_RESTAURANTS = [
    {
        "id": 1,
        "name": "Baraka Grill",
        "address": "12 Crescent Road, London",
        "lat": 51.5074,
        "lng": -0.1278,
        "cuisine_type": "Turkish",
        "halal_status": "halal",
        "avg_rating": 4.8,
        "review_count": 12,
        "last_verified": "2026-04-16T12:00:00",
        "contributor_id": 1,
    }
]


def _connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


@contextmanager
def get_db() -> Iterable[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    try:
        with get_db() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
            _seed(conn)
    except sqlite3.DatabaseError:
        for extra_path in (DB_PATH, DB_PATH.with_suffix(DB_PATH.suffix + '-wal'), DB_PATH.with_suffix(DB_PATH.suffix + '-shm')):
            if extra_path.exists():
                extra_path.unlink()
        with get_db() as conn:
            for statement in SCHEMA_STATEMENTS:
                conn.execute(statement)
            _seed(conn)


def _seed(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO users (id, telegram_id, display_name, reputation, is_editor) VALUES (?, ?, ?, ?, ?)",
        SEED_USERS,
    )

    for product in SEED_PRODUCTS:
        conn.execute(
            """
            INSERT OR IGNORE INTO products (
                barcode, name, brand, ingredients, halal_status, certification_body,
                cert_number, source_url, contributor_id, editor_approvals
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product["barcode"],
                product["name"],
                product["brand"],
                product["ingredients"],
                product["halal_status"],
                product["certification_body"],
                product["cert_number"],
                product["source_url"],
                product["contributor_id"],
                product["editor_approvals"],
            ),
        )

    for restaurant in SEED_RESTAURANTS:
        conn.execute(
            """
            INSERT OR IGNORE INTO restaurants (
                id, name, address, lat, lng, cuisine_type, halal_status,
                avg_rating, review_count, last_verified, contributor_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                restaurant["id"],
                restaurant["name"],
                restaurant["address"],
                restaurant["lat"],
                restaurant["lng"],
                restaurant["cuisine_type"],
                restaurant["halal_status"],
                restaurant["avg_rating"],
                restaurant["review_count"],
                restaurant["last_verified"],
                restaurant["contributor_id"],
            ),
        )

    rebuild_fts(conn)


def rebuild_fts(conn: sqlite3.Connection) -> None:
    conn.execute("INSERT INTO products_fts(products_fts) VALUES ('rebuild')")


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def load_json_data(filename: str) -> Any:
    return json.loads((STATIC_DIR / filename).read_text(encoding="utf-8"))


def ensure_user(conn: sqlite3.Connection, user_id: int) -> dict[str, Any]:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is not None:
        return dict(row)

    conn.execute(
        "INSERT INTO users (id, telegram_id, display_name, reputation, is_editor) VALUES (?, ?, ?, ?, ?)",
        (user_id, 100000 + user_id, f"User {user_id}", 0, 0),
    )
    created = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return dict(created)
