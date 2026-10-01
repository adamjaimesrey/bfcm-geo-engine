# BFCM GEO Engine

**A pipeline that scores how easily AI search engines can extract answers from a brand's blog content, prioritises the pages to fix before Black Friday / Cyber Monday, and generates paste-ready edit briefs for the content team.**

Built with Claude Code for a consumer-appliance brand. The client's identity has been anonymized ("Ecommerce" on `ecomusa.example`, with invented product names), and **all data in this repository is synthetic**.

---

## The problem

Shoppers increasingly research purchases through AI answers (ChatGPT, Gemini, AI Overviews) rather than ten blue links. Those systems quote pages that are easy to extract from: a direct answer under a question heading, a clean comparison table, an FAQ with matching schema, concrete numbers. This is **GEO (Generative Engine Optimization)**.

Before the biggest retail weekend of the year, a content team needs to know:

- **Which** of its blog posts matter most for purchase decisions?
- **How extractable** is each one today, and **what exactly** is weak?
- **What should the page say instead**, in copy that can be pasted straight in?

This pipeline answers all three for a fixed set of in-scope posts (steam irons and handheld steamers).

---

## How it works

```mermaid
flowchart TD
    A[In-scope blog bank] --> B[1. Ingest & filter]
    G1{{G1 soft gate: GSC export?}} -. absent: run provisionally .-> B
    B --> C[2. Classify content type]
    P[(content-type-patterns.md)] --> C
    C --> D[3. Fetch live HTML & score GEO extractability]
    G2{{G2 gate: every page fetched or cached?}} --> D
    R[(scoring-rules.md)] --> D
    D -.-> X[3.5 Competitor-relative scoring: deferred]
    D --> E[4. Prioritise, bucket & flag content gaps]
    E --> W[Prioritised worklist .xlsx]
    W --> F[5. LLM edit briefs]
    V[(naming-conventions.md + product specs)] --> F
    F --> H[Human review]
    H -->|problem found| L[QA log: issues A to U]
    L -->|new prompt rule + code check| F
    H -->|approved| O[Paste-ready .docx briefs]
```

| Stage | Script | What it does |
|---|---|---|
| 1. Ingest | `ingest.py` | Joins the blog inventory to the in-scope bank, mapping columns **by header name**. The join must match the bank exactly, or the run stops. |
| 2. Classify | `classify.py` | Tags each post as comparison, buying guide, gift guide, price bracket or informational, using patterns kept in `reference/content-type-patterns.md`. The first four are "decision content", the pages that matter most for purchases. |
| 3. Score | `score.py` | Fetches each page politely (descriptive user-agent, rate limit, cache reused on re-runs) and scores it 0–100 against a fixed rubric: answer-first paragraphs, question headings, comparison tables, FAQ + FAQPage schema, stats, citations, schema completeness, freshness, gift-persona language, and a **penalty for keyword stuffing**. Each page gets its `weakest_criteria`. |
| 4. Prioritise | `prioritize.py` | Ranks decision-content pages worst-first, routes each to a strategy bucket, and flags content types with too few posts as candidate new content (flagged, never auto-created). |
| 5. Edit briefs | `remediate.py` | For priority pages, calls the Anthropic Messages API to write a brief: proposed metadata, an answer-first block, a comparison table, an FAQ, JSON-LD and placement notes. Grounded in the brand's product-spec files and naming conventions, then checked in code before output. |
| Checks | `check_specs.py` | Validates the product-spec files the briefs rely on. |

---

## Design decisions worth noticing

**Every stage has an explicit gate, and the gates fail differently on purpose.** G1 is *soft*: without a Search Console export, the run continues and the worklist is clearly marked provisional rather than blocked. G2 is *self-satisfying*: missing pages are fetched and cached, and the run only halts if a page is unrecoverable, naming it. G3 (the API key) only gates Stage 5.

**Behaviour lives in configuration, not code.** Scoring weights, classification patterns and the brand vocabulary sit in `reference/*.md`. Tuning the engine means editing a readable file, not a script.

**A two-strike rule stops automation going in circles.** If a step fails or is rejected twice, the agent stops trying and proposes the cheapest reliable fallback: for a small set, automate the clean majority and hand the ambiguous minority to a human with a dropdown of valid values; for a large set, sample and spot-check, and report the residual error rate.

**The output is held to an editor's standard.** Every LLM brief was reviewed by hand, and each recurring failure became a numbered issue with a rule added to the prompt and, where possible, a check in code. The full log is in [`reference/stage5-prompt-issues.md`](reference/stage5-prompt-issues.md). A few of them:

| Issue | What went wrong | The rule it created |
|---|---|---|
| **B** | Briefs said "weave in…" instead of writing the copy | Every field is finished, paste-ready copy; notes may only say *where*, never *what* |
| **F** | A comparison table listed a product type the brand doesn't sell, making the brand look like it had a gap | Never put a non-brand product type in a table alongside the brand's products |
| **J** | Keyword volume drove optimisation for a product category too new to have search volume | For new-to-market categories, warn loudly and optimise for alignment and vocabulary instead |
| **K** | Meta title and H1 named two product categories while the body and table covered three | Meta + H1, body and table must name the identical category set, or the brief fails loudly |
| **P** | A proposed meta title ran to 76 characters | Max 60 characters, enforced in the prompt **and** in a code check |
| **S** | The intro set a benchmark that a recommended product didn't meet | No summary may state a threshold a recommended product fails |

**Honest about what isn't built.** The Search Console join is specified (G1, striking-distance and low-CTR signals) but not yet implemented, so the worklist runs in provisional mode. Competitor-relative scoring (Stage 3.5) is deferred. Both are listed as future work in `SPEC.md`.

**Part of a larger system.** Pages that are thin or superseded are routed to a "refresh / consolidate" bucket, the hand-off point to a sister pipeline: [SEO Cannibalization Engine](https://github.com/adamjaimesrey/seo-cannibalization-engine).

---

## Run the demo

Requires Python 3.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
bash scripts/run_demo.sh
```

The demo runs Stages 1–4 on synthetic data, fully offline (pages are served from a cache of 8 fake blog posts deliberately varied in quality, so scores range from single digits to the high 90s). It writes the prioritised worklist to `output/sihs-worklist.xlsx`.

Stage 5 needs an Anthropic API key (see `.env.example`), so the demo skips it. A finished example brief for one page from the demo worklist is in [`sample_output/example-brief.md`](sample_output/example-brief.md): follow that page from its score, to its rank, to the edits that fix its weakest criteria.

---

## Built with Claude Code

`CLAUDE.md` holds the working rules every session reads first (stage gates, data-handling rules, token discipline, the two-strike rule), and `SPEC.md` is the design contract, written before the code. Each stage was built in plan mode, one step at a time, verified against real data before being trusted, and committed after passing.

---

## Repository structure

```
scripts/          one script per stage, plus run_demo.sh and leak_check.py
reference/        scoring rubric, classification patterns, controlled vocabulary, QA log
sample_data/      synthetic inputs and cached pages for the demo
sample_output/    an example Stage 5 brief
CLAUDE.md         instructions for Claude Code
SPEC.md           design specification
```

---

## About

Built by Adam Jaimes Rey, SEO and GEO consultant.

---

## Licence

All rights reserved. This repository is shared for review and portfolio purposes only.
