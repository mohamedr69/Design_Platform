# Review 33, dimension D4: population, gate, feasibility and harness consumability

**Agent:** R33-D4, task ORCH-03.1/D4, Claude Opus 5.5 (`claude-opus-5-5`), effort High.
**Nature:** an owner-delegated independent Claude AI review (authority A-03). It is **not** human sign-off. It authorizes nothing and approves nothing. M2 stays CHANGES STILL REQUIRED, and M3 has not started.
**Method:** read-only. No provider or model request and no prediction. The harness was not run and no adapter was built. All counts come from my own scripts in the scratchpad (`.../scratchpad/r33-d4/`: `verify_manifests.py`, `recount.py`, `mixed.py`, `docres.py`, `strata.py`, `runset_sim.py`, `runset_proj.py`, `lit.py`, `ledger_stage.py`, `shape.py`). They were run with the backend venv Python and `PYTHONDONTWRITEBYTECODE=1`. The r26.2 rows were not read: `LABELS-NORMALISED.json` was inspected for key names and value types only. The candidate and baseline trees were touched only by `git rev-parse` and `git status`.

## 0. Inputs and hashes (recomputed)

| Item | Result |
|---|---|
| `fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json` | `15c4114d…82d0ed`. 110 entries, 0 mismatches, nothing unlisted except the manifest and the package check |
| `fresh-cohort-r32-reviewed/evidence/EVIDENCE-MANIFEST.json` | `64c03667…31c6`. 45 entries, 0 mismatches. `PACKAGE-CHECK.json` ok, 18 of 18 |
| `review31/evidence/EVIDENCE-MANIFEST.json` | `d5fe1649…c460`. 58 entries, 0 mismatches. Harness file hashes equal `BINDING-MANIFEST.json` (`2dfef08e…`) |
| Draft labels / reviewed labels | `ebd1e24d…a334` (both copies) / `00e53e82…7779` |
| `FIELD-POPULATION.json` (reviewed package) | `5b9cf095…4505` |
| Conventions, selection, source manifest, crops, evidence index | `5c09d4d2…`, `bf71779a…`, `951e8697…`, `b1760b64…` (189 lines), `0d0db4f8…` |
| `RENDERS.json`, `PROJECT-VERIFICATION.json` | `175a3a10…e8be`, `4cecf2fc…f1c4` |
| Label review folder | final `920a21d6…`, consolidated `70f94632…`, critique `ad6798dc…`, dispositions `e8828bec…` |
| `DRAFT-DECLARATION.v2.json` | `19720ad9…8b5d` |
| Staging `C:/t/r2x/r32-stage` | 72 staged files, 149 renders and 189 crops re-hashed against `SOURCE-MANIFEST` / `EVIDENCE-INDEX`: 0 mismatches. Labelled pages equal `min(page_count, 4)` for all 70 documents with their own rulings (144 pages) |
| Candidate / baseline | `a8aacedd…` clean / `3d5607d9…` clean |
| AI ledger (read-only URI) | 483 entries, 17 scopes |

## 1. Independent recount (check 1)

Rule: per field, count the distinct documents, after aliases F031→F001, F052→F038, F059→F046 and F070→F067, that have `resolved_for_scoring` = yes **and** `carries_fact` = yes. A document with `unresolved` in either value is excluded.

| Field | My count | FIELD-POPULATION | REVIEW-NOTE.final (both yes / after count-once) | Unresolved, excluded | Upper bound |
|---|---|---|---|---|---|
| identity | **57** | 57 (same 57 ids) | 59 / 57 | F069 | 57 (F069 `carries_fact` is no under either answer) |
| revision | **38** | 38 (same ids) | 40 / 38 | F019 | 39 |
| decision | **38** | 38 (same ids) | 39 / 38 | none | 38 |

