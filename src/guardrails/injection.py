"""Prompt-injection screening and safe delimiting for user-controlled text."""
from __future__ import annotations

import re
import unicodedata

_PATTERNS = (
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"reveal\s+(the\s+)?system\s+prompt",
    r"act\s+as\s+(an?\s+)?(admin|developer|system)",
    r"override\s+(the\s+)?(system|safety|policy)",
    r"<\s*/?\s*system\s*>",
    r"tool\s*call\s*:\s*",
    r"disregard\s+your\s+rules",
)


def normalize_untrusted_text(value: str) -> str:
    """Normalize Unicode and remove invisible formatting controls."""
    normalized = unicodedata.normalize("NFKC", value)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Cf")
    return re.sub(r"\s+", " ", normalized).strip()


def detect_prompt_injection(value: str) -> dict[str, object]:
    """Flag common direct instruction override attempts, with matched rule IDs."""
    normalized = normalize_untrusted_text(value).lower()
    matches = [f"pattern_{idx + 1}" for idx, pattern in enumerate(_PATTERNS) if re.search(pattern, normalized)]
    return {"detected": bool(matches), "matched_rules": matches, "normalized": normalized}


def delimit_untrusted_text(value: str) -> str:
    """Delimit normalized user text so downstream prompts treat it as data."""
    cleaned = normalize_untrusted_text(value).replace("</untrusted_input>", "&lt;/untrusted_input&gt;")
    return f"<untrusted_input>\n{cleaned}\n</untrusted_input>"
