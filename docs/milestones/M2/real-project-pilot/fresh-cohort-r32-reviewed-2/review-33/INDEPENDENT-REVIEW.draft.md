# Independent M2 Preparation Review 33 (DRAFT)

- **Task:** ORCH-03.2, synthesis and draft verdict.
- **Agent:** R33-SYNTH, Claude Opus 5.5 (`claude-opus-5-5`), effort High. Fresh and isolated.
- **Authority:** A-03, the owner's 2026-10-03 decision on a Claude-only workflow.
- **Date:** 2026-10-03.
- **Nature of this review:** an owner-delegated independent Claude AI review. It is **not** human sign-off. This is a **draft**. R33-CRITIC (adversarial critique) and R33-FINAL (dispositions and final verdict) follow, and then R33-VERIFY. Nothing here approves, authorizes or self-approves anything.
- **Standing status:** M2 is CHANGES STILL REQUIRED, and M3 has not started.
- **Sources:** the four dimension reports and their findings in `dimensions/`, plus my own recomputations and image reads (section 2).

| Dimension file | sha256 (first 16 hex digits) |
|---|---|
| D1-report.md / D1-findings.json | `d8003c531e75f8db…` / `f5a8a780a38e761d…` |
| D2-report.md / D2-findings.json | `636719edd8170e58…` / `ba98df0ae975ba61…` |
| D3-report.md / D3-findings.json / D3-escalation-rulings.json | `e8164fbbcda3b5da…` / `5596a87605d0bf95…` / `4a26e8c631ac91ca…` |
| D4-report.md / D4-findings.json | `283dd58a904dc4f8…` / `74170a67a94650f5…` |

## 1. Verdict

**PREPARATION ACCEPTED WITH CONDITIONS**

**Why this verdict.**
- There is no blocker.
- Nine findings are major. Eight are CONFIRMED and one is UNVERIFIABLE (R33-01 to R33-09).
- Under the verdict rule, confirmed majors allow at most acceptance with conditions.
- None of the majors shows that the frozen cohort, the evidence, the label truth or the counts are wrong:
  - every binding recomputes;
  - an image check of 98 items refuted 0 rows;
  - the populations recount exactly.
- The majors concern four things:
  - two open escalations, which this review now rules;
  - unrecorded convention amendments;
  - a policy conflict that only the owner can resolve;
  - harness and declaration work that must exist before any declaration.

**What this verdict accepts.** Each item is accepted as frozen, subject to the conditions below:
- the verified six-project cohort and the frozen 72-file pool;
- the staged evidence;
- `r32-labels-draft-1` and its independent Claude review;
- the application of that review as `r32-labels-reviewed-1`;
- the counted populations, 57/38/38. They become 57/39/38 once the D-005 ruling is applied.
- The pool-level gate (each field at least 12) is met with 0 extensions.

**Conditions to meet before any declaration** (each is linked to its finding):

| # | Condition | Finding |
|---|---|---|
| C-1 | Apply the D-004 and D-005 rulings (section 4) mechanically as **`r32-labels-reviewed-2` in a new package** with its own manifest, a recount and a new FIELD-POPULATION. The expected counts are 57/39/38. The F069 p1/p3 identity rows are written as `ambiguous`. `r32-labels-draft-1` and `r32-labels-reviewed-1` stay unchanged. If the owner instead adopts topic (h2) and/or topic (i), the alternative rows in section 4 apply. | R33-03 |
| C-2 | Record count-once (c)(ii) as an explicit amendment to convention section 1, with the F031 p3 caveat, or revert to byte-identical-only counting. Also record (d1), (e)/D-001, (g)(1), (g2)/D-002, (h)/D-003, (d2) and (f) as amendments or interpretations in the declaration. | R33-04, R33-11 |
| C-3 | The owner resolves AI-ACCURACY-POLICY §8 for this run, which forbids gold labels "approved solely by another model". This takes an append-only amendment or waiver, or a human check of the rows that will be scored. | R33-02 |
| C-4 | The owner, with an independent review, decides the stratum leg of the concentration rule and freezes the choice. Whatever the choice, the adapter must populate `stratum`. | R33-01 |
| C-5 | A correction task, with tests and a re-freeze, delivers the harness adapter set out in section 5: per-field resolution and page-field exclusion, an r32 lane scorer and live runner, a converter, B-sandbox ingestion, and a run-set selector with defined unsupported controls and canonical ids only. | R33-05, R33-06, R33-07 |
| C-6 | An offline test of evaluator .10 against the converted r32 labels, with zero model calls, covering each comparison rule named in R33-09. Any evaluator change is a separate candidate correction. | R33-09 |
| C-7 | A new declaration that replaces the stale DRAFT-DECLARATION.v2 bindings (section 5), written only after C-1 to C-6 are frozen. | R33-08 |
| C-8 | The minor findings' disclosures (R33-10 to R33-22) are carried into the declaration or into append-only addenda. | R33-10 to R33-22 |