- **Raw value tallies over 72 documents.** Identity: yes/yes 59, yes/no 8, no/no 2, unresolved/no 1, null 2. Revision: 40 / 24 / 5 / unresolved-unresolved 1 / null 2. Decision: 39 / 30 / 1 / 0 / null 2. "Null" means F052 and F070, the byte-identical copies, which have no rulings and no pages.
- **Agreement with the label review.** The REVIEW-NOTE "resolved_for_scoring yes" column (67 / 64 / 69) also matches.
- **By project (counted).**
  - Identity: 15744 5, 22349 10, 26687 10, 27331 12, 29255 9, 3563 11.
  - Revision: 2, 1, 9, 12, 4, 10.
  - Decision: 0, 2, 3, 12, 10, 11. This matches `by_project_decision`.
- **By selection stratum.**
  - Decision: review_signal 37, other 1 (F072).
  - Identity: review_signal 36, drawing_signal 16, other 5.
  - Revision: review_signal 29, drawing_signal 8, other 1.

## 2. Consistency, document level against page level (check 2)

- **Every `carries_fact` yes holds.** All 138 yes document-fields (59 + 40 + 39, including the aliases) have at least one in-scope page where the field is `present`, association `resolved` and `excluded_from_scoring` false. There are 0 exceptions.
- **Every `carries_fact` no holds.** None of those document-fields has such a page.
- **Eight `carries_fact` no fields have a page in state `present` that is not counted.** Each follows a convention ruling:
  - F003, F004, F005, F006 (p1, p2) and F015 revision: `present`, association `uncertain`. This is the embedded "- R0n" suffix (frozen §4, ruling (g)).
  - F024 and F029 identity: `present`, `uncertain`. This is the reply-sheet reference (ruling (g2), D-002).
  - F069 identity, p1 and p3: `present`, association `resolved`, **`excluded_from_scoring` true**, `review_status` unresolved (D-004). See D4-03.
- **F019 revision:** the page is `ambiguous`, excluded, unresolved/unresolved (D-005).
- **F067 decision:** the page is `ambiguous`, no/no.
- **Vocabulary found.**
  - States: present, absent, ambiguous. No page is `illegible` or `unsupported`.
  - Association: resolved, uncertain.
  - Decision class: approved (13 pages), approved as noted (59), revise and resubmit (7).
  - `absent_kind`: no_decision_area 61, blank_decision_area 2.
  - `resubmission_required` is yes on 9 rows, all class "approved as noted".

## 3. Gate, concentration, matched population, feasibility (check 3)

- **The gate as written is met at pool level.** FEASIBILITY v2 rules 3–4 and plan §2.2 require at least 12 resolved, independently reviewed documents per field, with no partial run. The result is 57/38/38, with 0 extensions. Planning predicted decision 15.2 expected (worst case 5, P(<12) = 0.757). The actual count is 38.
- **The run-time population is not 57/38/38.** Plan §2.3 takes the run set as at most 16 decision-bearing documents, then tops identity and revision up to 16 (at most 8 top-ups), then adds 4 negative and 2 unsupported controls, for at most 30 documents. My Monte Carlo approximation is below; no run-set selector exists to run.

  | Field | Documents in the run set |
  |---|---|
  | decision | exactly 16 |
  | revision | 16 in 99.9% of draws (the top-ups are F041, F046, F050, F056, F057, F058 and F060 from 26687, and F043 and F067 from 15744) |
  | identity | 16 to 24, median about 19–20 |

  Labelled run-set documents before the controls: 16 to 24.
- **The matched population is smaller again.** `score_bcr.matched` keeps only documents that B **and** C attempted and that are not unsupported. B always counts as attempted (`score_lane`, policy "none"). So the realistic matched population is **16 for decision and for revision**, a margin of only **4 documents** over the minimum of 12.
- **Ways the margin is lost:**
  - C does not attempt a document (deadline, elapsed time, or a breaker/allowance refusal; a refusal also makes the comparison INCOMPLETE);
  - C returns `unsupported_input`;
  - alias double counting, if the selector does not draw canonical ids only;
  - an adapter rule that makes F019 (a decision document) non-primary;
  - the per-project rolling limit of 60 per day across all tracks. Run-set documents per project average about 4–5, with a maximum of 10; at up to 8 requests per document, a heavy project can exceed 60.
