"""P1 - Capture current PDPs (SPEC 9.4). One representative URL per variant group.
Saves data/raw/pdp/<group>/full.png, sections/NN-<slug>.png and sections.json, then
updates reference/pdp-index.csv (current_screenshot, sections_json, status=captured).

Usage:
  python scripts/pdp_capture.py --group airlift-spin-suction-steamer   # one group (G-P1 test)
  python scripts/pdp_capture.py --all                     # every group not yet captured
  add --refresh to re-capture groups that already have sections.json
"""
import argparse
import csv
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
INDEX = BASE / "reference" / "pdp-index.csv"
RAW = BASE / "data" / "raw" / "pdp"
DELAY_S = 3
BLOCK_WORDS = ("access denied", "just a moment", "attention required", "captcha", "forbidden", "are you a robot")

EXTRACT_JS = r"""
() => {
  const SKIP = 'header, nav, footer, script, style, noscript, [role=dialog], [aria-modal=true], ' +
               '[data-bv-show], [id^="BVRR"], [id^="bv-"], [class*="bv-cv2"], [class*="bv_main"]';
  const BLOCK = new Set(['H1','H2','H3','H4','P','LI','TD','TH','DT','DD','FIGCAPTION','BLOCKQUOTE','LABEL']);
  const isHeading = el => /^H[1-4]$/.test(el.tagName) || el.getAttribute('role') === 'tab'
                          || (el.classList.contains('data') && el.classList.contains('title'));
  const root = document.querySelector('main, #maincontent, .page-main') || document.body;
  const all = Array.from(root.querySelectorAll('*')).filter(el => !el.closest(SKIP));
  const qualifies = el => BLOCK.has(el.tagName) || isHeading(el) ||
      ((el.tagName === 'DIV' || el.tagName === 'SPAN') &&
       Array.from(el.childNodes).some(n => n.nodeType === 3 && n.textContent.trim()));
  const out = [];
  for (const el of all) {
    if (!qualifies(el)) continue;
    if (el.parentElement && el.parentElement.closest('h1,h2,h3,h4,[role=tab]')) continue;
    const hasBlockChild = Array.from(el.querySelectorAll('*')).some(c => qualifies(c));
    let text = hasBlockChild && !isHeading(el)
      ? Array.from(el.childNodes).filter(n => n.nodeType === 3).map(n => n.textContent).join(' ')
      : el.textContent;
    text = text.replace(/\s+/g, ' ').trim();
    if (!text) continue;
    const r = el.getBoundingClientRect();
    const visible = r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
    out.push({tag: el.tagName.toLowerCase(), heading: isHeading(el), text, visible,
              y: Math.round(r.top + window.scrollY), h: Math.round(r.height)});
  }
  const ld = Array.from(document.querySelectorAll('script[type="application/ld+json"]')).map(s => {
    try { const j = JSON.parse(s.textContent); return [].concat(j['@graph'] || j).map(x => x['@type']); }
    catch (e) { return []; } }).flat();
  const micro = Array.from(document.querySelectorAll('[itemtype]')).map(e => (e.getAttribute('itemtype') || '').split('/').pop());
  const md = document.querySelector('meta[name="description"]');
  const can = document.querySelector('link[rel="canonical"]');
  const h1 = document.querySelector('h1');
  return {blocks: out, title: document.title, meta_description: md ? md.content : '',
          canonical: can ? can.href : '', h1: h1 ? h1.textContent.replace(/\s+/g,' ').trim() : '',
          jsonld_types: ld, microdata_types: [...new Set(micro)], page_height: document.documentElement.scrollHeight,
          page_width: document.documentElement.scrollWidth};
}
"""

HIDE_OVERLAYS_JS = r"""
() => {
  document.querySelectorAll('[role=dialog],[aria-modal=true],.modals-overlay,.modal-popup').forEach(e => e.style.display='none');
  const vw = innerWidth, vh = innerHeight;
  document.querySelectorAll('body *').forEach(e => {
    const s = getComputedStyle(e);
    if ((s.position === 'fixed' || s.position === 'sticky') && e.offsetWidth * e.offsetHeight > 0.25 * vw * vh)
      e.style.display = 'none';
  });
}
"""


def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")[:50] or "section"


def build_sections(blocks):
    sections, cur = [], {"heading": "(top of page)", "level": "", "blocks": []}
    for b in blocks:
        if b["heading"]:
            sections.append(cur)
            cur = {"heading": b["text"], "level": b["tag"], "visible": b["visible"], "y": b["y"], "blocks": []}
        else:
            cur["blocks"].append(b)
    sections.append(cur)
    out = []
    for i, s in enumerate(s for s in sections if s["blocks"] or s["heading"] != "(top of page)"):
        vis_blocks = [b for b in s["blocks"] if b["visible"]]          # visible = its CONTENT is visible
        ys = [b["y"] for b in vis_blocks] + ([s["y"]] if vis_blocks and s.get("visible") else [])
        ends = [b["y"] + b["h"] for b in vis_blocks]
        out.append({"index": i, "heading": s["heading"], "level": s["level"],
                    "visible": bool(ys),
                    "y_top": min(ys) if ys else None, "y_bottom": max(ends) if ends else None,
                    "text": "\n".join(b["text"] for b in s["blocks"])})
    return out


REVIEW_START = {"reviews", "customer reviews", "rating snapshot", "ratings & reviews", "ratings and reviews"}
REVIEW_END = {"faq", "faqs", "frequently asked questions"}


