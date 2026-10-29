# Chunking and retrieval

The current indexer preserves PDF source filename, document version marker, page, content hash, stable chunk ID, kind and identifier. It recognizes visible four-digit heading lines, GRI-like rules and chapter-note headings; other pages remain page-level passages rather than being discarded. `find_headings_naming_article` ranks heading titles separately from raw material text, helping with cases where the name of an article (for example, a flask) differs from its material (for example, stainless steel).

Notes are separately typed when the page text exposes a recognizable note boundary. The current parser's regex extraction is intentionally conservative and must be checked against real documents. PDF page numbers are retained. Re-running index build upserts by stable chunk ID and changes only new/different hashes or embedding-version metadata.

**Current state:** lexical matching over `corpus/processed/chunks.jsonl`. `embed_model=lexical`, `embed_model_version=lexical-v1`. The embedding model and Chroma upsert are deferred; do not treat this as a semantic index. OCR-needed pages are detected by low extracted-text length, but automatic OCR execution is not wired in the current indexer.
