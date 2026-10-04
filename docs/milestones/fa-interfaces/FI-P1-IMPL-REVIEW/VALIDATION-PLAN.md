# FI-P1 bounded real-model validation — recorded scope (NOT RUN)

Status: **not authorised to run.** The review verdict is CHANGES REQUIRED
(REVIEW.md). This plan runs only after every entry gate below is met and the
owner approves this scope. Any change to scope or limits is recorded here
first.

## Entry gates (all required)

| gate | condition | how checked |
|---|---|---|
| G1 code | F1 fixed with tests (a present non-current drawing, an empty or narrowed read set -> provisional and accept refused); F2, F3, F4 fixed with tests; F13 (no looks on non-plan sheets) fixed; focused suites and full suite = baseline | independent re-review PASS on the new HEAD |
| G2 route | `AI_CLAUDE_CLI` set to an existing Claude Code >= 2.1.280 (owner action D1), `claude --version` recorded | `ClaudeCodeProvider.supports("claude-opus-5-5", exact=True)` and `("claude-fable-5-1", exact=True)` both true |
| G3 disk | >= 5 GB free on C: (now ~0.5 GB) | `df` before start |
| G4 isolation | sandbox DB and sandbox folder created; live DB hash of `project_fa_interfaces` row 5 recorded (read only) | before / after comparison |

## Sandbox

- Database: SQLite backup of the live DB opened `mode=ro` into
  `scratchpad\validation\sandbox.db`, upgraded to head there. Sandbox
  project 5 `source_folder_path` points at the sandbox folder (in the sandbox
  DB only). `UPLOADS_ROOT` = a scratch copy holding the existing DXF
  conversions (same sha256, so no conversion and no change of evidence).
- Folder: byte copies (hash-verified against the originals) of exactly these
  documents into `scratchpad\validation\EP-30880\03- Drawings\IFC\...`, same
  relative paths:

| package | document | sha256 prefix |
|---|---|---|
| SM | `Mechanical/.../SMOKE LAYOUT.dwg` | `fe304ccf33fa` |
| HVAC | `Mechanical/.../VENTILATION LAYOUT.dwg` | `8eea8dd66621` |
| GB | `Electrical/GB/BINGHATTI TITANIA GATEBARRIER SYSTEM LAYOUT.dwg` | `eda8dd8d0747` |
| GB | `Electrical/GB/Shop Drawings-Titania rev01.dwg` | `a7fb4efa61a6` |
| ACS | `.../BINGHATTI TITANIA ACCESS CONTROL SYSTEM LAYOUT & SCHEMATIC DIAGRAM.dwg` | `a3eda925` |
| FF | `.../FIRE FIGHTING LAYOUT.dwg` | `496fe63a` |
| ARCH/FA IFC | FIRE ALARM LAYOUT.dwg R0 (filed FA IFC, from uploads) | DWG `66043c11` |
| SCHED | the six `P025-13-*.xls(x)` mechanical schedules | as listed in the reading |

  The PDFs are not copied (unsupported; their absence is a known limitation,
  not under test). No original is opened for writing.

## Look scope (the damper look is the expensive part)

A validation harness (outside app code) restricts `visual.wanted` to six plan
sheets and records the filter in its output. Chosen to cover the reported
cases: both MSD drawings on the same floor, door tags, ambiguity, and the
aligned union.

| sheet | floor | labels | windows = Opus requests | what it tests |
|---|---|---|---|---|
| SM-101 | B3 | 2 | 2 | "SD" door tags on the smoke drawing |
| M-07-V101 | B3 | 4 | 2 | the 2 MSDs on symbols `5741B`/`5741D` + 2 door tags |
| SM-104 | GF | 5 | 4 | door tags, 1 ambiguous label |
| M-07-V104 | GF | 5 | 4 | door tags, 2 ambiguous labels |
| SM-117 | Roof | 16 | 6 | 9 ambiguous; union with V117 |
| M-07-V117 | Roof | 14 | 7 | 3 ambiguous; union with SM-117 |
| **total** | | **46** | **25** | |

