"""Flag spreadsheet drag-fill errors in the spec files: a row whose numbers
are each exactly +1 from the row above (same category) in 2+ spec columns.
Usage: python scripts/check_specs.py"""
import csv, re
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "reference"
SKIP = {"category", "product_name", "sku", "url", "source", "last_verified"}

def num(v):
    m = re.search(r"-?\d+(?:\.\d+)?", str(v).replace(",", ""))
    return float(m.group()) if m else None

found = 0
for f in sorted(REF.glob("product-spec-*.csv")):
    rows = list(csv.DictReader(open(f, encoding="utf-8")))
    cols = [c for c in rows[0] if c not in SKIP] if rows else []
    for prev, cur in zip(rows, rows[1:]):
        if prev["category"] != cur["category"]:
            continue
        hits = [c for c in cols
                if num(prev[c]) is not None and num(cur[c]) is not None
                and num(cur[c]) - num(prev[c]) == 1]
        if len(hits) >= 2:
            found += 1
            print(f"SUSPECT DRAG-FILL in {f.name}:")
            print(f"  above: {prev['product_name']}")
            print(f"  row:   {cur['product_name']}")
            print(f"  +1 in: {', '.join(hits)}\n")
print("No drag-fill suspects found." if not found else f"{found} suspect row(s) - check them manually.")