def norm(t):
    t = re.sub(r"[^a-z0-9 ]+", " ", t.lower()).replace("ecommerce ", " ")
    return re.sub(r"\s+", " ", t).strip()


def filter_sections(sections, h1, product_names):
    """Split sections into the page's own copy (kept), related-product cards (names recorded) and reviews (dropped)."""
    h1n = norm(h1)
    names = [norm(n) for n in product_names]
    kept, related, n_rel, n_rev, in_reviews = [], [], 0, 0, False
    for s in sections:
        hn = norm(s["heading"])
        if hn in REVIEW_START or hn.startswith("reviews"):
            in_reviews = True
        elif in_reviews and hn in REVIEW_END:
            in_reviews = False
        if in_reviews:
            n_rev += 1; continue
        if hn == "related products":
            n_rel += 1; continue
        is_known_product = any(n[:35] and (hn.startswith(n[:35]) or n.startswith(hn[:35])) for n in names if n)
        is_price_card = len(s["text"]) <= 60 and "$" in s["text"]
        if hn and hn != h1n and (is_known_product or is_price_card):
            n_rel += 1
            if s["heading"] not in related:
                related.append(s["heading"])
            continue
        kept.append(s)
    for i, s in enumerate(kept):
        s["index"] = i
    return kept, {"related_product_cards": n_rel, "reviews": n_rev}, related


def capture(page, group, url, variant_urls, out_dir, product_names):
    resp = page.goto(url, wait_until="domcontentloaded", timeout=60000)
    status = resp.status if resp else None
    try:
        page.wait_for_load_state("networkidle", timeout=20000)
    except Exception:
        pass
    page.keyboard.press("Escape")
    for _ in range(12):                      # scroll to trigger lazy-loaded sections
        page.mouse.wheel(0, 1200); page.wait_for_timeout(300)
    page.evaluate("window.scrollTo(0, 0)"); page.wait_for_timeout(500)
    page.evaluate(HIDE_OVERLAYS_JS)

    data = page.evaluate(EXTRACT_JS)
    probe = (data["title"] + " " + data["h1"]).lower()
    if (status and status >= 400) or any(w in probe for w in BLOCK_WORDS) or not data["h1"]:
        out_dir.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(out_dir / "blocked.png"), full_page=False)
        raise RuntimeError(f"BLOCKED or not a PDP (HTTP {status}, title '{data['title']}', h1 '{data['h1']}'). "
                           f"See {out_dir / 'blocked.png'}")

    sec_dir = out_dir / "sections"; sec_dir.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(out_dir / "full.png"), full_page=True)
    sections, excluded, related = filter_sections(build_sections(data["blocks"]), data["h1"], product_names)
    for s in sections:
        if s["visible"] and s["y_bottom"] and s["y_bottom"] > s["y_top"]:
            top = max(0, s["y_top"] - 20)
            h = min(s["y_bottom"] + 20, data["page_height"]) - top
            p = sec_dir / f"{s['index']:02d}-{slug(s['heading'])}.png"
            page.screenshot(path=str(p), full_page=True,
                            clip={"x": 0, "y": top, "width": data["page_width"], "height": h})
            s["screenshot"] = str(p.relative_to(BASE))
    doc = {"variant_group": group, "url": url, "variant_urls": variant_urls, "http_status": status,
           "captured": date.today().isoformat(), "title": data["title"],
           "meta_description": data["meta_description"], "h1": data["h1"], "canonical": data["canonical"],
           "jsonld_types": data["jsonld_types"], "microdata_types": data["microdata_types"],
           "related_products": related, "excluded_sections": excluded, "sections": sections}
    (out_dir / "sections.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
    return sections


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--group"); ap.add_argument("--all", action="store_true"); ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    if not (a.group or a.all):
        sys.exit("Use --group <variant_group> or --all")

    rows = list(csv.DictReader(open(INDEX, encoding="utf-8")))
    cols = list(rows[0].keys())
    groups = {}
    for r in rows:
        groups.setdefault(r["variant_group"], []).append(r)
    todo = [a.group] if a.group else list(groups)
    if a.group and a.group not in groups:
        sys.exit(f"FATAL: unknown group '{a.group}'")

    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        done, failed = 0, False
        for g in todo:
            out_dir = RAW / g
            if (out_dir / "sections.json").exists() and not a.refresh:
                print(f"  skip {g} (already captured)"); continue
            members = sorted(groups[g], key=lambda r: r["product_name"])
            try:
                secs = capture(page, g, members[0]["url"], [m["url"] for m in members], out_dir,
                               [r["product_name"] for r in rows])
            except Exception as e:
                print(f"FATAL {g}: {e}")
                print("Stopping the batch so a blocked site isn't hammered. Fix, then re-run (captured groups are skipped).")
                failed = True
                break
            for m in members:
                m["current_screenshot"] = str((out_dir / "full.png").relative_to(BASE))
                m["sections_json"] = str((out_dir / "sections.json").relative_to(BASE))
                m["status"] = "captured"
            with open(INDEX, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
            vis = sum(s["visible"] for s in secs)
            print(f"  OK  {g}: {len(secs)} sections ({vis} visible, {len(secs) - vis} hidden e.g. closed tabs)")
            done += 1
            time.sleep(DELAY_S)
        browser.close()
    print(f"Done. {done} group(s) captured.")
    if failed:
        sys.exit(2)


if __name__ == "__main__":
    main()
