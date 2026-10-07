# M5 safe Apply: implementation of ORCH-039 (U2-M5-SAFE-APPLY)

Role: ep-implementer (Claude Opus 5.5, high effort), fresh and isolated. Date: 7 October 2026.
Branch `task/m5-safe-apply`, worktree `G:/dev (2)/dev/ep-platform-merged/wt-m5`, created from `roadmap/u2` at
`f15ac011e14612477a805625d14446430ed75d30` (code equal to 668f92f: `git diff 668f92f f15ac01` touches docs only).
Implementation commit: `c274205`. Evidence: `evidence/safe-apply/` (hashes in its `MANIFEST.json`).

Inputs read, in the card's order: the ORCH-035 disposition and findings; M3 decision pack rows OD-14..OD-17;
the M3 policy contract (B-14, B-15, B-16, P-07); roadmap section 8 M5; the candidate. The candidate was rebuilt in
scratch from `b5c2222` + `rdm2-candidate.patch` (v2.1 hashes reproduced: service `facccdf8…`, Apply tests
`934ab357…`, cad `43672b30…`, verify `449ad1af…`) + `RDM2-R1-correction.patch` (git blobs `b8e161b`, `b3480d4`
reproduced). Nothing under `docs/milestones/redesign/` or M1-M4 was edited.

Evidence classes: FUNCTIONAL-MOCKED (stand-in AutoCAD = a Python script echoing the script and printing markers;
stand-in read-back = the source DXF with the script's inserts/erases applied) and SQLITE (the suite's real
file-backed WAL database, two real connections). **No REAL-AUTOCAD and no REAL-MODEL claim is made.** A passing
suite is evidence, not acceptance.

## Requirement -> change -> test -> result