**What this verdict does NOT authorize:**
- any provider or model request;
- any B, C, R or P validation run, or any prediction;
- any model-request budget, use of the 556 ceiling, or experiment ledger scope;
- alternates for extension capacity;
- a default extraction variant;
- M2 acceptance or M3;
- any change to frozen packages, labels, production data or OneDrive originals;
- any claim of human sign-off.

The rulings in section 4 are this review's rulings, not owner decisions.

## 2. Evidence checked

**Recomputed by R33-SYNTH.** All of the following match.

| Item | Result |
|---|---|
| Packet manifest `fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json` | `15c4114d…82d0ed`; 110 entries, 0 mismatches; 112 files on disk (the manifest and PACKAGE-CHECK are unlisted) |
| Reviewed manifest | `64c03667…31c6`; 45 entries, 0 mismatches; 47 on disk. It binds `package_check_sha256` `7ff3594b…3018`, which equals the current file |
| review31 manifest | `d5fe1649…c460`; 58 entries, 0 mismatches; 60 on disk |
| Draft labels / conventions / FROZEN-SELECTION | `ebd1e24d…a334` / `5c09d4d2…e570` / `bf71779a…5d21` |
| SOURCE-MANIFEST / CROPS / EVIDENCE-INDEX / RENDERS | `951e8697…e259` / `b1760b64…1cd1ff` / `0d0db4f8…32ba08b8` / `175a3a10…e8be` |
| PROJECT-VERIFICATION / AUTHORIZATION | `4cecf2fc…f1c4` / `fd20167a…721d` |
| Reviewed labels / FIELD-POPULATION | `00e53e82…7779` / `5b9cf095…4505` |
| Label review folder (23 files) | final `920a21d6…`, consolidated `70f94632…`, critique `ad6798dc…`, dispositions `e8828bec…` |
| DRAFT-DECLARATION.v2 | `19720ad9…8b5d` |
| Response ledger `M2-REVIEW-RESPONSE.md` | whole file `f0a4ffac…c65b`; first 156,880 bytes `6e296c28…fa0d4` |
| Staging re-hash, `C:/t/r2x/r32-stage` | 72 staged PDFs against SOURCE-MANIFEST `staged_sha256`, 149 renders and 189 crops against EVIDENCE-INDEX: 0 mismatches. `renders/` holds 447 files (149 png, 149 txt and 149 words.json) |
| Byte-identical pairs | the `staged_sha256` groups are exactly [F038, F052] and [F067, F070] |
| AI ledger (`mode=ro`, `uri=True`) | 483 entries, 17 scopes, 0 limit amendments |

**Counts (my own script).** Raw yes/yes is 59/40/39. After the aliases F031→F001, F052→F038, F059→F046 and F070→F067, the counts are **57/38/38**:
- F069 identity and F019 revision are excluded as unresolved.
- `resolved_for_scoring` yes is 67/64/69.
- There are 72 documents and 144 labelled pages.
- Page level and document level disagree in 0 cases.

The counts by stratum and by project are:

| Field | review_signal | drawing_signal | other | By project |
|---|---|---|---|---|
| Decision | 37 | 0 | 1 | 27331 12, 3563 11, 29255 10, 26687 3, 22349 2, 15744 0 |
| Identity | 36 | 16 | 5 | |
| Revision | 29 | 8 | 1 | |

**Images I read myself** (bound evidence only; my zooms and rotations are scratch derivatives, not evidence):
- `renders/F069-p1.png`
- the header of `renders/F069-p3.png`
- `renders/F062-p1.png`
- `crops/F019-p1-0.03_0.84_0.2_1-r90.png`
- `crops/F019-p1-0.38_0.86_0.44_0.99-r90.png`
- `renders/F019-p1.png`, with a rotated zoom of the revision table: REV 00 05-03-16 and REV 01 09-05-16

