# Official corpus register and download instructions

**Do not use this index for legal decisions until a human has checked every file's issuing authority, effective date and amendments.** No PDFs are bundled in this repository; no tariff text is invented.

## Required sources

| Corpus requirement | Official starting point | File convention | Version metadata to record |
|---|---|---|---|
| General Rules for Interpretation (GRI), General/Section Notes and First Schedule | CBIC official website: https://www.cbic.gov.in/ and its Customs Tariff / statutory document pages. The CBIC customs tariff register page is available at https://www.cbic.gov.in/entities/cbic-content-mst/NDA0MDE%3D | `CBIC_Customs_Tariff_First_Schedule_<effective-date>.pdf` | Notification/amendment date, effective-from date, retrieval date, official page URL |
| Chapter 73, including chapter notes | Same current consolidated First Schedule to the Customs Tariff Act, 1975 from CBIC | `CBIC_Customs_Tariff_Ch73_<effective-date>.pdf` if the chapter is downloaded separately | Effective date and source URL |
| Chapter 96, including chapter notes | Same current consolidated First Schedule to the Customs Tariff Act, 1975 from CBIC | `CBIC_Customs_Tariff_Ch96_<effective-date>.pdf` if downloaded separately | Effective date and source URL |
| ITC(HS) Schedule-II Export Policy and General Notes | DGFT official website: https://www.dgft.gov.in/; find the latest **notified** Schedule-II export-policy schedule under Regulatory Updates / ITC(HS). The DGFT's notification announcing the Schedule-II update dated 13 January 2025 is available at https://content.dgft.gov.in/Website/Notification_ITCHS.pdf | `DGFT_ITC_HS_Schedule_II_<effective-date>.pdf` | Notification number/date, effective-from date, publication URL, retrieval date |

Do not use old `ITC (HS), 2018` PDFs or a trade notice marked draft as the current export policy. Download the latest consolidated notified schedule from DGFT and record amendments. The dated notification above is an official entry point; it is not a substitute for downloading the latest consolidated schedule currently hosted by DGFT.

## Procedure

1. Download the current CBIC First Schedule containing GRI and section/chapter notes; if easier to handle, split the official PDF into the relevant pages for Chapters 73 and 96 without editing the source text.
2. Download the current notified DGFT Schedule-II Export Policy and the current General Notes to Export Policy.
3. Place PDFs into `corpus/raw/`. Record source URL, official document title, notification/effective date and retrieval date in a local source manifest; do not commit a restricted or non-redistributable file.
4. Run `make index` and inspect `corpus/processed/index_status.json` and `python scripts/inspect_corpus.py`.
5. Have a human confirm that GRI, Chapter 73 and Chapter 96 notes, candidate headings, and policy conditions actually appear in the extracted text. The vacuum-flask case is not considered confirmed until the real heading and GRI passages have been checked.

## Version, licensing and integrity

Use only official public-source PDFs and retain their original content. Follow the source website's usage/copyright notices. Store SHA-256 hashes and dates in the submission manifest if you distribute copies. Do not modify the original files. The parser's `doc_version` is currently `unrecorded`; add the verified version metadata before treating the index as production evidence.
