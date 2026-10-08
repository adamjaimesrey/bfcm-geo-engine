"""P0 - Build reference/pdp-index.csv: one row per PDP from the three spec files,
with variant groups (SPEC 9.2). Re-running keeps any values later stages wrote.
Usage: python scripts/pdp_index.py"""
import csv
import re
from pathlib import Path

REF = Path(__file__).resolve().parent.parent / "reference"
SPEC_FILES = ["product-spec-garment.csv", "product-spec-fans.csv", "product-spec-vacuums.csv"]
OUT = REF / "pdp-index.csv"
NON_SPEC = {"category", "product_name", "sku", "url", "source", "last_verified"}
COLS = ["variant_group", "product_name", "sku", "url", "category", "current_screenshot", "sections_json",
        "layout_template", "cosmo_score", "priority", "edit_docx", "after_image", "status"]
IDENTITY = {"variant_group", "product_name", "sku", "url", "category"}

# Colour/finish suffixes after the last comma that mark a colour variant.
COLOURS = {"black", "silver", "blue", "green", "red coral", "yellow", "aqua green", "copper", "metal", "white"}
# Products confirmed by the owner as colour-only variants despite different names: name prefix -> base it joins.
SAME_PRODUCT = {}   # none: AirLift Spin (12 min) and Spin Deluxe (16 min) differ in steam time per fill


def base_name(name):
    for prefix, base in SAME_PRODUCT.items():
        if name.startswith(prefix):
            return base
    parts = name.rsplit(",", 1)
    if len(parts) == 2 and parts[1].strip().lower() in COLOURS:
        return parts[0].strip()
    return name.strip()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().replace("+", " plus ")).strip("-")


def main():
    rows = []
    for fn in SPEC_FILES:
        f = REF / fn
        if not f.exists():
            raise SystemExit(f"FATAL: missing {f}")
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            spec_key = tuple((k, (v or "").strip()) for k, v in sorted(r.items()) if k not in NON_SPEC)
            rows.append({**r, "_base": base_name(r["product_name"]), "_spec": spec_key})

    # group = same category + same base name + identical specs
    groups = {}
    for r in rows:
        groups.setdefault((r["category"], r["_base"], r["_spec"]), []).append(r)
    # if one base name splits into several spec-distinct groups, suffix each with its first member's finish
    bases = {}
    for (cat, base, spec) in groups:
        bases.setdefault((cat, base), []).append(spec)
    used = {}
    for (cat, base, spec), members in groups.items():
        gid = slug(base)
        if len(bases[(cat, base)]) > 1:
            tail = members[0]["product_name"].rsplit(",", 1)
            gid += "-" + slug(tail[1] if len(tail) == 2 else "standard")
        if gid in used:
            raise SystemExit(f"FATAL: group name collision '{gid}': {used[gid]} vs {members[0]['product_name']}")
        used[gid] = members[0]["product_name"]
        for m in members:
            m["variant_group"] = gid

    old = {}
    if OUT.exists():
        old = {r["sku"]: r for r in csv.DictReader(open(OUT, encoding="utf-8"))}

    out = []
    for r in sorted(rows, key=lambda x: (x["category"], x["variant_group"], x["product_name"])):
        row = {c: "" for c in COLS}
        row.update({c: r[c] for c in IDENTITY})
        prev = old.get(r["sku"], {})
        if prev.get("variant_group") != r["variant_group"]:
            prev = {}   # product moved to a different group: its old screenshots/scores no longer apply
        for c in COLS:
            if c not in IDENTITY and prev.get(c):
                row[c] = prev[c]
        row["status"] = row["status"] or "indexed"
        out.append(row)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(out)

    n_groups = len({r["variant_group"] for r in out})
    print(f"Wrote {OUT.name}: {len(out)} PDPs in {n_groups} variant groups")
    multi = {}
    for r in out:
        multi.setdefault(r["variant_group"], []).append(r["product_name"])
    for g, names in multi.items():
        if len(names) > 1:
            print(f"  group {g}: {len(names)} variants")


if __name__ == "__main__":
    main()
