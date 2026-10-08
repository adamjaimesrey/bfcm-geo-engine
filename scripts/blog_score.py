"""Stage 3 - GEO extractability scoring (absolute) per reference/blog-scoring-rules.md. Gate G2: live HTML for all in-scope posts cached to data/raw/blog-html/."""

import json
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
CLASSIFIED_CSV = BASE_DIR / "data" / "processed" / "blog-classified.csv"
HTML_CACHE_DIR = BASE_DIR / "data" / "raw" / "blog-html"
OUTPUT_CSV = BASE_DIR / "data" / "processed" / "blog-scored.csv"
BANK_CSV = BASE_DIR / "reference" / "sihs-blog-bank.csv"

USER_AGENT = "bfcm-geo-engine/1.0 (SEO GEO audit; internal tool)"
OFFLINE = os.environ.get("GEO_OFFLINE") == "1"  # never touch the network; cache miss is fatal
FETCH_TIMEOUT = 10
FETCH_DELAY_SECONDS = 1.5
RETRY_DELAY_SECONDS = 2

WEIGHTS = {
    "answer_first": 20,
    "question_headings": 10,
    "comparison_table": 15,
    "qa_faq_block": 15,
    "stats_count": 10,
    "citations_count": 5,
    "schema_completeness": 10,
    "freshness": 5,
    "gifting_persona_language": 10,
}
SUB_SCORE_COLUMNS = list(WEIGHTS.keys()) + ["keyword_stuffing_penalty"]

QUESTION_WORDS = ("who", "what", "why", "how", "when", "which", "is", "does", "can")
GIFT_PHRASES = (r"\bgift\b", r"\bfor him\b", r"\bfor her\b", r"\bpresent\b")
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for", "with",
    "is", "are", "was", "were", "be", "been", "it", "its", "this", "that", "as",
    "at", "by", "from", "your", "you", "will", "can", "if", "not", "so", "than",
    "into", "up", "out", "about", "then", "also", "our", "we",
}


