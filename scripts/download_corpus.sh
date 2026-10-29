#!/usr/bin/env bash
set -euo pipefail
mkdir -p corpus/raw
# Official files are deliberately not hardcoded to a stale tariff edition.
# Supply URLs copied from the current official pages if direct URLs are available.
fetch_if_set() {
  local env_name="$1" filename="$2" url="${!1:-}"
  if [[ -n "$url" ]]; then
    echo "Downloading ${filename} from an explicitly supplied official URL..."
    curl --fail --location --retry 2 --output "corpus/raw/${filename}" "$url"
  else
    echo "Not downloading ${filename}: set ${env_name} to the current official direct PDF URL after checking its effective date."
  fi
}
fetch_if_set CBIC_TARIFF_PDF_URL "CBIC_Customs_Tariff_First_Schedule_current.pdf"
fetch_if_set DGFT_SCHEDULE_II_PDF_URL "DGFT_ITC_HS_Schedule_II_current.pdf"
echo
echo "Official starting points:"
echo "  CBIC: https://www.cbic.gov.in/ (Customs Tariff / First Schedule)"
echo "  DGFT: https://www.dgft.gov.in/ (latest notified ITC(HS) Schedule-II export policy)"
echo "No source PDF was generated or substituted automatically. See corpus/SOURCES.md."