- **How likely the loss is.** If each document is lost independently with probability 10%, 20% or 30%, then P(matched < 12) is 1.7%, 20% or 55%. **12 is at risk.**
- **Concentration (plan §5.5, `score_bcr.concentration`).** The stratum leg fires whenever a field has positive net gain and one stratum holds more than half of it. Decision documents are 37/38 review_signal, so any positive decision net gain is flagged as "concentrated". The one exception is net gain 2 split exactly 1/1 with F072. See D4-07.
- **Project distribution.** Three projects hold 33 of the 38 decision documents, and 15744 has none. In the simulated run set, the largest single-project share of the 16 decision documents is 5–7 (7 or more in about 28% of draws). A net gain of 1 is always concentrated.

## 4. Harness consumability (check 4): the adapter `r32-labels-reviewed-1` would need

**What the frozen harness expects** (read from the source):
- `score_bcr` labels: `{documents: {doc: {project, stratum, resolved: bool, independent_review: bool, in_scope_pages: n, facts: {"<page>": {identity|revision|decision: value | None}}}}}`.
- `has_fact`: a value that is not None or empty.
- `primary`: document-level `resolved` and `independent_review`.
- `coverage_counts`: treats None as "truth absent", so a `discovery_absent` on that page counts as a verified absence.
- `critical_split` and the dry-run tripwire: classify a critical as resolved or unresolved **per document**.
- The dry run's `LABELS-NORMALISED.json` shape: top-level `{source, independent_review, documents}`; doc key `"EP-<ep>/<relative_path>"`; fields `draft_id`, `project` (= "EP-…"), `stratum`, `resolved`, `independent_review`, `in_scope_pages`, `facts` (page-string keys; str or None values).
- `score_lane.py` and `run_lane.py` / `dry_run.py`:
  - they read `C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json` and the r26.2 register, page and uncertainty files;
  - they score evaluator .10 (`m2_eval6.evaluate(REG, PAGE, rows, page1_corrections, …)`) over `DECL.sources.sample.documents_planned`;
  - they build coverage with `coverage_v4.document_coverage(planned, …, max_pages=4)`;
  - they replay final-A and the L3 captures. No live runner exists.
- `capture_store`: keys on the document sha256 and page. The byte-identical pairs F038/F052 and F067/F070 share content keys.

**Adapter requirements and schema mismatches**

