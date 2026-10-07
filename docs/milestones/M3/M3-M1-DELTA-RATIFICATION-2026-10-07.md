# M3 ratification record for the M1 delta cells — 7 October 2026

Milestone: **M3 - Ownership, Access & Memory Policy**. This is the separate dated ratification record the owner chose on 7 October 2026 (Pack open question 3, [M3-DECISION-PACK.md](M3-DECISION-PACK.md) section 2b, Q-3): the M1 refresh's delta cells are **SETTLED by reference to this record**. The M1 files ([M1R-DATA-OWNERSHIP-DELTA.md](../M1/refresh-2026-10-06/M1R-DATA-OWNERSHIP-DELTA.md), its CSV, and [M1R-ACCEPTANCE-RECORD.md](../M1/refresh-2026-10-06/M1R-ACCEPTANCE-RECORD.md)) are not rewritten; their content stays as accepted on 6 October 2026.

Ratified by: owner (mohamedr69, Mohamed Elazab) on 2026-10-07 (session messages relayed by the orchestrator; Pack sections 2, 2a, 2b). Contract: [M3-POLICY-CONTRACT-DRAFT.md](M3-POLICY-CONTRACT-DRAFT.md) Parts B and C.

Scope rule (Q-2): only the cells listed here are settled by this record. Every other delta cell that merely contains the word PROPOSED stays as the M1 refresh left it, unless an already-ratified policy or OD decision governs it; wording alone is not owner approval.

Reading rule: "Owner" is the target owner the M1 refresh proposed, now ratified as proposed unless the row says otherwise. "Settled by" names the Part B decision or Part C row that settles the cell. Where a filed decision overrides a proposed row, the decision prevails and the row is flagged (Part C header rule).

## A. The 18 PROPOSED owner cells (Part C rows B-1..B-18)

| CSV cell | Owner (ratified as proposed) | Settled by |
|---|---|---|
| SBQ.result | BOQ Processor, shop-drawing lineage separate from the Design Sheet BOQ; M7 to confirm; engineer-edit layer | C row B-1 (D-09 extended) |
| SBQ.source | as SBQ.result; separate last-editor field | C row B-2 |
| JOB.row | M7 shared processing registry, as the job record | C row B-3 |
| JOB.queue_claim | as JOB.row; M7 idempotency key per stage and input fingerprint | C row B-4 |
| JOB.worker | as JOB.row | C row B-5 |
| JOB.process_split | as JOB.row; M7 stage records | C row B-6 |
| CACHE.page_ocr | M7 shared processing registry / AI platform service; registered text/OCR stage artifact | C row B-7 |
| CACHE.page_box | as CACHE.page_ocr | C row B-8 |
| CACHE.pdf_memo (LEGACY) | as CACHE.page_ocr; retires with the legacy whole-folder scan | C row B-9 |
| CACHE.result_cache | as CACHE.page_ocr; under the M7 content-reuse contract | C row B-10; reuse bounded by OD-04 (a) and OD-11 (shared rows never deleted by one project) |
| AI.usage | AI platform service (M7, M22); usage record | C row B-11 |
| AI.budget_limits | as AI.usage; budget configuration | C row B-12 |
| AI.reading_store | as CACHE.page_ocr; registered model-reading artifact under the content-reuse contract | C row B-13; OD-04 (a) sub-answer (server-side reuse only for a blocked project) |
| USR.account | Platform registry / auth service | C row B-14; access policy OD-19 (b); department by admin as account administration, OD-06 |
| USR.role_access | as USR.account | C row B-15; OD-19 (b), OD-18 amended, Q-1 (engineering manager = `design_manager`), P-24 capabilities |
| USR.login_state | as USR.account | C row B-16; OD-19 |
| USR.session | as USR.account | C row B-17; OD-19 |
| USR.activity_event | as USR.account; the "mine" list becomes a membership view | C row B-18; OD-19 (b), OD-11 (append-only, survives archive) |

## B. The 4 NEW-PROPOSED conflicts and S-2 (Part C rows B-19..B-23)