**Pixel comparisons of bound renders:**
- F001-p1 against F031-p1, and F001-p2 against F031-p2: 0 differing pixels.
- F046-p1 against F059-p1: 1,183 pixels differ by more than 64 grey levels, all inside x 0.842–0.882, y 0.856–0.911.

**Relied on from the dimensions, not repeated by me:**
- OneDrive `os.stat` for 72 of 72 files (D1).
- `git rev-parse`/`status` for candidate `a8aacedd` and baseline `3d5607d9`, both clean (D1, D4).
- The modification-time cutoff of 06:50Z across the five trees (D1).
- The network-code census (D1, D2).
- The rebuild and the 21 packaged tests (D1).
- The 98-item stratified image check (D3).
- The harness source reading and the Monte Carlo of the run set (D4).
- The selection order-key recomputation and the authority timeline (D2).

**Correction to a dimension.** D1-03 said PACKAGE-CHECK.json is unbound in all three packages. That is **refuted for the reviewed package**, whose manifest carries `package_check_sha256`. It still holds for the packet and for review31 (R33-12).

## 3. Findings

All findings are in `FINDINGS.json`: 0 blocker, 9 major, 13 minor and 7 info. Majors are listed first.

| ID | Sev. | Verdict | Finding | Required action |
|---|---|---|---|---|
| R33-01 | major | CONFIRMED | The stratum leg of the concentration rule makes decision ELIGIBLE unreachable: 37 of the 38 decision documents are review_signal. It very likely fires for identity (36/57) and revision (29/38) as well. If `stratum` is missing, all documents fall into one bucket and the leg fires for every field. | C-4 |
| R33-02 | major | CONFIRMED | AI-ACCURACY-POLICY §8 conflicts with gold labels that were drafted and reviewed by Claude only. No authority entry addresses this. | C-3 (owner) |
| R33-03 | major | CONFIRMED | D-004 and D-005 are open in reviewed-1, and F069 p1/p3 are stored as `present` EP-15744. Both are ruled here (section 4). | C-1 |
| R33-04 | major | CONFIRMED | Count-once (c)(ii) for content duplicates is an unrecorded amendment to convention section 1. Without it the counts are 59/40/39 on reviewed-1 and 59/41/39 on reviewed-2. | C-2 |
| R33-05 | major | CONFIRMED | `score_bcr` has no per-field resolution and no page-field exclusion, and None is read as "absent". 30 pages in 27 documents mix scorable and non-scorable fields. | C-5 |
| R33-06 | major | CONFIRMED | `score_lane` and `run_lane` are bound to the four-arm run and r26.2. There is no live runner, converter or ingestion. | C-5 |
| R33-07 | major | CONFIRMED | No run-set selector exists, the unsupported controls are undefined, and there is a risk of drawing an alias twice. | C-5 |
| R33-08 | major | CONFIRMED | DRAFT-DECLARATION.v2 is stale on 10 points and has no r32 bindings. | C-7 |
| R33-09 | major | UNVERIFIABLE | It is unknown whether evaluator .10 handles whitespace, dashes, Arabic text, compilations and resubmission tolerance. | C-6 |
| R33-10 | minor | CONFIRMED | The run-time matched margin is about 4 for decision and revision. | Disclose |
| R33-11 | minor | CONFIRMED | (d1), (e)/D-001, (g)(1), (g2), (h)/D-003, (d2) and (f) are not recorded as amendments. | C-2 |
| R33-12 | minor | CONFIRMED | PACKAGE-CHECK is unbound in the packet and in review31 (the reviewed package binds it). | Bind or disclose |
| R33-13 | minor | CONFIRMED | The 149 words.json files are unbound. | Disclose |
| R33-14 | minor | UNVERIFIABLE | The packet verifier ran the validator from the drafter's folder. | Re-run from the packaged copy |
| R33-15 | minor | CONFIRMED | The wording of the consent record and A-03 is not verbatim, and it does not cover Claude agents reading the images. | Owner confirmation |
| R33-16 | minor | CONFIRMED | 930 databases were read against 959. | Disclose or list |
| R33-17 | minor | CONFIRMED | The extension order uses the pool seed, not the declared extension seeds. | Disclose and bind |
| R33-18 | minor | CONFIRMED | The new duplicate rule leaves 68 distinct documents. | Disclose |
| R33-19 | minor | CONFIRMED | There is a latent conflict over alternates for capacity. | Owner, only if needed |
| R33-20 | minor | CONFIRMED | Batch reviewers wrote in parallel. | Owner confirms or objects |
| R33-21 | minor | CONFIRMED | A-03's list of documents naming Codex is incomplete. | Declaration and an optional note |
| R33-22 | minor | CONFIRMED | The opening of the r26.2 labels after the freeze is not disclosed. | Append-only disclosure |
| R33-23 | info | CONFIRMED | Integrity and bindings hold. | — |
| R33-24 | info | CONFIRMED | A-02 scope was respected, and the originals are hydrated but unchanged. | — |
| R33-25 | info | CONFIRMED | Verification and selection conform. The universe is 3,046 against 2,455, and extension capacity is 34/36 and 22/36. | Disclose |
| R33-26 | info | CONFIRMED | 98 items were image-checked and 0 rows refuted. The labels are AI-made, not human-signed. | Disclose that it is a sample |
| R33-27 | info | CONFIRMED | The recount gives 57/38/38, consistent with the page labels. | — |
| R33-28 | info | CONFIRMED | The A-03 process was followed. The CRITIC entry is missing from the agents array, and scratch images are cited in notes. | Disclose |
| R33-29 | info | CONFIRMED | The owner-only items listed in section 6 remain. | — |

