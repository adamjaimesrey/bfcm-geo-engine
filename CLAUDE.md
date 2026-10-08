# CLAUDE.md — bfcm-geo-engine

Claude Code reads this before acting. Keep it short.

## What this is

A GEO/SEO pipeline that scores and prioritises Ecommerce's steam-iron and
handheld-steamer blog content for Black Friday / Cyber Monday. It filters the blog
to a fixed in-scope set (the **SIHS-blog-bank**, 51 posts), classifies each page by
decision-content type, scores each page's extractability against a fixed rubric
(absolute — no competitor comparison in the MVP), joins GSC signals to prioritise,
and outputs a worklist table (`output/blog-worklist.xlsx`). **Full details live
in `SPEC.md` — read
it before building.** MVP = Stages 0–4. Stage 5 (LLM copy-remediation,
`scripts/blog_remediate.py`) was built after the MVP; its rules live in
`reference/blog-stage5-prompt-issues.md`. Stage 3.5 (competitor-relative) is deferred;
do not build it or install its dependencies.

## How to work with me

- **One step at a time.** Issue one command or decision, then stop and wait for my
  output. No batching, no long option lists.
- **Plan Mode before any non-trivial build.** Show the plan, wait for approval,
  then write code.
- **Be explicit.** "Open this file and add this exact line" — not vague guidance.
- **MVP-first.** Park maintenance items and edge cases for later; note them, don't
  build them.

## Stage gates (preconditions — do not skip)

Each stage checks its precondition before running and halts with a clear message
if unmet. Full table in `SPEC.md` §4.

- **G1 (soft, HITL) — Stage 1:** `data/raw/gsc-pages.csv`. If absent, set
  `gsc_joined=False`, warn loudly, continue in intent-only mode; prioritisation is
  provisional until joined. Do NOT block the MVP on this.
- **G2 (self-satisfied) — Stage 3:** live HTML for all 51 posts. Fetch and cache to
  `data/raw/blog-html/`; hard-halt only if a URL is unrecoverable after retry, listing
  the failed slugs.
- **G3 — Stage 5 only:** `ANTHROPIC_API_KEY` in `.env` (see `.env.example`). Not needed for Stages 0–4.
- **G3.5 (deferred) — Stage 3.5 only:** competitor-URL list. Out of MVP scope.

## Token discipline

- Use Claude Code only for genuine build/debug work.
- Mechanical operations (git, file moves, checksums, folder creation) go in the
  **plain terminal**, not here.
- Never read large data files or raw HTML into context. Parse in Python and print
  summaries.

## Data handling (non-negotiable)

- Map CSV columns by **header name, never by position** — export column order is
  not guaranteed (applies to both `gsc-pages.csv` and `sihs-blog-bank.csv`).
- The `sihs-blog-bank.csv` → inventory join must yield **exactly 51 rows**. Fail
  loudly if not.
- **Verify from disk before trusting printed output.** Use a CSV-aware row count
  (`python3 -c`), not `wc -l`, for files that may contain embedded newlines.
- Write intermediate output to `data/processed/`; never overwrite `data/raw/` or
  `reference/`.
- **Be polite to the live site.** Descriptive user-agent, rate-limit fetches, and
  reuse `data/raw/blog-html/` cache on re-runs — never re-hit a page already cached.
- Scoring weights/thresholds live in `reference/blog-scoring-rules.md`; classification
  patterns in `reference/blog-content-type-patterns.md`. Change those files, not the
  code, to tune behaviour.

## Tech stack (MVP)

- Python 3 in a `.venv`.
- `pandas`, `requests`, `beautifulsoup4`, `lxml`, `openpyxl` — nothing else.
  (Deviation from [cannibalization-engine](https://github.com/adamjaimesrey/seo-cannibalization-engine):
  `requests` + `beautifulsoup4`/`lxml` are needed to fetch and parse live HTML in Stage 3.)
- Stage 5 only adds `anthropic` and `python-docx`. No ChromaDB / vector-store packages.
- Stage 4 output is a worklist table at `output/blog-worklist.xlsx` (pandas +
  openpyxl). No dashboard/plotly.

## Secrets & version control

- `.env` is in `.gitignore`; API keys never enter git history. (`.env` /
  `ANTHROPIC_API_KEY` are Stage 5 only — not needed for Stages 0–4.)
- `data/raw/blog-html/` is gitignored (fetched cache, re-derivable).
- Git for version control. Commit after each passing test with a descriptive
  message. Verify the file was written before committing.

## Model selection

- Sonnet 5 is the default for routine scripting.
- Escalate to Opus 5 within Claude Code if Sonnet stalls twice on the same problem.

## Two-strike escalation (fallback rule)

A step "fails" if it crashes OR produces a result that doesn't pass review — both count.

- After **2** failed/rejected attempts at the same step, STOP iterating. Do not attempt a third automated fix on the same approach.
- Instead, propose the **most reliable fallback for the data size**:
  - Small, fixed set (≤ ~100 rows): narrow automation to the clean majority and hand the ambiguous minority to the user as a manual pass — a spreadsheet with a dropdown of valid values + a one-line rule of thumb per value. Merge the user's answers back as explicit overrides.
  - Large set: switch from "fix every case" to "sample + spot-check", and flag the residual error rate rather than chasing 100%.
- Always prefer the fallback that costs the fewest Claude Code tokens; manual-in-terminal beats another CC round.
- State plainly when the two-strike threshold is hit and why, so the user can choose to override.
