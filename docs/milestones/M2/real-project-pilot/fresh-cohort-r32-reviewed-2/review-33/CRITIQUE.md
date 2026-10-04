# Review 33 adversarial critique (R33-CRITIC)

- **Task:** ORCH-03.3. **Agent:** R33-CRITIC, Claude Opus 5.5 (`claude-opus-5-5`), effort High. This is a fresh, isolated agent. It is not R33-D1 to R33-D4, not R33-SYNTH, not the drafter, not any R32REV-* label reviewer and not any R32APPLY-* agent.
- **Of:** `INDEPENDENT-REVIEW.draft.md` (sha256 `06537a553b9c12429dca02e4173ef6f73761baf5e4deb230c3355973a8b7cb40`), `FINDINGS.json` and `ESCALATION-RULINGS.json`. The machine-readable form of this critique is `CRITIQUE.json`.
- **Nature:** this is an owner-delegated independent Claude AI review. It is **not** human sign-off. It approves and authorizes nothing.
- **Standing status:** M2 is **CHANGES STILL REQUIRED**, and M3 has **not started**.

## Result

| | |
|---|---|
| Verdict challenged | **No.** PREPARATION ACCEPTED WITH CONDITIONS fits the NEXT-BOUNDED-TASK definitions. There are 0 blockers, and every major is remedied by a condition to meet before the declaration. |
| Disagreements | 13 |
| Material | 5 (C-001 to C-005) |
| Escalation ruling challenged | **D-005**: AMBIGUOUS instead of PRESENT '00' (C-001). D-004 is confirmed, but its basis should be restated (C-007). |
| Count challenged | Revision after reviewed-2 should be 38, not 39 (C-001). R33-05 should read 25 documents, not 27 (C-003). |
| Authorization check | Nothing in the draft, FINDINGS or ESCALATION-RULINGS authorizes a run, a budget, a ledger scope, a default, M2 acceptance or M3. |

## 1. What I recomputed myself

Everything below was read-only. Scripts and scratch zooms are in my scratchpad `r33-critic/`; they are derivatives, not evidence.

| # | Item | Result |
|---|---|---|
| 1 | Packet manifest `fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json` | `15c4114d…82d0ed`. 110 entries, 0 mismatches, 112 files on disk |
| 2 | Reviewed manifest | `64c03667…31c6`. 45 entries, 0 mismatches, 47 on disk. It binds `package_check_sha256` `7ff3594b…3018`, which equals the file, so the draft's correction of D1-03 is right |
| 3 | review31 manifest | `d5fe1649…c460`. 58 entries, 0 mismatches. DRAFT-DECLARATION.v2 is `19720ad9…8b5d` and BINDING-MANIFEST is `2dfef08e…5fba` |
| 4 | Draft labels, conventions, FROZEN-SELECTION, SOURCE-MANIFEST, CROPS, EVIDENCE-INDEX, RENDERS, AUTHORIZATION, PROJECT-VERIFICATION | `ebd1e24d…a334`, `5c09d4d2…e570`, `bf71779a…5d21`, `951e8697…e259`, `b1760b64…3cd1ff`, `0d0db4f8…08b8`, `175a3a10…e8be`, `fd20167a…721d`, `4cecf2fc…f1c4`. All match |
| 5 | Reviewed labels and FIELD-POPULATION | `00e53e82…7779` and `5b9cf095…4505` |
| 6 | Label-review folder | 23 files: final `920a21d6…4c5b`, consolidated `70f94632…3ff8`, critique `ad6798dc…7eef`, dispositions `e8828bec…30a7` |
| 7 | Response ledger | The whole file (160,093 bytes) hashes to `f0a4ffac…c65b`. The first 156,880 bytes hash to `6e296c28…fa0d4` |
| 8 | Staging | 72 PDFs match their `staged_sha256`, and 149 renders, 149 text layers and 189 crops match EVIDENCE-INDEX: 0 mismatches. The byte-identical groups are exactly [F038, F052] and [F067, F070] |
| 9 | Populations (my own script) | Raw yes/yes is 59/40/39. Counted after aliases it is **57/38/38**. `resolved_for_scoring` yes is 67/64/69. Unresolved: F069 identity and F019 revision. Document/page consistency over 216 document-fields: 0 exceptions |
| 10 | Strata and projects | Decision: review_signal 37, other 1 (F072). Identity: 36/16/5. Revision: 29/8/1. Decision by project: 27331 12, 3563 11, 29255 10, 26687 3, 22349 2 |
| 11 | Document-level resolution mappings | "Any field yes" gives 57/38/38, "no field unresolved" gives 56/38/37, and "all fields yes" gives 50/37/32. All three equal R33-05 |
| 12 | Mixed pages | 30 non-scorable rows (21 present+uncertain, 6 ambiguous, 3 excluded) on 30 pages in **25** documents, not 27 |
| 13 | Corrected and resubmission rows | 47 rows ruled `correct`; 9 rows with `resubmission_required` |
| 14 | Extension capacity, from FROZEN-SELECTION rules and the 302-path order | Extension 1 (cap 18 per project) gives 6+6+6+6+5+5 = **34**. Extension 2 (cap 24) gives 6+6+6+4 = **22** |
| 15 | AI ledger (`mode=ro`, `uri=True`) | entries 483, scopes 17, limit_amendments 0. Models used in entries: claude-sonnet-5 457, claude-opus-5 5, sonnet 13, blank 8 |
| 16 | OneDrive originals (os.stat only, never opened) | 72 of 72 match `selected_size` and `selected_modified_utc` |
| 17 | Sealed projects | PROJECT-VERIFICATION `sealed_round2` (10 EPs) and review06 ROUND2-SELECTION (34 projects) do not overlap the 6 cohort EPs or the 4 alternates |
| 18 | Git (read-only) | Candidate `a8aacedd…` and baseline `3d5607d9…`: both clean |
| 19 | Pixel comparisons | F001/F031 p1 and p2: 0 px. F046/F059 p1: 1,183 px differ by more than 64 levels, inside x 0.842–0.882, y 0.856–0.911 (a seal outside the title block); the title blocks are identical |
| 20 | Dimension and review files | All 9 dimension-file hashes in the draft's header table match. PACKAGE-CHECK hashes: packet `6be07739…`, reviewed `7ff3594b…`, review31 `301bb051…` |

