# Portable Module-Library Resolution (owner decision 4; F001)

## Rule

`module_library(code, change_id)` (`service.py:423`) returns the module's block file **in this installation's** `app/redesign/library` folder:

1. The code must be listed in that folder's `modules.json` (today CR, CT1 and CT2) and must match `^[A-Z0-9]{1,8}$`. This rejects `../CR`, lower case, empty values and unknown codes.
2. The path is `(<library>/<code>.dwg).resolve()`. It must sit directly in the resolved library folder and end in `.dwg`.
3. It must exist and be a regular file.

Any failure raises `ApplyError("Change <id>: …")`, naming the change and the code but not the stored legacy path.

`to_cad()` (`service.py:1336`) calls `module_library` for every insert of an interface change, and for any insert that carries a `library` key. The stored `insert.library` is never read for execution. The dict passed to `cad` is a copy with the resolved path, so the stored value stays in the database unchanged, as history (owner decision 4). A library insert with no interface code is refused.

Resolution happens in `apply()` before the run folder is made and before AutoCAD starts (`service.py:1638`), so a missing library file fails the job with no AutoCAD process.

## GC-01

| | |
|---|---|
| Approved changes carrying an office-PC (PC-A) library path | 5 (RD-M1 E05); the 6th carries one too but is `proposed` |
| Paths in the generated script | the current library only. The isolated AutoCAD run used a frozen copy at `…\code (2)\backend\app\redesign\library\`, a path with a space and parentheses like the real install (`AUTOCAD-VALIDATION.md`) |
| Stored values after Apply | unchanged |

## Tests

`test_ct1_ct2_and_cr_resolve_from_this_installations_library`, `test_a_stored_office_pc_path_never_reaches_the_script`, `test_an_unknown_module_code_is_refused`, `test_a_missing_library_file_is_refused_before_autocad` (asserts that the fake AutoCAD was never launched), and the updated `test_a_library_block_is_brought_in_from_its_file_only_by_the_first_insert_and_noted`.
