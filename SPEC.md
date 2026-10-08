# SPEC — bfcm-geo-engine

## 1. Purpose

Score and prioritise the **GEO/SEO extractability** of Ecommerce's steam-iron and
handheld-steamer blog content ahead of Black Friday / Cyber Monday, so we know
**which pages to optimise, how good each one currently is, and what to fix**.

The engine ingests a fixed, in-scope set of blog URLs (the **SIHS-blog-bank**),
classifies each page by decision-content type, scores each page against a fixed
extractability rubric (absolute — no competitor comparison in the MVP), joins
Google Search Console signals to prioritise, and produces a prioritised
worklist table (`output/blog-worklist.xlsx`).

AI copy-remediation (Stage 5, `scripts/blog_remediate.py`) was built after the MVP and
is documented in §4. Competitor-relative scoring (Stage 3.5) is scoped but
deferred (see §7).

## 2. Scope

### In scope (MVP)

- **Only the 51 posts in `reference/sihs-blog-bank.csv`** — steam-iron +
  handheld/garment-steamer content. Nothing else on the blog is processed.
- **Absolute extractability scoring** against a fixed rubric. No competitor
  content is fetched or compared in the MVP.
- **Stages 0–4.**

### Beyond the MVP

- **Stage 5** — LLM copy-remediation (edits, FAQ blocks, gift personas). Built; see §4.
- **Stage 3.5** — competitor-relative scoring (Semji-style Content Score). Deferred — see §7.

## 3. Data sources

| Source | Path | Origin | MVP |
|--------|------|--------|-----|
| SIHS-blog-bank (scope) | `reference/sihs-blog-bank.csv` | Provided (51 posts) | ✅ |
| Blog URL inventory (89) | `reference/blog-url-inventory.csv` | Cloned from an earlier site-crawl study | ✅ |
| Steam-iron SKUs (×7) | `reference/skus-steam-irons.csv` | Provided | ✅ |
| Handheld-steamer SKUs (×11) | `reference/skus-handheld-steamers.csv` | Provided | ✅ |
| Product specs by category | `reference/product-spec-{garment,fans,vacuums}.csv` | Provided | Stage 5 |
| Focus keywords / prompts / fan-outs | `reference/blog-focus-keywords.csv` | Semji export | Stage 5 |
| Category naming vocabulary | `reference/naming-conventions.md` | Authored | Stage 5 |
| GSC Pages export | `data/raw/gsc-pages.csv` | **Manual export (HITL)** | ✅ (soft) |
| Live page HTML (51 posts) | `data/raw/blog-html/<slug>.html` | Fetched by the pipeline | ✅ |

> Manual export is the MVP path for GSC. The GSC API is a future enhancement,
> not part of MVP. Live HTML is fetched by the pipeline itself (public URLs);
> a Screaming Frog custom-extraction export may be supplied instead.

### Expected input columns

- `sihs-blog-bank.csv`: `slug`, `url`, `category` (`steam_iron` | `garment_steamer` | `both`).
- `gsc-pages.csv` (Search Console → Pages): `Top pages`, `Clicks`, `Impressions`,
  `CTR`, `Position`.

> Column names may differ slightly on export. Ingest must map by **header name,
> never by position.**

## 4. Stages

| Stage | Name | Script | MVP |
|-------|------|--------|-----|
| 0 | Setup & scope | `scripts/blog_setup.py` (or manual) | ✅ |
| 1 | Ingest, filter & GSC join | `scripts/blog_ingest.py` | ✅ |
| 2 | Content-type classification | `scripts/blog_classify.py` | ✅ |
| 3 | GEO extractability scoring (absolute) | `scripts/blog_score.py` | ✅ |
| 4 | Prioritise, gap analysis & worklist table | `scripts/blog_prioritize.py` | ✅ |
| 5 | AI copy-remediation (built) | `scripts/blog_remediate.py` | ✅ (post-MVP) |
| 3.5 | Competitor-relative scoring | (deferred) | ⏸️ |

### Gate summary (preconditions per stage)

| Gate | Precondition | Blocks | Behaviour if unmet |
|------|--------------|--------|--------------------|
| G1 (soft, HITL) | `data/raw/gsc-pages.csv` present | Stage 1 join | Run in intent-only mode; set `gsc_joined=False`; warn loudly; prioritisation flagged provisional. **Status: the GSC join is specified but not yet implemented in this build** — Stage 1 never reads the file, so every run behaves as if G1 were unmet and the worklist's `gsc_signal` is always "provisional (no GSC)". |
| G2 (self-satisfied) | Live HTML fetched for all 51 posts | Stage 3 | Fetch missing pages, cache to `data/raw/blog-html/`. Hard-halt only if any URL cannot be retrieved after retry, listing the failed slugs. |
| G3 | `ANTHROPIC_API_KEY` in `.env` (see `.env.example`) | Stage 5 only | `blog_remediate.py` exits with a clear message if the key is missing. |
| G3.5 (deferred) | Competitor-URL list per target query | Stage 3.5 only | Out of MVP scope. |

