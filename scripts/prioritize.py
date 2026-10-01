"""Stage 4 - Prioritise decision-content + gap analysis; write worklist table.
Reads data/processed/sihs-scored.csv. Precondition: sihs-scored.csv exists.
Output: output/sihs-worklist.xlsx (pandas + openpyxl). No dashboard/plotly."""

import sys
from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter

BASE_DIR = Path(__file__).resolve().parent.parent
SCORED_CSV = BASE_DIR / "data" / "processed" / "sihs-scored.csv"
OUTPUT_XLSX = BASE_DIR / "output" / "sihs-worklist.xlsx"

REQUIRED = ["slug", "category", "content_type", "geo_score",
            "weakest_criteria", "decision_content"]
DECISION_TYPES = ["buying_guide", "comparison_vs", "gift_guide", "price_bracket"]


def main():
    if not SCORED_CSV.exists():
        sys.exit(f"FATAL: {SCORED_CSV} not found (run Stage 3 first).")

    scored = pd.read_csv(SCORED_CSV)
    missing = [c for c in REQUIRED if c not in scored.columns]
    if missing:
        sys.exit(f"FATAL: sihs-scored.csv missing columns: {missing}")

    # normalise decision_content to bool (defensive against str parsing)
    dc = scored["decision_content"].astype(str).str.strip().str.lower()
    scored["_dc"] = dc.isin(["true", "1", "yes"])

    # --- prioritise: decision-content only, worst score first ---
    work = scored[scored["_dc"]].copy()
    work = work.sort_values("geo_score", ascending=True).reset_index(drop=True)
    work.insert(0, "priority_rank", range(1, len(work) + 1))
    work["geo_score"] = work["geo_score"].round(1)
    work["strategy_bucket"] = "geo_consideration"
    work["gsc_signal"] = "provisional (no GSC)"

    cols = ["priority_rank", "slug"]
    if "url" in work.columns:
        cols.append("url")
    cols += ["category", "content_type", "geo_score",
             "weakest_criteria", "strategy_bucket", "gsc_signal"]
    out = work[cols]

    # --- write xlsx ---
    with pd.ExcelWriter(OUTPUT_XLSX, engine="openpyxl") as writer:
        out.to_excel(writer, index=False, sheet_name="worklist")
        ws = writer.sheets["worklist"]
        ws.freeze_panes = "A2"
        for i, col in enumerate(out.columns, start=1):
            width = max([len(str(col))] + [len(str(v)) for v in out[col]]) + 2
            ws.column_dimensions[get_column_letter(i)].width = min(width, 60)

    # --- verify + report ---
    reread = pd.read_excel(OUTPUT_XLSX)
    print(f"Wrote {OUTPUT_XLSX} ({len(reread)} rows, re-read from disk)\n")

    print("=== Worklist (priority order, feeds Stage 5) ===")
    show = [c for c in ["priority_rank", "slug", "content_type",
                        "geo_score", "weakest_criteria"] if c in out.columns]
    print(out[show].to_string(index=False))

    # --- gap analysis across all in-scope posts ---
    counts = scored["content_type"].value_counts()
    gaps = [t for t in DECISION_TYPES if counts.get(t, 0) == 0]
    print(f"\n=== gap analysis (all {len(scored)}) ===")
    print(counts.to_string())
    if gaps:
        print(f"\nCONTENT GAPS (zero posts) -> candidate NEW content, do NOT auto-create: {gaps}")


if __name__ == "__main__":
    main()
