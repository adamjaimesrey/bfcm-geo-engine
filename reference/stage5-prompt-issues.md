# Stage 5 prompt — issues log (fixes for scripts/remediate.py)

Running list of shortcomings found while reviewing the 11 generated .docx briefs.
Fix ALL of these in the remediate.py prompt in one pass, then regenerate the batch.
Reference implementation of the target output = the hand-amended 01_best-ecommerce-clothes-steamer.docx.

| # | Issue | Fix at prompt stage | Status |
|---|-------|---------------------|--------|
| A | Brief used the SKU master-list as the product source, so it listed products NOT on the live page (e.g. PowerPress, FiberCare, DuoPress, AirLift on the best-ecommerce-clothes-steamer post). | Prompt must use ONLY the products actually present on the page (from the fetched page content). Use SKU data solely to enrich specs for those on-page products — never to introduce a product. | open |
| B | Some sections gave vague instructions ("weave in…", "mention…", "add a callout about…") instead of finished copy. | Every field except editorial_notes must be FINISHED, PASTE-READY copy — the exact words for the page. editorial_notes may be instructional but PLACEMENT ONLY (where to paste), never what to write. | open |
| C | Gifting persona was a standalone descriptive section. | Remove the standalone gifting section. Weave persona framing into (1) the comparison table's "Best For (who it suits)" column and (2) a dedicated gift FAQ that maps each persona to a product. | open |

## Notes
- Standard: the client's content editor pastes from the docx with zero writing. Content = spoon-fed and verbatim; only placement is instructed.
- Re-running remediate.py overwrites output/edits/ with fresh API calls — reviewed copies live in Drive.

## Issue F (CRITICAL)
| F | A comparison table included a non-Ecommerce product type ("Clamp-style handheld press — Not a Ecommerce product category") alongside Ecommerce products, making Ecommerce look like it lacks a solution for that pain point. | The agent must NEVER place a product type/service Ecommerce does not offer as a row/entry ALONGSIDE Ecommerce products in a comparison. Ecommerce must be shown covering every pain point in the comparison. A competitor category may be discussed in body prose (as the "vs" subject), but never sits in the table as a gap. | open |

## Issue H
| H | A spec that doesn't apply to a product type was written as a negative/ambiguous "N/A (iron)" (e.g. heat-up time for irons, which reach temperature effectively on switch-on). | When a spec has no concrete value because it doesn't apply to that product type, never write "N/A", "N/A (iron)", or blank. Use a positive, active term that reframes it as a benefit — e.g. heat-up for an iron = "Instant heat". Reserve a plain "—" only for a spec that is genuinely irrelevant to the category (e.g. steam output on a fan). | open |

## Issue I (SCOPE EXTENSION - new required inputs; clone from cannibalization-engine)
| I | Engine never ingests the article's focus keyword, focus prompt, or 4 query fan-outs, so it cannot refocus a page whose slug/H1/meta drifted from intent (e.g. airlift-suction-vs-steam-iron). | Add focus_keyword, focus_prompt, and 4 query_fan_outs as REQUIRED inputs (source: Semji). Clone the refocus logic from cannibalization-engine. Agent must: (a) identify focus KW per Semji; (b) refocus article to it where slug/H1/meta/body have drifted; (c) ensure content answers the focus prompt + all 4 fan-outs. Needs SPEC.md (inputs+stage) and CLAUDE.md changes, not just a prompt edit. | open |

## Issue J (CRITICAL - AirLift suction-steamer KW-volume caveat)
| J | KW volume was treated as the optimization driver, but AirLift suction steamers (AirLift Spin; AirLift Spin Deluxe) are new to market with little-to-no Semrush volume - so volume is the wrong signal for any article touching this category. | Whenever slug/meta/H1/body references AirLift / suction steamers (Spin or Spin Deluxe), the agent MUST loudly warn: "Expect little-to-no KW volume - suction steamers are new to market; do NOT let KW volume drive optimization here." Weight Issues K & L instead. | open |

## Issue K (CRITICAL - three-way alignment: meta+H1 <-> body <-> comparison table)
| K | airlift-suction-vs-steam-iron compared 3 categories in body (steam irons, handheld steamers, suction steamers) but H1/meta named only 2, and the table covered only 2 (missing steam irons). | The product-category set must be IDENTICAL across (1) meta title+description+H1, (2) body, (3) comparison-table rows. Agent reconciles all three to one agreed set before generating edits; if exact alignment is not achievable, FAIL LOUDLY and flag the mismatch. | open |

