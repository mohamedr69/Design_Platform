# M2 Review 06: BOQ / Design Sheet results

The three tracks are kept apart:
1. the deterministic reader (an evaluation track, not an application path);
2. the application with the model disabled;
3. the application with the real model (AI-EV0), plus the blind row-verification variants (EV1/EV2).

Scoring throughout uses the frozen BOQ evaluator .3, with labels v2 (the Review 05 corrections) and the holdout BOQ labels.

## 1. Deterministic reader

Sheet extractor versions: `2026-09-28.2` in Review 05, `2026-09-29.1` in the candidate. The configurations were run cleanly one after another, each with both knobs set explicitly (`scripts/boq_exp.py`, outputs in `boqexp/`).

**Sanity check.** The candidate code with both knobs off (configuration A) reproduced Review 05's extraction exactly: 5 critical, part 288/292, quantity 310/311.

| Configuration | Set | Critical | Part tp / accepted / held / missed (recovery) | Quantity tp / accepted / held / missed (recovery) |
|---|---|---|---|---|
| A: Review 05 behaviour | pilot, 15 sheets | 5 | 288 / 292 / 132 / 235 (43.7%) | 310 / 311 / 121 / 264 (44.5%) |
| **B: candidate** (`HOLD_ON_PASS_DISAGREEMENT`) | pilot | **4** | 287 / 291 / 133 / 235 (43.6%) | 310 / **310** / 122 / 264 (44.5%) |
| C: B + part cross-check at every confidence (`CONFIRM_CATALOG_BELOW=101`) | pilot | 2 | 243 / 245 / 179 / 235 (36.9%) | 264 / 264 / 168 / 264 (37.9%) |
| A | holdout, 4 sheets (exposed) | 4 | 13 / 13 / 36 / 57 | 18 / 22 / 36 / 61 |
| **B: candidate** | holdout | **3** | 12 / 12 / 37 / 57 | 17 / 20 / 38 / 61 |
| C | holdout | 3 | 10 / 10 / 40 / 56 | 15 / 18 / 41 / 60 |

**What B fixed:**
- EP-30088 SIGA-IB, printed 75 and read 15 (pilot);
- EP-8430 PC+Monitor, printed 2 and read "\| 9" (holdout).

**What remains under B (open, D-R6-C).** Seven confident misreads, all at 91–95% strip confidence:

| Set | Sheet | Printed | Read |
|---|---|---|---|
| pilot | EP-14119 | SIGA-AA50 | SIGA-AASO |
| pilot | EP-26082 | PT-1S+ | PT-1S |
| pilot | EP-30088 | PT-1S+ | PT-1S |
| pilot | EP-30088 | 4-FWAL4 | 4-FWALA |
| holdout | EP-8430 | 1 (three rows) | 4 |

**Why C is not adopted.** It removes 2 more pilot critical errors (SIGA-AASO and 4-FWALA), but it costs about 15% of recovery on the pilot and still leaves PT-1S+. Additional passes over the same pixels by the same engine are not independent evidence (the R5-04 rule). C is reported as a measured option for the reviewer.

## 2. The application with the model disabled

`scripts/run_boq_app.py boq-app-off`, on the four eligible sheets of EP-30784 and EP-30088:
- `ensure` → 200 with 0 items. Each sheet is recorded "Not read: AI assistance is disabled (AI_ENABLED=false)", with the reason.
- A second `ensure` is idempotent.
- The `boq-reread` job ends with "No Design Sheet could be read, so nothing was compared and the BOQ is unchanged". Nothing is removed and nothing is invented.

This is unchanged from Review 05.

## 3. The application with the real model (AI-EV0)

`scripts/run_boq_app.py boq-app-ev0 --ai`. This is the application's own path: `POST /boq/ensure`, the `boq-read` job, `sheet_reader`. It covered the four eligible sheets, which contain 3 of the 5 pilot deterministic critical cases.

| Track, same 4 sheets | Critical | Part tp / accepted / held / missed | Quantity tp / accepted / held / missed |
|---|---|---|---|
| Deterministic B | 2 | 113 / 115 / 45 / 3 | 121 / 121 / 45 / 4 |
| **Application model path** | **1** (EP-30088: PT-1S+ read as PT-1S) | **155** / 156 / 5 / 2 | **163** / 163 / 5 / 2 |

- **Calls:** 41 requests:

  | Task | Model | Calls |
  |---|---|---|
  | `read_sheet_page` | sonnet-5 | 18 |
  | `read_sheet_row_close_up` | **opus-5** | 10 |
  | `read_cell` | sonnet-5 | 7 |
  | `verify_boq_row_crops` | sonnet-5 | 5 |
  | `verify_boq_row_crops` | — | 1 explicit **timeout**, recorded as an outcome |

  Model time 1,437 s; 278,200 input and 132,234 output tokens; cost unknown.
- **Wall time:** EP-30784 566 s, EP-30088 971 s.
- **Persistence:** 166 BOQ items were stored. The second `ensure` was idempotent, and the `boq-reread` job succeeded: items before/after 82/82 and 84/84, **0 removed**.
- **Finding:** this is the first real-model BOQ evidence. On these sheets the model path recovers far more than the deterministic reader, and has one critical error where the deterministic reader has two. The remaining error, PT-1S+ read as PT-1S (a lost "+"), is shared by both readers.