## 2. Images I re-read (bound evidence)

| Image | What it shows | Verdict |
|---|---|---|
| `renders/F069-p1.png` | Design Sheet, 5-Aug-18, "Refrence : EP-15744", Quotation for Fire Alarm System | CONFIRMED |
| `renders/F069-p3.png` | Design Sheet, 4-Aug-18, "Refrence : EP-15744", Quotation for Emergency Lighting System | CONFIRMED |
| `renders/F062-p1.png` | Transmittal: "Project ID : EP-15744", document no. EP-15744/SM/FAS/201 | CONFIRMED |
| `renders/F068-p1.png` | T&C request form: "Oracle Job No. / OM No." EP-15744. The draft did not re-read this; I did | CONFIRMED |
| `crops/F019-p1-0.03_0.84_0.2_1-r90.png` | DATE 09-05-16, DWG. NO FAM-PIV-MAH-SPD-FA-2633-007, "Rev. no." 00 | CONFIRMED |
| `crops/F019-p1-0.38_0.86_0.44_0.99-r90.png`, plus a scratch rotation of `renders/F019-p1.png` | REV 01 09-05-16 AS PER CONSULTANT COMMENTS; REV 00 05-03-16 ISSUED FOR APPROVAL | CONFIRMED |
| `crops/F043-p2-0_0_0.2_1-r270.png` | "…ANNEXURE B - Rev. 0 -DATE:5-3-2014" running header (D-003) | CONFIRMED |
| `crops/F014-p1-0.84_0.02_1_0.35.png` | Civil Defence approved-plans stamp; the yellow "APPROVED" box is separate | CONFIRMED |
| `crops/F035-p3-0.15_0.52_0.95_0.75.png` | Handwritten mixed outcome ("delapidated" as written); an ambiguous row | CONFIRMED |
| `crops/F029-p1-0.08_0.08_0.6_0.13.png` | "Reply to comments for SCS Rev.00", Reference …-018-R00 ((g2) applies) | CONFIRMED |
| `crops/F072-p1-0.12_0.8_0.9_0.84.png` | "C - Revise & Resubmit" ticked (the only "other"-stratum decision) | CONFIRMED |
| `crops/F027-p1-0.35_0.85_0.66_1.png` | du "No Objection" Building NOC, signed | CONFIRMED |
| `crops/F012-p1-0.8_0.89_0.92_0.94.png` | "FAM-PIV-MAH-SPD-FA-2633-007 A", DATE 09-05-16, Rev. no. 01 | CONFIRMED |

