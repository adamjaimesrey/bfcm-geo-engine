#!/bin/bash
# Run P5 brief batches unattended until all groups have a brief.
# Stops early if: a run makes no progress (e.g. session limit), any brief fails the renderer's checks,
# or any brief has a "for_owner" item. Safe to re-run: finished groups are skipped.
# Usage (from the project folder):  bash scripts/pdp_run_p5_batches.sh
set -u
cd "$(dirname "$0")/.." || exit 1
source .venv/bin/activate
unset ANTHROPIC_API_KEY            # never bill API credits: use the logged-in Pro subscription only
TOTAL=33
MAX_RUNS=12
mkdir -p logs
count() { ls data/processed/pdp-briefs/*.json 2>/dev/null | wc -l | tr -d ' '; }

for i in $(seq 1 "$MAX_RUNS"); do
  before=$(count)
  if [ "$before" -ge "$TOTAL" ]; then echo "DONE: all $TOTAL briefs written."; exit 0; fi
  echo "=== Run $i: $before of $TOTAL done; starting next 3 ($(date +%H:%M)) ==="
  claude -p "Follow reference/pdp-prompts/p5-brief.md exactly for the next 3 variant groups." \
    --permission-mode acceptEdits \
    --allowedTools "Read" "Write" "Edit" "Bash(python scripts/pdp_render.py *)" \
    > "logs/p5-run-$i.log" 2>&1
  after=$(count)
  echo "    briefs now: $after of $TOTAL (log: logs/p5-run-$i.log)"
  if [ "$after" -le "$before" ]; then
    echo "STOP: no new briefs this run (session limit or an error). Check the log, then re-run this script."; exit 1
  fi
  if ! python scripts/pdp_render.py --all > "logs/p5-render-$i.log" 2>&1; then
    echo "STOP: a brief failed the renderer's checks. See logs/p5-render-$i.log"; exit 1
  fi
  needs_owner=$(python3 -c "
import json, glob
for f in glob.glob('data/processed/pdp-briefs/*.json'):
    for x in json.load(open(f)).get('for_owner', []):
        if str(x).strip(): print(f.split('/')[-1][:-5], '->', x)")
  git add data/processed/pdp-briefs reference/pdp-index.csv >/dev/null 2>&1
  git commit -q -m "P5 briefs: auto run $i ($after of $TOTAL)" && echo "    committed."
  if [ -n "$needs_owner" ]; then
    echo "STOP: these briefs need you (for_owner):"; echo "$needs_owner"; exit 1
  fi
done
echo "Reached $MAX_RUNS runs without finishing; re-run the script to continue."
