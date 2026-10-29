"""Small deterministic entity extraction used before evidence retrieval."""
from __future__ import annotations

import re
from typing import Any


def extract_entities(request: dict[str, Any]) -> dict[str, Any]:
    """Extract article/material clues without making a tariff determination."""
    description = str(request.get("product_description", ""))
    use = str(request.get("intended_use") or "")
    return {
        "description": description,
        "materials": list(request.get("materials", [])),
        "intended_use": use,
        "words": re.findall(r"[a-z0-9]+", (description + " " + use).lower()),
        "hs_hint_chapter": str(request.get("hs_hint", ""))[:2] or None,
    }
