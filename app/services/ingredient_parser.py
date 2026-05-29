from __future__ import annotations

import re
from functools import lru_cache

from app.db import load_json_data


@lru_cache(maxsize=1)
def _e_lookup() -> dict:
    return load_json_data("e_number_lookup.json")


@lru_cache(maxsize=1)
def _arabic_lookup() -> dict:
    return load_json_data("arabic_ingredients_dict.json")


def _verdict(default: str, name: str) -> str:
    lowered = name.lower()
    if "gelatin" in lowered or "lard" in lowered:
        return "haram"
    if "emulsifier" in lowered or "flavour" in lowered:
        return "dubious"
    return default


def parse_ingredients(ingredients: str) -> list[dict]:
    tokens = [token.strip() for token in re.split(r",|;", ingredients) if token.strip()]
    e_lookup = _e_lookup()
    arabic_lookup = _arabic_lookup()
    parsed = []
    for token in tokens:
        code = token.upper()
        if code in e_lookup:
            item = e_lookup[code]
            parsed.append(
                {
                    "ingredient": code,
                    "display_name": item["name"],
                    "status": item["status"],
                    "explanation": item["explanation"],
                }
            )
            continue
        if token in arabic_lookup:
            item = arabic_lookup[token]
            parsed.append(
                {
                    "ingredient": token,
                    "display_name": item["transliteration"],
                    "status": item["status"],
                    "explanation": item["meaning"],
                }
            )
            continue
        parsed.append(
            {
                "ingredient": token,
                "display_name": token.title(),
                "status": _verdict("halal", token),
                "explanation": "Community/local dictionary analysis.",
            }
        )
    return parsed
