# Output Verification (F023)

An Apply's copy becomes a result only when **every** check passes (`verify.verify`, `verify.py:94`). Otherwise `apply()` raises `ApplyError("…did not verify…: <problems>")`, sets `output_status = "failed"`, and the copy stays in the run folder as diagnostic evidence. It is never published or stored as the output.

| # | Check | Source |
|---|---|---|
| 1 | AutoCAD exit code is 0. Necessary but **not sufficient**: the validation showed exit code 0 after a script that AutoCAD cancelled | `CadRun.returncode` |
| 2 | No `EP-RD-FAIL:<nonce>` marker. Markers count only as **whole lines** (v2): the Core Console echoes a top-level expression's value, so a printed marker also comes back once as a quoted string (seen in the AutoCAD validation) | `parse_log` |
| 3 | No `EP-RD-NOSAVE:<nonce>` marker | `parse_log` |
| 4 | Exactly one `EP-RD-OK:<nonce>`, whose counts equal the expected inserts and erases of the approved set | `parse_log`, `cad.expected_counts` |
| 5 | The copy exists and its SHA-256 differs from the source's | `CadRun.copy_sha256` / `source_sha256` |
| 6 | Read back: the copy is converted to DXF by the platform's own converter (`convert.convert_dwg_to_dxf`, into a temp folder, then into the run folder) and opened with ezdxf. It is compared **by model-space handle** with the *source DWG read back by the same converter* (cached once per source hash as `redesign/source-readback-<sha256[:16]>.dxf`). The stored DXF another PC's converter made is not used, so the comparison is like for like | `_source_readback`, `_readback`, `verify.reconcile` |
| 6a | every expected erase is gone | `not_erased` must be empty |
| 6b | nothing else in model space is gone | `unexpected_erasures` must be empty |
| 6c | every expected insert is a **new** INSERT of its block within 0.001 units of its insertion point | `inserts_missing` must be empty |
| 6d | no other new INSERT exists | `unexpected_inserts` must be empty |
| 7 | the decision snapshot is unchanged (`CONCURRENCY-GUARD.md`) | `_snapshot` |

Read-back runs only when checks 1, 2 and 4 already pass, so a failed run costs no second AutoCAD process. If the read-back cannot be made (no source DXF, conversion error, unreadable DXF), verification is **incomplete**, and that is a failure ("could not be read back").

New CIRCLE and TEXT entities (markers, labels, module notes) are counted in `added_by_type` and reported, not failed: the marker count follows the approved set.

Everything is written to `runs/<apply id>/verification.json`:
- ok and problems;
- parsed markers;
- the read-back reconciliation;
- return code and nonce;
- source and copy hashes;
- the expectation.

The full AutoCAD log is `autocad.log` in the same folder.

Not checked by the product: changes to the attributes of existing entities. The AutoCAD validation compared them as extra evidence: the only differences were AutoCAD's renumbering of anonymous `*U` blocks (identical content) and one floating-point normalisation (`AUTOCAD-VALIDATION.md` section 3). An attribute check that tolerates those is proposed for later (`NEXT-MILESTONE-HANDOFF.md`).

## Tests

`test_the_markers_are_this_runs_and_never_the_echo`, and `test_an_unchanged_unreadable_or_incomplete_output_is_refused`, which covers:
- the copy unchanged;
- no completion marker;
- exit code 3;
- an unreadable read-back;
- a missing insert in the read-back.

Also `test_an_unexpected_erasure_in_the_read_back_fails_the_apply` and `test_the_approved_changes_are_made_checked_and_kept`. The real-AutoCAD read-back of GC-01 is in `AUTOCAD-VALIDATION.md`.
