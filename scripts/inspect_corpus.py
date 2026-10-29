#!/usr/bin/env python3
"""Show live indexed passages related to vacuum-flask classification research."""
from __future__ import annotations

import json
from pathlib import Path

path = Path(__file__).resolve().parents[1] / "corpus" / "processed" / "chunks.jsonl"
if not path.exists():
    raise SystemExit("No processed chunks. Download current official PDFs, run `make index`, then retry.")
terms = {"vacuum", "flask", "container", "gri", "9617"}
found = []
for line in path.read_text(encoding="utf-8").splitlines():
    try:
        item = json.loads(line)
    except json.JSONDecodeError:
        continue
    text = (str(item.get("heading_title", "")) + " " + str(item.get("identifier", "")) + " " + str(item.get("text", ""))).lower()
    if any(term in text for term in terms):
        found.append(item)
for item in found[:50]:
    print(json.dumps({key: item.get(key) for key in ("chunk_id", "doc", "doc_version", "chapter", "heading", "heading_title", "kind", "identifier", "page", "text")}, ensure_ascii=False, indent=2))
if not found:
    print("No matching passage found. Do not assume the vacuum-flask case is confirmed.")
