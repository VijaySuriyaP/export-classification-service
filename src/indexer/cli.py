"""Indexer command line interface: build, reembed (currently lexical), status."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.indexer.chunk import chunk_pages
from src.indexer.embed_index import INDEX_DIR, upsert_chunks
from src.indexer.parse import parse_pdf

CORPUS_RAW = Path(__file__).resolve().parents[2] / "corpus" / "raw"


def build() -> dict[str, int]:
    """Parse all PDF files found under corpus/raw and update the lexical index."""
    pages = []
    files = sorted(CORPUS_RAW.glob("*.pdf"))
    for path in files:
        pages.extend(parse_pdf(path))
    chunks = chunk_pages(pages)
    result = upsert_chunks(chunks)
    result["pdf_count"] = len(files)
    result["page_count"] = len(pages)
    (INDEX_DIR / "index_status.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not files:
        print("No PDFs found. Place official source PDFs in corpus/raw/; no synthetic tariff text is generated.")
    return result


def main() -> None:
    """Dispatch the selected indexer command."""
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["build", "reembed", "status"], default="status", nargs="?")
    args = parser.parse_args()
    status_path = INDEX_DIR / "index_status.json"
    if args.command in {"build", "reembed"}:
        build()
    else:
        print(status_path.read_text(encoding="utf-8") if status_path.exists() else '{"chunk_count":0}')


if __name__ == "__main__":
    main()
