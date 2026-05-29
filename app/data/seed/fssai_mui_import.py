#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from app.db import get_db, init_db, rebuild_fts


def import_csv(path: Path) -> int:
    init_db()
    count = 0
    with path.open(newline="", encoding="utf-8") as handle, get_db() as conn:
        reader = csv.DictReader(handle)
        for row in reader:
            conn.execute(
                """
                INSERT OR REPLACE INTO products (
                    barcode, name, brand, ingredients, halal_status, certification_body,
                    cert_number, source_url, contributor_id, editor_approvals
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["barcode"],
                    row["name"],
                    row.get("brand"),
                    row.get("ingredients", ""),
                    row.get("halal_status", "unknown"),
                    row.get("certification_body"),
                    row.get("cert_number"),
                    row.get("source_url"),
                    1,
                    2,
                ),
            )
            count += 1
        rebuild_fts(conn)
    return count



def main() -> None:
    parser = argparse.ArgumentParser(description="Import CSV seed data into the HalalCheck SQLite database.")
    parser.add_argument("csv_file", type=Path)
    args = parser.parse_args()
    imported = import_csv(args.csv_file)
    print(f"Imported {imported} products from {args.csv_file}")


if __name__ == "__main__":
    main()