The F012 row is used only as cross-document context for C-001, never as F019 label evidence. No REFUTED label row exists in the draft or in D3, so there is no REFUTED row to re-examine. I re-examined the count-affecting corrected rows (D-003 on F043) and both escalations instead.

## 3. Material disagreements

### C-001: D-005 should be AMBIGUOUS, not PRESENT "00"

**The draft's position.** Frozen section 4 makes the cell the primary source, so the frozen text decides on "00". Revision becomes 39.

**My position.**
- **The frozen text points to ambiguous.** Section 4 names as primary source "the page's own **current** revision, from its revision cell". On F019 p1 the table's latest row (01, 09-05-16) carries the same date as the title-block DATE (09-05-16). So the page does not establish that the cell is current. That is the frozen section 2 definition of `ambiguous` ("which of several candidates is the field cannot be established from the page"), and it needs no topic (i).
- **Earlier reviewers agree.** The R32 disposer wrote: "The image does not settle which revision is current." The draft itself calls "01" plausible.
- **The cost is lopsided.** Under the frozen stop rules, a critical acceptance on **resolved** truth makes B terminal (comparison INVALID) or C terminal ("candidate failed the safety gate"). On unresolved truth it is only reported. Revision is a critical field (AI-ACCURACY-POLICY: "Verify critical identity/revision/decision facts").
- **Nothing is gained at the gate.** Revision is 38 either way, which is at least 12. F019 also carries a counted decision, so it will likely enter the run set.

**Consequence if adopted:**
- D-005 is AMBIGUOUS, with candidates 00 and 01, excluded;
- F019 revision is no/no;
- **reviewed-2 expects 57/38/38**;
- PRESENT "00" stays as the owner alternative.

### C-002: R33-02 and C-3 must name the same-family risk

The AI ledger shows that the system under test used Claude models: claude-sonnet-5 457 entries, claude-opus-5 5, sonnet 13. Every label agent so far is Claude Opus 5.5: the drafter, B1 to B7, the consolidator, critic and disposer, D1 to D4, the synthesiser and this critic. Policy section 8 ("not … approved solely by another model") bites hardest when labeller and predictor share a family, because correlated misreadings hide the critical false acceptances that the zero-critical gate is meant to catch.

D3's check is a same-model re-read of about 46 of roughly 382 accept rows. With 0 refuted, the 95% upper bound is about 6.5%.

**C-3 should:**
1. state this fact to the owner;
2. recommend a human check of every page-field row that will be scored in the frozen run set (at most 30 documents and 120 pages), after the selector freezes and before B, with a waiver only as the fallback;
3. have the declaration state the assurance level.

### C-003: R33-05's document count is wrong

There are 30 pages, as the draft says, but in **25** documents, not 27: F002, F003, F004, F005, F006, F007, F008, F011, F013, F015, F019, F020, F024, F025, F028, F029, F030, F032, F034, F035, F036, F037, F043, F067 and F069. Each such page has exactly one non-scorable field.

### C-004: two declaration bindings are missing

1. **Project AI policies.** AI-ACCURACY-POLICY section 7 requires the record to hold "project AI policies" and the run to use "project-policy-eligible documents". No dimension and not the draft checks or binds these for the six EPs. The live application database holds none of these projects, so the sandbox policy must be declared.
2. **The policy hash.** BINDING-MANIFEST binds AI-ACCURACY-POLICY.md at `7efa891b…`. A section 8 amendment would change that hash, and the preflight refuses on any difference, so the policy must be re-bound.

Also, the expected-use estimates (B about 6, C about 135) were four-arm based and must be re-estimated for the r32 run set.

### C-005: Review 33 should rule count-once (c)(ii)

The draft accepts 57/38/38, but C-2 leaves "revert to 59/40/39" open. NEXT-BOUNDED-TASK requires rulings on the carried-over items, and Review 33 ruled D-004 and D-005 with the same authority. It should rule (c)(ii) **adopted** for this cohort, with the F031 p3 caveat, and C-2 becomes a recording step. The pixel evidence supports this: 0 px for F001/F031, and only an out-of-title-block seal for F046/F059. Otherwise the accepted populations must be stated conditionally.

