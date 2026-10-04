# Independent M2 Preparation Review 33 (FINAL)

- **Task:** ORCH-03.4, dispositions of the critique and the final verdict.
- **Agent:** R33-FINAL, Claude Opus 5.5 (`claude-opus-5-5`), effort High. A fresh, isolated agent, different from R33-D1 to D4, R33-SYNTH and R33-CRITIC.
- **Authority:** A-03, the owner's 2026-10-03 decision on a Claude-only workflow.
- **Date:** 2026-10-03.
- **Nature of this review:** an owner-delegated independent Claude AI review. It is **not** human sign-off. It does **not** authorize a live run, a budget, a ledger scope, a default variant, M2 acceptance or M3. Nothing here approves or self-approves anything.
- **Standing status:** M2 is **CHANGES STILL REQUIRED**. M3 has **not started**.

**Built from** (sha256 recomputed by R33-FINAL):

| File | sha256 |
|---|---|
| `INDEPENDENT-REVIEW.draft.md` (R33-SYNTH) | `06537a553b9c12429dca02e4173ef6f73761baf5e4deb230c3355973a8b7cb40` |
| `FINDINGS.json` (R33-SYNTH) | `39a40941aed340a65a7555a8e6c3079b51fa67cb567981475cbeba2cca65c49a` |
| `ESCALATION-RULINGS.json` (R33-SYNTH, preserved unedited) | `4deb4bacf81d918568acbb01fd176624a256e99aa1dc834f9973a6063a9557c5` |
| `CRITIQUE.json` / `CRITIQUE.md` (R33-CRITIC) | `8089391e68f77561d7a63cc9f120f1438c806ff8aeb184431be1526443867cc8` / `0175de38059931aac5dceb95056df18aa55396b71a1807f9ae3c22f3c16e4abc` |
| `DISPOSITIONS.json` (R33-FINAL) | `ceb8fdcc6cc3e54219ab22686fc663a66c93ca5ed44316255ddf24745018315b` |
| `ESCALATION-RULINGS.final.json` (R33-FINAL; governs the reviewed-2 application) | `e2fe503d96a3bc08c99ce52862d2017a567f6e2a6677744f43750c5ebc7611a0` |
| `dimensions/` D1 report / findings | `d8003c53…a331` / `f5a8a780…918c` |
| `dimensions/` D2 report / findings | `636719ed…c928` / `ba98df0a…d452` |
| `dimensions/` D3 report / findings / escalation rulings | `e8164fbb…b38b` / `5596a876…4e11` / `4a26e8c6…fb47` |
| `dimensions/` D4 report / findings | `283dd58a…8f50` / `74170a67…b4b1` |

`FINDINGS.json` is the draft's register. The final register of findings is the table in section 3 of this file. Where it differs from `FINDINGS.json`, this file governs.

## 1. Verdict

**PREPARATION ACCEPTED WITH CONDITIONS**

**The verdict rule.** The rule comes from the ORCH-03.4 task instruction issued to R33-FINAL. NEXT-BOUNDED-TASK.md defines the four verdicts but gives no mapping (C-010).
- Any CONFIRMED blocker gives CHANGES REQUIRED or BLOCKED BY MISSING EVIDENCE.
- CONFIRMED majors allow at most PREPARATION ACCEPTED WITH CONDITIONS, with each condition named.
- Otherwise the verdict is PREPARATION ACCEPTED.

**How the verdict follows from the rule:**
- There are **0 blockers**.
- There are **10 majors**. Nine are CONFIRMED (R33-01 to R33-08 and R33-30), and one is UNVERIFIABLE (R33-09).
- So the ceiling is PREPARATION ACCEPTED WITH CONDITIONS, and each condition is named below.
- No major shows that the frozen cohort, the staged evidence, the page-level label truth or the counts are wrong:
  - every binding recomputes;
  - a stratified image check of 98 items refuted 0 rows;
  - the populations recount exactly.
- The majors concern four things:
  - rulings that must be applied mechanically;
  - convention amendments that must be recorded;
  - two owner-only policy decisions (§8 and the concentration rule) and one unchecked policy prerequisite (project AI policies);
  - harness and declaration work that must exist before any declaration.
- The critic did not challenge the verdict category. The dispositions do not change it.

**What this verdict accepts.** Each item is accepted as frozen, subject to the conditions:
- the verified six-project cohort and the frozen 72-file pool;
- the staged evidence (72 PDFs, 149 renders, 189 crops, hash-bound);
- `r32-labels-draft-1` and its independent Claude review;
- the application of that review as `r32-labels-reviewed-1`;
- the counted populations, **identity 57, revision 38, decision 38**. These counts stand under this review's ruling that adopts count-once (c)(ii) for the content duplicates F031→F001 and F059→F046 (section 4). They are unchanged after `r32-labels-reviewed-2`, which leaves nothing unresolved.
- the pool-level gate (each field at least 12), which is met with 0 extensions under every option in section 4.

**Conditions to meet before any declaration** (each linked to its finding):