| # | Item | r32-labels-reviewed-1 | Harness input | Normaliser only, or a code change? |
|---|---|---|---|---|
| 1 | Key | pool id `F###` + page "1"–"4"; `ep`; staged sha256 | `"EP-<ep>/<relative_path>"` + page string; rows keyed the same way by the sandbox DB | Normaliser: map the pool id to the doc key through `SOURCE-MANIFEST` (ep, relative_path, staged sha256). Metadata used as a key, never as evidence |
| 2 | Resolution granularity | per field (`review.<field>.resolved_for_scoring`) | per document (`resolved`) | **Code change** for an exact result. A normaliser forces a choice: "any field yes" gives 57/38/38 but classes F019 revision criticals as resolved; "no field unresolved" gives 56/38/37; "all fields yes" gives 50/37/32 |
| 3 | Page-field exclusion | 30 pages in 27 documents with a non-scorable field next to scorable ones: 21 present+uncertain, 6 ambiguous, 3 excluded/unresolved | none: None = absent | **Code change**, or the normaliser drops whole pages, which also loses those pages' scorable fields. With None, a C `discovery_absent` counts as a verified absence and an accepted value is scored against "absent" |
| 4 | State vocabulary | present / absent (`absent_kind` → UR / n/a) / ambiguous (/ illegible / unsupported, unused); association resolved/uncertain | a value or None | Normaliser for present+resolved → literal and absent → None. Ambiguous and uncertain need #3 |
| 5 | Literal comparison | (i2): whitespace-insensitive; en dash in "MAT – 116" (3 literals); Arabic literals (F043 p1 identity with Arabic-Indic digits; 11 decision rows on F014, F016, F038) | done inside evaluator .10 | **UNVERIFIABLE** (candidate source not opened). Needs a test before the declaration |
| 6 | Decision value | `literal` + `class` (approved / approved as noted / revise and resubmit) + `resubmission_required` | r26.2 decision string; `NO_DECISION = (None, "", "UR", "n/a")` | Normaliser picks class or code. Tolerating "resubmit" on the 9 `resubmission_required` rows needs alternative-truth support: **UNVERIFIABLE**, and likely a code change |
| 7 | Compilations (F002, F035, F043, F069) | truth keyed (pool id, page); never one file value | evaluator per-page records; `y` is document-level (clean on any component) | Normaliser keys by page. Whether evaluator .10 scores the mirror's file-level value against a compilation is UNVERIFIABLE |
| 8 | Aliases / duplicates | `count_once_aliases`; F052 and F070 have no pages; F031 has extra pages 3–4 | every document key counts once; same sha256 → shared capture | Normaliser and selector: canonical ids only (exclude F031, F052, F059, F070 from the run set), or score aliases with the canonical truth and count once |
| 9 | Unresolved rows | F069 p1/p3 identity (state present, excluded), F019 p1 revision (ambiguous, excluded) | none | Normaliser must honour `excluded_from_scoring` / `review_status` unresolved; exact handling needs #2 and #3 |
| 10 | `in_scope_pages`, `stratum`, `project` | `RENDERS.pages_in_scope`, `FROZEN-SELECTION.stratum`, `ep` | required keys | Normaliser |
| 11 | Lane scoring and runner | — | `score_lane.py` and `run_lane.py` are hard-bound to the four-arm declaration, r26.2 and final-A/L3 | **Code change**: a new r32 lane scorer and a live runner, an r32 → evaluator-input (REG/PAGE/uncertainty, `planned`) converter, a B-sandbox ingestion of exactly the run set, a new binding manifest and new tests |
| 12 | Run-set selector | — | not implemented anywhere | **Code**: new, tested, frozen before B |