### Stage 5 — AI copy-remediation (built)

`scripts/blog_remediate.py` reads `output/blog-worklist.xlsx`, and for each priority page
sends the cached page text, current meta title/description/H1 (`page_meta()`), the
matching category spec file(s), the naming vocabulary and (where `refocus=YES`) the
focus keyword/prompt/fan-outs to the Anthropic Messages API. It writes one
paste-ready `.docx` edit brief per page to `output/blog-edits/`. The prompt rules (A–U) and
the reasoning behind each are logged in `reference/blog-stage5-prompt-issues.md`;
`validate()` enforces the countable ones in code (meta title ≤ 60 / description ≤ 155
characters, table ≤ 5 rows and ≤ 5 columns) and adds fail-loud warnings.

- **Preconditions:** `blog-worklist.xlsx`, cached HTML in `data/raw/blog-html/`, spec files
  in `reference/`. **G3:** `ANTHROPIC_API_KEY`.
- **Usage:** `python scripts/blog_remediate.py` (all rows) or `python scripts/blog_remediate.py <slug>`.
- **Output:** `output/blog-edits/<rank>_<slug>.docx` (re-running overwrites; keep reviewed copies elsewhere).
- **Spec QA:** `scripts/check_specs.py` scans `reference/product-spec-*.csv` for
  spreadsheet drag-fill errors (consecutive rows in a category whose numbers are each
  exactly +1 in 2+ columns) so bad specs don't reach the briefs. Run it before Stage 5.

### Stage 0 — Setup & scope

Create the folder structure and `.venv`, install MVP dependencies, and place the
four `reference/` files. Confirm `reference/sihs-blog-bank.csv` loads and contains
51 rows.

- **Preconditions:** none (bootstrap).
- **Output:** working environment; reference files in place.

### Stage 1 — Ingest, filter & GSC join

Load `blog-url-inventory.csv` with pandas. Inner-join to `sihs-blog-bank.csv` on
`url` to reduce the 89-post inventory to the 51 in-scope posts (fail loudly if the
join count ≠ 51). Load `data/raw/gsc-pages.csv` (map by header name), join by URL.

- **Signals to compute:** `striking_distance` (Position 5–20), `low_ctr_high_impr`
  (impressions above median AND CTR below median), carry `Unique Inlinks` if present.
- **Preconditions:** `sihs-blog-bank.csv` and `blog-url-inventory.csv` present.
  **G1 (soft):** if `gsc-pages.csv` is absent, set `gsc_joined=False` and continue.
- **Output:** `data/processed/blog-filtered.csv`.

### Stage 2 — Content-type classification

Classify each SIHS post by regex on `slug` / `Title` / `H1` / `H2` (patterns
documented in `reference/blog-content-type-patterns.md`):

- `comparison_vs` — contains `vs`, `versus`, `compare`
- `buying_guide` — contains `best`, `guide`, `choosing`, `which`
- `gift_guide` — contains `gift`, `for-him`, `for-her`, `for-home`
- `price_bracket` — contains `under-$`, `budget`, `cheap`
- `informational` — everything else (how-to, definitions)

Set `decision_content=True` for the first four (the GEO-priority types).

- **Preconditions:** `blog-filtered.csv` exists.
- **Output:** `data/processed/blog-classified.csv`.

### Stage 3 — GEO extractability scoring (absolute)

For each post, fetch and cache live HTML (`data/raw/blog-html/<slug>.html`), parse with
BeautifulSoup, and score 0–100 against a fixed rubric (weights/thresholds in
`reference/blog-scoring-rules.md`). Signals:

- `answer_first` — a concise (~40–60 word) answer directly under a question-style H2
- `question_headings` — count of question-formatted H2/H3
- `comparison_table` — HTML `<table>` present
- `qa_faq_block` — Q&A/FAQ block present **and** `FAQPage` schema present
- `stats_count` / `citations_count` — numeric stats and outbound citations
- `keyword_stuffing_penalty` — keyword-density flag (per GEO paper, penalise)
- `schema_completeness` — Article / FAQPage / BreadcrumbList present
- `freshness` — last-modified date
- `gifting_persona_language` — recipient-persona framing present

Emit per-page `geo_score` + sub-scores + a `weakest_criteria` list.

- **Preconditions:** `blog-classified.csv` exists. **G2:** live HTML available for
  all 51 posts (fetch + cache; hard-halt only on unrecoverable fetch failures,
  listing failed slugs). Be polite to the live site: set a descriptive user-agent,
  rate-limit, and reuse cache on re-runs (never re-hit a page already cached).