## 4. Non-material disagreements

| ID | Target | Point |
|---|---|---|
| C-006 | R33-01 | `score_bcr.evaluate` pools all fields' reasons into **one** outcome. The stratum leg therefore makes the whole candidate NOT ELIGIBLE whenever C improves decision, not just "decision". C-4's owner card should say so |
| C-007 | D-004 basis | The outcome (AMBIGUOUS) is right. But the basis uses F062/F068 to exclude "present" while refusing the same kind of evidence ((h2)) to reach "absent". Restate the basis on the page alone |
| C-008 | D-005 row | The region `[0.04,0.86,0.43,0.99]` spans both the cell and the table. A present row should carry the cell's region. Moot if C-001 is adopted |
| C-009 | Draft section 2 | The CROPS abbreviation "…1cd1ff" should be "…3cd1ff". The file itself matches |
| C-010 | Verdict | The "verdict rule" quoted in section 1 is not found in any readable file. R33-FINAL should cite it. The verdict holds under the NEXT-BOUNDED-TASK definitions |
| C-011 | R33-20 / section 8 | Review 33's own D1 to D4 also wrote in parallel. Disclose this together with R33-20 |
| C-012 | R33-21 | Add M2-REVIEW-RESPONSE.md lines 1070 and 1098 (append-only mentions of Codex) |
| C-013 | Reliance on D2 | D2's abbreviations for the conventions (…8570) and the review31 manifest (…7460) are wrong and repeat ORCH-001's typos. The files are intact, but D2's recomputation claims are not fully demonstrated |

## 5. Missing checks

| ID | Check | Status |
|---|---|---|
| M-001 | Project AI policies and eligibility of the six EPs | Missing (C-004), material |
| M-002 | Labeller against the evaluated model's family | Missing (C-002), material |
| M-003 | Contested resolved rows against the terminal stop rules | Missing (C-001), material |
| M-004 | Re-binding the policy hash and re-estimating expected use | Missing (C-004) |
| M-005 | Other run-control ledgers (stat only) | Done by me. `project-day.sqlite` and `doc-allowance.sqlite` mtimes are unchanged since 2026-10-01 22:17 +04, and `runs/` since 21:51 +04. This supports "no run" |
| M-006 | Sealed projects, independent of D2 | Done by me: CONFIRMED |
| M-007 | OneDrive originals, independent of D1 | Done by me: CONFIRMED, 72 of 72 |
| M-008 | Source of the verdict rule | UNVERIFIABLE (C-010) |
| M-009 | Disclosure of Review 33's own parallel writers | Missing (C-011) |

## 6. Checks where I agree with the draft

- **Integrity:** every named binding recomputes.
- **Staging:** fully bound.
- **Populations:** the recount is 57/38/38 (raw 59/40/39).
- **Consistency:** document level agrees with page level everywhere.
- **D-004:** AMBIGUOUS, with no count effect.
- **Carried-over items:** D-003, the byte-identical aliases and the "- R0n" non-counting are all right.
- **Extension capacity:** 34 of 36 and 22 of 36.
- **Universe:** 3,046 PDFs, of which 2,585 are eligible, against 2,455 in Review 31. The feasibility basis is superseded by the actual counts.
- **Ledger:** unchanged at 483/17/0.
- **No authorization:** nothing in the draft authorizes a provider or model request, a B/C/R/P run, the 556 ceiling, a ledger scope, alternates for capacity, a default, M2 acceptance or M3.
- **The majors:** R33-01 to R33-09 are majors on their merits. None is a blocker to accepting the preparation itself.

## 7. Independence and limits

**What I did not open:**
- the drafter's folder `C:/t/iso/work/r2x/r32` or the implementer's folder `r32b`;
- any arm output, replay or `C:/t/r2x/runs` content;
- the r26.2 labels or `LABELS-NORMALISED.json` rows;
- any OneDrive file (stat only);
- any database other than the AI ledger (read-only URI);
- any candidate or baseline source (git `rev-parse` and `status` only).

**What I did not do:** I made no network, provider or model request and no prediction. I ran no package script.

**What I wrote:** only `CRITIQUE.json` and this file in the review folder, plus scratch files in my own scratchpad.

**Limits:** file names were not used as evidence. Independence rests on my own context. Transcripts of the other agents are not available to me.
