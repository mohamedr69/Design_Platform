# Apply Snapshot Guard (owner decision 5; Apply part of F032; part of F030)

## Fingerprint

`content_fingerprint(row, source_sha256)` (`service.py:1450`) is the SHA-256 of canonical JSON (sorted keys, compact) of:
- the source drawing hash;
- the ordered (by id) **drawn set**, each with:
  - id, status, `confirmed`, `needs_confirmation`, action, `moved`, `edited` and interface code;
  - the remove target (`n`, `handle`, `block`, `erasable`);
  - the insert (`block`, `layer`, `scale`, `rotation`, `model`, `seen`, `make`);
- every change's `[id, status, confirmed]`, sorted. A change approved, skipped or confirmed anywhere in the redesign therefore changes the fingerprint, even if it is not drawn.

`_snapshot()` adds the row's `updated_at`, which `onupdate` moves on every write to the row.

## Where it is checked

| When | Compared | On mismatch |
|---|---|---|
| Job start (`_refusal`) | job `params.fingerprint`, taken at POST, vs the current content fingerprint | `ApplyRefused`: nothing runs; the row is untouched |
| After AutoCAD and verification, before publication (`service.py:1665-1669`) | snapshot taken after the "making" commit vs one recomputed from a fresh read of the row (`db.expire_all()`) | `ApplyStale`: `output_status = "stale"`, the output **not published**, the run folder kept as evidence; a new Apply is required |

No merge is attempted. Apply itself writes the row only twice: "making" before the snapshot, and the final status after the comparison.

## Why Apply no longer calls `refresh()`

Before RD-M2, Apply called `refresh()`, which re-placed changes from an earlier placing version and re-ran coordination, then committed. That changed positions the engineer had not seen (F030) and moved `updated_at` under the snapshot. Apply now makes exactly the stored, approved placings. If an approved change was placed by an earlier version (no `seen`/`placed`), Apply refuses and asks for the change to be placed again. RD-M1 showed that re-running coordination on GC-01's stored plan changes no position (E18), so GC-01's drawn set is identical either way.

## Not addressed (out of scope)

Plan's whole-row rewrite during a long Plan, and PATCH-vs-PATCH races, are general Plan/PATCH concurrency (F032 outside Apply) and are unchanged. The guard only ensures that an Apply never publishes a result made from a snapshot that is no longer current.

## Tests

`test_approvals_changed_while_autocad_worked_are_not_published`: another DB session approves a change while the read-back runs, and the result is `ApplyStale`, status "stale", with no output file. Also `test_a_job_asked_for_before_the_approvals_changed_is_refused`.
