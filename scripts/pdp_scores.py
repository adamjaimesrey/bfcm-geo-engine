"""P3 - Validate COSMO score files written by Claude Code and update the index (SPEC 9.4/9.8).
Reads data/processed/pdp-scores/<group>.json, checks the format, checks every quote appears
word-for-word on the captured page, recomputes cosmo_score, sets priority in reference/pdp-index.csv.
Usage: python scripts/pdp_scores.py      (exit code 2 if any file is invalid)"""
import csv
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "reference" / "pdp-index.csv"
RAW = BASE / "data" / "raw" / "pdp"
SCORES = BASE / "data" / "processed" / "pdp-scores"
QUESTIONS = ["isA", "used_for_audience", "used_for_function", "used_for_event", "capable_of", "cause_benefit"]
BFCM_CATEGORIES = {"steam_iron", "handheld_steamer", "suction_steamer"}


def squash(t):
    return re.sub(r"\s+", " ", t).strip()


def page_text(group):
    d = json.load(open(RAW / group / "sections.json", encoding="utf-8"))
    parts = [d.get("h1", "")] + [s["heading"] + " " + s["text"] for s in d["sections"]]
    return squash(" ".join(parts))


def check(path, groups):
    errs = []
    try:
        d = json.load(open(path, encoding="utf-8"))
    except Exception as e:
        return None, [f"not valid JSON: {e}"]
    g = d.get("variant_group")
    if g != path.stem:
        errs.append(f"variant_group '{g}' does not match file name '{path.stem}'")
    if g not in groups:
        return None, errs + [f"unknown variant_group '{g}'"]
    if not (RAW / g / "sections.json").exists():
        return None, errs + ["page not captured (no sections.json)"]
    hay = page_text(g)
    qs = d.get("questions", {})
    if sorted(qs) != sorted(QUESTIONS):
        errs.append(f"questions must be exactly {QUESTIONS}")
    total = 0
    for q in QUESTIONS:
        item = qs.get(q, {})
        sc = item.get("score")
        if not isinstance(sc, int) or not 0 <= sc <= 3:
            errs.append(f"{q}: score must be a whole number 0-3, got {sc!r}"); continue
        total += sc
        ev = item.get("evidence", [])
        if not isinstance(ev, list):
            errs.append(f"{q}: evidence must be a list"); continue
        if sc > 0 and not ev:
            errs.append(f"{q}: score {sc} needs at least one quote")
        for e in ev:
            quote = squash(str(e.get("quote", "")))
            if not quote:
                errs.append(f"{q}: empty quote")
            elif quote not in hay:
                errs.append(f"{q}: quote not found word-for-word on the page: \"{quote[:80]}\"")
        if sc < 3 and not str(item.get("gap", "")).strip():
            errs.append(f"{q}: score {sc} < 3 needs a 'gap'")
    if not isinstance(qs.get("capable_of", {}).get("missing_attributes", None), list):
        errs.append("capable_of: 'missing_attributes' must be a list (empty if none)")
    return (round(total / 18 * 100) if not errs else None), errs


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    cols = list(rows[0].keys())
    groups = {r["variant_group"]: r["category"] for r in rows}
    results, missing, bad = {}, {}, 0
    for f in sorted(SCORES.glob("*.json")):
        score, errs = check(f, groups)
        if errs:
            bad += 1
            print(f"INVALID {f.name}:")
            for e in errs:
                print(f"   - {e}")
        else:
            results[f.stem] = score
            d = json.load(open(f, encoding="utf-8"))
            missing[f.stem] = len(d["questions"]["capable_of"].get("missing_attributes", []))
    # BFCM categories first, then lowest score, then MORE missing filter attributes first, then name
    ranked = sorted(results, key=lambda g: (groups[g] not in BFCM_CATEGORIES, results[g], -missing[g], g))
    prio = {g: i for i, g in enumerate(ranked, 1)}
    for r in rows:
        g = r["variant_group"]
        if g in results:
            r["cosmo_score"], r["priority"] = str(results[g]), str(prio[g])
            if r["status"] in ("", "indexed", "captured"):
                r["status"] = "scored"
        else:
            r["cosmo_score"], r["priority"] = "", ""
            if r["status"] == "scored":
                r["status"] = "captured"   # score file removed: back to captured
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    print(f"\n{len(results)} valid, {bad} invalid, {len(groups) - len(results) - bad} not scored yet")
    for g in ranked:
        print(f"  #{prio[g]:<3} {results[g]:>3}/100  {groups[g]:<18} {g}")
    if bad:
        sys.exit(2)


if __name__ == "__main__":
    main()
