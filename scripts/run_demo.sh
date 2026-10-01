#!/usr/bin/env bash
# Stage synthetic sample_data into the expected locations and run Stages 1-4.
set -euo pipefail

export PYTHONDONTWRITEBYTECODE=1
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || { echo "FATAL: $PY not found (create the .venv first)" >&2; exit 1; }

REF_FILES=(sihs-blog-bank blog-url-inventory focus-keywords product-spec-garment
           product-spec-fans product-spec-vacuums skus-steam-irons skus-handheld-steamers)

mkdir -p data/raw/html data/processed output

# Never overwrite a reference file that isn't an identical demo copy.
for f in "${REF_FILES[@]}"; do
  if [ -e "reference/$f.csv" ] && ! cmp -s "sample_data/$f.csv" "reference/$f.csv"; then
    echo "FATAL: reference/$f.csv exists and differs from the demo copy; refusing to overwrite." >&2
    exit 1
  fi
done
for f in "${REF_FILES[@]}"; do cp "sample_data/$f.csv" "reference/$f.csv"; done
cp sample_data/html/*.html data/raw/html/
echo "Staged demo data -> reference/, data/raw/html/"

echo; echo "=== Stage 1: ingest ===";   "$PY" scripts/ingest.py
echo; echo "=== Stage 2: classify ==="; "$PY" scripts/classify.py
echo; echo "=== Stage 3: score (offline, cache only) ==="; GEO_OFFLINE=1 "$PY" scripts/score.py
echo; echo "=== Stage 4: prioritise ==="; "$PY" scripts/prioritize.py

cat <<MSG

Outputs:
  Stage 1  data/processed/sihs-filtered.csv
  Stage 2  data/processed/sihs-classified.csv
  Stage 3  data/processed/sihs-scored.csv
  Stage 4  output/sihs-worklist.xlsx

Note: GSC join not implemented in this build (G1 soft gate) - worklist is provisional.
Stage 5 skipped: needs ANTHROPIC_API_KEY (see .env.example). Example output: sample_output/example-brief.md
MSG
