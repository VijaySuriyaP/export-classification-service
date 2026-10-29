# Vacuum-flask reference case — requires official corpus confirmation

The project prompt names a section 4.1 vacuum-flask case and expects a heading-title search to find a heading naming vacuum flasks even when the user describes a stainless-steel flask. This repository deliberately does not assert a heading passage, tariff code, GRI decision or export-policy row without inspecting the current official source PDFs.

To confirm the case:

1. Download the latest effective Customs Tariff First Schedule/GRI and the latest DGFT Schedule-II from official sources listed in `corpus/SOURCES.md`.
2. Run `make index`.
3. Run `python scripts/inspect_corpus.py` and retain the actual chunk IDs, document version, page and exact extracted passage.
4. Have a domain reviewer verify extraction against the PDF (especially section/chapter notes and the heading-title line).
5. Update this file with the actual passage references and effective date only after that confirmation.

Status: `needs_corpus_confirmation`.
