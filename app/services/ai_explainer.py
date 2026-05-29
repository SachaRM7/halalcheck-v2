from __future__ import annotations

import os
from typing import Any

import requests

PROMPT_TEMPLATE = (
    "Explain the halal implications of these ingredients in plain language for Muslim consumers. "
    "Return a concise paragraph. Ingredients: {ingredients}"
)


def explain_ingredients(ingredients: list[dict[str, Any]]) -> str:
    api_key = os.getenv("MINIMAX_API_KEY")
    api_base = os.getenv("MINIMAX_API_BASE", "https://api.minimax.chat/v1")
    model = os.getenv("MINIMAX_MODEL", "MiniMax-M2.7")
    ingredient_names = ", ".join(item["ingredient"] for item in ingredients)
    fallback = (
        "AI-assisted explanation unavailable, so HalalCheck used the local ingredient dictionary. "
        "Review the certification body and ingredient breakdown before consuming."
    )
    if not api_key:
        return fallback

    try:
        response = requests.post(
            f"{api_base}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You explain halal product ingredients clearly and conservatively."},
                    {"role": "user", "content": PROMPT_TEMPLATE.format(ingredients=ingredient_names)},
                ],
                "temperature": 0.2,
            },
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return payload["choices"][0]["message"]["content"].strip()
    except Exception:
        return fallback
