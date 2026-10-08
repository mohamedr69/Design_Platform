# Proposed roadmap note U10 (NOT applied)

Task: ORCH-037 (ep-scribe). Worktree `G:/dev (2)/dev/ep-platform-merged/roadmap-u2`, branch `roadmap/u2`, HEAD at start `573780a561fac560b5e5b5344c227f348eb65fb2`.
Date: 2026-10-07.

**This note is a proposal.** `docs/UNIFIED_MASTER_ROADMAP.md` is not edited. The owner may paste the lines below. Every statement is taken from the delta survey `MR/orchestrator/surveys/U2-DELTA-DRAWINGS-PROCESSING-2026-10-07.md` (snapshot 22:13:40 local, 2026-10-07, live clone HEAD 7a1bf6f, all changes uncommitted) and the inventories written under ORCH-037. The provider-boundary review ORCH-038 is pending and is not cited. No acceptance, PASS or measured result is claimed.

Supporting records (all in this worktree):
- `docs/milestones/M1/M1-DELTA-ADDENDUM-2026-10-07.md`
- `docs/milestones/redesign/RD-M1-refresh-2026-10-06/M2R-DELTA-ADDENDUM-2026-10-07.md`
- `docs/milestones/M6/M6-INVENTORY-2026-10-07.md`
- `docs/milestones/M7/M7-INVENTORY-2026-10-07.md`
- `docs/milestones/M10/M10-GET-SIDE-WORK-ADDENDUM-2026-10-07.md`

## A. Section 3, "Core platform" (add after the paragraph that ends "...is not automatically present merely because their reports are in docs..." or at the end of the Core platform subsection)

> **Uncommitted drawings and processing change set, surveyed 7 October 2026 (implemented / partial, not accepted).** The owner's live clone carries uncommitted code (22 modified tracked files plus untracked files; HEAD 7a1bf6f, whose backend and frontend equal the roadmap base 668f92f): an AI classification pass that runs as a new last phase of document processing (`document_classification_ai.py`, `document_processing.py:524-540`), a Drawings Assistant (`drawings_chat.py`), a Drawings Log per IFC sheet and an IFC folder import, and sheet numbers read from the DXF. None of it is in the frozen M4 trees. Its records are in `docs/milestones/M6/M6-INVENTORY-2026-10-07.md`, `docs/milestones/M7/M7-INVENTORY-2026-10-07.md` and `docs/milestones/M10/M10-GET-SIDE-WORK-ADDENDUM-2026-10-07.md`. It adds two new per-feature model-routing switches (chat and classification) and two new GET-side behaviors (a folder scan on `GET /ifc-drawings/folder` and on every `GET /drawings/log`; reconcile-on-read reaching `log?view=ifc` and its export). It proves nothing about accuracy.

## B. Section 7, status column (replace or extend the cell text for M6, M7 and M10)

M6, current text: "Classification V2 code/inspector foundations present; not formally accepted."
Proposed M6 cell:

> Classification V2 code/inspector foundations present; not formally accepted. An uncommitted AI classification pass (`source="ai"`, weak documents only, confirmed rows protected by code) is implemented / partial, not accepted; no precision, recall or false-supported measurement exists (`docs/milestones/M6/M6-INVENTORY-2026-10-07.md`).

M7, current text: "document worker, domain records and some dependencies exist as five unrelated stores ...; unified contract is incomplete (RC-36)."
Proposed M7 text, appended:

> An uncommitted classify phase after the shop-drawing reconcile (`document_processing.py:524-540`) is the first extra stage; it has no stage status, per-stage key, producing job id, model or prompt column, or cancel path. It is the pilot consumer for the M7 stage record, not M7 evidence (`docs/milestones/M7/M7-INVENTORY-2026-10-07.md`).

M10, current text: "many DB-backed views exist; residual read-time production prevents full acceptance."
Proposed M10 text, appended:

> Uncommitted work adds a scanning GET (`GET /ifc-drawings/folder`) and extends folder-listing and reconcile-on-read to `GET /drawings/log`, its export and `summary`, and a changed Home count; six handlers are listed in `docs/milestones/M10/M10-GET-SIDE-WORK-ADDENDUM-2026-10-07.md`.

## C. Section 8 detail lines (optional; the card names sections 3 and 7, offered for the owner's convenience)

- M6 detail, after "Use stored extraction first, bounded AI where justified...": "The AI classification pass of 7 October 2026 is the bounded-AI path; its shadow evaluation items are listed in `docs/milestones/M6/M6-INVENTORY-2026-10-07.md` section 3."
- M7 detail, after "Implement the shared registry/artifact contract in section 5.": "Add the classify stage's attributes (model id, prompt version, producing job, status and skip reasons per document, stage idempotency key, cancel) to the design list."
- M10 detail, after the exit paragraph: "Record the six handlers of the 7 October 2026 addendum in the consumer record."

## D. Lines the scribe deliberately did not propose

- Nothing for M1 or M2 status cells: both keep their accepted wording; their addenda are records only.
- Nothing for M12 or M24 (Drawings Assistant as a stand-alone AI workflow with browser-stored conversation and two-grain memory, survey section 6): the card did not name them. The survey proposes listing it there as "implemented stand-alone workflow, not accepted"; the owner may add it.
- Nothing for M3 (P-02, B-04): the survey's observations that no conflict record is written when an AI answer disagrees with a confirmed row, and that server-boundary policy enforcement is absent, are in the M6 inventory only.