def normalize_slug(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().str.rstrip("/")


def load_classified() -> pd.DataFrame:
    df = pd.read_csv(CLASSIFIED_CSV)
    expected_rows = len(pd.read_csv(BANK_CSV))
    if len(df) != expected_rows:
        print(
            f"FATAL: expected {expected_rows} rows (rows in blog bank) in {CLASSIFIED_CSV}, got {len(df)}.",
            file=sys.stderr,
        )
        sys.exit(1)
    return df


def fetch_html(session: requests.Session, slug: str, url: str) -> tuple:
    """Return (html, fetch_ok, fetched_over_network)."""
    cache_path = HTML_CACHE_DIR / f"{slug}.html"
    if cache_path.exists():
        return cache_path.read_text(encoding="utf-8"), True, False
    if OFFLINE:
        return None, False, False

    for attempt in range(2):
        try:
            resp = session.get(url, timeout=FETCH_TIMEOUT, headers={"User-Agent": USER_AGENT})
            if resp.ok:
                cache_path.write_text(resp.text, encoding="utf-8")
                return resp.text, True, True
        except requests.RequestException:
            pass
        if attempt == 0:
            time.sleep(RETRY_DELAY_SECONDS)

    return None, False, True


def is_question_heading(text: str) -> bool:
    text = text.strip().lower()
    if not text:
        return False
    if text.endswith("?"):
        return True
    return text.split()[0] in QUESTION_WORDS


def score_answer_first(soup: BeautifulSoup) -> float:
    for heading in soup.find_all(["h2", "h3"]):
        if not is_question_heading(heading.get_text()):
            continue
        sibling = heading.find_next_sibling()
        while sibling is not None and sibling.name != "p":
            if sibling.name in ("h2", "h3"):
                break
            sibling = sibling.find_next_sibling()
        if sibling is not None and sibling.name == "p":
            word_count = len(sibling.get_text().split())
            if 15 <= word_count <= 80:
                return WEIGHTS["answer_first"]
        break
    return 0.0


def score_question_headings(soup: BeautifulSoup) -> float:
    count = sum(1 for h in soup.find_all(["h2", "h3"]) if is_question_heading(h.get_text()))
    return min(count, 3) / 3 * WEIGHTS["question_headings"]


def score_comparison_table(soup: BeautifulSoup) -> float:
    return WEIGHTS["comparison_table"] if soup.find("table") else 0.0


def json_ld_blocks(soup: BeautifulSoup) -> list:
    blocks = []
    for tag in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        blocks.extend(data if isinstance(data, list) else [data])
    return blocks


def schema_types_present(blocks: list) -> set:
    types_found = set()
    for block in blocks:
        entries = block.get("@graph", [block]) if isinstance(block, dict) else [block]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            entry_type = entry.get("@type")
            entry_types = entry_type if isinstance(entry_type, list) else [entry_type]
            types_found.update(t for t in entry_types if t)
    return types_found


def score_qa_faq_block(soup: BeautifulSoup, schema_types: set) -> float:
    if "FAQPage" in schema_types:
        return WEIGHTS["qa_faq_block"]
    for heading in soup.find_all(["h2", "h3", "h4"]):
        text = heading.get_text().strip().lower()
        if "faq" in text or "frequently asked" in text:
            return WEIGHTS["qa_faq_block"]
    return 0.0


def score_stats_count(body_text: str) -> float:
    count = len(re.findall(r"\b\d+(?:\.\d+)?%?\b", body_text))
    return min(count, 5) / 5 * WEIGHTS["stats_count"]


def score_citations_count(soup: BeautifulSoup) -> float:
    count = 0
    for link in soup.find_all("a", href=True):
        host = urlparse(link["href"]).netloc
        if host and "ecomusa.example" not in host:
            count += 1
    return min(count, 3) / 3 * WEIGHTS["citations_count"]


def score_schema_completeness(schema_types: set) -> float:
    expected = {"Article", "FAQPage", "BreadcrumbList"}
    return len(schema_types & expected) / len(expected) * WEIGHTS["schema_completeness"]


def score_freshness(blocks: list) -> float:
    date_str = None
    for block in blocks:
        entries = block.get("@graph", [block]) if isinstance(block, dict) else [block]
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            date_str = entry.get("dateModified") or entry.get("datePublished")
            if date_str:
                break
        if date_str:
            break
    if not date_str:
        return 0.0
    try:
        parsed = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return 0.0
    age_days = (datetime.now(timezone.utc) - parsed).days
    if age_days <= 365:
        return WEIGHTS["freshness"]
    if age_days <= 730:
        return WEIGHTS["freshness"] / 2
    return 0.0


def score_gifting_persona_language(body_text: str) -> float:
    lowered = body_text.lower()
    if any(re.search(pattern, lowered) for pattern in GIFT_PHRASES):
        return WEIGHTS["gifting_persona_language"]
    return 0.0


def score_keyword_stuffing_penalty(body_text: str) -> float:
    words = [w for w in re.findall(r"[a-z']+", body_text.lower()) if w not in STOPWORDS]
    if not words:
        return 0.0
    top_count = Counter(words).most_common(1)[0][1]
    density = top_count / len(words)
    if density <= 0.02:
        return 0.0
    penalty_fraction = min((density - 0.02) / (0.06 - 0.02), 1.0)
    return -15 * penalty_fraction


def score_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    body_text = soup.get_text(separator=" ")
    blocks = json_ld_blocks(soup)
    schema_types = schema_types_present(blocks)

    scores = {
        "answer_first": score_answer_first(soup),
        "question_headings": score_question_headings(soup),
        "comparison_table": score_comparison_table(soup),
        "qa_faq_block": score_qa_faq_block(soup, schema_types),
        "stats_count": score_stats_count(body_text),
        "citations_count": score_citations_count(soup),
        "schema_completeness": score_schema_completeness(schema_types),
        "freshness": score_freshness(blocks),
        "gifting_persona_language": score_gifting_persona_language(body_text),
        "keyword_stuffing_penalty": score_keyword_stuffing_penalty(body_text),
    }
    scores["geo_score"] = max(0.0, min(100.0, sum(scores.values())))
    scores["weakest_criteria"] = weakest_criteria(scores)
    return scores


def weakest_criteria(scores: dict, max_items: int = 3) -> str:
    attainment = [(name, scores[name] / WEIGHTS[name]) for name in WEIGHTS]
    attainment.sort(key=lambda pair: pair[1])
    below_half = [name for name, ratio in attainment if ratio < 0.5][:max_items]
    if below_half:
        return "; ".join(below_half)
    return attainment[0][0]


def failed_row() -> dict:
    scores = {col: float("nan") for col in SUB_SCORE_COLUMNS}
    scores["geo_score"] = float("nan")
    scores["weakest_criteria"] = "fetch_failed"
    return scores


def main():
    HTML_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    classified = load_classified()

    session = requests.Session()
    failed_slugs = []
    rows = []

    for _, row in classified.iterrows():
        slug, url = row["slug"], row["url"]
        html, fetch_ok, fetched_over_network = fetch_html(session, slug, url)

        result = {"fetch_ok": fetch_ok}
        if fetch_ok:
            result.update(score_page(html))
        else:
            result.update(failed_row())
            failed_slugs.append(slug)

        rows.append(result)

        if fetched_over_network:
            time.sleep(FETCH_DELAY_SECONDS)

    scored = pd.concat([classified.reset_index(drop=True), pd.DataFrame(rows)], axis=1)

    if OFFLINE and failed_slugs:
        print(
            f"FATAL: GEO_OFFLINE=1 and no cached HTML in {HTML_CACHE_DIR} for: {', '.join(failed_slugs)}",
            file=sys.stderr,
        )
        sys.exit(1)

    if len(scored) != len(classified):
        print(
            f"FATAL: expected {len(classified)} output rows, got {len(scored)}.",
            file=sys.stderr,
        )
        sys.exit(1)

    scored.to_csv(OUTPUT_CSV, index=False)

    reread = pd.read_csv(OUTPUT_CSV)
    print(f"Output written to {OUTPUT_CSV} ({reread.shape[0]} rows, CSV-aware re-read)")

    fetch_success = int(scored["fetch_ok"].sum())
    print(f"\nfetch success: {fetch_success} / {len(scored)}")
    if failed_slugs:
        print(f"failed slugs ({len(failed_slugs)}): {', '.join(failed_slugs)}")

    print("\ngeo_score distribution:")
    print(scored["geo_score"].describe().to_string())

    decision_content = scored[scored["decision_content"] == True].sort_values("geo_score")
    print(f"\ndecision_content=True posts, worst-first ({len(decision_content)} rows):")
    print(
        decision_content[["slug", "content_type", "geo_score", "weakest_criteria"]].to_string(
            index=False
        )
    )


if __name__ == "__main__":
    main()
