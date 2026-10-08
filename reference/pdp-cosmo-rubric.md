# COSMO rubric — ecomusa.example PDPs (APPROVED 2026-10-06)

Source of truth for P3 (scoring) and P5 (edit briefs). Scope: ecomusa.example PDPs only; Amazon is out of scope.
"COSMO score" is the name of this rubric. COSMO itself is Amazon's system and does not read ecomusa.example;
the payoff on ecomusa.example is GEO: AI search engines extract clear, contextualised product facts more readily
than bare spec lists.

---

## 1. The formula (applies to every rewritten bullet or block)

**[Customer Outcome] + [Technical Feature] + [Real-World Use Case]**

The same idea as a triplet: `[Feature] -> solves -> [Human problem] -> suitable for -> [Real-world situation]`

| | Example (Velora Steam Iron 2400) |
|---|---|
| Weak (feature list) | "2400 W power, 400+ SteamGrid holes, anti-drip, retractable cord." |
| Strong (formula) | "Smooth linen shirts fast before work: 2400 W and 400+ SteamGrid holes spread steam evenly across the fabric, so there are no dry patches to go back over." |

Every claim must be backed by the spec files or the page. No unprovable comparatives ("half the time", "3x faster")
unless the page or Ecommerce states the basis.

---

## 2. The six questions and how each is scored (0-3)

| Score | Meaning |
|---|---|
| 0 | Not answered anywhere on the PDP |
| 1 | Feature only, or vague ("versatile", "powerful"); no outcome or use case |
| 2 | Answered clearly, in the words a shopper would use |
| 3 | Answered with figures AND the stretch element in the last column below |

**COSMO score = total points / 18 x 100** (rounded).

| Relation | Question | Score 2 looks like | Score 3 adds (stretch) |
|---|---|---|---|
| isA | What exactly is it? | Precise type + category in shopper words: "handheld suction garment steamer" | Size/format figure: "2-quart", "1.3 L tank" |
| used_for_audience | Who is it for? | Named audience: "for frequent travelers" | Who it is NOT for, stated as plainly as the benefit |
| used_for_function | What job does it do? | One job per sentence, plain words | The job tied to a specific fabric or garment |
| used_for_event | Which occasion or situation? | Situations, not personas: "hotel-room touch-ups" | 2+ distinct situations, incl. a BFCM/holiday one |
| capable_of | What can it do, and what are the limits? | Concrete figures (see section 3) | At least one stated limit ("not for thick denim") |
| cause/benefit | What is the benefit, and why? | Benefit stated | Benefit + mechanism + proof ("because suction holds the fabric taut against the heated plate") |

---

## 3. Filter attributes per category (exclusion logic)

AI shopping assistants drop a product when a filter attribute is missing (e.g. "lightweight steamer, no ironing
board" removes products that don't state weight or board requirement). A PDP can't score 3 on capable_of unless it
states its category's attributes. Values come from the spec files; anything missing is flagged, never invented.

| Category | Attributes the PDP must state |
|---|---|
| Steam irons | power (W); continuous steam + boost (g/min); soleplate (type, holes); tank size; cord type/length; weight |
| Steam stations | boiler pressure (bar); steam (g/min); tank size; heat-up time; weight/footprint; needs an ironing board |
| Handheld steamers | heat-up time; steam (g/min); tank size + run time; weight; voltage (travel); no ironing board needed |
| AirLift suction steamers | suction (Pa); steam (g/min); heat-up; tank + run time; weight; no ironing board needed |
| Full size steamers | heat-up; steam (g/min); tank + run time; height/footprint; what's included (hanger, board) |
| Fans | airflow; noise (dB); speeds; oscillation; size/footprint; remote |
| Stick vacuums | suction (AW); battery run time; noise (dB); weight; bin capacity |

Accessories (ironing boards, lint removers, cleaning kits) are out of scope for PDP scoring.

---

## 4. Reference: Crispa Mini Air Fryer (annotated)

| Bullet | Answers | Why it works / what's missing |
|---|---|---|
| QUICK RESULTS | function, capable_of, benefit | Figure (390°F) + job (set time/temp). "twice as fast as an oven" has no proof: benefit stays at 2 |
| LIGHTER COOKING | isA, benefit | Plain benefit; mechanism only implied (hot air instead of oil) |
| COUNTER-FRIENDLY | isA, event, benefit | Closest to the formula: feature (1.8-quart, slim) + outcome (less clutter) + situation (countertop) |
| SHAKE REMINDERS | function, benefit | Benefit with mechanism: alert -> shake -> crispier food |
| SMALL-KITCHEN FIT | audience, event | "1-2 people" names the audience; "not for families" is only implied |
| EASY CLEAN-UP | capable_of | Concrete, checkable: dishwasher-safe basket and tray |
| BUILT-IN SAFETY | capable_of, benefit | Benefit with mechanism: powers off when the timer ends or the basket is removed |
| TRUST AND SUPPORT | capable_of (proof) | Certification + warranty + 850W/120V as trust signals |

**Patterns to copy:** a short CAPS label per bullet, one job per bullet, a figure in most bullets, plain words.
**Its gaps (so the reference does not score 18/18):** no explicit "not for"; the speed claim is unproven; few occasions.

---

## 5. Rules carried over from the blog stage

- **Naming (L):** canonical category names from `naming-conventions.md`.
- **Specs (M):** values verbatim from the routed spec file; never invent; flag anything missing.
- **No contradictions (S):** no claim or benchmark that conflicts with the specs or another section.
- **Exact replacements (T):** every edit quotes the current text and gives the exact new text; pick the best option, never offer several.
- **Layout:** edits fit the category's layout template (`pdp-layout-patterns.md`); any break gets a one-line justification.

---

## 6. BFCM gifting bullet (one per PDP)

Each PDP brief includes one gifting + durability bullet in this phrasing:
> **A gift built to last:** [product] arrives ready to gift, and Ecommerce keeps spare parts available, so it can be repaired rather than replaced.

Never add a time period (no "for X years").

---

## 7. Parked (not in this rubric)

- Review mining: inject phrases customers use in reviews into bullets. Useful later; needs a review export.
- Anything Amazon-specific (ASINs, Alexa ranking, A+ content).

---

## 8. Scoring clarifications (added after the first batch)

- **Location does not change a score.** Text in closed accordions and FAQ answers counts the same as visible copy. Only how plainly it is stated matters.
- **used_for_audience = 3** only if the page explicitly names a user or situation the product is NOT suited to, in plain words. A hedged line ("some users may prefer...", "may still benefit from...") scores 2.
- **cause_benefit = 3** needs all three: the benefit, the mechanism (why it works), AND proof. Proof = a stated test or lab result, certification, or a comparison with a named baseline. Specs alone are not proof; a mechanism without proof scores 2.
- **Evidence must answer the question it is filed under.** A quote that supports a different question does not count towards this one.
- **Same evidence, same score:** apply each level identically across all products.
- **Existing claims are approved.** The "no unprovable comparatives" rule in section 1 applies only to NEW copy we
  write. Claims already on the live page are Ecommerce's: keep them; a missing basis keeps cause_benefit at 2 and
  becomes an optional question for the client's content editor, never a removal.
