# Review 33, dimension D2: cohort, authority and process adherence

- **Task:** ORCH-03.1/D2, agent label R33-D2.
- **Model:** Claude Opus 5.5 (`claude-opus-5-5`), effort High, by my own system context.
- **Mode:** fresh, isolated and read-only.

**What this review is not.** It is an owner-delegated independent Claude AI review, **not a human sign-off**. It approves and authorizes nothing.

**What this review did not do:**
- no provider or model request, no network access, no prediction;
- no state-changing git command;
- no OneDrive file opened (os.stat only);
- no database opened except the AI ledger, read-only through its URI;
- the drafter's folder `C:/t/iso/work/r2x/r32`, the implementer's folder `r32b`, arm outputs, replays and r26.2 label contents were not opened;
- no staged image was read, because this dimension needs no image reading.

**Disclosure.** A recursive `grep -c Codex` over `review31/` counted one match in `review31/dry-run/LABELS-NORMALISED.json`. No row content was displayed or read.

**Status.** M2 is **CHANGES STILL REQUIRED** and M3 has **not started**. Nothing in this report changes either.

## Result

**No blocker.** There are 2 major, 9 minor and 9 info findings.

- **D2-11 (major, concentration rule).** As written, the rule makes decision eligibility unreachable on this population.
- **D2-13 (major, policy conflict).** AI-ACCURACY-POLICY §8 conflicts with Claude-only gold labels.

Both majors are owner or declaration decisions. Neither is a defect in the preparation.

**Confirmed:**
- A-02 scope adherence, project verification, the frozen selection, A-03 independence of review and application, and frozen-state integrity.
- My recount of the reviewed labels: identity **57**, revision **38**, decision **38**. F069 is excluded from identity and F019 from revision.

## Inputs re-hashed (all match the task's values)

| Item | sha256 / count |
|---|---|
| `fresh-cohort-r32` manifest | `15c4114d…d0ed`: 110/110 files match, no unlisted file except the manifest and check files |
| Draft labels | `ebd1e24d…a334` |
| Conventions | `5c09d4d2…8570` |
| Frozen selection | `bf71779a…5d21` |
| Source manifest | `951e8697…e259` |
| Crops | `b1760b64…d1ff` |
| Evidence index | `0d0db4f8…08b8` |
| Label review: final | `920a21d6…4c5b` |
| Label review: consolidated | `70f94632…3ff8` |
| Label review: critique | `ad6798dc…7eef` |
| Label review: dispositions | `e8828bec…30a7` |
| Label review folder | 23 files, byte-identical to `fresh-cohort-r32-reviewed/review-r32-draft-1/` |
| `fresh-cohort-r32-reviewed` manifest | `64c03667…31c6`: 45/45 files match |
| Reviewed labels | `00e53e82…7779` |
| `review31` manifest | `d5fe1649…7460`: 58/58 files match |
| `DRAFT-DECLARATION.v2` | `19720ad9…8b5d` |
| `M2-REVIEW-RESPONSE.md` | `f0a4ffac…c65b`; its first 156,880 bytes hash to `6e296c28…fa0d4` |
| `AUTHORIZATION-2026-10-02.md` | `fd20167a…721d`, equal to the A-02 value |
| Packet inputs and draft copy in the reviewed package | byte-identical to the originals (5 inputs, plus the draft) |

## (1) A-02 scope: CONFIRMED within scope (D2-01)

**Order of events.** Everything happened after the owner's answer at 18:55Z.

| Time (UTC, 2026-10-02) | Event |
|---|---|
| 18:57:59Z | project verification |
| 18:59:13Z | selection frozen |
| 18:59:49Z to 19:01:52Z | staging (72/72 staged; source sha256 equals staged sha256) |
| until 20:06Z | rendering, drafting and packaging |

The label review, the application of rulings and this preparation review followed under A-01 and A-03.

**AI ledger** (opened with `file:…?mode=ro`):
- 483 entries, 17 scopes, 0 limit amendments;
- newest entry 2026-10-01T18:17:43Z;
- `.sqlite` mtime 2026-10-01T18:17:50Z; `-wal` is 0 bytes.

**Other evidence of no run:**
- The `C:/t/r2x/runs` directory mtime is 2026-10-01T17:51:11Z (directory stat only).
- The package scripts contain no network or provider code. The only database opens are read-only ledger counts.

**Sealed projects.** The 10 sealed EPs listed in PROJECT-VERIFICATION equal the Round-2 projects marked sealed in `review06/.../ROUND2-SELECTION.json`. None of the 34 Round-2 EPs is in the cohort or among the alternates.

**OneDrive originals.** Checked with os.stat for 72/72: size and mtime equal the SOURCE-MANIFEST selection values.

