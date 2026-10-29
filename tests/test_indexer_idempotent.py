"""Idempotent JSONL index upsert tests."""
import json

from src.indexer.embed_index import upsert_chunks


def test_second_build_changes_zero_chunks(tmp_path) -> None:
    path = tmp_path / "chunks.jsonl"
    item = {"chunk_id": "fixture:1", "content_hash": "abc", "embed_model_version": "lexical-v1", "text": "non-official fixture"}
    first = upsert_chunks([item], path)
    second = upsert_chunks([item], path)
    assert first["changed_chunks"] == 1
    assert second["changed_chunks"] == 0
    assert json.loads(path.read_text().splitlines()[0])["chunk_id"] == "fixture:1"


def test_changed_hash_updates_only_changed_chunk(tmp_path) -> None:
    path = tmp_path / "chunks.jsonl"
    original = [{"chunk_id": "a", "content_hash": "one", "embed_model_version": "v1"}, {"chunk_id": "b", "content_hash": "two", "embed_model_version": "v1"}]
    upsert_chunks(original, path)
    changed = [dict(original[0], content_hash="changed"), original[1]]
    assert upsert_chunks(changed, path)["changed_chunks"] == 1