Each finding's evidence is in `FINDINGS.json`.

## 4. Rulings on the escalations and carried-over items

These are rulings of this review, adopted from R33-D3 after I re-read the decisive images. They are recorded in `ESCALATION-RULINGS.json`. **Any row they change must be applied as `r32-labels-reviewed-2` in a new package before any declaration.** `r32-labels-reviewed-1` stays frozen.

### D-004: F069 p1 and p3 identity. Ruling: AMBIGUOUS

**Page evidence:**
- **F069-p1:** an Al Arabia "Design Sheet" dated 5-Aug-18 with "Refrence : EP-15744", subject "Quotation for Fire Alarm System".
- **F069-p3:** a second Design Sheet dated 4-Aug-18 with the same "Refrence : EP-15744", subject "Quotation for Emergency Lighting System".
- **F062-p1:** the same issuer prints "Project ID : EP-15744" and the document number "EP-15744/SM/FAS/201".
- **F068-p1:** prints "Oracle Job No. / OM No." EP-15744, as read by D3.

**Basis.** Section 2 of the frozen conventions defines `ambiguous` as a readable value whose role cannot be established from the page. Here the page gives only the bare label "Refrence".
- `present` is not defensible. Section 3 never lets a job number be the identity, and the issuer uses this value as its project or job number elsewhere.
- `absent` would require reading the role from other documents, which is topic (h2). The owner has not adopted (h2).

**Resulting rows (both pages):**
- `state: ambiguous`, `literal: null`;
- candidates [EP-15744, printed label "Refrence", role not established on the page];
- `association: resolved`, `excluded_from_scoring: true`;
- other_identities unchanged.

**Document level:** F069 identity is `resolved_for_scoring: no`, `carries_fact: no`.

**Row change:** yes. Reviewed-1 stores `present` / EP-15744 / `unresolved`.

**Count impact:** none. Identity stays 57.

**Owner alternative ((h2) adopted):** `absent`, with EP-15744 recorded in other_identities. F069 identity becomes yes/no, and the population is still 57.

### D-005: F019 p1 revision. Ruling: PRESENT "00"

**Page evidence:**
- **Title-block crop:** "Rev. no." reads 00, the DATE is 09-05-16, and DWG. NO is FAM-PIV-MAH-SPD-FA-2633-007.
- **Revision table, rotated on the render:** REV 00 05-03-16 ISSUED FOR APPROVAL and REV 01 09-05-16 AS PER CONSULTANT COMMENTS.

**Basis.** Section 4 of the frozen conventions makes the revision cell or title-block REV field the primary source. It uses the table only "when only a revision-history table is printed". A cell is printed here, so the frozen text decides which candidate is the field, and section 2's `ambiguous` does not apply. A rule making a cell/table conflict ambiguous would be topic (i), which amends section 4 and has not been adopted.

**Disclosure.** The table row 01 shares its date with the title block, so a prediction of "01" is plausible. The declaration must name F019 revision as a contested row.

**Resulting row:**
- `state: present`, `literal: "00"`, `printed_label: "Rev. no."`;
- semantic role: title-block revision cell;
- `association: resolved`, region [0.04, 0.86, 0.43, 0.99], `excluded_from_scoring: false`;
- note: table row 01 and the title-block DATE 09-05-16.

