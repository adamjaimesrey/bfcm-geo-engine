# P5 prompt: PDP edit briefs (approved template, pilot = Brisa 3-in-1)

Read CLAUDE.md, SPEC.md §9, reference/pdp-cosmo-rubric.md, reference/naming-conventions.md and
reference/pdp-layout-patterns.md first. Do NOT call the Anthropic API and do NOT write or edit any script.

## Which groups

Take the next N variant groups (N is given in the instruction that pointed you here) from
reference/pdp-index.csv, in ascending `priority` order, skipping any group that already has a file in
data/processed/pdp-briefs/. Do one group at a time: write its brief file, render it, then move to the next.

## Inputs (per group; read only these)

- data/raw/pdp/<group>/sections.json (never open the PNGs)
- data/processed/pdp-scores/<group>.json
- this product's rows in the spec file for its category: reference/product-spec-garment.csv,
  reference/product-spec-fans.csv or reference/product-spec-vacuums.csv

## Rules

- Close the gaps in the score file. Edits go only in the page's existing slots for its layout template;
  any new slot needs a one-line justification in `layout_note`.
- At most 12 edits, biggest score gains first, listed in page order top to bottom.
- `replace`/`remove`: `current` copied character-for-character from sections.json. `add`: `current` is "".
- New copy follows the formula (customer outcome + technical feature + real-world use case), paste-ready.
- **Existing claims on the page are Ecommerce-approved: never remove or weaken them.** You may only fix their
  wording (naming rules) or add context around them. Where a claim lacks a stated basis, add a `for_client_editor`
  item: `if_confirmed` = add the basis to the claim; `if_not` = keep the claim exactly as it is.
- New claims you write must come from sections.json or the spec file. The score file's `notes` are leads to
  check, never facts to copy.
- Every item has an action-taker. Edits are for the client's content editor. Nothing else goes in the brief.
- `for_client_editor`: questions only Ecommerce can answer. Each has `ask` (what to ask, and whom), `if_confirmed`
  (the exact change) and `if_not` (what to publish). Every edit must be publishable without the answer.
- **A fact that is blank in the spec file and not on the page** (e.g. tank size, cord, heat-up time) is a
  `for_client_editor` item asking the Product Manager for it: `if_confirmed` = the exact sentence to add with the
  value; `if_not` = publish without it. The owner has already checked these; do not send them to `for_owner`.
- A spec-file value that is blank but STATED ON THE PAGE is not a problem: use the page value in the copy
  and record it in `spec_backfill` as {"column": "<spec column>", "value": "<value>", "quote": "<exact page text>"}.
- `for_owner`: only a spec-file value that CONTRADICTS the page. One line each: what's wrong and where.
  Leave it empty if there are none.
- If the page contradicts itself and the spec file settles it, write an edit setting the spec-file value;
  if not, add a `for_client_editor` item.
- Off-vocabulary category terms (e.g. "traditional iron") get an edit with the exact replacement from
  naming-conventions.md.
- `gifting_bullet`: the rubric §6 phrasing with this product's name, no time period.
- `why`: plain English, no rubric codes. `questions`: the rubric keys the edit improves (empty for a pure
  naming fix).
- `target_scores`: realistic; don't award a 3 the rubric wouldn't give.

## Output (per group)

Write data/processed/pdp-briefs/<group>.json in exactly this format:

```json
{
  "variant_group": "<group>",
  "product_name": "<product name>",
  "for_client_editor": [{"ask": "...", "if_confirmed": "...", "if_not": "..."}],
  "for_owner": [],
  "spec_backfill": [],
  "layout_note": "...",
  "edits": [{"where": "<slot>", "action": "replace | add | remove", "current": "<exact page text or empty>",
             "new": "<paste-ready text>", "why": "...", "questions": ["isA"]}],
  "gifting_bullet": {"where": "<slot>", "text": "..."},
  "target_scores": {"isA": 0, "used_for_audience": 0, "used_for_function": 0, "used_for_event": 0,
                    "capable_of": 0, "cause_benefit": 0}
}
```

Then run `python scripts/pdp_render.py --group <group>`. If it reports errors, fix that group's JSON
(maximum 2 attempts), then move to the next group.

## When the N groups are done

Stop and report a table: group | edits | score now -> target | for_client_editor items | for_owner items.
Do not commit; the owner commits from the plain terminal.
