# Content-type classification patterns (Stage 2)

Regex applied to slug / Title / H1 / H2. First match wins, in this order.

| Type | Match (case-insensitive) | decision_content |
|------|--------------------------|------------------|
| comparison_vs | `\bvs\b`, `versus`, `compare` | yes |
| buying_guide | `best-.*-for-`, `best-ecommerce`, `-top-picks`, `multi-purpose` | yes |
| gift_guide | `gift`, `for-him`, `for-her`, `for-home` | yes |
| price_bracket | `under[- ]?\$?\d+`, `budget`, `cheap` | yes |
| informational | (fallback — how-to, definitions) | no |

Notes:
- `decision_content=True` flags the GEO-priority types (the ones worth scoring hard).
- Tune here, not in classify.py.
