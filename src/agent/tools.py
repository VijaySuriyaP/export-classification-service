"""Evidence-retrieval tools over the current official-corpus JSONL index."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

INDEX_PATH = Path(__file__).resolve().parents[2] / "corpus" / "processed" / "chunks.jsonl"


def _tokens(value: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", value.lower()))


class AgentTools:
    """Lexical retrieval adapter with explicit provenance and per-call trace."""

    def __init__(self, request: dict[str, Any], index_path: Path | None = None) -> None:
        self.request = request
        self.index_path = index_path or INDEX_PATH
        self.trace: list[dict[str, Any]] = []
        self.call_count = 0

    def _record(self, tool: str, started: float, args: dict[str, Any], results: list[dict[str, Any]]) -> None:
        self.call_count += 1
        self.trace.append({"tool": tool, "args": args, "result_ids": [x.get("chunk_id") for x in results], "latency_ms": round((time.monotonic() - started) * 1000, 3)})

    def all_chunks(self) -> list[dict[str, Any]]:
        """Load indexed chunks; empty index is an explicit no-evidence state."""
        if not self.index_path.exists():
            return []
        chunks = []
        with self.index_path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    item = json.loads(line)
                    if isinstance(item, dict) and item.get("chunk_id") and item.get("text"):
                        chunks.append(item)
                except json.JSONDecodeError:
                    continue
        return chunks

    def corpus_search(self, query: str, filters: dict[str, Any] | None = None, limit: int = 8) -> list[dict[str, Any]]:
        """Lexically rank chunks, optionally filtering by chapter and kind."""
        started = time.monotonic()
        filters = filters or {}
        terms = _tokens(query)
        ranked = []
        for chunk in self.all_chunks():
            if filters.get("chapter") and str(chunk.get("chapter")) != str(filters["chapter"]):
                continue
            if filters.get("kind") and chunk.get("kind") != filters["kind"]:
                continue
            content_terms = _tokens(str(chunk.get("heading_title", "")) + " " + str(chunk.get("text", "")))
            score = len(terms & content_terms) / max(1, len(terms))
            if score > 0:
                ranked.append((score, chunk))
        ranked.sort(key=lambda pair: (-pair[0], str(pair[1].get("chunk_id", ""))))
        results = [dict(item, retrieval_score=round(score, 4)) for score, item in ranked[:limit]]
        self._record("corpus_search", started, {"query": query, "filters": filters, "limit": limit}, results)
        return results

    def find_headings_naming_article(self, term: str, limit: int = 8) -> list[dict[str, Any]]:
        """Search headings by title, not only by raw material words."""
        started = time.monotonic()
        terms = _tokens(term)
        ranked = []
        for chunk in self.all_chunks():
            if chunk.get("kind") != "heading":
                continue
            title = _tokens(str(chunk.get("heading_title", "")))
            score = len(terms & title) / max(1, len(terms))
            if score > 0:
                ranked.append((score, chunk))
        ranked.sort(key=lambda pair: (-pair[0], str(pair[1].get("chunk_id", ""))))
        results = [dict(item, retrieval_score=round(score, 4)) for score, item in ranked[:limit]]
        self._record("find_headings_naming_article", started, {"term": term, "limit": limit}, results)
        return results

    def get_clause(self, identifier: str) -> dict[str, Any] | None:
        """Return an exact clause by identifier, if indexed."""
        started = time.monotonic()
        matches = [item for item in self.all_chunks() if item.get("identifier") == identifier]
        self._record("get_clause", started, {"identifier": identifier}, matches[:1])
        return matches[0] if matches else None

    def list_notes_for(self, heading_or_chapter: str) -> list[dict[str, Any]]:
        """Return notes matching a chapter/heading context."""
        started = time.monotonic()
        digits = re.findall(r"\d+", heading_or_chapter)
        chapter = (digits[0][:2] if digits else "")
        results = [x for x in self.all_chunks() if x.get("kind") in {"section_note", "chapter_note"} and (not chapter or str(x.get("chapter", "")).zfill(2) == chapter)]
        self._record("list_notes_for", started, {"heading_or_chapter": heading_or_chapter}, results)
        return results

    def get_request_field(self, name: str) -> Any:
        """Expose only a field from the already validated request."""
        started = time.monotonic()
        value = self.request.get(name)
        self.trace.append({"tool": "get_request_field", "args": {"name": name}, "result_ids": [], "latency_ms": round((time.monotonic() - started) * 1000, 3)})
        self.call_count += 1
        return value

    def policy_lookup(self, hs_code: str) -> dict[str, Any] | None:
        """Find an exact export-policy row in indexed official passages."""
        started = time.monotonic()
        matches = [x for x in self.all_chunks() if x.get("kind") == "policy" and str(x.get("hs_code", x.get("heading", ""))) == hs_code]
        self._record("policy_lookup", started, {"hs_code": hs_code}, matches[:1])
        return matches[0] if matches else None
