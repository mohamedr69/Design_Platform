# Idempotency, Recovery and Cancellation (F016, F017, F033, F034)

## What an Apply job carries

At POST time (`routers/redesign.py:106`), `apply_request()` stores three things in the job's `params`, beside `drawing_id` and `user_id`:
- `source_sha256`: the redesign row's source hash;
- `fingerprint`: the content fingerprint of the decision snapshot (`CONCURRENCY-GUARD.md`);
- `drawn`: the number of changes to make.

The runner passes `request=job.params`, `job_id` and `job_created_at` to `apply()` (`runners.py:279`). No column or migration is added.

## Refusals before anything runs

`_refusal()` (`service.py:1475`) is checked first. A refusal raises `ApplyRefused`, which the runner turns into a failed job with the message. **The redesign row is not touched**, so a "made" output stays "made".

| Refusal | Condition |
|---|---|
| Already made | `row.output_status == "made"` and `row.output_at > job.created_at`. This is RD-M1 F017: job 119 had made `…1654.dwg` at 12:55:35, after it was created at 12:54:19; its worker stopped, and the copied DB still said "running". |
| Source changed | `params.source_sha256 != row.source_sha256` |
| Decisions changed | `params.fingerprint != content_fingerprint(row)`: the job was asked for before approvals or placings changed |
| Same set already made | a succeeded Apply job of the same project and drawing whose `result.fingerprint` equals the current one and whose output file still exists |

A stale worker is not treated as a failed business operation. `jobs.recover_stale` is unchanged: it still requeues the job, and the Apply decides from the redesign row whether its work was already done.

Separately, at run time `apply()` refuses (as `ApplyError`, before AutoCAD) when the source file's hash differs from `row.source_sha256`, or when an approved change was placed by an earlier version (no `seen`/`placed`).

## Unique, never-overwritten outputs (F033, F016)

- Name: `<drawing stem> <rev> - Redesign <UTC YYYYmmdd-HHMMSS-ffffff>Z d<drawing id> s<source sha256[:12]> j<job id>-<10 random hex>.dwg` (`_unique_output`, `service.py:1531`).
- Written with `os.open(O_CREAT | O_EXCL)` (`_publish`, `service.py:1538`): an existing file raises `ApplyError` and is left byte-identical. A partly written file is deleted.
- Stored as a path **relative** to the uploads root (`row.output_path`). `output_file_for()` (`service.py:1503`) resolves it, rebases an older absolute path from another PC at its `EP-<n>` component, and returns `None` for anything that resolves outside the uploads root. `GET output.dwg` uses it, so an older PC-A path now downloads the file that is on this PC (RD-M1 F016).
- Each Apply has its own run folder, `redesign/runs/<apply id>/`: script, full AutoCAD log, `verification.json` and the read-back DXF. The work copy is deleted only after a successful publish; on failure it stays as evidence.

## Cancellation (F034)

`check()` is called:
1. before anything is touched (after the refusals);
2. before the run folder and AutoCAD;
3. inside `cad.run` before `Popen`, then about once a second while AutoCAD works (`POLL_S`);
4. after AutoCAD returns;
5. before and after the read-back conversion;
6. after verification;
7. before the snapshot re-check and publication.

On `jobs.Cancelled` while AutoCAD runs, the process is killed, its output is collected and written to `autocad.log`, and the error passes on. `apply()` sets `output_status = "cancelled"` ("nothing was published; the run's log is kept") and re-raises, so the job ends `cancelled`. `jobs.Interrupted` (the worker stopping) gives `interrupted`. A cancel before anything starts leaves the row untouched.

## Tests

`test_a_completed_apply_is_not_run_again_after_worker_recovery` reproduces job 119 in an in-memory DB: a job created 26 h earlier, its row made 76 s after creation, `recover_stale` requeues it, and the real runner refuses ("already made") without starting AutoCAD. Also: `test_the_same_approved_set_is_not_made_twice_by_a_second_job`, `test_a_changed_source_is_refused`, `test_a_job_asked_for_before_the_approvals_changed_is_refused`, `test_two_applies_in_the_same_minute_get_two_files`, `test_an_existing_output_is_never_overwritten`, `test_the_output_is_stored_relative_and_read_back_safely`, `test_an_older_absolute_path_from_another_pc_is_found_under_this_uploads_folder`, `test_a_cancel_before_autocad_runs_nothing` and `test_a_cancel_while_autocad_works_stops_it_and_publishes_nothing` (a real child process is killed mid-run).
