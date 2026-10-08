# Rehearsal finding R43-40-F1: the bound harness's dry mode cannot exercise real baseline facts (STOPPED; for Verification 44)

Task R43-40 section 3 item 1 and Verification 43 check 8 item 6 require an offline dry rehearsal in which lane B's deterministic
baseline processing (frozen-r13) produces real facts for at least F009, F020 and F030 and the tripwire judges them against the
resolved truth. The card says: find and fix the cause of v3's `exercise_no_facts` in the dry-mode driver only; if the cause is
inside the bound harness, STOP and report it. **The cause is inside the bound harness. This part was stopped. Nothing in the
harness was changed and no workaround was run.** This record authorizes nothing.

## What the v4 dry rehearsal shows (reproduced, 0 requests)

The single 24-document dry run of this package (`dry-run/exercise-single/`, stamp `r43d-single-30b02b`, the review43 harness
byte copy checked against `f35355aa...374a7`) ran every lane with reader `none`:

| file (this package) | sha256 | what it shows |
|---|---|---|
| `dry-run/exercise-single/RUN-REPORT.json` | `95c94899e036f8fa1fa16339a214c50850d36c0824e5aea941de5d5e3ba50484` | lanes B, C, R, P reader `none`; run FINISHED; 0 model requests; ledger unchanged |
| `dry-run/exercise-single/LANE-B.json` | `91f4eb4352e36f45b3f97aafb61855cc7702defaf00dea2c99921c93ef09b148` | `application_processing_run` false; tripwire entries for F009, F020, F030: `resolved []`, `unresolved []`, `when exercise_no_facts` |
| `dry-run/exercise-single/_trip-in-B.json` | `c5b4794a814b61a060da17389e02d771cc86e411d1c68a139bac597760ef039f` | the tripwire input: `{"extracted": null}` for every run-set document |
| `dry-run/exercise-single/_trip-out-B.json` | `e6cc2d728fa2b1c15329fce7868fdb0dbb9784cc176cd8a514cca50e02d90334` | F009, F020, F030: `facts 0`, identity / revision / decision `critical 0, unresolved 0` |

Per-document outcome for the three documents: **not exercised** (0 facts; the tripwire saw nothing). The stop condition that
ended v3 (a resolved-truth critical in B on F009 page 3) can neither fire nor be shown not to fire in this mode.

## Cause (bound files of `PILOT/review43/scripts/harness-r32`, unchanged)

1. `runner_r32.py` (sha256 `87ca348e...1c9e`) line 772: the run configuration sets `"reader": "application" if (live or synthetic
   is not None) else "none"`. A dry run gets the application reader only with `--dry-synthetic`.
2. `runner_r32.py` line 865: a synthetic drill is refused unless it holds only `SYN*` documents of EP-990001
   (`refused: a synthetic drill holds only SYN* documents of EP-990001`).
3. `lane_r32.py` (sha256 `d98790ca...edaa`) lines 84-86: `if MODE == "dry" and READER == "application": ... assert not cohort,
   "dry mode never runs a reader on a cohort document"`.
4. `lane_r32.py` lines 470-472: with reader `none`, lane B calls `b_tripwire({pid: {"extracted": None}}, "exercise_no_facts")`
   for every run-set document, so the tripwire evaluates no fact.

This is a deliberate rule of the harness since review34 ("Dry mode never reads a cohort document with an application reader",
`review34/COMMANDS.md`; Review 34 finding R34-18: the application processes the real cohort PDFs for the first time in live B),
carried unchanged into review39, review42 and review43, and disclosed in v3 and v4 (`disclosures[1]`). The v3 dry exercise had
the same property; it was not a driver choice: `dry_exercise_r42.py` has no option that changes the reader.

## Why no driver-side fix was made

A dry-mode driver cannot obtain real lane-B facts on F009, F020 and F030 without either editing a bound harness file (lines
above) or disguising cohort documents as synthetic ones (renaming them `SYN*`, moving them to EP-990001 and substituting a
synthetic truth), which would defeat the rule and would not judge against the resolved truth. Neither was done.

## Options for Verification 44 and the owner (none taken here)

1. A reviewed harness change, re-bound in a new harness manifest: a dry `baseline-facts` drill (lane B only, reader
   `application`, the run-set subset F009 / F020 / F030, every request ending at the refusing DryStub, the tripwire against the
   resolved truth), with its own tests and verification.
2. An out-of-harness offline rehearsal under the package guard: the frozen-r13 application's processing of the staged F009, F020
   and F030 PDFs in a sandbox with AI disabled and a refusing global provider, judged by the bound `tripwire_r32.py` /
   `lane_judge_r32.py` unchanged. It would show the identity facts but would not be the harness's dry mode.
3. Keep the R34-18 rule as is; then condition (b) of A-13 item 3 ("the dry rehearsal exercises F009/F020/F030 and passes") is
   not met by this package and is the owner's to re-decide.

Existing evidence that is **not** a rehearsal of this kind (cited only): the R43 review package's harness-side confirmation
(`R43-REVIEW-PACKAGE/R43-HARNESS-JUDGE-OUTPUT.json`): `lane_judge_r32.judge_document` of the frozen review42 harness on facts
observed from the text layers of pages 3 and 4 (fixtures) after the grammar fix: F009, F020, F030 and F021 0 criticals.

## Statuses

- Condition (b) of A-13 item 3: **not demonstrated by this package**.
- Harness: unchanged; Verification 43's verdict on it is not contested (the rule is a design choice, not a defect).
- Authorizes nothing. M4 (historical M2): CHANGES STILL REQUIRED. M3: accepted.