**Side effect (D2-19, info).** All 72 originals were cloud-only placeholders at selection. They are now hydrated (the `RECALL_ON_DATA_ACCESS` bit is clear), which is about 249.5 MB held locally. This follows from the authorized download.

## (2) Consent record (D2-02 and D2-03, minor)

**What the record covers.** The verbatim question lists metadata discovery, download, staging, rendering and *label drafting*. The answer is "I authorize this". On that basis the record suffices for discovery, download, staging, rendering and drafting.

**Limits:**
- **"Preparation" was added.** The "Scope as recorded" table and A-02 add "and preparation", which is not in the question.
- **The option wording was the assistant's.** The record does not say that the dialog option the owner selected was worded by the assistant. Only A-02 and ORCH-001 add that qualification.
- **The later steps rest on A-03.** The label review, the application and this review rest on A-01 and A-03. A-03's source owner message is "not reproduced in full", so I cannot verify its verbatim text (UNVERIFIABLE).
- **Claude reading the images (D2-03).** Read literally, "does NOT cover any provider or model request" also covers Claude agents reading staged images. Every document reads the clause as "through the application or experiment harness" (Review 32, A-03 item 5). The authorization record itself carries no such qualifier.

**What the owner should confirm** (optional, does not block), in a chat message of his own:
1. the 18:55Z authorization is his;
2. "preparation" covers the label review, the application and this review;
3. Claude agents may read the staged page images of the six projects.

The orchestrator should also preserve the verbatim A-03 message, append-only.

## (3) Project verification: CONFIRMED (D2-04), with one disclosure gap (D2-05)

**What matches Review 31 and COHORT-PROPOSAL.md:**
- the same six primaries, and the same four alternates in order;
- for each EP: one folder, class `project`, the folder name carries the EP number, the contractor equals the R31 record, and `contractor_cluster_used_by` is empty;
- not in Round 2; `replacements: []`;
- the R31 `used_sets` and `selector_core` were reused unchanged (the review31 manifest re-hash proves it).

**One disclosed rule adjustment.** S5 narrative mentions that occur only in the Review 32 proposal files are not counted as use, so used EPs read 209 (199 + 10).

**Gap (D2-05).** The re-check read **930** databases; Review 31 read **959**.
- `used_sets.build` skips unreadable databases with `except sqlite3.Error: continue`, so it fails open and records nothing.
- A metadata listing today shows 957 `*.db` files under `C:/t` and 5 under `backend/`. None was opened.
- The difference is neither explained nor listed. Review 31's check over 959 databases remains valid for the databases that existed then.
- **Required:** disclose the difference, or list the unread databases (read-only), before the declaration.

## (4) Frozen selection against plan v2 section 2 and feasibility v2

**Conformance (D2-06, CONFIRMED):**
- seed `m2-r30-pool-2026-10-02`;
- quotas 40 / 20 / 12, with no `fill`;
- 12 documents per project;
- regular expressions identical to the R31 selector;
- `rules_sha256` matches the rules text;
- `order_key` recomputed for 374/374 rows, 0 mismatches, and both orders are ascending.

The review-signal part of the pool comes from: 3563 12, 27331 12, 29255 12, 22349 2, 26687 2, 15744 0.

**Deviations:**
- **D2-07 (minor).** DRAFT-DECLARATION.v2 and feasibility v2 declare separate extension seeds: `m2-r31-extension-1-2026-10-02` and `m2-r31-extension-2-2026-10-02`. The frozen file instead takes extensions from the single pool-seed order. This is not disclosed. No extension was drawn.
- **D2-08 (minor).** The duplicate rule (lower-cased name plus size) is new. It let through:
  - byte-identical F038 = F052 (two different strata) and F067 = F070;
  - content duplicates F001 / F031 and F046 / F059.

  The effective pool is therefore 68 distinct documents.