The SM-119 riser diagram (268 labels, 54 windows) is out of scope by design.

## Expected requests and hard limits

| route | expected | hard cap (abort above) | per request |
|---|---|---|---|
| route probe (exactness) | 2 (Opus, Fable: "reply OK") | 2 | — |
| Opus damper look `claude-opus-5-5`, effort high, exact | 25 | 30 | max output 1500 tokens, `drawing_review_timeout_s` |
| Fable orchestrator `claude-fable-5-1`, effort high, exact | 8 (7 package FP1 + 1 run FP2) | 16 (one retry each) | input <= 150k tokens (observed 9.6k chars), output <= 8000, 900 s |
| **total** | **35** | **48** | |

Wall clock <= 90 min. `fa_agent_parallel = 2`. Abort immediately on the first
`model_substituted`, on any request not exact / not at high effort, on the cap,
or on any write outside the sandbox. No retry-review, no second run.

## Answer key (prepared before the run, from the DXF geometry alone)

For each of the 46 labels: its settled symbol (id, bounds, centre) or its
expected hold reason (architecture `$0$` block / shared / no symbol /
ambiguous), and whether its text is a door tag. Gate Barrier: the conflict
group `GATE|GF|conflict` with both GB drawings, 0 gate CR rows.

## How errors are caught

- **False equipment location.** The code accepts a damper only when the model's
  point lies within 0.15 m of a settled, non-architectural symbol's bounds;
  otherwise the label is held ("elsewhere"). The harness additionally checks
  every damper row in scope: `location_state == "symbol"`, `anchor` equals the
  answer key's symbol centre, `label_anchor` equals the label point. Reported:
  model points outside any symbol (count, distance), labels held "elsewhere".
  Any accepted row whose anchor is not an answer-key symbol = FAIL.
- **Door tags as dampers.** An "SD" tag on a `$0$` door block stays held even
  if the model says damper. Reported: how many door tags the model called a
  damper (a model-quality figure, not a schedule error). Any door tag
  appearing as a row = FAIL.
- **Incorrect CR counts.** Gate rows in scope must be 0 with the GF conflict
  held and both drawings listed; Fable's `conflict_proposals` are recorded
  only. Any gate CR row, or the conflict missing, = FAIL. Damper CR counts per
  floor are recomputed by the harness from the answer key and the model's
  verdicts and must equal the schedule's rows (B3: 2 if Opus calls both MSDs
  dampers; Roof: the union of SM-117 and V117 with items drawn on both counted
  once).
- **Publication.** The harness never calls accept. The scoped run's
  publication state is recorded but has no meaning (out-of-scope labels are
  filtered); the sandbox is discarded afterwards. Live
  `project_fa_interfaces` row 5 unchanged (read-only hash before / after).

## Success criteria

1. Every request exact, at high effort, `models_used == requested` (no
   substitution), within the caps.
2. All 46 labels answered or held with a stated reason; no silent skip.
3. Zero rows outside the answer key; zero door-tag rows; zero gate CR rows;
   per-floor damper counts equal the harness's recomputation.
4. Fable review `completed` (8 calls), its output validated (no unknown
   reference adopted, nothing it says changes a count); or, if Fable fails,
   the review `missing`/`partial` and the run provisional — a correct outcome,
   reported as such.
5. Live DB row unchanged; no original document modified.

## Recorded per request

task, requested model, models used, effort, exact flag, input / output tokens
(from the response), cache hit, duration, window or package. Token totals are
taken from the sandbox `ai_usage` table (it has no run id; the sandbox holds
only this run).

## Not claimed

No accuracy rate beyond these 46 labels, no speed gain (no matched baseline),
no production readiness. A full run (78 Opus windows once F13 is fixed) needs
a separate approval after this one passes.