| # | Condition | Finding |
|---|---|---|
| C-1 | Apply the final D-004 and D-005 rulings and the carried-over recordings (section 4) mechanically as **`r32-labels-reviewed-2` in a new package**, with its own manifest, a recount and a new FIELD-POPULATION. The expected counts are **57/38/38**, with no unresolved rows. The row list is in section 4.4. `r32-labels-draft-1` and `r32-labels-reviewed-1` stay unchanged. If the owner instead takes an alternative in section 4, the alternative rows apply. | R33-03 |
| C-2 | Record in reviewed-2 and in the declaration's amendment and interpretation list: count-once (c)(ii), ruled ADOPTED here as an amendment to convention section 1 with the F031 p3/p4 caveat; (d1); (e)/D-001; (g)(1); (g2)/D-002; (h)/D-003; (d2); (f); and the page-specific D-005 reading of sections 2 and 4. | R33-04, R33-11 |
| C-3 | **Owner only.** Resolve AI-ACCURACY-POLICY §8 for this run. §8 forbids gold labels "approved solely by another model". Every label agent is Claude Opus 5.5, and the evaluated extraction requests in the AI ledger are also Claude (`claude-sonnet-5` 457, `claude-opus-5` 5, `sonnet` 13, blank 8). The two routes are below. Whichever route is taken, the declaration states the assurance level (C-7). | R33-02 |
| C-4 | **Owner, with an independent review.** Decide the stratum leg of the concentration rule and freeze the choice. Whatever the choice, the adapter must populate `stratum`. | R33-01 |
| C-5 | A correction task, with tests and a re-freeze, delivers the harness adapter in section 5.1: per-field resolution and page-field exclusion, an r32 lane scorer and live runner, a converter, B-sandbox ingestion, and a run-set selector with defined unsupported controls and canonical ids only. | R33-05, R33-06, R33-07 |
| C-6 | An offline test of evaluator .10 against the converted r32 labels, with zero model calls, covering each comparison rule named in R33-09. Any evaluator change is a separate candidate correction. | R33-09 |
| C-7 | A new declaration that replaces the stale DRAFT-DECLARATION.v2 bindings and adds the new ones (section 5.2), written only after C-1 to C-6 and C-9 are frozen. | R33-08, R33-30 |
| C-8 | The minor findings' disclosures (R33-10 to R33-22) are carried into the declaration or into append-only addenda. | R33-10 to R33-22 |
| C-9 | Check and record the AI policy and eligibility of EP-3563, 22349, 27331, 15744, 26687 and 29255 (AI-ACCURACY-POLICY §7), and bind the record. Where a project has no policy, the owner states one. | R33-30 |

**The two routes for C-3:**
- **(a) Human check.** A human check against the originals of every page-field row that will actually be scored in the frozen run set: at most 30 documents and at most 120 pages, done after the selector freezes and before B runs. This is the only route that satisfies §8 as written.
- **(b) Amendment or waiver.** An append-only owner amendment or waiver of §8 for this run. The policy hash must then be re-bound (C-7).

**What this verdict does NOT authorize:**
- any provider or model request;
- any B, C, R or P validation run, or any prediction;
- any model-request budget, any use of the 556 ceiling, or an experiment ledger scope;
- alternates for extension capacity;
- a default extraction variant;
- M2 acceptance or M3;
- any change to frozen packages, labels, production data or OneDrive originals;
- any claim of human sign-off.

The rulings in section 4 are this review's rulings, not owner decisions.

## 2. Evidence checked

**Recomputed by R33-SYNTH and re-recomputed by R33-FINAL.** All of the following match the frozen values.

| Item | Result |
|---|---|
| Packet manifest `fresh-cohort-r32/evidence/EVIDENCE-MANIFEST.json` | `15c4114d…82d0ed`. SYNTH: 110 entries, 0 mismatches; 112 files on disk (the manifest and PACKAGE-CHECK are unlisted) |
| Reviewed manifest | `64c03667…31c6`. SYNTH: 45 entries, 0 mismatches; it binds `package_check_sha256` |
| review31 manifest | `d5fe1649…c460`. SYNTH: 58 entries, 0 mismatches |
| Draft labels / conventions / FROZEN-SELECTION | `ebd1e24d…a334` / `5c09d4d2…e570` / `bf71779a…5d21` |
| SOURCE-MANIFEST / CROPS / EVIDENCE-INDEX | `951e8697…e259` / `b1760b64…3cd1ff` / `0d0db4f8…32ba08b8` (CROPS abbreviation corrected, C-009) |
| RENDERS / PROJECT-VERIFICATION / AUTHORIZATION | `175a3a10…e8be` / `4cecf2fc…f1c4` / `fd20167a…721d` (SYNTH) |
| Reviewed labels / FIELD-POPULATION | `00e53e82…7779` / `5b9cf095…4505` |
| Label review folder (23 files, counted by R33-FINAL) | final `920a21d6…`, consolidated `70f94632…`, critique `ad6798dc…`, dispositions `e8828bec…` |
| DRAFT-DECLARATION.v2 / AI-ACCURACY-POLICY.md | `19720ad9…8b5d` / `7efa891b…4f47` |
| `score_bcr.py` (review31 harness) | `5a3828a5…7d1a` (R33-FINAL, read only) |
| Response ledger `M2-REVIEW-RESPONSE.md` | whole file `f0a4ffac…c65b`; first 156,880 bytes `6e296c28…fa0d4` |
| Staging `C:/t/r2x/r32-stage` | 72 files, 149 render PNGs and 189 crops (counted by R33-FINAL). SYNTH re-hashed these against SOURCE-MANIFEST and EVIDENCE-INDEX: 0 mismatches |
| AI ledger (`mode=ro`, `uri=True`, by R33-FINAL) | 483 entries, 17 scopes, 0 limit amendments. Models: `claude-sonnet-5` 457, `sonnet` 13, blank 8, `claude-opus-5` 5 |
| Other run-control state (stat only, R33-FINAL) | `project-day.sqlite` 2026-10-01 22:17:43, `doc-allowance.sqlite` 22:17:50, `r2x-ledger.sqlite` 22:17:50, `C:/t/r2x/runs` 21:51:11 (+04). Nothing has changed since the four-arm run |