**Conclusion.** `population_gate` alone can be fed by a normaliser and reproduces 57/38/38. Feeding the frozen harness end to end is different: it needs new or changed harness code (#2, #3, #11, #12, and possibly #5–#7 in the evaluator). That requires a correction task, re-testing and a new binding manifest and draft declaration.

## 5. DRAFT-DECLARATION.v2: what the final declaration must replace or add (check 5)

**Now inconsistent with the frozen preparation:**
- `status` ("no labels … no owner permission").
- `labels.status` "not drafted".
- `labels.review` "Codex reviewer". A-03 makes this an owner-delegated independent Claude AI review.
- `cohort.permission` "REQUIRED …". A-02 exists (`fd20167a…`) but covers access only. Provider use, the budget and the ledger scope remain unauthorized.
- `selection.feasibility_sha256` `ed1decfe…`. These are planning ranges, superseded by the counts.
- Extension-2 capacity "yes (120)" with alternate 22317. A-02 does not grant alternates for capacity. This is moot, because 0 extensions were used.
- `evaluators.lane_scoring` `score_lane.py` `17ed2ba3…` is bound to the four-arm declaration and r26.2.
- `dry_run` `ac60194c…` exercised the four-arm sample, not r32.
- `stop_rules` "tripwire … against the frozen labels" has no per-field resolution.
- `binding_manifest` `2dfef08e…` contains no r32 binding.

**Bindings to add or replace:**
- Labels:
  - `r32-labels-reviewed-1` `00e53e82…7779`, or `r32-labels-reviewed-2` after the D-004/D-005 rulings;
  - draft `ebd1e24d…`;
  - conventions `5c09d4d2…`;
  - final response `920a21d6…`, dispositions `e8828bec…`, critique `ad6798dc…`, consolidated `70f94632…`;
  - the normalised-labels hash and the normaliser code hash.
- Population:
  - `FIELD-POPULATION.json` `5b9cf095…`: 57/38/38, unresolved F069 (identity) and F019 (revision), aliases, upper bound 57/39/38;
  - extensions used 0;
  - gate result.
- Cohort and selection:
  - verified cohort `PROJECT-VERIFICATION.json` `4cecf2fc…`, no replacement;
  - `FROZEN-SELECTION.json` `bf71779a…` (rules `84a0bdec…`, seed `m2-r30-pool-2026-10-02`);
  - universe 3,046 / eligible 2,585 against the 2,455 in Review 31, disclosed.
- Extension facts:
  - the frozen order has 302 review-signal paths;
  - capacity is 34 of 36 for extension-1 and 22 of 36 for extension-2;
  - neither was drawn;
  - an alternate for capacity needs a new owner decision.
- Staging:
  - `SOURCE-MANIFEST` `951e8697…`, `RENDERS.json` `175a3a10…`, `CROPS.jsonl` `b1760b64…`, `EVIDENCE-INDEX` `0d0db4f8…`;
  - the stage directory;
  - package manifests `15c4114d…` and `64c03667…`.
- Run set:
  - the selector code;
  - the run-set manifest hash;
  - the definition of the 2 unsupported controls.
- Harness:
  - the new lane scorer, live runner, B ingestion and adapter with their tests;
  - any `score_bcr` change.
- Caps: B 240 and C 240 (equal, 8 × 30), R 40, P 36, total 556. These stay consistent with a run set of 30 or fewer, and expected use about 171 remains an estimate.
- Stop rules: per-field resolved/unresolved for the tripwire, keyed by pool id.
- Authorization: an owner authorization for provider use, budget and ledger scope that names the final declaration hash.

## 6. Response ledger (check 6)

- **File.** `M2-REVIEW-RESPONSE.md` `f0a4ffac…`, 160,093 bytes. The first 156,880 bytes hash to `6e296c28…`, and the first 153,812 bytes hash to `afddd562…`. Both are as stated.
- **Entry 1 (offset 153813, fresh-cohort-r32).**
  - Manifest `15c4114d…`, 110 files, 72/149/189 staged, `bf71779a…`, `951e8697…`, `5c09d4d2…`, `ebd1e24d…` all equal the package.
  - The projection 62/39/39 equals `DRAFT-PROJECTION.json`.
  - 432/210/56 equal the worklists and questions.
  - The entry still says "Codex reviewer"; A-03 supersedes this.
- **Entry 2 (offset 156881, reviewed package).**
  - 45 files, manifest `64c03667…`, check 18 of 18, labels `00e53e82…` all equal the package.
  - 432/210/56 and the page-field status counts equal `applied`.
  - 57/38/38, the F069/F019 exclusions, upper bound 57/39/38 and 72/70/68 all equal `FIELD-POPULATION.json`.
  - Ledger 483/17 equals the read-only query.

## Findings

See `D4-findings.json` (D4-01 to D4-13). In summary:
- **Counts:** confirmed (57/38/38), and the document/page consistency holds.
- **Gate:** met at pool level. The run-time matched margin is only 4 for decision and revision.
- **Concentration:** the stratum leg is structurally unsatisfiable for decision.
- **Harness:** the frozen harness cannot consume r32 labels without new and changed code (runner, lane scorer, run-set selector, per-field resolution and page-field exclusion). The evaluator's handling of whitespace, dashes, Arabic, resubmission and compilations is unverifiable here.
- **Declaration:** DRAFT-DECLARATION.v2 has 10 stale or missing bindings.
- **Ledger:** both appended entries are accurate.
