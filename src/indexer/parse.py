"""PDF text extraction with a per-page OCR-needed marker."""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any


def parse_pdf(path: str | Path) -> list[dict[str, Any]]:
    """Extract text per page and retain page numbers; mark empty pages for OCR fallback."""
    path = Path(path)
    pages: list[dict[str, Any]] = []
    try:
        import fitz
        with fitz.open(path) as document:
            for page_index, page in enumerate(document, 1):
                text = page.get_text("text") or ""
                text = re.sub(r"[ \t]+", " ", text).strip()
                pages.append({"doc": path.name, "doc_version": "unrecorded", "page": page_index,
                    "text": text, "ocr_needed": len(text) < 20,
                    "content_hash": hashlib.sha256(text.encode()).hexdigest()})
        return pages
    except Exception as exc:
        raise RuntimeError(f"could not parse PDF {path.name}: {type(exc).__name__}") from exc