## 4. Blind row verification (AI-EV1 / AI-EV2) on the deterministic reader's rows

- **Rows:** the candidate's deterministic rows (configuration B) on the four eligible sheets.
- **EV1 selection:** every held row plus the frozen, seeded 20% audit of accepted rows. **EV2:** every row.
- **Blind read:** a crop of the row, with no reader value in the prompt. Readings are compared afterwards.
- **Runner:** `scripts/run_boq_ev.py`. Declared in addenda 1 and 3.

| Track | Verifier | Fresh requests | Model time | Tokens in / out | p50 latency | Outcome |
|---|---|---|---|---|---|---|
| AI-EV1 BOQ | `.1` | 67 (sonnet-5, all ok) | 484 s | 347,508 / 19,037 | 7.2 s | complete, 4 sheets |
| AI-EV2 BOQ | `.1` | 99 (sonnet-5, all ok) | 699 s | 516,373 / 28,261 | 7.0 s | **stopped** after 2 of 4 sheets, once the verifier defects below were found |
| AI-EV1b BOQ | **`.2`** | 54 (sonnet-5, all ok) | 468 s | 297,718 / 25,967 | 8.3 s | complete, the two FAS sheets |

### Verifier `.1` defects, found in this exploration and kept as evidence

1. **The prompt dropped leading quantities.** It asked for the quantity "not the row's item number". On these layouts the quantity is the first column, so the model returned an empty quantity for most rows.
2. **The part comparison dropped symbols.** It used `norm`, which removes punctuation, so `PT-1S` validated against a blind `PT-1S+`. **One wrong accepted row was therefore "validated"** (`missed_wrong_accepted`) in both EV1 and EV2.

As a result, `.1` produced many false alarms: EV2 wrongly questioned 28 correct accepted rows on EP-30088 FAS.

There were also three runner bugs:
- a join crash on extra rows;
- the same on the missing `fields` key;
- held-row batches without the sheet's geometry.

Each was fixed and the run resumed from its own database. Answers already paid for were replayed as cache hits. The crash logs are kept (`realmodel/run_boq_ev*_attempt*`).

### Verifier `.2` (`read-boq-row-2026-09-29.2`)

- The quantity cell is its own image, taken from the reader's `quantity_span`.
- Parts are compared literally: upper case, whitespace ignored.
- Tests: `test_boq_part_is_compared_literally_and_the_quantity_cell_is_its_own_image`, and the policy cases.

**Part reading, on the 50 rows of the two FAS sheets that have part truth:**

| Reader | Parts right |
|---|---|
| Deterministic OCR reader | 41 / 50 |
| Blind verifier `.1` | 47 / 50 |
| **Blind verifier `.2`** | **50 / 50** |

With `.2`, **9 reader part errors are read right and 0 errors are introduced.** The corrections include:
- the critical `PT-1S+` (accepted by the reader as `PT-1S`), now **caught** as a `conflict`;
- `SIGA-AA50` ×2 (reader `SIGA-AASO` / `SIGA-AAS0`);
- `3-CAB5B`, `4-CAB16D`, `SIGA-OSHD-FCN`, `757-7A-T`, `G1ARN` and `757-7A-SS70`.

**Quantity reading:** 22 / 50 right and 28 empty. The empty ones are mostly component rows, whose count is printed as "( n )" inside the description column; their quantity cell is genuinely empty. Under the `.1`/`.2` policy an empty blind quantity against a reader value is a conflict, so `.2` still wrongly questions 12 correct accepted rows (EV1b: 1 caught, 12 questioned, 6 confirmed).

### A stricter policy, re-validated deterministically on the stored readings (exploration)

`realmodel/boq_policy2_revalidate.py` → `score/boq-ev1b-policy2-revalidation.json`. It makes no new calls, and it was **shaped after seeing these exposed results**. The rule:
- a literal part disagreement is a conflict;
- a non-empty blind quantity that disagrees is a conflict;
- an empty blind quantity cell leaves the quantity *unverified*, not in conflict.

| Rows | Reader right | Reader wrong |
|---|---|---|
| Accepted | 18 → 6 validated, 12 part-validated / quantity unverified, **0 questioned** | 1 → **conflict (caught)** |
| Held | 21 → 10 validated, 11 part-validated | 11 → **conflict**; in every case the blind reading is the truth where it reads |

No validated row is wrong in this sample. This is a **candidate** for the next frozen policy. It has to be frozen and then shown on unseen sheets before any claim.

### Not run

- EV2 with verifier `.2`: the declared request total left no room (690 of 700 used).
- EV1 and EV2 on EP-26082, EP-14119 and EP-8430, the other critical cases: those projects have no recorded AI policy.
- The EV1 audit sample did not include the other two EP-30088 critical rows as accepted rows, so EV1 cannot say whether the verifier would catch 4-FWALA. The frozen audit rule decides which rows are read, not the truth.
