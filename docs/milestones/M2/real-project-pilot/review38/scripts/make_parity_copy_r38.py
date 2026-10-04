"""ORCH-08 (R38HARNESS-IMPL): two copies of the ORCH-06 parity scripts for the cross-page what-if (CROSS-PAGE-WHATIF.json).

Usage: make_parity_copy_r38.py <record json (absolute)>      refuses if a target folder exists
Copies PILOT/evaluator-offline-r32/scripts/common_r35.py and run_evaluator_offline_r32.py (hash-checked against the
evaluator-offline-r32 manifest 86dd81d3...) to
  C:/t/iso/work/r2x/r38/parity/r36-side/scripts/   the harness side judged by the FROZEN review36 harness (imported in place
                                                    from PILOT/review36/scripts/harness-r32, read-only): the 'before'
  C:/t/iso/work/r2x/r38/parity/r38-side/scripts/   the harness side judged by the r38 harness (rule CP-R38): the 'after'
and applies EXACTLY the substitutions in SUBST (each must occur the stated number of times): the work folder (the run's
only write root and its never-created database path), the harness folder, the expected harness-module hashes (r38 side:
lane_judge_r32, tripwire_r32, score_lane_r32 and the new page_relations_r38), and, on the r38 side only, (a) the lane
document handed to the judge carries the source sha256 of the document's staged bytes (SOURCE_BOUND, as the r38 scorer's
lanes carry it: score_lane_r32 puts the row's sha256, which coverage_v4's eligibility binds to the staged sha256), and
(b) the new judge outcome 'recovered_conflict' maps to the verdict 'correct_and_cross_page'. Nothing else changes: the
guards (no network, no subprocess, provider classes stubbed, writes only under the work folder) and the emission are the
ORCH-06 code."""
import datetime
import difflib
import hashlib
import json
import pathlib
import sys

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "evaluator-offline-r32"
MANIFEST_SHA = "86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7"
ROOT = pathlib.Path("C:/t/iso/work/r2x/r38/parity")
R38_HARNESS = pathlib.Path("C:/t/iso/work/r2x/r38/harness-r32")
R36_HARNESS = PILOT / "review36" / "scripts" / "harness-r32"
LC34, LC36 = "ec2221c825db6a629cafc42fffe854e2593393860a942f2e1ec9762eec16a3e6", "c23ba577dfb298361fabef6ffb06e0f80eb3ad338ee22e7a487197d9c4b86a09"
OLD = {"lane_judge_r32": "a0b6b7c83262ddb2d1337d5ed17296a5aa6fa26cc6ebbee18afcb3cf48f0ca45",
       "tripwire_r32": "42dc6226700852f84762bdd7759bb7592de72778fe92aaad7f7993db291f14d0",
       "score_lane_r32": "c25f4d8994631b0fe5b52c1eb4d5bb0f7227f15a4b26c671e72e9c7e31c3c915"}


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def subst(side: str) -> dict:
    work = (ROOT / f"{side}-side").as_posix()
    common = [('WORK = pathlib.Path("C:/t/iso/work/r2x/r35")', f'WORK = pathlib.Path("{work}")', 1),
              (f'"literal_compare_r32": "{LC34}"', f'"literal_compare_r32": "{LC36}"', 1)]
    if side == "r36":
        common.append(('HARNESS_DIR = REVIEW34 / "scripts/harness-r32"', f'HARNESS_DIR = pathlib.Path("{R36_HARNESS.as_posix()}")', 1))
    else:
        new = {m: sha((R38_HARNESS / f"{m}.py").read_bytes()) for m in OLD}
        prel = sha((R38_HARNESS / "page_relations_r38.py").read_bytes())
        common.append(('HARNESS_DIR = REVIEW34 / "scripts/harness-r32"',
                       f'HARNESS_DIR = pathlib.Path("{R38_HARNESS.as_posix()}")\nSOURCE_BOUND = True       # ORCH-08 what-if: the lane document carries the staged sha256', 1))
        for m in ("lane_judge_r32", "tripwire_r32"):
            common.append((f'"{m}": "{OLD[m]}"', f'"{m}": "{new[m]}"', 1))
        common.append((f'"score_lane_r32": "{OLD["score_lane_r32"]}"', f'"score_lane_r32": "{new["score_lane_r32"]}",\n    "page_relations_r38": "{prel}"', 1))
        common.append(('    jd = J.judge_document(truth, pool_id, {"facts": facts})',
                       '    jd = J.judge_document(truth, pool_id, {"facts": facts, "source_sha256": truth["documents"][pool_id]["staged_sha256"] if SOURCE_BOUND else None})', 1))
        common.append(('    elif outcome == "recovered_clean":\n        verdict = "correct"',
                       '    elif outcome == "recovered_conflict":\n        verdict = "correct_and_cross_page"\n    elif outcome == "recovered_clean":\n        verdict = "correct"', 1))
    run = [("C:/t/iso/work/r2x/r35/run/no-database-never-created.db", f"{work}/run/no-database-never-created.db", 2)]
    return {"common_r35.py": common, "run_evaluator_offline_r32.py": run}


def main(record):
    record = pathlib.Path(record)
    mraw = (PKG / "evidence" / "EVIDENCE-MANIFEST.json").read_bytes()
    if sha(mraw) != MANIFEST_SHA:
        raise SystemExit("PACKET MISMATCH: evaluator-offline-r32 manifest")
    man = json.loads(mraw.decode("utf-8"))["files"]
    out = {"made_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "source_manifest_sha256": MANIFEST_SHA, "sides": {}}
    for side in ("r36", "r38"):
        dst = ROOT / f"{side}-side" / "scripts"
        if dst.exists():
            raise SystemExit(f"refused: {dst} exists")
        dst.mkdir(parents=True)
        (dst.parent / "run").mkdir()
        files = {}
        for name, subs in subst(side).items():
            src = PKG / "scripts" / name
            b = src.read_bytes()
            if sha(b) != man[f"scripts/{name}"]["sha256"]:
                raise SystemExit(f"PACKET MISMATCH: {name}")
            t = b.decode("utf-8")
            for old, new, n in subs:
                if t.count(old) != n:
                    raise SystemExit(f"{side} {name}: {old!r} occurs {t.count(old)} times, expected {n}")
                t = t.replace(old, new)
            with open(dst / name, "x", encoding="utf-8", newline="\n") as fh:
                fh.write(t)
            diff = list(difflib.unified_diff(b.decode("utf-8").splitlines(), t.splitlines(), lineterm="", n=0))
            files[name] = {"source": src.as_posix(), "source_sha256": sha(b), "copy": (dst / name).as_posix(), "copy_sha256": sha(t.encode("utf-8")),
                           "substitutions": [{"old": o, "new": nw, "count": c} for o, nw, c in subs], "diff": diff}
        out["sides"][side] = files
    record.write_text(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({s: {n: v["copy_sha256"] for n, v in f.items()} for s, f in out["sides"].items()}, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
