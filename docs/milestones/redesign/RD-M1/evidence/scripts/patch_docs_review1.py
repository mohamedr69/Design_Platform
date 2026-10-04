"""Apply independent-review round 1 changes to the package documents (producer edits)."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = sys.argv[1]


def patch(path, pairs):
    s = open(path, encoding="utf-8").read()
    for a, b in pairs:
        assert a in s, (os.path.basename(path), a[:80])
        s = s.replace(a, b)
    open(path, "w", encoding="utf-8", newline="\n").write(s)


# findings.py: F005 reproduction path
patch(os.path.join(HERE, "findings.py"), [(
    'reproduction="python evidence/scripts/wall_layers.py and effective_layer.py against a copy of the source DXF (REPRODUCTION-RUNBOOK step 6).",',
    'reproduction="Copy evidence/scripts/*.py to ISO/scripts (they resolve the DXF as ISO/src/EP-30880/source.dxf and write to ISO/work, relative to their own folder), copy the source DXF there, then run wall_layers.py, effective_layer.py and invisible_flag.py (REPRODUCTION-RUNBOOK section 1 and step 6).",')])

# build_evidence.py: E01 header offset, sibling clone folder name
be = os.path.join(HERE, "build_evidence.py")
patch(be, [
    ('"; Only user-profile path prefixes are replaced; line numbers below are original line + 1.\\n"',
     '"; Only user-profile path prefixes are replaced; E01 line number = original script line + 2 (two header lines).\\n"'),
    ('] + [(re.compile(re.escape(h)), alias) for h, alias in _hosts().items()]',
     '] + [(re.compile(re.escape(h)), alias) for h, alias in _hosts().items()] + [\n'
     '    (re.compile(r"[A-Z]{4,}-AL-[A-Z]{4,}---AI-PLATFORM"), "<sibling clone folder>")]'),
])

R = os.path.join(PKG, "RD-M1-REPORT.md")
patch(R, [
    ("Evidence: E01 line 51, E05, E13, E16, E18;",
     "Evidence: original script line 51 (= E01 line 53), E05, E13, E16, E18;"),
    ("**Confirmed by data and geometry:** approved modules are mounted on a non-plotting parking-block line (F006).",
     "**Confirmed by data and code:** two approved modules sit on parking-block geometry admitted through raw layer `0` "
     "(effective `29-PARKING`, which the wall filter would exclude by name) (F006). That this line does not plot is a "
     "*visual* observation, explained by the DXF invisible flag for the ZCV segment only; for the ELECTRIC PUMP segment "
     "it is unexplained. The wall index also takes 4,351 invisible-flag segments (F005)."),
    ("the wall index admits non-wall geometry (≈10% of segments are on a wall layer).",
     "the wall index admits non-wall geometry (≈10% of segments are on a wall layer, counted by *raw* layer)."),
    ("Finding counts: **Critical 2 · High 8 · Medium 17 · Low 4** (31; `FAILURE-INVENTORY.md`).",
     "Finding counts: **Critical 2 · High 9 · Medium 18 · Low 6** (35; `FAILURE-INVENTORY.md`; F032–F035 were added after the first "
     "independent review)."),
    ("the WAL grew during the audit;", "the WAL was rewritten during the audit (mtime changed, size constant);"),
    ("| 15–19 workflow | F002 (**Critical**), F018, F019, F030, F017, F016 |",
     "| 15–19 workflow | F002 (**Critical**), F032 (High), F018, F019, F030, F017, F016, F034, F035 |"),
    ("| 20–24 Apply | F001 (High, blocker), F004 (High), F023 (High), F024, F031 |",
     "| 20–24 Apply | F001 (High, blocker), F004 (High), F023 (High), F033, F024, F031 |"),
    ("| Outer repo git | HEAD `e2d8cfdb8376599562f6ec91f519c2efb7d43f54`, branch `master`; status as in the session's start snapshot (logs modified, `<sibling clone folder>/` untracked) |",
     "| Outer repo git | HEAD `e2d8cfdb8376599562f6ec91f519c2efb7d43f54`, branch `master`; status as in the session's start snapshot (logs modified, a sibling clone folder untracked) |"),
    ("RD-M1 requires a fresh read-only reviewer. The reviewer's result is recorded in `INDEPENDENT-REVIEW.md` (added by the reviewer's output, not by the producer's judgement). The producer does not approve this package.",
     "RD-M1 requires a fresh read-only reviewer. Round 1 (a separate agent that did not produce the audit) returned **CHANGES REQUIRED**: "
     "7 required documentation changes and 6 non-blocking notes. The core bindings, data safety, the Apply-input regeneration and "
     "F001/F002/F003/F017 were independently confirmed. Its report is reproduced verbatim in `INDEPENDENT-REVIEW.md`, followed by the "
     "producer's change log. The producer does not approve this package; acceptance rests with the re-review."),
])

G = os.path.join(PKG, "GOLDEN-CASE-SELECTION.md")
patch(G, [("the `<sibling clone folder>` clone,", "the sibling clone folder in the outer repo,")])

D = os.path.join(PKG, "DATA-SAFETY-REPORT.md")
patch(D, [
    ("| After T1 |",
     "| T0 timing | T0 started ≈3 minutes after the audit began (≈19:43). The independent reviewer closed that gap: no file under `ep-platform` "
     "(venv and node_modules excluded) is newer than 19:40 except the live DB/WAL and the package; `.git/index` was touched at 19:43:30 (see below). |\n| After T1 |"),
])

RB = os.path.join(PKG, "REPRODUCTION-RUNBOOK.md")
patch(RB, [
    ("All scripts are in `evidence/scripts/` (user-profile paths redacted; set `ISO` below to your own isolated folder and edit the constants at the top of `q.py`, `snapshot_db.py`, `hash_tree.py` accordingly).",
     "All scripts are in `evidence/scripts/` (user-profile paths redacted). **Copy them to `ISO/scripts/`**: `render_case.py`, "
     "`wall_layers.py`, `effective_layer.py`, `analyse_changes.py`, `ai_variation.py`, `dump_case.py` and `reproduce_apply_input.py` "
     "resolve `ISO/src`, `ISO/work`, `ISO/code` and `ISO/hash` relative to their own folder (`HERE/..`), so they do not run from "
     "`evidence/scripts/`. `invisible_flag.py` holds an absolute DXF path. Edit the absolute constants at the top of `q.py`, "
     "`snapshot_db.py`, `hash_tree.py` and `invisible_flag.py`."),
    ("| 6 | `python scripts/wall_layers.py '<probes>'` and `python scripts/effective_layer.py '<probes>'` (probe JSON in `COMMANDS.md`) | `segments_kept_total 92093`; probe `invisible-rect-left-edge` → layer `0` / effective `…$0$29-PARKING` via `*U442` |",
     "| 6 | `python scripts/wall_layers.py '<probes>'`, `python scripts/effective_layer.py '<probes>'` (probe JSON in `COMMANDS.md`), `python scripts/invisible_flag.py` | `segments_kept_total 92093`; probe `invisible-rect-left-edge` → layer `0` / effective `…$0$29-PARKING` via `*U442`; 4,351 invisible-flag segments. (`effective_layer.py` reports layer visibility only, not the entity invisible flag.) |"),
])

T = os.path.join(PKG, "TEST-RESULTS.md")
patch(T, [("| Cross-host requeue of a job whose work already completed | F017 |",
           "| Cross-host requeue of a job whose work already completed | F017 |\n"
           "| Concurrent Plan/PATCH/Apply writes (lost updates) | F032 |\n"
           "| Same-minute output name overwrite; Apply cancellation; confirm flag | F033, F034, F035 |\n"
           "| Wall index ignoring the DXF invisible flag | F005 |")])

P = os.path.join(PKG, "CURRENT-PIPELINE.md")
patch(P, [
    ("LINE/POLYLINE not matching `NOT_WALLS` on **raw** layer; 2 m grid",
     "LINE/POLYLINE not matching `NOT_WALLS` on **raw** layer; entity invisible flag, layer state and viewport freeze ignored; 2 m grid"),
    ("| keeps approved/skipped/moved/edited verbatim (S:1134) | Mixed |",
     "| keeps approved/skipped/moved/edited verbatim (S:1134); rewrites the whole row after every answer, no concurrency control (F032) | Mixed |"),
])

H = os.path.join(PKG, "NEXT-MILESTONE-HANDOFF.md")
patch(H, [
    ("| 6 | One AutoCAD run",
     "| 5b | Unique output names (no same-minute overwrite in uploads or archive); Apply honours cancel; `confirm`-flagged inserts not drawn until confirmed | F033, F034, F035 | Unit tests on name generation, the `check` callback and `_drawn` |\n| 6 | One AutoCAD run"),
    ("provenance and read-side writes (F018–F020),", "provenance, read-side writes and concurrency (F018–F020, F032),"),
])
print("docs patched")