**Universe difference (D2-09, info).** The two universes are 3,046 PDFs (with long-path handling) and 2,455 (Review 31's walk). Effects:
- **None on the prevalence feasibility table.** That table depends only on the number of documents (72 / 108 / 144).
- **None on the cap-bound capacity.** From the actual eligible review-signal counts (3563 134, 22349 7, 27331 71, 15744 5, 26687 12, 29255 113), min(cap, n) gives 60 / 78 / 96, the same as Review 31's table.

**Realized extension yield.** That table was an upper bound. A simulation of the frozen order gives:

| Extension | Yield | By project |
|---|---|---|
| Extension 1 | **34 of 36** | 6 / 6 / 6 / 6 / 5 / 5 |
| Extension 2 | **22 of 36** | 6 / 6 / 6 / 4 |

The shortfall arises because the pool used the 12-document cap of 22349, 15744 and 26687 on drawing and other documents.

**Latent conflict (D2-10, minor).** Two rules provide for alternates to enter the cohort for capacity:
- the frozen extension-2 rule, "alternate projects enter in their order";
- Review 31's plan, which places EP-22317 at Extension 2.

A-02 permits alternates only as replacements, and the extension-1 rule says nothing about a 2-path shortfall. This needs an owner decision only if an extension is ever needed. The gate is met at 57 / 38 / 38, so none is needed now.

## (5) A-03 process adherence: CONFIRMED (D2-14), with two minor points

**Independence:**
- **Agents.** The 7 batch reviewers, the consolidator, the critic and the disposer all ran `claude-opus-5-5` at High effort, with self-reports. All batch files record `independent_of_drafter: true` and `predictions_consulted: false`.
- **Forbidden paths.** A pattern scan for forbidden paths (drafter folder, r26.2, arms, replay, runs, OneDrive, `.db` / `.sqlite`) over all batch, critique, final and disposition JSON returned **0 hits**.
- **Application.** The rulings were applied by a different fresh agent, R32APPLY-IMPL, in a new folder `r32b` and a new package. ORCH-005 records an independent re-derivation by R32APPLY-VERIFY.
- **Limit.** Independence rests on records and self-reports. The transcripts are not available.

**Nothing frozen was edited in place:**
- the manifests match;
- the copies are byte-identical;
- the newest mtimes are packet 2026-10-02T20:06Z, review folder 2026-10-03T06:12:39Z, staging 20:00Z.

**Wording.** The phrase "Claude … NOT human sign-off" appears in:
- all 7 batch JSON files and all 7 notes;
- the critique (JSON and markdown) and the dispositions;
- both review notes;
- the reviewed-labels `status`;
- the reviewed PREPARATION-REPORT;
- the response-ledger entry.

**One write-capable agent at a time (D2-15, minor).**
- B1 to B7 ran at the same time, from 04:49:51Z to 05:11:01Z, each writing its own file.
- A-03 item 5's single reviewer became a 7 + 1 + 1 + 1 pipeline.
- The orchestrator recorded this interpretation for the owner to object to. The outputs are disjoint and verified by hash.
- **Required:** the owner confirms or objects.

**Codex naming (D2-16, minor).** These places are amended by A-03 and are not defects.
- *Listed by A-03:* LABEL-CONVENTIONS-R32.md l.67, REVIEWER-PACKET.md, the template's `review_kind`, review31/CORRECTION-REPORT.md l.113.
- *Not in A-03's list:* review31 plan v2 l.44, feasibility v2 l.8, budget card v2 l.22, CORRECTION-REPORT.md l.121, **DRAFT-DECLARATION.v2.json l.150 (`labels.review`)**, `make_draft_declaration_v2.py`, `harness/dry_run.py`, fresh-cohort-r32/PREPARATION-REPORT.md l.102, `make_review_packet_r32.py`, and historical M2-REVIEW-RESPONSE.md entries.
- *An error in A-03's list:* it names `FIELD-POPULATION.json`, which has 0 Codex mentions.
- **Required:** the final declaration must replace `labels.review`.

## (6) Concentration and the matched population

**The concentration rule cannot be met for decision (D2-11, major).** The rule is in plan v2 §5.5, DRAFT-DECLARATION.v2 l.217 and `score_bcr.concentration`:

```python
conc = net > 0 and (max(by_p.values()) > net / 2 or max(by_s.values()) > net / 2)
```

Its result feeds `reasons_not_eligible` (l.263). The counted documents by stratum (strata from FROZEN-SELECTION):

| Field | review_signal | drawing | other |
|---|---|---|---|
| Decision (38) | **37** | 0 | 1 (F072) |
| Identity (57) | 36 | 16 | 5 |
| Revision (38) | 29 | 8 | 1 |

Why this makes eligibility unreachable:
- **Decision.** Any positive net gain that F072 does not carry alone comes more than half from review_signal, so decision is NOT ELIGIBLE by construction.
- **Identity, very likely.** The run set takes decision documents first (up to 16), and 37 of the 38 carry identity.
- **Revision, less so.** The 9 revision-only top-up documents are drawing / other.

By project, the decision documents split 27331 12, 3563 11, 29255 10, 26687 3, 22349 2, 15744 0. The largest share is 31.6%, so the project leg has no structural problem.

**Required before the declaration.** The owner and an independent review must decide whether the stratum leg applies when the run-set population comes from one stratum by design. The choice must be frozen in the declaration. Otherwise the decision outcome is fixed before the run.

**Matched population (D2-12, info).** On counts, at least 12 matched documents per field fits within the 30-document run set:

| Field | How the run set reaches it | Matched |
|---|---|---|
| Decision | up to 16 of 38 | ≤ 16 |
| Identity | 37 of 38 decision documents carry identity | ≥ 15 |
| Revision | worst case 7 of 16, plus up to 8 top-ups from 9 revision-only documents | ≥ 12 |

The run set totals 16 + 8 + 4 + 2 = 30.

Points for the declaration and for D4:
- whether both arms actually attempt these documents is UNVERIFIABLE before the run (breaker and stop rules);
- no run-set selector is implemented in the harness;
- the adapter must map the count-once aliases F031, F052, F059 and F070.

## (7) PREPARATION-REPORT statuses (D2-18, info)

**Both reports** list the seven statuses separately, and each was truthful when written.
- **r32 report (20:06Z).** It predates A-03, so "PENDING, Codex reviewer" is superseded, not false.
- **Reviewed report.** Its figures recompute: 57 / 38 / 38, F069 and F019 excluded, upper bound 57 / 39 / 38, ledger 483 / 17, and the agent list. It keeps the two packages apart.

**Gaps:**
- *D2-17 (minor).* ORCH-001 finding 8 required disclosure that the drafting session opened the r26.2 label sets after the conventions were frozen. Neither report discloses it, and the r32 report says "Never used: … earlier labels". The underlying fact is UNVERIFIABLE to me.
- *Optional.* The reviewed FIELD-POPULATION.json has no label-truth statement.
- *Optional.* ORCHESTRATOR-STATE.md still describes the label review as "in progress".

## Authority conflict (D2-13, major)

AI-ACCURACY-POLICY.md (`7efa891b…4f47`), §8:

> "Gold labels must be independently checked against originals, not generated or approved solely by another model."

**The conflict.** `r32-labels-reviewed-1` was drafted by Claude and approved by Claude agents only. Its status reads "NOT human-signed; NOT a human review". No A-01 to A-03 entry, ORCH-001 to 005 entry, Review 31 or 32 document, or preparation report addresses this sentence. A-03 and Review 32 accept AI review for *preparation*; they do not amend the policy.

**Required.** An owner decision before the declaration. Either:
- an explicit, append-only amendment or waiver of §8 for this run, quoted in the declaration; or
- a human check of the scored label rows.

This is a "material authority conflict", which is an A-03 stop condition.

## Owner-only items that remain (D2-20)

1. **Provider-use permission** naming the six cohort EPs. A-02 excludes provider use. Both the Review 31 budget card (step 2) and `DRAFT-DECLARATION.v2` `cohort.permission` expected the permission to cover it.
2. **The final live-validation declaration.** It must replace these `DRAFT-DECLARATION.v2` bindings:
   - `cohort.permission`;
   - `labels.status` and `labels.review` wording, and the reviewed-label hash `00e53e82…`;
   - the extension order or seeds (D2-07);
   - the count-once aliases;
   - the concentration-rule decision (D2-11).
3. **Model budget and ledger scope:** B 240, C 240, R 40, P 36, at most 556 in total.
4. **Resolution of AI-ACCURACY-POLICY §8** (D2-13).
5. **Alternates for extension capacity**, only if an extension is ever needed (D2-10). Extension 1 stands at 34; Extension 2 would need EP-22317 for 14 documents.
6. **Optional confirmations:**
   - the consent wording, and Claude agents reading the images (D2-02, D2-03);
   - the parallel-reviewer interpretation (D2-15).

## Commands used (all read-only; scripts in my scratchpad `r33-d2/`)

- **Hashes:** `sha256sum` of every input, plus the 156,880-byte prefix of the response ledger. `vman.py` re-hashed all three manifests and checked for unlisted files.
- **Selection:** `fs.py`, `fs2.py` and `fs3.py` print the rules and counts, recompute the order keys and simulate the extension draws.
- **Round-2 cross-check:** `r2.py` compares the cohort with ROUND2-SELECTION (sealed list).
- **Populations:** `pop.py` breaks the counted documents down by stratum and project; `rc2.py` recounts the reviewed labels.
- **Label review records:** `rr.py` and `fo.py` read the agent lists, the `files_opened` lists and the forbidden-path scan.
- **Originals:** `st.py`, `st2.py` and `st3.py` run os.stat on the 72 originals (size, mtime, attributes) and summarize SOURCE-MANIFEST.
- **Ledger:** `led.py` reads the ledger counts through `?mode=ro`.
- **Metadata:** `find C:/t -name "*.db"` (listing only), and os.stat of the `C:/t/r2x/runs` directory.
- **Git and text:** `git status --porcelain` (read-only); `grep` for Codex wording, "not human sign-off" wording, r26 disclosure and network code.

The packages, folders and evidence I reviewed are left exactly as I found them. My only writes are this file and `D2-findings.json`; I ran my own scripts from my scratchpad.