**Document level:** F019 revision is `resolved_for_scoring: yes`, `carries_fact: yes`.

**Row change:** yes.

**Count impact:** revision goes from 38 to 39 (F019, EP-3563). Identity stays 57 and decision 38.

**Owner alternative ((i) adopted):** `ambiguous` with candidates 00 and 01. F019 revision becomes no/no, and the population stays 38.

### Carried-over convention items

| Item | Page evidence | Ruling | Rows, document values and counts |
|---|---|---|---|
| Count-once F031→F001 | Renders p1 and p2 differ by 0 px (my check). F031 p3 is a Comments Resolution Sheet showing MAT - 116 / Rev 02, the same values as F001 | Defensible, but (c)(ii) is an unrecorded amendment to section 1, and its condition is not literally met on F031 p3 → C-2 | No row change. With (c)(ii) the counts are 57/38/38 (reviewed-1); without it they are 59/40/39 |
| Count-once F059→F046 | 1,183 px differ by more than 64 levels, only in the seal region (my check). The title-block text is identical, and neither page has a decision | Defensible under (c)(ii), which remains an unrecorded amendment → C-2 | No row change; this pair is part of the 59/40/39 difference above |
| Byte-identical F052→F038 and F070→F067 | Identical `staged_sha256` (my check) | Frozen section 1 applies | Count once |
| Page-keyed compilations F002, F035, F043, F069 | Different submittals on different pages (D3 image reads) | Required by frozen section 7. D-003 (F043 revision yes/yes) is accepted. The scorer rule must be bound → C-5/C-6 | D-003 is already in revision 38 |
| Whitespace-insensitive literals (F023, F067, "- R0n", "FA- 6001", "EM- 104") | Printed spacing (D3) | The labels correctly keep the printed form (section 3). Comparison is a scorer rule → C-6 | None |
| LACASA/Scale "- R0n" suffixes (F005, F006, F007, F011 and others) | The suffix is the only revision source (D3) | Not counted under sections 4 and 7. Counting them would be a convention change that needs the owner | None. Counting them would add up to 8 to revision |
| (d1) resubmission_required on mixed options (9 rows) | Marks on "Approved as noted / Resubmit", "B+Resubmit" and "B+R" (D3) | The class is defensible, but the amendment is not recorded. The scorer tolerance must be defined → C-2, C-6 | None |
| (e)/D-001 F025 Code C "Not Approved (Re-submit…)" | Legend on F025-p1 (D3) | Revise and resubmit is defensible. Record it as an amendment → C-2 | None |
| (g)(1), (g2)/D-002, (h)/D-003, (d2), (f) | F034-p3, F028-p4, F043 (D3) | Record them as interpretations → C-2 | D-003 adds 1 to revision (already counted) |

**Populations after reviewed-2 with these rulings:** identity 57, revision 39, decision 38, with nothing left unresolved. The gate (at least 12) is met under every option, including no (c)(ii) at all: 59/41/39.

## 5. Harness adapter requirements and declaration bindings

These are requirements only. Nothing here was built.

### 5.1 What the frozen harness needs before it can consume r32 labels

**Keys.**
- Map the pool id (`F###`) and page string to `EP-<ep>/<relative_path>` through SOURCE-MANIFEST.
- File metadata is used as a key, never as evidence.

**Per-field resolution.**
- `score_bcr.primary` is per document today. It must become per field, or a fixed conservative normaliser rule must be declared together with its effect.
- The possible document-level mappings give 57/38/38, 56/38/37 or 50/37/32 (R33-05).

**Page-field exclusion.**
- A "not scorable" marker distinct from None is needed. It covers `ambiguous`, `present` with association `uncertain`, and `excluded_from_scoring`.
- Otherwise a C `discovery_absent` counts as a verified absence.
- The critical tripwire must classify per field, keyed by pool id.

**States.**
- `present` + `resolved` becomes the literal.
- `absent` becomes None, with `absent_kind` mapped to UR or n/a.
- `ambiguous` and `uncertain` become not scorable.
- `excluded_from_scoring` and `review_status` unresolved are honoured until reviewed-2 exists.

**Decision value.**
- Map the class and literal to the evaluator vocabulary.
- Define the tolerance on the 9 `resubmission_required` rows.

**Compilations.** Truth is keyed by (pool id, page) for F002, F035, F043 and F069. A file-level truth is never used.