- **Output:** `data/processed/blog-scored.csv`.

### Stage 4 — Prioritise, gap analysis & worklist table

Compute `priority_score = f(decision_content, category, GSC impressions/striking_distance [if gsc_joined], inlinks, (100 − geo_score))`.
Route each page to a strategy bucket:

- `geo_consideration` (comparison / best-for) — content-cluster optimise
- `striking_distance_generic` — category/PDP support
- `under_linked` — internal-link target to the promo hub
- `refresh_consolidate` — thin / superseded (hand to [cannibalization-engine](https://github.com/adamjaimesrey/seo-cannibalization-engine))

Gap analysis: decision-content types with few/no posts → **flag** as candidate NEW
content (optimise existing first; never auto-create). Emit
`output/blog-worklist.xlsx` via pandas + openpyxl — a single table sorted by
priority, columns: `slug, category, content_type, geo_score, weakest_criteria,
strategy_bucket, gsc_signal`.

- **Preconditions:** `blog-scored.csv` exists.
- **Output:** `data/processed/blog-prioritized.csv`, `output/blog-worklist.xlsx`.

## 5. Folder structure

```
bfcm-geo-engine/
├── .claude/settings.json
├── CLAUDE.md
├── SPEC.md
├── requirements.txt
├── .gitignore
├── .env                      # ANTHROPIC_API_KEY — Stage 5 only, gitignored
├── .env.example              # documents the key, no real value
├── data/
│   ├── raw/
│   │   ├── gsc-pages.csv      # manual GSC export (HITL, soft gate)
│   │   └── blog-html/             # fetched page HTML cache (<slug>.html)
│   └── processed/            # filtered → classified → scored → prioritized
├── reference/
│   ├── sihs-blog-bank.csv    # scope: 51 posts (provided)
│   ├── blog-url-inventory.csv
│   ├── skus-steam-irons.csv
│   ├── skus-handheld-steamers.csv
│   ├── product-spec-*.csv    # garment / fans / vacuums (Stage 5)
│   ├── blog-focus-keywords.csv    # Stage 5 refocus inputs
│   ├── naming-conventions.md
│   ├── blog-stage5-prompt-issues.md
│   ├── blog-content-type-patterns.md
│   └── blog-scoring-rules.md
├── scripts/
│   ├── blog_setup.py
│   ├── blog_ingest.py
│   ├── blog_classify.py
│   ├── blog_score.py
│   ├── blog_prioritize.py
│   ├── blog_remediate.py          # Stage 5
│   ├── check_specs.py        # spec-file QA
│   └── leak_check.py         # anonymisation check (showcase copy only)
└── output/
    ├── blog-worklist.xlsx
    └── blog-edits/                # Stage 5 .docx briefs
```

## 6. Environment

- Python 3 in a `.venv`.
- **MVP dependencies:** `pandas`, `requests`, `beautifulsoup4`, `lxml`,
  `openpyxl`.
- **Deviation from [cannibalization-engine](https://github.com/adamjaimesrey/seo-cannibalization-engine)** (`pandas`/`openpyxl` only):
  Stage 3 must fetch and parse live HTML, so `requests` + `beautifulsoup4`/`lxml`
  are added. Stage 5 adds `anthropic` and `python-docx`. No ChromaDB / vector-store
  packages.

## 7. Future work (specified, not yet built)

### Stage 1 GSC join

Specified in §4 (G1) and Stage 1 but **not implemented in this build**: reading
`data/raw/gsc-pages.csv`, joining by URL, and computing `striking_distance` and
`low_ctr_high_impr`. Until built, prioritisation is provisional (intent-only) and
no GSC-driven signal appears in the worklist. Listed alongside Stage 3.5 below.

### Stage 3.5 — Competitor-relative scoring (deferred)

Add a per-target-query ranked **competitor-URL list** (HITL gate, from the Part-2
competitor identification / a Semji export). Scrape those pages (existing
trafilatura scraper) and re-score each SIHS page *relative* to the top-ranking
competitors, Semji-style. **Out of MVP scope.**

## 8. Definition of done (MVP)

Running the scripts in order against the real inputs produces:

1. `data/processed/blog-filtered.csv` — the in-scope posts (51 in the real build; one row per blog-bank row), flagged provisional (GSC join not yet implemented).
2. `data/processed/blog-classified.csv` — a content-type tag per post.
3. `data/processed/blog-scored.csv` — a `geo_score` + sub-scores + weakest criteria per post.
4. `data/processed/blog-prioritized.csv` — priority score + strategy bucket per post + gap flags.
5. `output/blog-worklist.xlsx` — a priority-sorted worklist table.

Each stage halts with a clear message if its precondition gate is unmet (G1 soft:
continue with a provisional flag; G2: hard-halt only on unrecoverable fetch failures).
