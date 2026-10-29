"""Structure-aware chunking for headings, rules, notes and policy rows."""
from __future__ import annotations

import hashlib
import re
from typing import Any

_HEADING = re.compile(r"^\s*(\d{4})\s+(.{3,160})$", re.M)
_GRI = re.compile(r"(?im)^\s*(?:Rule\s*)?(1|2|3\s*\([abc]\)|4|5|6)\s*[.):-]?\s+(.{15,})")
_NOTE = re.compile(r"(?im)^\s*(?:Chapter|Section)?\s*Note\s+(\d+[a-z]?(?:\([a-z0-9]+\))?)\s*[.: -]+(.{10,})")


def _chunk_id(doc: str, identifier: str, page: int, text: str) -> str:
    """Build a stable ID from source file, structural identifier and text hash."""
    digest = hashlib.sha256(f"{doc}|{identifier}|{page}|{text}".encode()).hexdigest()[:16]
    return f"{doc}:{identifier}:{page}:{digest}"


def _make_chunk(page: dict[str, Any], text: str, kind: str, identifier: str, chapter: str = "", heading: str = "", title: str = "") -> dict[str, Any]:
    """Create chunk payload with provenance and content hashes."""
    normalized = re.sub(r"\s+", " ", text).strip()
    doc = page["doc"]
    content_hash = hashlib.sha256(normalized.encode()).hexdigest()
    return {"chunk_id": _chunk_id(doc, identifier, int(page["page"]), normalized), "doc": doc,
        "doc_version": page.get("doc_version", "unrecorded"), "chapter": chapter, "heading": heading,
        "heading_title": title, "kind": kind, "identifier": identifier, "page": int(page["page"]),
        "content_hash": content_hash, "embed_model": "lexical", "embed_model_version": "lexical-v1", "text": normalized}


def chunk_pages(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chunk pages by obvious tariff structures; never invent missing text."""
    output: list[dict[str, Any]] = []
    for page in pages:
        text = str(page.get("text", ""))
        if not text.strip():
            continue
        has_structure = False
        for match in _HEADING.finditer(text):
            code, title = match.group(1), match.group(2).strip()
            if not title or len(title) > 160:
                continue
            output.append(_make_chunk(page, match.group(0), "heading", f"Heading-{code}", code[:2], code, title))
            has_structure = True
        for match in _GRI.finditer(text):
            rule = match.group(1).replace(" ", "")
            rule = f"GRI-{rule}"
            output.append(_make_chunk(page, match.group(0), "gri", rule, "", "", rule))
            has_structure = True
        for match in _NOTE.finditer(text):
            note_num = match.group(1)
            chapter_match = re.search(r"(?i)chapter\s+(\d{1,2})", text[:match.start() + 40])
            chapter = chapter_match.group(1).zfill(2) if chapter_match else ""
            output.append(_make_chunk(page, match.group(0), "chapter_note", f"Ch{chapter}/Note-{note_num}", chapter))
            has_structure = True
        # Keep the page passage as a fallback for citations where no structure matched.
        if not has_structure:
            output.append(_make_chunk(page, text, "page", f"Page-{page['page']}", str(page.get("chapter", ""))))
    # Exact deduplication keeps reruns idempotent.
    unique = {item["chunk_id"]: item for item in output}
    return list(unique.values())