**Aliases.** Run sets use canonical ids only (no F031, F052, F059 or F070), or aliases score against the canonical truth and count once. Captures key on sha256, so the byte-identical pairs share their captures.

**Metadata.**
- `project` comes from `ep`.
- `stratum` comes from FROZEN-SELECTION. It is required (see R33-01).
- `in_scope_pages` comes from RENDERS `pages_in_scope`.

**New code**, built and tested in a correction task, re-frozen, and bound by a new binding manifest:
- an r32 lane scorer;
- a live runner;
- an r32 → evaluator-input converter (REG, PAGE, uncertainty and the planned list);
- ingestion of exactly the run set into the B sandbox;
- a run-set selector, with the 2 unsupported controls defined or the plan amended.

**Evaluator .10.** It needs an offline test with zero model calls of:
- whitespace-insensitive comparison;
- en-dash and hyphen variants;
- Arabic and Arabic-Indic literals;
- page-keyed compilations;
- the decision vocabulary.

### 5.2 DRAFT-DECLARATION.v2 (`19720ad9…`) bindings that the final declaration must replace or add

**Replace:**
- `status`;
- `labels.status` ("not drafted");
- `labels.review` ("Codex reviewer"; under A-03 this is now an owner-delegated independent Claude AI review, not human sign-off);
- `cohort.permission`;
- `selection.feasibility_sha256` `ed1decfe…`;
- the extension-2 route through alternate 22317;
- `evaluators.lane_scoring` `score_lane.py` `17ed2ba3…`;
- `dry_run` `ac60194c…`;
- `stop_rules` (the tripwire must be per field);
- `binding_manifest` `2dfef08e…`.

**Add:**
- **Labels:**
  - `r32-labels-reviewed-2` and its package manifest, or `r32-labels-reviewed-1` `00e53e82…` if the owner rules otherwise;
  - draft `ebd1e24d…` and conventions `5c09d4d2…`;
  - review chain `920a21d6…`, `70f94632…`, `ad6798dc…`, `e8828bec…`;
  - Review 33 final hashes;
  - the normalised-labels hash and the normaliser code hash;
  - the amendment and interpretation list (C-2);
  - the §8 resolution (C-3).
- **Population:** the new FIELD-POPULATION (expected 57/39/38), the aliases, extensions used 0, and the gate result.
- **Cohort and selection:**
  - PROJECT-VERIFICATION `4cecf2fc…`, with no replacement;
  - FROZEN-SELECTION `bf71779a…` (seed `m2-r30-pool-2026-10-02`);
  - the universe of 3,046 against 2,455, disclosed;
  - extension facts: 302 review-signal paths, capacity 34/36 and 22/36, none drawn, and an alternate needs the owner.
- **Staging:**
  - SOURCE-MANIFEST `951e8697…`, RENDERS `175a3a10…`, CROPS `b1760b64…`, EVIDENCE-INDEX `0d0db4f8…`;
  - package manifests `15c4114d…` and `64c03667…`;
  - the PACKAGE-CHECK hashes, or a statement that they are unbound (R33-12).
- **Run set:** the selector code hash, the run-set manifest hash, and the definition of the controls.
- **Harness:**
  - the new scorer, runner, converter, ingestion and tests;
  - any `score_bcr` change;
  - the concentration decision (C-4).
- **Caps:** B 240, C 240, R 40, P 36, at most 556. These are consistent with a run set of 30 or fewer.
- **Authorization:** an owner authorization for provider use, budget and ledger scope that names the declaration hash.

## 6. Remaining gates before a live run

1. **C-1 to C-8 met and independently verified:**
   - reviewed-2 package frozen;
   - harness correction frozen and tested;
   - evaluator test done.
2. **Owner: the AI-ACCURACY-POLICY §8 resolution** (R33-02).
3. **Owner, with an independent review: the concentration-rule decision** (R33-01).
4. **Owner: the provider-use permission for EP-3563, 22349, 27331, 15744, 26687 and 29255.** A-02 covers access, staging, drafting and preparation only.
5. **Owner: the final fresh live-validation declaration** (bindings, scopes, caps 240/240/40/36, stop rules).
6. **Owner: the model-request budget (at most 556) and an experiment ledger scope.** None exists today; the ledger stands at 483 entries and 17 scopes.
7. **Owner, only if an extension is ever needed:**
   - alternates for capacity (A-02 open point);
   - the extension-1 shortfall rule.
