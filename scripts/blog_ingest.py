"""Stage 1 - Ingest, filter (full inventory -> SIHS blog bank) & GSC join. Gate G1 (soft): data/raw/gsc-pages.csv; if absent, gsc_joined=False and continue."""

import sys
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
BANK_CSV = BASE_DIR / "reference" / "sihs-blog-bank.csv"
INVENTORY_CSV = BASE_DIR / "reference" / "blog-url-inventory.csv"
OUTPUT_CSV = BASE_DIR / "data" / "processed" / "blog-filtered.csv"


def normalize_slug(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().str.rstrip("/")


def load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    bank = pd.read_csv(BANK_CSV)
    inventory = pd.read_csv(INVENTORY_CSV)
    return bank, inventory


def merge_bank_with_inventory(bank: pd.DataFrame, inventory: pd.DataFrame):
    bank = bank.copy()
    inventory = inventory.copy()
    bank["_slug_key"] = normalize_slug(bank["slug"])
    inventory["_slug_key"] = normalize_slug(inventory["Slug"])

    dup_mask = inventory["_slug_key"].duplicated(keep=False)
    dup_inventory_slugs = sorted(inventory.loc[dup_mask, "_slug_key"].unique().tolist())

    merged = bank.merge(
        inventory[["_slug_key", "Unique Inlinks"]],
        on="_slug_key",
        how="left",
        indicator=True,
    )

    unmatched_bank_slugs = sorted(
        merged.loc[merged["_merge"] == "left_only", "slug"].tolist()
    )
    return merged, unmatched_bank_slugs, dup_inventory_slugs


def validate_merge(merged: pd.DataFrame, expected_rows: int, unmatched_bank_slugs: list, dup_inventory_slugs: list) -> int:
    matched_count = int((merged["_merge"] == "both").sum())
    ok = (
        len(merged) == expected_rows
        and not unmatched_bank_slugs
        and not dup_inventory_slugs
    )
    if not ok:
        lines = [
            f"FATAL: expected {expected_rows} matched rows (rows in blog bank); "
            f"got {len(merged)} merged rows, {matched_count} matched.",
            "",
            "Bank slugs with NO matching inventory row:",
        ]
        lines += [f"  - {s}" for s in unmatched_bank_slugs] or ["  (none)"]
        lines += ["", "Inventory-side duplicate slug collisions (ambiguous matches):"]
        lines += [f"  - {s}" for s in dup_inventory_slugs] or ["  (none)"]
        print("\n".join(lines), file=sys.stderr)
        sys.exit(1)
    return matched_count


def build_output(merged: pd.DataFrame) -> pd.DataFrame:
    out = merged[["slug", "url", "category", "Unique Inlinks"]].rename(
        columns={"Unique Inlinks": "unique_inlinks"}
    )
    out["gsc_joined"] = False
    out["striking_distance"] = pd.NA
    out["low_ctr_high_impr"] = pd.NA
    return out[
        ["slug", "url", "category", "unique_inlinks",
         "gsc_joined", "striking_distance", "low_ctr_high_impr"]
    ]


def main():
    bank, inventory = load_inputs()
    merged, unmatched_bank_slugs, dup_inventory_slugs = merge_bank_with_inventory(bank, inventory)
    matched_count = validate_merge(merged, len(bank), unmatched_bank_slugs, dup_inventory_slugs)

    out = build_output(merged)
    out.to_csv(OUTPUT_CSV, index=False)

    print(f"Inventory rows loaded: {len(inventory)}")
    print(f"Bank rows loaded: {len(bank)}")
    print(f"Matched rows: {matched_count} (expected {len(bank)})")
    print("Category breakdown:")
    print(out["category"].value_counts().to_string())
    print("gsc_joined = False")
    print(
        "WARNING: GSC join not performed (data/raw/gsc-pages.csv not read in this build). "
        "striking_distance and low_ctr_high_impr are NA for all rows; "
        "prioritisation will be PROVISIONAL until GSC data is joined."
    )
    reread = pd.read_csv(OUTPUT_CSV)
    print(f"Output written to {OUTPUT_CSV} ({reread.shape[0]} rows, CSV-aware re-read)")


if __name__ == "__main__":
    main()
