# M2 Review 11: the reviewer's sequences, before and after

- **The script:** the reviewer's `retention_probe.py`, unchanged except for its root and output folder. It pushes synthetic evidence through the real merge, the real selection and the full evaluator, with no provider and no document.
- **Before:** on `frozen-r10` (`a34d3f8`). This **reproduces** the reviewer's `retention-probe-results.json` exactly (compared after removing CR).
- **After:** on `frozen-r11` (`a977364`). This is **new**.
- **Files:** [`evidence/probes/`](evidence/probes/).

## A. History pruning: ANN read with revision 02, then revision 03 re-read

| Actual read | `a34d3f8`: association / decision recovery | `a977364`: association / decision recovery |
|---|---|---|
| 2 | `held:revision_changed` / `held_only` | `held:revision_changed` / `held_only` |
| 3 | `held:revision_changed` / `held_only` | `held:revision_changed` / `held_only` |
| 4 | `held:revision_changed` / `held_only` | `held:revision_changed` / `held_only` |
| 5 | `held:revision_changed` / `held_only` | `held:revision_changed` / `held_only` |
| **6** | **`current` / `recovered_clean`** (revision 02 left history) | `held:revision_changed` / `held_only` |
| 7 | `current` / `recovered_clean` | `held:revision_changed` / `held_only` |

**Control** (an explicit `target_revision=02`): `held:revision_changed` / `held_only` in both.

## B. Attempt-number collision: a legacy targetless revision at attempt 13, identity re-read as X-SD-9

| Actual read | Caller's attempt number | `a34d3f8` | `a977364` |
|---|---|---|---|
| 14 | 13 | `held:context_changed` / `missed` | `held:context_changed` / `missed` |
| **15** | 13 | **`not_recorded` / `recovered_clean`** | `held:context_changed` / `missed` |
| 16–20 | 13 | `not_recorded` / `recovered_clean` | `held:context_changed` / `missed` |

**The attempt number this probe shows.** The probe supplies its own attempt number: it imitates the old stage expression `len(attempts) + 1`. The candidate keeps that number for display and orders by its own persistent `seq`. In the real stage (`evidence_stage`), the attempt number is the `seq` itself, so the persisted test sees unique, increasing numbers (see REGRESSION.md).

## The reviewer's association probe and earlier probes

- **The association probe** (`association_probe.py`), on `frozen-r10` (reproduced exactly) and `frozen-r11` (new): all five cases are **identical**.
  - `legacy_unchanged_control`: `correct` / `recovered_clean`.
  - `legacy_changed_identity`: `held_unassociated`.
  - `recorded_target_control`: `held_unassociated`.
  - `review08_revision_without_target`: `held_unassociated`.
  - `known_revision_without_identity`: `held_correct` / `held_only`.
- **The earlier probes** (`probes.py`: illegible reads, missing hash, heading and zero, explicit changed target), on `frozen-r10` (reproduced exactly) and `frozen-r11` (new): **identical**.
