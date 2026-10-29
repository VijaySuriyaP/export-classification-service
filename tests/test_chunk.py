"""Chunk structure tests using explicitly non-official sample text."""
from src.indexer.chunk import chunk_pages


def test_heading_chunk_preserves_title_and_metadata() -> None:
    page = {"doc": "NOT_OFFICIAL_test.txt", "doc_version": "fixture-only", "page": 1,
        "text": "7301 Sheet piling of iron or steel\nSome fixture text about an example heading."}
    chunks = chunk_pages([page])
    headings = [x for x in chunks if x["kind"] == "heading"]
    assert headings
    assert headings[0]["heading"] == "7301"
    assert headings[0]["heading_title"].startswith("Sheet piling")
    assert headings[0]["chunk_id"]