| Requirement (card) | Change | Test(s) in `tests/test_redesign_apply.py` unless named | Result |
|---|---|---|---|
| cad.py, verify.py byte-identical to v2.1 | copied; committed blobs hash `43672b30…`, `449ad1af…` (LF) | script tests 9-12 of the candidate; `test_redesign.py` | pass |
| `to_cad`, `module_library` as in the candidate | ported; source text identical to the candidate (AST comparison) | `test_ct1_ct2_and_cr_resolve…`, `test_a_stored_office_pc_path…`, `test_an_unknown_module_code…` | pass |
| Confirmation rule | `requires_confirmation`, `_drawn`, `adjust(confirmed=)`, `view`, readiness blocker, `ChangeIn.confirmed` | `test_a_spot_to_confirm…`, `test_a_moved_approved_change_stays_approved_and_its_confirmation_is_asked_again`, readiness test | pass |
| Snapshot + refusal guards; stale | `content_fingerprint`, `_snapshot` (taken after Apply's own "making" write), `apply_request`, `_refusal`; compare under the lock -> `ApplyStale` | `test_approvals_changed_while_autocad_worked…`, `test_a_job_asked_for_before…`, `test_a_changed_source…`, recovery and second-job tests | pass |
| Relative, unique, exclusive outputs | `output_file_for`, `_unique_output`, `_stage` (O_EXCL) + `_finalize` (hard link, or Windows rename; never overwrites) | `test_two_applies…`, `test_an_existing_output_is_never_overwritten`, `test_the_output_is_stored_relative…` | pass |
| Read-back, markers, fail on incomplete scripts | `cad.run`, `verify`, `_readback`, `_source_readback` | parametrised refusal test (5 cases), markers/echo tests, `test_an_unexpected_erasure…` | pass |
| Correction's `apply()` structure | kept: final compare, rename and state change in one write transaction; cleanup of a file whose commit failed | `test_a_commit_failure_after_exclusive_publication_removes_the_output` | pass |
| Runner and router | runner passes `request`, `job_id`, `job_created_at`; `start_apply` -> 422 when `readiness()` is not ready or nothing is drawn; params carry the snapshot | `test_the_apply_endpoint_refuses_with_422…`, `test_the_real_readiness_refuses…`, `test_nothing_approved_means_no_apply_job`, `test_the_page_says…`, `test_prep_readiness.py` | pass |
| RedesignPanel wording | "Proposed, not drawn until approved", "Confirm this spot", "held until you approve it", stale / refused / nothing published, "published separately to the project archive"; no "filed in" | `tsc --noEmit` on a scratch copy: 0 errors (`tsc-frontend.txt`) | type-checks; not rendered |
| OD-15 a: no archive write by Apply | archive copy removed from `apply()` | `test_apply_never_writes_into_the_project_archive` | pass |
| OD-15 a: explicit publication | `service.publish()`, `POST …/publish`: only an output a succeeded Apply job made and whose `verification.json` says ok; staged then no-overwrite rename; 409 when the name exists; ActivityEvent `redesign.published` (user, time, file, sha256, job); `output_relative` set | `test_publishing_to_the_archive_is_explicit_unique…`, `test_only_a_verified_copy_can_be_published…`, `test_publish_needs_an_editor` | pass |
| OD-17 b | modules resolved by code from the active `LIBRARY` in `to_cad` (script time); stored paths untouched | `test_library_paths_with_spaces_are_resolved_at_script_time…`; `test_redesign.py` library test | pass |

## Disposition fixes applied while porting

- U2M5-02/04: the DWG is copied to `.<name>.part` (exclusive, fsync) **before** the lock; inside `BEGIN IMMEDIATE`
  only the snapshot compare, the no-overwrite link/rename and the commit. Proved by
  `test_the_dwg_copy_holds_no_database_lock…` (an unrelated-table write during the copy completes in < 1 s).
- U2M5-03: the last `check()` runs before the lock; no `check()`/`progress()` inside it.
- U2M5-04: `sweep_orphans()` removes stale `.part` files and moves final-named outputs no row or succeeded job
  refers to into `redesign/orphaned/` (never deleted); skips projects with an active Apply; files younger than
  15 minutes are left. Runs in the IFC worker's housekeeping (start-up and every 30 s, slot 0).
- U2M5-07: no BOM in `service.py` (`test_service_py_has_no_byte_order_mark`).
- U2M5-09: failed, stale, refused, cancelled attempts change only `output_status`/`output_error`;
  `last_output()` serves the earlier copy (`test_a_failed_attempt_and_a_stale_one_leave_the_earlier_copy_downloadable`).
- U2M5-10: `refresh()` is no longer called by Apply; changes placed by an earlier version are refused
  (`test_apply_never_places_or_coordinates_again…`, `test_a_change_placed_by_an_earlier_version…`).
- U2M5-14: gate at the server boundary (422), and `readiness()` remains the first refusal inside the job
  (recorded as `refused`; the output is left as it was).

## Concurrency evidence (file-backed SQLite, WAL, app busy timeout 15 s, two real connections, `apply()` in a thread)

- (a) `test_concurrent_publication_an_edit_started_inside_the_window_waits…`: Apply is held at the rename inside the
  lock; an approval PATCH (service `adjust`, bypassing the 409 guard) on a second connection does not commit for
  1.5 s; after release Apply commits `made` with the pre-PATCH fingerprint and the new approval is kept.
- (b) `…an_edit_committed_before_the_lock_makes_the_apply_stale…`: PATCH committed after staging, before the lock:
  `stale`, no output and no `.part` left, newer approval kept.
- Mutation M1 (lock removed, the pre-RDM2-R1 read restored), run on c274205's code and restored byte for byte
  (sha `ddccfe85…` before and after): **2 failed** - (a) "an approval committed inside the publication window" and
  the candidate's lock-primitive test; (b) passes, as expected (it proves the compare, not the lock).
  `mutation-M1-lock-removed.{log,xml}`.
- Mutation M2 (the copy moved inside the lock): the unrelated-writer test **fails** with "database is locked".
  `mutation-M2-copy-inside-lock.{log,xml}`. Control after restore: 4 passed.

## Runs (`runs.txt`, `targeted.*`, `full-suite.*`)

- Baseline at f15ac01 before the port: `test_redesign.py` + `test_drawing_prep.py` 30 passed (log not kept; cad.py was copied in after collection, so the run used the old modules). The disposition records the same 30/30.
- Targeted on c274205 (`test_redesign_apply`, `test_redesign`, `test_drawing_prep`, `test_prep_readiness`):
  **93 passed** (59 + 16 + 14 + 4). The 30 earlier tests stay green; `test_redesign.py:78` is replaced by the
  stricter `ep_erase` assertion, not deleted.
- Full suite on c274205 (M4 command shape, `AI_ENABLED=false DATA_ROOT=`): **1878 tests, 1842 passed, 1 failed,
  35 skipped**, 2091.65 s. Against M4 run 2 (1819 tests, 2 failed): no new failure;
  `test_proposed_materials::test_the_part_catalogue_knows_every_number…` fails with the same message as the
  baseline; `test_persistence::test_a_data_root_gathers…` no longer fails (the M4 `_env_file=None` repair is in
  this base and wt-m5 has no `.env`). `full-suite-comparison.json`.

## Adaptations (and why)

- `service.py`: not the candidate file; functions ported onto the bb5871d code. `requires_confirmation`, `_drawn`,
  `_snapshot`, `_locked_publish_row`, `_publish` keep the candidate's logic with edited docstrings; `_refusal`
  returns `(reason, already_made)` so only a changed-request refusal is recorded; `apply()` adds `readiness()`
  first, the stage-then-rename publication, a source-hash re-check after the run, and keeps the earlier output.
- `test_redesign.py` library assertion updated for OD-17 b (it pinned the stored `C:/lib` path); `test_prep_readiness`
  first test now expects the 422 at the endpoint instead of a failed job (card requirement).
- The 37 candidate tests are unchanged except the fixture, which stubs `readiness()` "ready" so `_drawn` is tested
  on its own; real `readiness()` is tested separately (every blocker, plus the fixture refused for real).
- `.gitattributes`: `docs/milestones/M5/** -text`; `*.log` evidence force-added.

## Exit conditions only real AutoCAD can prove (OD-16 c run, to be scheduled by the owner)

1. Approved inserts and erases reconcile exactly against a Core Console read-back of the saved copy.
2. A missing block ("Function cancelled") or a mid-script LISP error, and the count check before QSAVE, publish nothing.
3. The standalone completion marker is recognised against a real `autocad.log` echo (nonce-bound).
4. The saved output is a valid DWG that opens and reads back.
5. Library paths with spaces (and parentheses) resolve and insert in a real `-INSERT name=path`.
6. Cancel or timeout kills the real Core Console process and publishes nothing.
7. The source drawing's sha256 is unchanged afterwards.
8. Hard-link creation on the target volume (`os.link`; Windows-rename fallback) and the archive volume, if it is a
   synced folder.

## Limitations

- The non-SQLite `with_for_update` path is untested (U2M5-08).
- A real crash between rename and commit was not produced; the sweep is tested on the files such a crash leaves.
- The frontend was type-checked, not rendered or exercised in a browser.
- `refresh()` stays in the module, unused by Apply.
- The independent review of this port is still required (U2M5-06).