8. **Owner, optional:**
   - confirm the consent scope and that Claude agents may read the images (R33-15);
   - confirm or object to the parallel batch reviewers (R33-20);
   - preserve A-03 verbatim.
9. **Process:** R33-CRITIC, R33-FINAL and R33-VERIFY complete. The orchestrator records ORCH-006.

## 7. Statuses (stated separately)

| Status | State |
|---|---|
| **Source permission and verification** | A-02 (owner, 2026-10-02 18:55Z) grants metadata discovery, download, staging, rendering, and label drafting and preparation for the six projects. Provider or model use is **not granted**. Verification: 10 of 10 pass with no replacement. The 72 originals are unchanged by `os.stat`, and their staged copies are hash-bound. |
| **Label drafting** | `r32-labels-draft-1` (`ebd1e24d…`) is complete and frozen. It is AI-drafted. |
| **Independent label review** | Complete and frozen: final `920a21d6…`, applied as `r32-labels-reviewed-1` (`00e53e82…`). It is an owner-delegated independent Claude AI review, not human sign-off. 0 of 98 sampled rows were refuted. Escalations D-004 and D-005 are ruled here, and `r32-labels-reviewed-2` is **pending** (C-1). |
| **Field populations** | Reviewed-1: identity 57, revision 38, decision 38, with F069 and F019 excluded. After reviewed-2: **57/39/38**. 0 extensions. |
| **Preparation gate** | Pool gate (each field at least 12) met. Review 33 draft verdict: **PREPARATION ACCEPTED WITH CONDITIONS** (C-1 to C-8), pending CRITIC and FINAL. |
| **Live-run authorization and budget** | **Not authorized.** No provider use, budget, ledger scope or use of the 556 ceiling. The AI ledger is unchanged at 483 entries and 17 scopes. |
| **M2** | **CHANGES STILL REQUIRED.** |
| **M3** | **Not started.** |

## 8. Independence statement

**Review 33 agents.** Each is a fresh, isolated Claude agent under A-03. The model and effort for R33-D1 to R33-D4 are as self-reported in their reports.

| Agent | Task | Model / effort | Mode |
|---|---|---|---|
| R33-D1 | ORCH-03.1/D1: integrity and bindings | Claude Opus 5.5 (`claude-opus-5-5`) / High | read-only; wrote `dimensions/D1-*` |
| R33-D2 | ORCH-03.1/D2: cohort, authority and process | Claude Opus 5.5 / High | read-only; wrote `dimensions/D2-*` |
| R33-D3 | ORCH-03.1/D3: label truth and escalations (image-based) | Claude Opus 5.5 / High | read-only; wrote `dimensions/D3-*` |
| R33-D4 | ORCH-03.1/D4: population, gate and harness | Claude Opus 5.5 / High | read-only; wrote `dimensions/D4-*` |
| R33-SYNTH | ORCH-03.2: synthesis and this draft | Claude Opus 5.5 (`claude-opus-5-5`) / High | read-only; wrote this file, `FINDINGS.json` and `ESCALATION-RULINGS.json` |
| R33-CRITIC | ORCH-03.3: adversarial critique (pending) | Claude Opus 5.5 / High; a different fresh agent | planned |
| R33-FINAL | ORCH-03.4: dispositions and final verdict (pending) | Claude Opus 5.5 / High; a different fresh agent | planned |
| R33-VERIFY | ORCH-03.5: mechanical check (pending) | fresh read-only agent; session model | planned |

**Rule.** No Review 33 agent may be:
- the drafter of `r32-labels-draft-1`;
- any label reviewer (R32REV-B1 to B7, CONSOLIDATE, CRITIC, DISPOSE);
- the implementer (R32APPLY-*);
- the orchestrator.

**My own position.** I, R33-SYNTH, am none of these. I did not open:
- the drafter's folder `C:/t/iso/work/r2x/r32` or the implementer's folder `C:/t/iso/work/r2x/r32b`;
- any arm output or replay;
- the contents of the r26.2 labels;
- any OneDrive file;
- any database other than the AI ledger, which I read with `mode=ro`;
- any candidate or baseline source.

I made no network request, no provider or model request and no prediction. I wrote only the three files named above and scratch files in my scratchpad (`r33-synth/`: a recount script and two zoom derivatives, which are not evidence).

**What independence rests on.** For the other agents it rests on their self-reports and the orchestrator's records. Transcripts are not available to me.