| Delta §7 item | Owner (ratified as proposed) | Settled by |
|---|---|---|
| 16 FA interface publication | Interface processor over the M7 registry; engineer publication is its protected override | C row B-19; OD-18 (a human confirmation, never AI) |
| 18 Fire-alarm IFC DXF parsed three ways | M7 shared processing registry, one CAD-conversion and DXF-parse stage | C row B-20 |
| 19 "IFC drawings counted" | IFC domain publishes one in-force and answers-complete flag | C row B-21; OD-13 (a) |
| 22 Canonical manufacturer name | Knowledge Processor keeps one manufacturer normaliser; M26 reads it | C row B-22 (D-12) |
| S-2 Draftsman names across projects | Platform registry / auth service holds the people list | C row B-23; OD-19 (b), OD-07, Q-10 |

## C. The inherited owners confirmed (Part C rows C-1..C-6)

| Fact group | Decision inherited | Settled by |
|---|---|---|
| DRV.review_run, sheets, floor_geometry, finding, decision, rules | D-04 | C row C-1 |
| DRV.fls_files | D-02 with D-04 | C row C-2 |
| DRV.ruling (owner) | D-04 | C row C-3; scope OD-12 (c), superseding the stretch note |
| PREP.plan_run, change, symbols, run, output, walls_index, columns_index | D-04 | C row C-4 |
| DFT.items, skipped_ready, draftsman, log | D-04, re-assigned | C row C-5; authority Q-10 (design engineer / primary owner operates, `design_manager` overrides, admin none); store owner RE-ASSIGNED 7 October 2026 (evening, R-3) to the M7 project assignment and access domain; drawing pages and services are consumers with no separate authoritative copy |
| ARC.root, folder, project_path_rebind | D-01 with D-02 | C row C-6; archive writes bounded by OD-15 (a) |

## D. The M3-OWNER-DECISION cells

| Cell or conflict | Settled by | Decision in one line |
|---|---|---|
| DRV.ruling (scope) and §7 S-1 | OD-12 (c) | project-local by default; company-wide only through OD-02 promotion; existing 260 rulings stay local to their project |
| PRJL.deletion | OD-11 (b)+(e) | hard delete only before a project was ever active; otherwise archive; purge separately governed; backups follow project retention |
| PRJL.upload_files | OD-11 (b) | an active project is archived, never deleted, so its uploads are kept; what a hard delete of a never-active project removes under `uploads/EP-N` is for the M7 deletion contract to state (the Pack's OD-11 row notes files left behind for a later project with the same EP number) |
| PRJL.archive_writes | OD-15 (a) | Apply writes only the platform copy; publication into the archive is a separate explicit engineer action with a unique non-overwriting name; other archive-writing flows listed for M7 |
| PRJL.backups | OD-11 (e) | kept with the project's retention |
| USR.account, USR.role_access, USR.login_state, USR.session, USR.activity_event | OD-19 (b), OD-18 amended, OD-06, Q-1, P-24 | central project membership administered by `design_manager`; admin is system administration only; capabilities are not roles |
| §7 item 9 "approved as noted" | OD-01 (c) restricted | not final by default; versioned configuration; per-project override by `design_manager` with reason; provisional where a stream cannot tell its states; Home and Drawings aggregates corrected or relabelled |
| §7 item 10 compliance learned answers | OD-02 (completed), OD-03 (d), OD-23, OD-24, P-25 controls (R-2) | automatic promotion on configured criteria or manual by `design_manager` / confirmer, never the author alone; provenance kept; retirement on withdrawal; the 84 stored rows stay project-local |
| §7 item 17 IFC symbol answers | OD-13 (a) with sub-rules; governed exception to the promotion workflow (P-25, R-2) | company-wide versioned library; engineer verification only; AI output a proposal; carry-overs carry no engineer authority; tombstoned unverify |
| §7 item 25 project documents to an AI provider | OD-04 (a) | every provider path, present and future, honours the project policy; server-side-only reuse for a blocked project |

## E. Not settled by this record

- The 103 other delta cells that contain the word PROPOSED (Q-2).
- The 17 SETTLED-GAP conflicts of delta §7, which carry to their named milestones (contract Part D1).
- G-01..G-04 and the 16 M3-tagged weakness rows: policy requirement with M3, guard implementation with M4 or M7 (Q-4; contract Part D2).
