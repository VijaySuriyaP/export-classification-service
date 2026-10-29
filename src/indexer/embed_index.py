"""Idempotent local JSONL index writer; semantic embeddings/Chroma are deferred."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

INDEX_DIR = Path(__file__).resolve().parents[2] / "corpus" / "processed"


def upsert_chunks(chunks: list[dict[str, Any]], index_path: Path | None = None) -> dict[str, int]:
    """Upsert by chunk ID and count only new or changed content records."""
    path = index_path or (INDEX_DIR / "chunks.jsonl")
    existing = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                item = json.loads(line)
                existing[item["chunk_id"]] = item
            except (json.JSONDecodeError, KeyError):
                continue
    changed = 0
    for chunk in chunks:
        previous = existing.get(chunk["chunk_id"])
        if previous is None or previous.get("content_hash") != chunk.get("content_hash") or previous.get("embed_model_version") != chunk.get("embed_model_version"):
            existing[chunk["chunk_id"]] = chunk
            changed += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(existing[key], ensure_ascii=False) + "\n" for key in sorted(existing)), encoding="utf-8")
    status = {"chunk_count": len(existing), "changed_chunks": changed, "index_path": str(path)}
    (path.parent / "index_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    return status
