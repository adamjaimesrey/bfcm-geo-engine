# GEO extractability scoring rubric (Stage 3, absolute)

Score 0-100. Weights are placeholders — tune here, not in score.py.

| Signal | Detection | Weight |
|--------|-----------|--------|
| answer_first | concise (~40-60 word) answer directly under a question H2 | 20 |
| question_headings | count of question-formatted H2/H3 | 10 |
| comparison_table | HTML `<table>` present | 15 |
| qa_faq_block | Q&A block present AND FAQPage schema | 15 |
| stats_count | numeric stats present | 10 |
| citations_count | outbound citations to credible sources | 5 |
| schema_completeness | Article / FAQPage / BreadcrumbList present | 10 |
| freshness | last-modified recency | 5 |
| gifting_persona_language | recipient-persona framing present | 10 |
| keyword_stuffing_penalty | keyword-density flag (SUBTRACTS) | -15 max |

Notes:
- Absolute scoring only — no competitor comparison (that's deferred Stage 3.5).
- Emit per-page geo_score + sub-scores + weakest_criteria list.
