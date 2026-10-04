# Fail-Closed CAD Script (F004)

## The problem (RD-M1)

The old script ran, for every insert:
- `(command "_.-INSERT" … 1.0 …)`
- `(setq ep_f (cdr (assoc 41 (entget (entlast)))))`
- `(entdel (entlast))`

then inserted again at the true scale, and ended with a bare `_.QSAVE`. A line that errors in the Core Console ends only that line; the next one still runs. After a failed insert, `(entlast)` was the **previous** entity (a marker, or, for the first insert of the script, the last entity of the original drawing), and it was deleted.

## The contract (`cad.script_lines`, `cad.py:88`)

Every step is one top-level line, guarded by `(if (not ep_failed) …)` and checked by the next line:

| Step | Line(s) | Safeguard |
|---|---|---|
| Before an insert | `(setq ep_b (entlast))` | the state immediately before |
| Measuring insert at scale 1 | `(command "_.-INSERT" <name or name=library> "_S" 1.0 …)` | if it errors, only this line ends |
| Check + measure | `(ep_new_insert ep_b <block> <id>)`: `(entlast)` must differ from `ep_b`, be an `INSERT`, and its group-2 name must equal the block (case-insensitive). Only then `ep_f` is read and **that entity** is `entdel`-ed | otherwise `ep_fail "insert"` |
| True-scale insert | `(command "_.-INSERT" <block> "_S" (/ scale ep_f) …)` | guarded |
| Check | `(ep_new_insert …)` again; counted in `ep_ins` | otherwise `ep_fail "insert"` |
| Erase | `(ep_erase <handle> <block> <x> <y> 0.01 <id>)`. The handle must resolve to an `INSERT` of the expected block, not in paper space (group 67), with layout `Model` (group 410), and within 0.01 drawing units of the insertion point the IFC reading found. Then `entdel`; the entity must be gone; counted in `ep_del` | otherwise `ep_fail "erase-target"` / `"erase-verify"`; nothing else is erased |
| Markers, labels, notes | `(ep_make (list …) <id>)` | `entmake` returning nil → `ep_fail "entmake"` |
| New WP block | `ep_copy` guarded by `ep_failed` | a missing source block leaves the later insert to fail its check |
| Count | `(if (and (not ep_failed) (or (/= ep_ins N) (/= ep_del M))) (ep_fail "count" "all"))` | N and M are computed by Python from the approved set |
| Save | `(if (not ep_failed) (progn (command "_.QSAVE") (setq ep_saved T)))` | there is **no bare `QSAVE` line** |
| Outcome | `EP-RD-OK:<nonce>:<ins>:<del>` if saved, else `EP-RD-NOSAVE:<nonce>`; each failure prints `EP-RD-FAIL:<nonce>:<step>:<change id>` | printed with `(strcat "EP-RD" "-OK:" …)`, so the Core Console's echo of the script never contains the joined marker |
| End | `_.QUIT` / `_Y` | not saved: QUIT discards the copy's changes |

The nonce is 16 random hex characters per run (`secrets.token_hex(8)`). Python accepts only markers carrying the run's own nonce (`verify.parse_log`).

## The runner (`cad.run`, `cad.py:246`)

- Creates `runs/<apply id>/` with `exist_ok=False`: a run never shares or reuses a folder.
- Copies the source into it and refuses if the copy's path equals the source path. AutoCAD is only ever given the copy.
- Runs `accoreconsole /i <copy> /s <script> /l en-US` with `cwd` set to the run folder, via `Popen`; polls every `POLL_S` (1 s); calls `check()` each poll; kills it after `TIMEOUT_S` (1200 s) or on cancel.
- Writes the complete log to `autocad.log` in every case (success, failure, cancel, timeout).
- Promotes nothing; promotion is `service.apply`'s, after verification.

## What AutoCAD did with it

See `AUTOCAD-VALIDATION.md`: one isolated GC-01 run with the real Core Console, a successful case and a first-insert-missing case.

## Tests (static, on the script text, and with a stand-in AutoCAD)

`test_a_failed_insert_stops_before_any_entdel_or_save`:
- no `(entdel (entlast))`;
- every `entdel` is the just-checked new insert;
- every step is guarded;
- every insert line is followed by its check;
- the count check comes before the only `QSAVE`, which is guarded.

Also `test_an_insert_failure_in_autocad_publishes_nothing`, `test_an_erase_is_made_only_on_the_symbol_meant` and the updated `test_the_autocad_script_erases_inserts_at_the_true_scale_and_marks_each_change`.

## Observed with the real AutoCAD 2027 (`AUTOCAD-VALIDATION.md`)

- On GC-01's 11 approved changes, every `ep_new_insert` check passed: library blocks resolved from the current library at a path with a space and parentheses; the count was 11/0; the guarded `QSAVE` returned `T`; the run's OK marker was printed.
- On a failed first `-INSERT` (missing block), AutoCAD printed `; error: Function cancelled` and **stopped reading the script**. Nothing after it ran and nothing was saved, and the process still exited with code 0. The RD-M1 F004 continuation hazard therefore does not occur in this build. The guards stay as defence in depth, and success is decided by Python, never by the exit code.
- `_.QUIT` / `_Y` answers "Really want to discard all changes to drawing?", so an unsaved copy is discarded, not saved.

- Session 2, control C: on a disposable copy, `ep_erase "5DD10" "CEILING SPEAKER" 1309.2 155.93 0.01` passed its checks (INSERT, block, model space, within 0.01 of the read insertion point). Only that entity was erased (read-back), and the count was 0/1.

## Limits

A wrong-target erase (a handle of another block, in paper space, or out of position) was tested only as script text and by unit tests, not with the real AutoCAD.