## Issue L (CRITICAL - native product-category naming; controlled vocabulary)
| L | Draft used vague non-native terms in H2s/table headers: "traditional iron" x3, "traditional steamer", "traditional steamers". | Use ONLY ecomusa.example native category names: Steam Stations, Steam Irons, Handheld Steamers, Handheld Suction Steamers (AirLift), Full Size Steamers, Ironing Boards, Stick Vacuums, Fans. Never prepend "traditional" or use off-vocabulary terms (e.g. "traditional iron" -> "steam iron"). Flag LOUDLY any deviation, especially in H1/H2 and table column headers. Hardcode vocabulary in reference/naming-conventions.md. | open |

## Issue M (spec-file routing by category)
| M | Product specs now live in three category-specific files with different schemas, not one master. | When building any spec-dependent element (comparison table, answer-first, FAQs, Product JSON-LD), the agent MUST read specs from the file that matches the page's product category: steam irons / steam stations / handheld steamers / suction steamers / full-size steamers -> reference/product-spec-garment.csv; fans -> reference/product-spec-fans.csv; stick vacuums -> reference/product-spec-vacuums.csv. Never pull specs from the wrong file, and never invent a column a file doesn't have. If a page spans categories, read from each relevant file. | open |

## Issue N (comparison-table threshold; no table for single-product categories)
| N | A comparison table requires >=2 same-category products; stick vacuum has only 1 product on ecomusa.example, so a comparison is impossible. | Do NOT generate a comparison table when the page covers fewer than 2 products of the same category. Stick vacuum = always omit the comparison table. Still generate every other element (answer-first/quick-answer, FAQs, Product JSON-LD, editorial notes). This extends Issue E (single-product -> spec/use-case table, never a fabricated multi-product comparison). | open |

## Issue A (REVISED - supersedes original A)
| A | "On-page products only" dropped a category the body discusses (#07: handheld steamers discussed, no handheld product on page), breaking 3-way alignment (K). | Product scope = every category the body discusses (any term, mapped via naming-conventions.md). Include all on-page products; for each discussed category with <2 on-page products, add products from that category's spec file to reach 2 (best fit for the article's angle, different price/use points). Every added product appears in BOTH the table and the body (paste-ready sentence + PDP link + placement) and is listed in Warnings as "Added, not on current page". Exceptions: never add an undiscussed category; never add accessories as comparison products; never add non-Ecommerce types (F); added products must exist in spec files, never invented (if <2 exist, use what exists and warn); colour-only variants share ONE row; single-product categories still follow N. | open |

## Issue O (table width)
| O | #07 table had 8 columns - too wide to read or paste. | Max 5 columns: Product (with its category) + Best For (who it suits) + up to 3 spec columns that apply to every row and best separate the options for this article. Non-applicable specs use the spec file's positive term. | open |

## Issue P (meta length)
| P | #06 proposed a 76-character meta title; Google truncates at ~60, cutting off "| Ecommerce". | proposed_meta_title max 60 characters (incl. spaces and "| Ecommerce"); proposed meta description max 155. Enforced twice: as a prompt rule AND a code check (validate()) that adds a Warning if either limit is exceeded. | open |

## Issue Q (table rows - representative subset)
| Q | #06 had 6 on-page products; showing all would make the table hard to scan. | Comparison table max 5 rows: the most relevant products for the article, covering every discussed category. Products not shown in the table stay in the body. Refines Issue A's "include every on-page product" (applies to the body, not the table). Code check warns if >5 rows or >5 columns. | open |

## Issue A (tightened - variants)
| A2 | #01 merged Velora Black + Silver into one row as "colour variants", although their specs differ (heat-up 30s vs 45s; 3 vs 1 steam levels). | Variants share ONE row only if ALL spec values in the spec file are identical. If any spec differs, treat them as separate products. | open |

## Issue S (no contradictions)
| S | #01 answer-first said "look for 30+ g/min" while recommending the PocketPuff (20 g/min) on the same page, implying a Ecommerce product falls short. | answer_first and any intro/summary copy must be fully consistent with every spec, table row, fan-out section and FAQ in the brief. Never state a benchmark or threshold that a recommended Ecommerce product does not meet. | open |

## Issue T (spoon-fed warnings)
| T | #01 warning said "recommend updating these H2s" without giving the new wording. | Any warning requiring a copy change must quote the EXACT current text and the EXACT replacement (e.g. Replace "1600 W power" with "1500 W power"). | open |

## Issue U (model couldn't see current meta)
| U | The body excerpt strips <head>, so the model never saw the current meta description (#01: "No current meta description was present"). | page_meta() reads the current meta title, meta description and H1 from the cached HTML and passes them to the model explicitly. Rule T also tightened: if several fixes are possible, choose ONE and give its exact text - never offer options. | open |
