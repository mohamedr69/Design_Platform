# FI-P1 implementation review — finding dispositions

For a fresh independent review of the corrected branch. Each finding was first
reproduced on the reviewed commit (`abd48fd` = `80b9603` + review docs) with a
probe that passes while the defect is present, then fixed and covered by a
regression test that asserts the corrected behaviour. No model was called;
nothing live was touched (worktree, scratch and data copies on G: only).

Evidence files (outside the repository, `G:\dev (2)\dev\fi-p1-work\`):
`probes/test_repro_findings.py`, `evidence/repro-before.txt` (15/15 probes
reproduce on the reviewed code), `evidence/repro-after.txt` (12/15 fail on the
corrected code; the 3 that still pass are explained under F9, F10, F12),
`evidence/real-after.txt` (the corrected workflow on a copy of EP-30880).

Regression tests: `backend/tests/test_fa_review_fixes.py` (one or more per
finding, through the API where an endpoint exists).

## Dispositions

| id | sev | disposition | change | regression tests |
|---|---|---|---|---|
| F1 | BLOCKER | **Fixed.** A deterministic publication gate (`workflow.publication_gate`) decides `complete_candidate` at the end of a run **and again at accept**, on a fresh folder listing. It refuses: folder not reachable / not configured / not synced; a folder part not listed; an empty current set; any drawing present but not read and current; any drawing `failed`, `unread` (incl. not synced) or `stale`; a published drawing not current now and not retired (A4, path-level); a manifest drawing without an agent report; a read drawing whose agent is not `complete` (partial look, model unavailable); drawings changed since the run; an open conflict; a review not `completed`; any orchestrator signal that lowers (F4). Accept of a former candidate that no longer holds is refused (422, or 409 when only the drawings changed) and the run is set back to provisional with its reasons. The orchestrator stand-in in every test agrees and recommends `complete_candidate`, so the refusals are the gate's. | `workflow.py` gate/accept, `models.py` + migration `f1a3c5e7b9d2` (`publication_reasons`) | `test_F1_*` (corrupt FF via accept API; all drawings failed → never published; unread cloud-only; drawing added after the run; folder unreachable at accept; model unavailable = partial coverage; a complete run still accepted) |
| F2 | MAJOR | **Fixed.** Gate connection points are never taken from a `fa_ifc` source (S13 W-5); what it names is held. GB-package drawings unchanged. | `service._read_source` | `test_F2_*` |
| F3 | MAJOR | **Fixed.** A gate conflict stays listed after a `govern` (in `settled`, status `governed`, with every drawing's connection points, lane roles and settlement), so it can be reopened or re-governed. Every decision keeps the ones it replaced in `history`; `reopen` and `restore` no longer delete. `govern` requires a reason **and an authority** (whose confirmation it rests on), recorded on the rows it publishes. A governed choice whose drawing is no longer among the conflict's is not applied and says so. | `service._gate_rows`, `_assemble`; router `decide` | `test_F3_*` |
| F4 | MAJOR | **Fixed.** Any package-level (FP1) or run-level (FP2) `publication_recommendation` other than `complete_candidate`, any coverage `dispute`, any `rework_request` and any `missing_or_suspect` keeps the run provisional, each said; the run-level recommendation cannot override them. | `workflow._orchestrator_signals` | `test_F4_*` (4 cases) |
| F5 | MINOR | **Fixed.** Retry review is refused for an accepted, unfinished or fully reviewed run; a second accept is refused. | `workflow.claim_retry`, `accept` | `test_F5_*` |
| F6 | MINOR | **Fixed (not by failing closed).** Orchestrator answers are checked against the schema (`shape_problem`) inside the call path: a malformed answer is `invalid_output`, retried once, never cached (and a cached malformed answer is not reused); the review is `failed(invalid_output)`, the run **completes** provisional. | `assist._call` opt-in `accept` hook; `workflow.shape_problem` | `test_F6_*` (4 shapes; asserts 4 calls then 8 on the next run: nothing cached) |
| F7 | MINOR | **Fixed.** Readings record each sheet's viewport windows (`SCAN_VERSION` 5). A union across drawings needs the pair's landmark alignment **and** that floor's sheets viewing the same model space in both (S13 W-4); items placed by their label only are counted once only when they pair one-to-one within tolerance; otherwise the floor is held with its reason (`frames` / `views` / `positions`). Items the look set aside (door tags) never hold a floor. | `scan.py`, `service._equipment_rows` + helpers | `test_F7_*` (5) |
| F8 | MINOR | **Fixed.** Retry review is a job (`fa_interfaces_review`, 202); the day's bound is claimed by a compare-and-set before queueing; the retry sends the **frozen** package payloads and run-level view parts (`review_inputs`); refused (409) while a read or review runs. | router, `runners.run_interfaces_review`, `jobs` lane, `workflow.claim_retry`/`run_retry`, migration `f1a3c5e7b9d2` (`review_retries`, `review_retry_day`) | `test_F8_*` (3) |
| F9 | MINOR | **Fixed.** An exact CLI request is accepted only when `modelUsage` shows the requested model itself answering with output; no usage, Haiku only, or zero output is `model_unverified` (never a result; the review state `unverified`). `models_used` is unchanged (its probe still passes by design). | `provider.model_confirmed` | `test_F9_*` (4 + accepted + workflow) |
| F10 | MINOR | **Fixed; one part by contract.** (a) Scan, run and retry share one dedup key, so the job table's partial unique index admits one at a time atomically. (b) The orchestrator's budget is its **reserved** allowance (W-BUD): its own daily cap `FA_ORCHESTRATOR_MAX_CALLS_PER_DAY` (64, EXAMPLE) counted on its own calls in the usage log, so the agents' looks cannot starve it; the general compliance cap (60/day, which the drawing review's looks already exempt themselves from) is not applied to it — the reviewer's F10b probe therefore still passes, by design. A run whose orchestrator allowance cannot cover its review starts **no paid look**, said per drawing. (c) Accept re-checks open conflicts (F1 gate). | router `read_key`; `workflow.review_calls_today`/`review_allowance`; config | `test_F10_*` (3) |
| F11 | MINOR | **Fixed.** `missing_or_suspect` entries must name a package of the input (others dropped, noted) and an issue from the enum (else invalid output); links and markup in any free text are withheld. | `workflow._validate`, `shape_problem` | `test_F11_*` |
| F12 | MINOR (safe side) | **Kept on the safe side — contract amendment proposed (A1).** Gate barriers on several drawings count only when they agree (same frame, every point matched) or an engineer governs with an authority. The S13 W-5 sentence "equal totals are counted once, from the role-bearing drawing" is **not** implemented: it conflicts with S13 W-4 ("equal counts alone are never credited") and would credit EP-30880-like cases where equal totals sit at different places. | — | `test_F12_*` |
| F13 | MAJOR (cost) | **Fixed.** Only labels on floor-plan sheets are looked at (the only place a damper is counted); labels on a riser / schematic / outside every sheet are reported per drawing agent (`not_looked`: sheet, title, count, reason) and in the run panel. EP-30880: 132 → 77 Opus requests for the same drawings (SM-119 268 labels, M-08-101 2 labels not looked at). | `visual.wanted`/`not_looked`, agent report | `test_F13_*` (2) |

## Found during the evidence (not in the review)

| id | what | disposition | tests |
|---|---|---|---|
| N1 | The new gate compared published drawings by exact hash; EP-30880's published fire-alarm IFC reading (made by older code, DXF hash) never matched the new reading (register hash, none) — no run could ever be accepted. | The gate checks published drawings path-level, as the scan's own advance (A4): current now, or retired. | `test_N1_*` |
| N2 | Stage 0.1 `snapshot_source_current` had the same mismatch, so the page called an unchanged fire-alarm IFC drawing "not verified now". | A fire-alarm IFC reading matches a snapshot one by register identity (path, `fa_drawing_id`, revision, DXF size, upload time), hashes equal when both present. | `test_N2_*` |
| N3 | Concurrency tests on the tests' in-memory database (one connection shared by all threads, `StaticPool`) were flaky (1 in ~10). Production uses a file database (a connection per thread); the real-data runs used one with two agents side by side. | Tests serialise their database work while still measuring agents side by side; 30/30 repeated runs pass. | `test_drawing_agents_run_side_by_side_*`, the end-to-end test |

## Contract amendments for the reviewer to accept

- **A1 (F12):** S13 W-5 "Across drawings… equal totals are counted once, from the role-bearing drawing" is replaced by: gate barriers on several drawings of one floor are counted only when the drawings agree (verified frame, every point matched) or an engineer governs, giving a reason and an authority; otherwise held. (S13 W-4 "equal counts alone are never credited" applies to gates too.)
- **A2 (F10):** W-BUD's reserved allowance is a per-project daily cap on the orchestrator's own calls (`FA_ORCHESTRATOR_MAX_CALLS_PER_DAY`), not the general compliance cap; no paid look is started when it cannot cover the run's review.
- **A3 (F4):** `missing_or_suspect` lowers the run like disputes and rework requests do.
- **A4 (F6/F9):** W-FST adds `failed(invalid_output)` (shape-checked, never cached) and `unverified` (exact model not shown answering).
- **A5 (F3):** `govern` requires an authority; decisions are append-only with history.
- **A6 (F13):** the damper look covers floor-plan sheets only; other sheets' labels are reported, not looked at.

## Behaviour changes on EP-30880 (copy, stand-in answers; not accuracy)

| | before (`80b9603`) | after |
|---|---|---|
| Opus look requests | 132 | 77 |
| Fable calls | 8 | 8 |
| damper rows (on symbols) | 107 | 107 (anchor never the label) |
| B3 dampers | 2, symbols `5741B` / `5741D` | same |
| Gate Barrier GF | held | held, with each drawing's connection points and roles |
| Sliding doors GF (ACS ∪ FA) | 4 counted as a union | held: the two drawings' GF sheets view different model space (F7) |
| publication | provisional (Gate conflict) | provisional: open conflicts Gate Barrier GF, Sliding Doors GF |
| limitations said | — | SM 3 PDFs; ACS 1 PDF; GB 1 PDF; SM 23 / HVAC 7 labels not settled on one block symbol |

## Not changed

- The EP-30880 Gate Barrier conflict stays **held**; no drawing is chosen.
- No live database, migration, service, drawing, Desktop or `ep-platform-merged` change.

## Round 2: the independent re-review of `180fd1f`

The re-review did not reach a verdict (its session ended mid-way), but its probes
(`fi-p1-work/review2/probes/test_review2_probes.py`) showed four residual defects
on `180fd1f`, and two observations. Each was reproduced by its probe on `180fd1f`,
fixed, and covered by a test that fails on `180fd1f` and passes now
(`evidence/r2-tests-before.txt`, `evidence/review2-probes-after-r2fix.txt`: every
`OK_*` probe still passes, every `DEFECT_*` probe now fails).

| id | sev | finding | disposition | regression tests |
|---|---|---|---|---|
| A5 | HIGH | A gate conflict (and any conflict between drawings) could be settled by a count (`resolve` with a qty) or dismissed through the API with no reason and no authority, publishing gate CR rows without the authority `govern` requires. | **Fixed.** `resolve` and `dismiss` of a conflict need a reason and an authority, recorded in the decision (with its history) and in each resolved row's evidence. Gate conflicts stay govern-only in the page; ENTRY/EXIT evidence is kept. | `test_A5_*` |
| W4 | MED (obs.) | A W-4 conflict (`CONFLICT|…`: drawings in unverified frames or different views, no drawings list) blocked acceptance and the page offered no way to settle it -- its own text asks "say how many there are". EP-30880's Sliding Doors GF is one. | **Fixed.** The page offers the count / not-an-interface for a W-4 conflict, asking the reason and the authority (A5). | `test_W4_*` (settled on an authority, the next run is a candidate and is accepted) |
| F10-r | MED | Looks were paid for when the route could not serve the orchestrator's model exactly; the review was then missing. | **Fixed.** Before any look, the orchestrator's model must be servable exactly as well as its allowance having room; otherwise no look, said in each agent's coverage reason. A Retry later completes the review but the run stays provisional (its drawings were never looked at); a new run covers them. | `test_F10_no_look_is_paid_for_when_the_route_cannot_serve_the_orchestrator`; `test_without_fable_…` updated to this |
| F8-r | LOW | A Retry whose job could not be queued (a read queued between its check and its enqueue) was refused with 409 but still spent one of the day's retries. | **Fixed.** The claim is given back by compare-and-set on the count it took. | `test_F8_a_retry_refused_when_its_job_cannot_be_queued_…` |
| A3-r | MED | The prompt asks Fable to name "a package with no drawing"; any `missing_or_suspect` lowered the run (amendment A3), so a project that legitimately lacks a package could never be accepted. | **Fixed.** A `source_missing` item naming a package with no drawing of any kind (no sources, no unread files, nothing stale) restates what the package report already shows and does not lower the run; it stays in Fable's proposal on the page. Every other item still lowers, including `source_missing` on a package with files (e.g. only unread PDFs -- a coverage limitation). Amendment A3 is narrowed accordingly. | `test_A3_*` (3) |
| F13-o | -- (obs.) | A floor-plan sheet whose floor is not identified is still looked at. | **Kept, deliberately.** Its labels become verification items the engineer places on a floor; the look decides whether each is a damper and where its symbol stands, which that answer needs. Only non-plan sheets (risers, schematics) are skipped (A6). | -- |

Contract amendments added: **A3 (narrowed)** as above; **A7 (A5/W4):** settling any conflict between
drawings -- governing, a count, or not an interface -- needs a reason and an authority.
