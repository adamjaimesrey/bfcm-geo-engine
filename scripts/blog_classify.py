"""Stage 2 - Content-type classification (buying/vs/gift/price/informational) per reference/blog-content-type-patterns.md. Precondition: blog-filtered.csv."""

import re
import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
FILTERED_CSV = BASE_DIR / "data" / "processed" / "blog-filtered.csv"
INVENTORY_CSV = BASE_DIR / "reference" / "blog-url-inventory.csv"
OUTPUT_CSV = BASE_DIR / "data" / "processed" / "blog-classified.csv"
BANK_CSV = BASE_DIR / "reference" / "sihs-blog-bank.csv"

# Transcribed from reference/blog-content-type-patterns.md, in priority order.
PATTERNS = [
    ("comparison_vs", [r"\bvs\b", r"versus", r"compare"], True),
    ("buying_guide", [r"\bbest\b", r"guide", r"choosing", r"which"], True),
    ("gift_guide", [r"gift", r"for-him", r"for-her", r"for-home"], True),
    ("price_bracket", [r"under[- ]?\$?\d+", r"budget", r"cheap"], True),
]


def normalize_slug(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().str.rstrip("/")


def load_and_join() -> pd.DataFrame:
    expected_rows = len(pd.read_csv(BANK_CSV))
    filtered = pd.read_csv(FILTERED_CSV)
    inventory = pd.read_csv(INVENTORY_CSV)

    filtered = filtered.copy()
    inventory = inventory.copy()
    filtered["_slug_key"] = normalize_slug(filtered["slug"])
    inventory["_slug_key"] = normalize_slug(inventory["Slug"])

    joined = filtered.merge(
        inventory[["_slug_key", "Title 1", "H1-1", "H2-1", "H2-2"]],
        on="_slug_key",
        how="left",
    )

    if len(joined) != expected_rows:
        print(
            f"FATAL: expected {expected_rows} rows (rows in blog bank) after inventory join, got {len(joined)}.",
            file=sys.stderr,
        )
        sys.exit(1)

    return joined


def build_blob(row: pd.Series) -> str:
    parts = [row["slug"]]
    return " ".join(str(p) for p in parts if pd.notna(p)).lower()


OVERRIDES = {
    "compact-fabric-steamer-for-trips": ("buying_guide", True, "override"),
    "multi-purpose-fabric-steamer-guide": ("buying_guide", True, "override"),
    "Ecommerce-Beginners-Guide-How-to-use-a-steamer": ("informational", False, "override"),
}


def classify_row(blob: str, slug: str) -> tuple:
    if slug in OVERRIDES:
        return OVERRIDES[slug]
    for content_type, regexes, decision_content in PATTERNS:
        for pattern in regexes:
            match = re.search(pattern, blob, re.IGNORECASE)
            if match:
                return content_type, decision_content, match.group()
    return "informational", False, ""


def main():
    joined = load_and_join()

    results = joined.apply(lambda row: classify_row(build_blob(row), row['slug']), axis=1)
    joined["content_type"] = results.apply(lambda r: r[0])
    joined["decision_content"] = results.apply(lambda r: r[1])
    joined["matched_on"] = results.apply(lambda r: r[2])

    out = joined.drop(columns=["_slug_key", "Title 1", "H1-1", "H2-1", "H2-2"])

    if len(out) != len(joined):
        print(
            f"FATAL: expected {len(joined)} output rows, got {len(out)}.",
            file=sys.stderr,
        )
        sys.exit(1)

    out.to_csv(OUTPUT_CSV, index=False)

    reread = pd.read_csv(OUTPUT_CSV)
    print(f"Output written to {OUTPUT_CSV} ({reread.shape[0]} rows, CSV-aware re-read)")

    print("\ncontent_type breakdown:")
    print(out["content_type"].value_counts().to_string())

    decision_count = int(out["decision_content"].sum())
    print(f"\ndecision_content=True count: {decision_count} / {len(out)}")

    print("\nslug -> content_type (all rows):")
    for _, row in out.iterrows():
        print(f"  {row['slug']} -> {row['content_type']}")


if __name__ == "__main__":
    main()