**Counts (R33-FINAL's own script over reviewed-1).**
- Raw yes/yes is 59/40/39.
- After the aliases F031→F001, F052→F038, F059→F046 and F070→F067, the counts are **57/38/38**.
- With the final rulings applied, the counts are still **57/38/38**.
- The owner alternatives give:
  - D-005 present: 57/39/38;
  - no (c)(ii): 59/40/39;
  - both: 59/41/39.
- `resolved_for_scoring` yes is 67/64/69.
- Page level and document level agree everywhere (SYNTH, and the FIELD-POPULATION consistency check).

**By stratum and project** (unchanged by the final rulings):

| Field | review_signal | drawing_signal | other |
|---|---|---|---|
| Decision | 37 | 0 | 1 (F072) |
| Identity | 36 | 16 | 5 |
| Revision | 29 | 8 | 1 |

Decision documents by project: 27331 12, 3563 11, 29255 10, 26687 3, 22349 2, 15744 0.

**Non-scorable rows (R33-FINAL).** 30 page-field rows on 30 pages in **25** documents: F002, F003, F004, F005, F006, F007, F008, F011, F013, F015, F019, F020, F024, F025, F028, F029, F030, F032, F034, F035, F036, F037, F043, F067 and F069. Each of these pages also has a scorable field. The rows are:
- 21 present with association uncertain;
- 7 ambiguous, including F019 p1 revision, which is also excluded;
- 2 F069 rows that are present but excluded.

**Images read** (bound evidence; zooms and rotations are scratch derivatives, not evidence):
- **R33-SYNTH:** `renders/F069-p1.png`, the header of `renders/F069-p3.png`, `renders/F062-p1.png`, the two F019 crops below, and `renders/F019-p1.png`.
- **R33-CRITIC:** `renders/F069-p1.png`, `F069-p3.png`, `F062-p1.png` and `F068-p1.png`, the F019 crops, and a rotation of the F019 render.
- **R33-FINAL:**
  - `crops/F019-p1-0.03_0.84_0.2_1-r90.png` ("Rev. no." 00, DATE 09-05-16);
  - `crops/F019-p1-0.38_0.86_0.44_0.99-r90.png`;
  - a scratch rotation of `renders/F019-p1.png`, showing REV 01 09-05-16 AS PER CONSULTANT COMMENTS and REV 00 05-03-16 ISSUED FOR APPROVAL;
  - `renders/F031-p3.png`, a Comments Resolution Sheet with Submittal No. MAT – 116 and Rev. 02.

**Pixel comparisons** (R33-FINAL, repeating SYNTH and CRITIC):
- F001-p1 against F031-p1, and F001-p2 against F031-p2: 0 differing pixels.
- F046-p1 against F059-p1: 1,183 pixels differ by more than 64 grey levels, all inside x 0.842–0.882, y 0.856–0.911.

**Relied on from the dimensions and the critic, not repeated by R33-FINAL:**
- OneDrive `os.stat` for 72 of 72 files (D1, and independently CRITIC M-007).
- `git rev-parse`/`status` for candidate `a8aacedd` and baseline `3d5607d9`, both clean (D1, D4).
- The modification-time cutoff and the network-code census (D1, D2).
- The rebuild and the 21 packaged tests (D1).
- The 98-item stratified image check (D3).
- The harness source reading and the Monte Carlo of the run set (D4).
- The sealed projects being disjoint from the cohort (D2, and independently CRITIC M-006).
- **Reduced weight on D2-only items** (C-013). D2's report abbreviates the conventions as `…8570` and the review31 manifest as `…7460`, and DECISION-LEDGER ORCH-001 has the same two typos. The true hashes end `…e570` and `…c460`, and the files are intact. So D2's selection order-key recomputation, authority timeline and database counts are treated as reported, not as independently demonstrated.

**Correction to a dimension (kept from the draft).** D1-03 said PACKAGE-CHECK.json is unbound in all three packages. That is refuted for the reviewed package, whose manifest binds it. It still holds for the packet and for review31 (R33-12).

## 3. Findings (final register)

There are 0 blockers, 10 majors, 13 minors and 7 info findings. Evidence for R33-01 to R33-29 is in `FINDINGS.json`. The changes made by the dispositions are marked †.

| ID | Sev. | Verdict | Finding | Required action |
|---|---|---|---|---|
| R33-01 † | major | CONFIRMED | The stratum leg of the concentration rule makes decision ELIGIBLE unreachable: 37 of the 38 decision documents are review_signal. It very likely fires for identity (36/57) and revision (29/38) as well. `score_bcr.evaluate` puts every field's concentration flag into one `reasons_not_eligible` list and sets one outcome, so a concentrated gain in any field makes the **whole comparison** NOT ELIGIBLE. C can then be ELIGIBLE only if it does not improve decision, except for a net gain of 2 split 1/1 with F072. If `stratum` is missing, every document falls into one bucket. | C-4 |
| R33-02 † | major | CONFIRMED | AI-ACCURACY-POLICY §8 conflicts with gold labels that were drafted and reviewed by Claude only, and no authority entry addresses it. The labeller and the evaluated model are from the same family: the ledger's evaluated requests are Claude Sonnet 5 and Opus 5, and every label agent is Claude Opus 5.5. Shared reading errors could inflate agreement and hide critical false acceptances. The D3 check (0 of 98 refuted) is a same-model re-read of a sample. | C-3 (owner) |
| R33-03 † | major | CONFIRMED | D-004 and D-005 are open in reviewed-1, where F069 p1/p3 are stored as `present` EP-15744. Both are now ruled AMBIGUOUS (section 4). | C-1 |
| R33-04 † | major | CONFIRMED | Count-once for content duplicates ((c)(ii)) is not covered by frozen section 1, which covers byte-identical files only. This review rules it ADOPTED as an amendment for this cohort. It must be recorded. Without it the counts would be 59/40/39. | C-2 |
| R33-05 † | major | CONFIRMED | `score_bcr` has no per-field resolution and no page-field exclusion, and it reads None as "absent". 30 pages in **25** documents mix scorable and non-scorable fields. | C-5 |
| R33-06 | major | CONFIRMED | `score_lane` and `run_lane` are bound to the four-arm run and r26.2. There is no live runner, converter or ingestion. | C-5 |
| R33-07 | major | CONFIRMED | No run-set selector exists, the unsupported controls are undefined, and an alias could be drawn twice. | C-5 |
| R33-08 | major | CONFIRMED | DRAFT-DECLARATION.v2 is stale on 10 points and has no r32 bindings. | C-7 |
| R33-09 | major | UNVERIFIABLE | It is unknown whether evaluator .10 handles whitespace, dashes, Arabic text, compilations and resubmission tolerance. | C-6 |
| R33-30 † (new) | major | CONFIRMED (eligibility itself UNVERIFIABLE) | AI-ACCURACY-POLICY §7 requires the record to hold "project AI policies" before execution and requires "project-policy-eligible documents". No package, plan, review or authority checks or binds the six projects' AI policy, and ORCH-001 records that the live application database holds none of them. The policy file is bound by hash (`7efa891b…`) in BINDING-MANIFEST and DRAFT-DECLARATION.v2. A §8 amendment would therefore break the preflight unless the policy is re-bound. The expected-use figures come from the four-arm sample. | C-9, C-7 |
| R33-10 | minor | CONFIRMED | The run-time matched margin is about 4 for decision and revision. | Disclose |
| R33-11 † | minor | CONFIRMED | (d1), (e)/D-001, (g)(1), (g2), (h)/D-003, (d2), (f) and the D-005 page reading are not recorded as amendments or interpretations. | C-2 |
| R33-12 | minor | CONFIRMED | PACKAGE-CHECK is unbound in the packet and in review31. | Bind or disclose |
| R33-13 | minor | CONFIRMED | The 149 words.json files are unbound. | Disclose |
| R33-14 | minor | UNVERIFIABLE | The packet verifier ran the validator from the drafter's folder. | Re-run from the packaged copy |
| R33-15 | minor | CONFIRMED | The wording of the consent record and A-03 is not verbatim, and it does not cover Claude agents reading the images. | Owner confirmation |
| R33-16 | minor | CONFIRMED | 930 databases were read against 959. | Disclose or list |
| R33-17 | minor | CONFIRMED | The extension order uses the pool seed, not the declared extension seeds. | Disclose and bind |
| R33-18 | minor | CONFIRMED | The new duplicate rule leaves 68 distinct documents. | Disclose |
| R33-19 | minor | CONFIRMED | There is a latent conflict over alternates for capacity. | Owner, only if needed |
| R33-20 † | minor | CONFIRMED | Parallel writers: the seven R32 batch reviewers (04:49:51–05:11:01Z), and Review 33's own D1–D4, which each wrote only their own `dimensions/` files in overlapping windows between 10:58 and 11:17 (+04). Both rely on the orchestrator's interpretation of A-03. | Owner confirms or objects |
| R33-21 † | minor | CONFIRMED | A-03's list of documents naming Codex is incomplete. Add the append-only response ledger `M2-REVIEW-RESPONSE.md` lines 1070 and 1098 to D2-16's list. | Declaration and an optional note |
| R33-22 | minor | CONFIRMED | The opening of the r26.2 labels after the freeze is not disclosed. | Append-only disclosure |
| R33-23 | info | CONFIRMED | Integrity and bindings hold. | — |
| R33-24 | info | CONFIRMED | A-02 scope was respected, and the originals are hydrated but unchanged. | — |
| R33-25 | info | CONFIRMED | Verification and selection conform. The universe is 3,046 against 2,455, and extension capacity is 34/36 and 22/36. | Disclose |
| R33-26 † | info | CONFIRMED | 98 items were image-checked and 0 rows refuted. This was a same-model sample re-read: AI-made, not human-signed, and not independent of the model family under test. | Disclose that it is a sample (and see C-3) |
| R33-27 † | info | CONFIRMED | The recount gives 57/38/38, consistent with the page labels and unchanged by the final rulings. | — |
| R33-28 | info | CONFIRMED | The A-03 process was followed. The CRITIC entry is missing from the agents array, and scratch images are cited in notes. | Disclose |
| R33-29 | info | CONFIRMED | The owner-only items listed in section 7 remain. | — |

## 4. Final rulings on the escalations and carried-over items

These are recorded in `ESCALATION-RULINGS.final.json`. The draft `ESCALATION-RULINGS.json` is preserved unedited, and where the two differ the final file governs. **Any row these rulings change must be applied as `r32-labels-reviewed-2` in a new package before any declaration.** `r32-labels-reviewed-1` stays frozen.

### 4.1 D-004: F069 p1 and p3 identity. Ruling: AMBIGUOUS (outcome unchanged; basis restated page-only, C-007)

**Page evidence:**
- **F069-p1:** a "Design Sheet" dated 5-Aug-18 with "Refrence : EP-15744", subject "Quotation for Fire Alarm System".
- **F069-p3:** a second Design Sheet dated 4-Aug-18 with "Refrence : EP-15744", subject "Quotation for Emergency Lighting System".
- Read by D3, SYNTH and CRITIC; CONFIRMED.

**Basis (page only).** The only candidate is EP-15744, printed under the bare label "Refrence".
- Frozen section 3 admits a letter or transmittal reference as identity, but it excludes project and job numbers.
- The page does not say which of these the value is.
- So its role cannot be established from the page, which is frozen section 2's `ambiguous`.
- `absent` would require taking the role from other documents (topic (h2)), which the owner has not adopted.
- F062-p1 ("Project ID : EP-15744") and F068-p1 ("Oracle Job No. / OM No.") are context only. They are not the basis of the ruling.

**Resulting rows (both pages):**
- `state: ambiguous`, `literal: null`;
- candidates [EP-15744, printed label "Refrence", role not established on the page];
- `association: resolved`, `excluded_from_scoring: true`, `review_status: ruled (Review 33, D-004)`;
- other_identities unchanged.

**Document level:** F069 identity becomes `resolved_for_scoring: no`, `carries_fact: no`.

**Count impact:** none. Identity stays 57.

**Owner alternative ((h2) adopted):** `absent`, with EP-15744 in other_identities. F069 identity becomes yes/no, and identity stays 57.

### 4.2 D-005: F019 p1 revision. Ruling: AMBIGUOUS (changed from the draft's PRESENT "00"; DISPOSITIONS D-001)

**Page evidence**, re-read by R33-FINAL:
- The title-block crop shows "Rev. no." 00, DATE 09-05-16 and DWG. NO FAM-PIV-MAH-SPD-FA-2633-007.
- The revision table, read on a rotated render, shows:
  - REV 00 05-03-16 ISSUED FOR APPROVAL;
  - REV 01 09-05-16 AS PER CONSULTANT COMMENTS.

**Basis.**
- **Two candidates.** The page offers two candidates for its own current revision: the cell (00) and the latest table entry (01).
- **The page itself contradicts the cell.** The title block's own DATE (09-05-16) is the date of row 01, not of row 00 (05-03-16). So the page does not establish that the cell holds the current revision.
- **Section 4 does not settle it.** Frozen section 4 says where the current revision is normally read: the cell first, and the table only when it is the only source. It does not resolve a conflict that the page itself exposes.
- **Section 2 applies directly.** Frozen section 2 defines `ambiguous` as a case where "which of several candidates is the field cannot be established from the page". That describes this page. The R32 disposer came to the same factual conclusion: "The image does not settle which revision is current".
- **Page-specific only.** This ruling adopts no general cell-against-table rule (topic (i)).

**Weighting** (critique M-003):
- **Stop-rule risk.** Under the frozen stop rules, a critical acceptance on **resolved** truth makes B terminal with the comparison INVALID, or makes C fail the safety gate. On unresolved truth it is only reported. Making a row this review regards as contested into resolved truth would open a known path to an INVALID comparison.
- **No gain at the gate.** Revision is at least 12 either way.

**Resulting row:**
- `state: ambiguous`, `literal: null`;
- candidates 00 ("Rev. no.", title-block cell) and 01 (latest revision-table entry, 09-05-16 AS PER CONSULTANT COMMENTS);
- `association: resolved`, region [0.04, 0.86, 0.43, 0.99], `excluded_from_scoring: true`, `review_status: ruled (Review 33, D-005)`.

**Document level:** F019 revision becomes `resolved_for_scoring: no`, `carries_fact: no`.

**Count impact:** none. Revision stays **38**.

**Disclosure.** F019 is a decision-bearing document. Its revision is excluded, and the adapter must honour that exclusion field by field (C-5).

**Owner alternative (frozen cell-first order governs):** `present` "00", with the cell's own region (about [0.04, 0.86, 0.06, 0.99], not the spanning region) and not excluded. F019 revision becomes yes/yes and revision becomes 39. The declaration must then name F019 revision as a contested row that falls under the resolved-truth stop rule.

### 4.3 Carried-over convention items

| Item | Page evidence | Final ruling | Rows, document values and counts |
|---|---|---|---|
| Count-once F031→F001 | p1 and p2 renders differ by 0 px (SYNTH, CRITIC and FINAL). F031 p3 is a Comments Resolution Sheet showing MAT – 116 and Rev 02, the same values as F001 (FINAL read). F031 p4 carries no field | **ADOPTED** for this cohort as a Review 33 ruling (C-005 adopted). It is recorded as an amendment to frozen section 1, with the caveat that F031 has pages 3 and 4, which F001 lacks, but adds no field value | No row change; the alias annotation is recorded in reviewed-2. Counts 57/38/38. The owner may reverse it, giving 59/40/39 |
| Count-once F059→F046 | 1,183 px differ by more than 64 levels, only in a seal outside the title block. The title blocks are identical (SYNTH, CRITIC and FINAL) | **ADOPTED**, under the same amendment | Included above |
| Byte-identical F052→F038 and F070→F067 | Identical `staged_sha256` | Frozen section 1 applies | Count once |
| Page-keyed compilations F002, F035, F043 and F069 | Different submittals on different pages (D3) | Required by frozen section 7. D-003 (F043 revision yes/yes) is accepted. The scorer rule must be bound | C-5, C-6 |
| Whitespace-insensitive literals (F023, F067, "- R0n", "FA- 6001", "EM- 104") | Printed spacing (D3) | The labels keep the printed form. Comparison is a scorer rule | C-6 |
| LACASA/Scale "- R0n" suffixes | The suffix is the only revision source (D3) | Not counted (sections 4 and 7). Counting them is an owner convention change | Up to +8 revision only if the owner amends |
| (d1) resubmission_required on mixed options (9 rows) | Marks such as "Approved as noted / Resubmit" and "B+R" (D3) | Defensible. Record it as an amendment and define the scorer tolerance | C-2, C-6 |
| (e)/D-001 F025 Code C "Not Approved (Re-submit…)" | Legend on F025-p1 (D3) | Revise and resubmit is defensible. Record it as an amendment | C-2 |
| (g)(1), (g2)/D-002, (h)/D-003, (d2), (f) | F034-p3, F028-p4, F043 (D3) | Record them as interpretations. D-003 adds 1 to revision (already counted) | C-2 |
| D-005 page-specific reading of sections 2 and 4 | F019-p1 | Record it as an interpretation, not a general topic (i) rule | C-2 |

**Populations after reviewed-2:** identity 57, revision 38, decision 38, with nothing unresolved. The gate (at least 12) is met under every option:
- 57/39/38 with the D-005 present alternative;
- 59/40/39 without (c)(ii);
- 59/41/39 with both.

### 4.4 Row changes that must be applied as `r32-labels-reviewed-2`

The changes are applied mechanically in a new package with its own manifest, recount and FIELD-POPULATION. `r32-labels-draft-1` and `r32-labels-reviewed-1` are not modified.

1. **`F069/p1/identity`:**
   - `state` changes from `present` to `ambiguous`.
   - `literal` changes from `EP-15744` to `null`.
   - Add `candidates` [{literal EP-15744, printed_label "Refrence", role "not established on the page"}].
   - `association` stays `resolved`, and `excluded_from_scoring` stays `true`.
   - `review_status` changes from `unresolved` to `ruled (Review 33, D-004)`.
   - The open question is closed with a reference to this review.
   - `other_identities` is unchanged.
2. **`F069/p3/identity`:** the same changes as row 1.
3. **`F069` document identity:**
   - `resolved_for_scoring` changes from `unresolved` to `no`.
   - `carries_fact` stays `no`.
   - The D-004 open question is marked ruled.
4. **`F019/p1/revision`:**
   - The state stays `ambiguous`, with candidates 00 and 01, and `excluded_from_scoring` stays `true`.
   - `review_status` changes from `unresolved` to `ruled (Review 33, D-005)`.
   - The open question is closed with a reference to this review.
5. **`F019` document revision:**
   - `resolved_for_scoring` changes from `unresolved` to `no`.
   - `carries_fact` changes from `unresolved` to `no`.
   - The F019 `questions` and `unresolved` entries for D-005 are marked ruled.
6. **`escalations[]`** (six entries for D-004 and D-005): each is marked ruled, with this review's final hash and `ESCALATION-RULINGS.final.json`.
7. **`count_once_aliases`:**
   - F031→F001 and F059→F046 are annotated as the Review 33 (c)(ii) ruling (an amendment to section 1), with the F031 p3/p4 caveat.
   - F052→F038 and F070→F067 are annotated as frozen section 1.
8. **An amendment and interpretation list** is added: (c)(ii); (d1); (e)/D-001; (g)(1); (g2)/D-002; (h)/D-003; (d2); (f); and the D-005 page reading.
9. **The new FIELD-POPULATION** must show 57/38/38 and `excluded_unresolved` empty, with the consistency check passing.

## 5. Harness adapter requirements and declaration bindings

These are requirements only. Nothing here was built.

### 5.1 What the frozen harness needs before it can consume r32 labels

**Keys.**
- Map the pool id (`F###`) and page string to `EP-<ep>/<relative_path>` through SOURCE-MANIFEST.
- File metadata is used as a key, never as evidence.

**Per-field resolution.**
- `score_bcr.primary` is per document today. It must become per field, or a fixed conservative normaliser rule must be declared together with its effect.
- The possible document-level mappings give 57/38/38, 56/38/37 or 50/37/32.

**Page-field exclusion.**
- A "not scorable" marker distinct from None is needed. It covers `ambiguous`, `present` with association `uncertain`, and `excluded_from_scoring`: 30 rows on 30 pages in 25 documents.
- Otherwise a C `discovery_absent` counts as a verified absence.
- The critical tripwire must classify per field, keyed by pool id. F019 revision and F069 identity must count as **unresolved** truth.

**States.**
- `present` + `resolved` becomes the literal.
- `absent` becomes None, with `absent_kind` mapped to UR or n/a.
- `ambiguous` and `uncertain` become not scorable.
- `excluded_from_scoring` is honoured.
- The adapter consumes reviewed-2, not reviewed-1.

**Decision value.**
- Map the class and literal to the evaluator vocabulary.
- Define the tolerance on the 9 `resubmission_required` rows.

**Compilations.** Truth is keyed by (pool id, page) for F002, F035, F043 and F069. A file-level truth is never used.

**Aliases.** Run sets use canonical ids only (no F031, F052, F059 or F070), or aliases score against the canonical truth and count once. Captures key on sha256, so the byte-identical pairs share their captures.

**Metadata.**
- `project` comes from `ep`.
- `stratum` comes from FROZEN-SELECTION. It is required whatever the C-4 decision.
- `in_scope_pages` comes from RENDERS `pages_in_scope`.

**New code**, built and tested in a correction task, re-frozen, and bound by a new binding manifest:
- an r32 lane scorer;
- a live runner;
- an r32 → evaluator-input converter (REG, PAGE, uncertainty and the planned list);
- ingestion of exactly the run set into the B sandbox;
- a run-set selector, with the 2 unsupported controls defined or the plan amended.

**Evaluator .10.** It needs an offline test with zero model calls (C-6) of:
- whitespace-insensitive comparison;
- en-dash and hyphen variants;
- Arabic and Arabic-Indic literals;
- page-keyed compilations;
- the decision vocabulary and the resubmission tolerance.

### 5.2 DRAFT-DECLARATION.v2 (`19720ad9…`) bindings that the final declaration must replace or add

**Replace:**
- `status`;
- `labels.status` ("not drafted");
- `labels.review` ("Codex reviewer"). It becomes an owner-delegated independent Claude AI review, not human sign-off;
- `cohort.permission`;
- `selection.feasibility_sha256` `ed1decfe…`;
- the extension-2 route through alternate 22317;
- `evaluators.lane_scoring` `score_lane.py` `17ed2ba3…`;
- `dry_run` `ac60194c…`;
- `stop_rules` (the tripwire must be per field);
- `binding_manifest` `2dfef08e…`;
- `limits.expected_use` (B about 6, C about 135, R about 10, P about 20, all taken from the four-arm sample). These must be re-estimated for the r32 run set;
- `thresholds_verbatim` and the AI-ACCURACY-POLICY hash `7efa891b…`, **if** §8 is amended (C-3 route (b)). Re-bind them in the new binding manifest, or the preflight refuses the run.

**Add:**
- **Labels:**
  - `r32-labels-reviewed-2` and its package manifest;
  - draft `ebd1e24d…` and conventions `5c09d4d2…`;
  - the review chain `920a21d6…`, `70f94632…`, `ad6798dc…`, `e8828bec…`;
  - Review 33 final hashes: this file (`REVIEW.sha256`), `DISPOSITIONS.json` and `ESCALATION-RULINGS.final.json`;
  - the normalised-labels hash and the normaliser code hash;
  - the amendment and interpretation list (C-2);
  - the §8 resolution (C-3);
  - **the assurance level** of the labels: AI-drafted, AI-reviewed, not human-signed, and from the same model family as the system under test, unless route (a) is taken. Under route (a), state the human-checked rows.
- **Population:** the new FIELD-POPULATION (expected 57/38/38), the aliases, 0 extensions used, and the gate result.
- **Cohort and selection:**
  - PROJECT-VERIFICATION `4cecf2fc…`, with no replacement;
  - FROZEN-SELECTION `bf71779a…` (seed `m2-r30-pool-2026-10-02`);
  - the universe of 3,046 against 2,455, disclosed;
  - the extension facts: 302 review-signal paths, capacity 34/36 and 22/36, none drawn, and an alternate needs the owner.
- **Project AI policies (C-9):** the policy and eligibility record for each of the six projects and its hash. This is what policy §7 requires.
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

1. **R33-VERIFY.** The mechanical check of this folder and of the frozen state. The orchestrator then records ORCH-006.
2. **Reviewed-2 frozen (C-1, C-2).** It is applied mechanically and independently verified, with the counts at 57/38/38.
3. **Correction task frozen and tested (C-5, C-6).** It covers the harness adapter, the selector and converter, and the offline evaluator test.
4. **Owner: AI-ACCURACY-POLICY §8 (C-3, R33-02).** Either:
   - route (a), the human check of the scored rows after the selector freezes; or
   - route (b), an append-only amendment or waiver, followed by re-binding of the policy hash.
5. **Owner, with an independent review: the concentration-rule decision (C-4, R33-01).**
6. **Project AI policies and eligibility checked and bound for the six projects (C-9, R33-30).** Where a policy is missing, the owner states one.
7. **Owner: provider-use permission for EP-3563, 22349, 27331, 15744, 26687 and 29255.** A-02 covers access, staging, drafting and preparation only.
8. **Owner: the final fresh live-validation declaration (C-7).** It covers bindings, scopes, caps 240/240/40/36 and the per-field stop rules.
9. **Owner: the model-request budget (at most 556) and an experiment ledger scope.** None exists today; the ledger stands at 483 entries, 17 scopes and 0 amendments.
10. **Owner, only if an extension is ever needed:**
    - alternates for capacity (A-02 open point);
    - the extension-1 shortfall rule.
11. **Owner, optional:**
    - confirm the consent scope and that Claude agents may read the images (R33-15);
    - confirm or object to the parallel writers, both the R32 batch reviewers and Review 33's D1–D4 (R33-20);
    - preserve A-03 verbatim;
    - complete A-03's list of documents naming Codex (R33-21).

## 7. Owner-only items

Nothing in this review decides any of these:
- the AI-ACCURACY-POLICY §8 resolution for this run (C-3);
- the concentration-rule stratum leg (C-4, with an independent review);
- the project AI policies where none exists (C-9);
- any reversal of this review's rulings by taking an owner alternative:
  - D-004: (h2) gives `absent`;
  - D-005: frozen cell-first gives `present` "00", and revision becomes 39;
  - (c)(ii) reversed gives 59/40/39;
  - LACASA/Scale suffixes counted (up to +8 revision);
- provider-use permission for the six projects;
- the final live-validation declaration;
- the model-request budget and the experiment ledger scope;
- alternates for extension capacity and the extension-1 shortfall rule, if ever needed;
- confirmation of the consent scope, of the parallel-writer interpretation of A-03, and of the A-03 wording;
- any default extraction variant, M2 acceptance and M3.

## 8. Statuses (stated separately)

| Status | State |
|---|---|
| **Source permission and verification** | A-02 (owner, 2026-10-02 18:55Z) grants metadata discovery, download, staging, rendering, and label drafting and preparation for the six projects. **Provider or model use is not granted.** Verification: 10 of 10 pass with no replacement. The 72 originals are unchanged by `os.stat` (D1, CRITIC), and their staged copies are hash-bound. The projects' AI policies are **not yet checked** (C-9). |
| **Label drafting** | `r32-labels-draft-1` (`ebd1e24d…`) is complete and frozen. It is AI-drafted (Claude Opus 5.5) and not human-signed. |
| **Independent label review** | Complete and frozen: final `920a21d6…`, applied as `r32-labels-reviewed-1` (`00e53e82…`). It is an owner-delegated independent Claude AI review, not human sign-off, and it comes from the same model family as the system under test. 0 of 98 sampled rows were refuted. Review 33 has now **ruled** D-004 and D-005 (both AMBIGUOUS) and (c)(ii) (ADOPTED). `r32-labels-reviewed-2` is **pending** (C-1). The §8 policy conflict is **open** for the owner (C-3). |
| **Field populations** | Reviewed-1: identity 57, revision 38, decision 38, with F069 identity and F019 revision excluded as unresolved. After reviewed-2: **57/38/38**, with nothing unresolved. 0 extensions. |
| **Preparation gate** | Pool gate (each field at least 12) **met** under every option. Review 33 final verdict: **PREPARATION ACCEPTED WITH CONDITIONS** (C-1 to C-9). |
| **Live-run authorization and budget** | **Not authorized.** No provider use, budget, ledger scope or use of the 556 ceiling. The AI ledger is unchanged at 483 entries, 17 scopes and 0 amendments. |
| **M2** | **CHANGES STILL REQUIRED.** |
| **M3** | **Not started.** |

## 9. Dispositions of the critique

The full record is in `DISPOSITIONS.json` (`ceb8fdcc…315b`). There are 22 items: 13 disagreements and 9 missing checks.

| Count | Value |
|---|---|
| Material total | **8**: C-001 to C-005, plus the material missing checks M-001 to M-003, which duplicate C-004, C-002 and C-001. There are 5 distinct material issues |
| Upheld (the draft stands) | **0** |
| Adopted (the critic is right; the change is applied) | **8** |
| Escalated (cannot be settled from the evidence) | **0** as dispositions. The owner-only decisions are carried as conditions C-3 and C-4, plus C-9 where a project policy is missing, and the owner alternatives are kept in section 4 |
| Noted (non-material) | **14**: C-006 to C-013 and M-004 to M-009 |

**Adopted:**
- **C-001:** D-005 ruled AMBIGUOUS, so revision stays 38 and the expected counts are 57/38/38.
- **C-002:** the same-family disclosure, with route (a) named as the one that meets §8 as written.
- **C-003:** 25 documents, not 27.
- **C-004 and M-001:** new finding R33-30 and condition C-9; the policy is re-bound if amended; expected use is re-estimated.
- **C-005:** (c)(ii) is ruled ADOPTED, so C-2 becomes a recording step.

**Noted, with text changes where useful:**
- **C-006:** the whole-comparison effect is added to R33-01.
- **C-007:** the D-004 basis is restated page-only.
- **C-008:** moot.
- **C-009:** CROPS abbreviation fixed.
- **C-010:** the verdict rule is cited from the ORCH-03.4 task text.
- **C-011:** R33-20 now covers D1–D4.
- **C-012:** R33-21 list completed.
- **C-013:** less weight on D2-only items.
- **M-005:** re-checked by stat.
- **M-006 and M-007:** relied on.

The verdict category is unchanged.

## 10. Independence statement

**Review 33 agents.** Each is a fresh, isolated Claude agent under A-03. The models and effort for D1 to D4 and SYNTH are as self-reported in their files, and CRITIC's as stated in `CRITIQUE.json`.

| Agent | Task | Model / effort | Mode and writes |
|---|---|---|---|
| R33-D1 | ORCH-03.1/D1: integrity and bindings | Claude Opus 5.5 (`claude-opus-5-5`) / High | read-only; `dimensions/D1-*` |
| R33-D2 | ORCH-03.1/D2: cohort, authority and process | Claude Opus 5.5 (`claude-opus-5-5`) / High | read-only; `dimensions/D2-*` |
| R33-D3 | ORCH-03.1/D3: label truth and escalations (image-based) | Claude Opus 5.5 (`claude-opus-5-5`) / High | read-only; `dimensions/D3-*` |
| R33-D4 | ORCH-03.1/D4: population, gate and harness | Claude Opus 5.5 (`claude-opus-5-5`) / High | read-only; `dimensions/D4-*` |
| R33-SYNTH | ORCH-03.2: synthesis and draft | Claude Opus 5.5 (`claude-opus-5-5`) / High | read-only; `INDEPENDENT-REVIEW.draft.md`, `FINDINGS.json`, `ESCALATION-RULINGS.json` |
| R33-CRITIC | ORCH-03.3: adversarial critique | Claude Opus 5.5 (`claude-opus-5-5`) / High; a different fresh agent | read-only; `CRITIQUE.json`, `CRITIQUE.md` |
| R33-FINAL | ORCH-03.4: dispositions and final verdict (this file) | Claude Opus 5.5 (`claude-opus-5-5`) / High; a different fresh agent | read-only elsewhere; `DISPOSITIONS.json`, `ESCALATION-RULINGS.final.json`, `INDEPENDENT-REVIEW.md`, `REVIEW.sha256` |
| R33-VERIFY | ORCH-03.5: mechanical check (pending) | fresh read-only agent; session model | planned; `INDEPENDENT-PACKAGE-CHECK.json` |

**Rule.** No Review 33 agent may be:
- the drafter of `r32-labels-draft-1`;
- any label reviewer (R32REV-B1 to B7, CONSOLIDATE, CRITIC, DISPOSE);
- the implementer (R32APPLY-*);
- the orchestrator.

All Review 33 agents, the drafter, the label reviewers and the evaluated extraction models are from the Claude family. This is model-level independence of process, not independence of model family (R33-02).

**My own position (R33-FINAL).** I am none of the excluded roles, and none of the other Review 33 agents. I did not open:
- the drafter's folder `C:/t/iso/work/r2x/r32` or the implementer's folder `C:/t/iso/work/r2x/r32b`;
- any arm output or replay;
- the contents of the r26.2 labels or any LABELS-NORMALISED rows;
- any OneDrive file;
- any database other than the AI ledger, which I read with `mode=ro` and `uri=True`. The other ledgers and `C:/t/r2x/runs` I only stat'ed;
- any candidate or baseline source.

**What I did and did not do.**
- I made no network request, no provider or model request and no prediction.
- I ran no package script.
- I wrote only the four files named above, plus scratch files in my scratchpad folder `r33-final/`: a recount script, two writer scripts and one rotation derivative, none of which is evidence.
- I did not edit the draft, `FINDINGS.json`, `ESCALATION-RULINGS.json`, the critique or the dimension files.

**What independence rests on.** For the other agents it rests on their self-reports and the orchestrator's records. Their transcripts are not available to me.

---
This review is an owner-delegated independent Claude AI review, not human sign-off. It does not authorize a live run, a budget, a ledger scope, a default variant, M2 acceptance or M3.
