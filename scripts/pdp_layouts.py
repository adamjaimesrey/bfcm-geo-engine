"""P2 - Layout patterns (SPEC 9.4). Turns each captured PDP into a sequence of section TYPES,
groups pages with the same sequence into a template per category, writes
reference/pdp-layout-patterns.md and the layout_template column of reference/pdp-index.csv.
Usage: python scripts/pdp_layouts.py"""
import csv
import json
from collections import Counter
from datetime import date
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "reference" / "pdp-index.csv"
RAW = BASE / "data" / "raw" / "pdp"
OUT = BASE / "reference" / "pdp-layout-patterns.md"
FAQ_HEADINGS = {"FAQ", "FAQS", "FREQUENTLY ASKED QUESTIONS"}
FIXED_SHARE = 0.5   # a heading on >= 50% of pages is a fixed site label, not product-specific copy
READABLE = {"top": "top of page", "buy_box": "buy box (H1, price, bullets)", "banner": "banner",
            "hidden_block": "hidden block", "faq_group": "FAQ group", "faq_q": "FAQ question"}


def key(h):
    return " ".join(h.split()).upper()


def tokens(doc, fixed):
    out, in_faq = [], False
    h1 = key(doc.get("h1", ""))
    for s in doc["sections"]:
        h = key(s["heading"])
        if s["heading"] == "(top of page)":
            t = "top"
        elif h == h1:
            if any(t == "buy_box" for t, _ in out):
                continue                      # hidden repeat of the product name (e.g. sticky bar): not layout
            t = "buy_box"
        elif h in FAQ_HEADINGS:
            in_faq, t = True, "FAQ"
        elif in_faq and (s["heading"].rstrip().endswith("?") or not s["text"].strip() or not s["visible"]):
            if not s["text"].strip():
                continue                      # FAQ group heading: not part of the layout shape
            t = "faq_q"
        elif h in fixed:
            in_faq = False
            t = h
        else:
            in_faq = False                    # visible ordinary content ends the FAQ region
            if not s["visible"]:
                continue                      # hidden non-FAQ block (e.g. mobile copy of a banner): not layout
            t = "banner"
        out.append((t, s["visible"]))
    return out


def collapse(seq):
    out = []
    for t, vis in seq:
        if out and out[-1][0] == t:
            out[-1][1] += 1; out[-1][2].append(vis)
        else:
            out.append([t, 1, [vis]])
    return out


ORIGINAL = {}


def describe(steps_by_group):
    """steps_by_group: list of collapsed sequences sharing one skeleton -> readable template lines."""
    lines = []
    for i, (tok, _, _) in enumerate(steps_by_group[0]):
        counts = [g[i][1] for g in steps_by_group]
        vis = [v for g in steps_by_group for v in g[i][2]]
        shown = "shown" if sum(vis) >= len(vis) / 2 else "hidden"
        n = f" x{min(counts)}" if min(counts) == max(counts) else f" x{min(counts)}-{max(counts)}"
        n = "" if max(counts) == 1 else n
        name = READABLE.get(tok, ORIGINAL.get(tok, tok))
        lines.append(f"{i + 1}. {name}{n} ({shown})")
    return lines


def main():
    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    cols = list(rows[0].keys())
    cat_of = {r["variant_group"]: r["category"] for r in rows}
    docs = {}
    for g in cat_of:
        f = RAW / g / "sections.json"
        if not f.exists():
            raise SystemExit(f"FATAL: {g} not captured yet (run P1 first)")
        docs[g] = json.load(open(f, encoding="utf-8"))

    freq = Counter()
    for d in docs.values():
        freq.update({key(s["heading"]) for s in d["sections"]})
        for s in d["sections"]:
            ORIGINAL.setdefault(key(s["heading"]), s["heading"].strip())
    fixed = {h for h, c in freq.items() if c >= FIXED_SHARE * len(docs) and h not in FAQ_HEADINGS}

    seqs = {g: collapse(tokens(d, fixed)) for g, d in docs.items()}
    template_of, md = {}, [f"# PDP layout patterns (P2, generated {date.today().isoformat()})", "",
                           "Each page is reduced to a sequence of VISIBLE section types (hidden duplicates, e.g. mobile copies",
                           "of banners, are ignored here; their text is still in sections.json). Fixed site labels keep their name;",
                           "product-specific headings become 'banner'. Edits in P5 must fit the page's template;",
                           "any break needs a one-line justification in the brief.", ""]
    for cat in sorted(set(cat_of.values())):
        groups = sorted(g for g in docs if cat_of[g] == cat)
        by_skel = {}
        for g in groups:
            by_skel.setdefault(tuple(s[0] for s in seqs[g]), []).append(g)
        ranked = sorted(by_skel.items(), key=lambda kv: -len(kv[1]))
        md += [f"## {cat} ({len(groups)} groups, {len(ranked)} template{'s' if len(ranked) > 1 else ''})", ""]
        for n, (skel, members) in enumerate(ranked, 1):
            tid = f"T-{cat}-{n}"
            for g in members:
                template_of[g] = tid
            md += [f"### {tid}: {len(members)} of {len(groups)} groups", ""]
            md += describe([seqs[g] for g in members])
            md += ["", "Groups: " + ", ".join(members), ""]
            if n > 1:
                main_skel = ranked[0][0]
                missing = [t for t in main_skel if t not in skel]
                extra = [t for t in skel if t not in main_skel]
                diff = []
                if missing: diff.append("missing " + ", ".join(READABLE.get(t, ORIGINAL.get(t, t)) for t in missing))
                if extra: diff.append("extra " + ", ".join(READABLE.get(t, ORIGINAL.get(t, t)) for t in extra))
                if not diff: diff.append("same sections, different order")
                md += [f"Differs from T-{cat}-1: " + "; ".join(diff), ""]
    OUT.write_text("\n".join(md) + "\n", encoding="utf-8")

    for r in rows:
        r["layout_template"] = template_of[r["variant_group"]]
    with open(INDEX, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    c = Counter(template_of.values())
    print(f"Wrote {OUT.name}: {len(c)} templates across {len(set(cat_of.values()))} categories")
    for t, n in sorted(c.items()):
        print(f"  {t}: {n} group(s)")


if __name__ == "__main__":
    main()
