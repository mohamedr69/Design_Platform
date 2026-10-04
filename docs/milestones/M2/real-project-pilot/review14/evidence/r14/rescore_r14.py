"""R14-03 re-score: stored outputs scored with the ORIGINAL labels and with the r14.1 AMENDED labels, separately named;
evaluator .9 (frozen-r12, unchanged) under each run's declared AI context, plus a declared overlay for the amended
small-batch labels' `supported_observations` (the only schema addition; evaluator .9 itself cannot read it).

OVERLAY_VERSION r2x-overlay-2026-09-30.1 -- for every critical fact of the evidence layer:
  * matched to a supported observation of the same field and literal (revision literals compared without a leading
    'Rev.' and dots) AND the recorded AI target is null (no identity anchor)  -> 'correct literal, accepted without a
    supported target': STILL critical (acceptance contract), retyped; no recovery or register credit;
  * the value is a supported literal of ANOTHER role (e.g. the revision literal 'Rev.0' accepted as an identity), or
    an observation whose role is HELD (the footer code)                    -> 'role error' / 'role not established':
    STILL critical, retyped;
  * no supported observation                                               -> 'literal false accept' (unchanged);
  * (a recorded target equal to the observation's association proposal would be 'held association', not critical;
    no such case occurs -- stated, not assumed).
Supported raw observations are also counted (every accepted or held fact matching one), apart from recovery.
Exposed runs: the Review 12 re-score set of the current baseline (det9 pilot / holdout, the matched model-disabled,
EV0, EV1, EV2), with rescore_r12.py's contexts."""
import collections
import copy
import json
import pathlib
import re
import sys

sys.path.insert(0, "C:/t/iso/frozen-r12/backend")
import os  # noqa: E402

os.environ.setdefault("AI_ENABLED", "false")
os.chdir("C:/t/iso/frozen-r12/backend")
from scripts import m2_eval5 as ev  # noqa: E402

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from overlay import OVERLAY_VERSION, overlay, recorded_target, rev_norm  # noqa: E402,F401

W = pathlib.Path("C:/t/iso/work/r2x")
P = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
L = W / "labels/r14"
OUT = W / "r14/rescore"
OUT.mkdir(parents=True, exist_ok=True)
FIELDS = ("identity", "revision", "decision")
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))


def headline(result):
    t = result["totals"]["evidence"]
    return {"critical": len(t["critical"]), **{f: {k: t["fields"][f][k] for k in ("readable", "asserted_distinct", "accepted_precision", "recovery")} |
                                                 {"recovery_counts": t["fields"][f]["recovery_counts"]} for f in FIELDS}}


summary = {"evaluator": ev.EVALUATOR_VERSION, "overlay": OVERLAY_VERSION, "small_batch": {}, "exposed": {}}
# --- small batch -----------------------------------------------------------------------------------------------------
REG = load(W / "labels/SMALL-BATCH-REGISTER-LABELS.json")          # page-1 records are unchanged by r14.1 -> same register labels
SB = {"original": load(W / "labels/SMALL-BATCH-LABELS.eval.json"), "amended-r14.1": load(L / "SMALL-BATCH-LABELS.amended-r14.1.json")}
DET = {"variant": None, "declared": "no AI evidence stage in this run"}
CTX = {"det": DET, "A": DET, "B": {"variant": "EV1", "profile": "default", "declared": "r2x-small declaration: default profile, EV1"},
       "C": {"variant": "EV2", "profile": "default", "declared": "r2x-small declaration: default profile, EV2"}}
for track, tag in (("det", "r2x-small-det"), ("A", "r2x-small-A"), ("B", "r2x-small-B"), ("C", "r2x-small-C")):
    rows = load(f"C:/t/r2x/runs/{tag}/out/rows.json")
    for version, pl in SB.items():
        res = ev.evaluate(REG, pl, rows, pl.get("page1_corrections"), ai_context=CTX[track])
        name = f"small-{track}__{version}"
        (OUT / f"{name}.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
        summary["small_batch"][name] = {**headline(res), **({"overlay": overlay(res, pl, rows)} if version != "original" else {})}
# --- exposed baseline runs -------------------------------------------------------------------------------------------
EXP = {"original": {"GOLD": load(P / "GOLDEN-LABELS.json"), "PAGES": load(P / "review05/labels/GOLDEN-LABELS-v2-PAGES.json"),
                    "HOLD": load(P / "review05/holdout/HOLDOUT-LABELS.json"), "HOLD_PAGES": load(P / "review05/holdout/HOLDOUT-PAGE-LABELS.json")},
       "amended-r14.1": {"GOLD": load(L / "GOLDEN-LABELS.amended-r14.1.json"), "PAGES": load(L / "GOLDEN-LABELS-v2-PAGES.amended-r14.1.json"),
                         "HOLD": load(L / "HOLDOUT-LABELS.amended-r14.1.json"), "HOLD_PAGES": load(L / "HOLDOUT-PAGE-LABELS.amended-r14.1.json")}}
MATCHED = load("C:/t/iso/work/r7/matched/MATCHED-DECLARATION.json")
mdocs = {d.replace("\\", "/") for d in MATCHED["selection"]["files_sha256"]}
RUNS = [("r7-det9-pilot-default", "GOLD", "PAGES", "C:/t/r6/det9-pilot/out/rows-default.json", None, DET),
        ("r7-det9-holdout-default", "HOLD", "HOLD_PAGES", "C:/t/r6/det9-holdout/out/rows-default.json", None, DET),
        ("matched-model-disabled", "GOLD", "PAGES", "C:/t/r6/det9-pilot/out/rows-default.json", mdocs, DET),
        ("matched-AI-EV0", "GOLD", "PAGES", "C:/t/r7/m-ev0/out/rows-default.json", mdocs, DET),
        ("matched-AI-EV1", "GOLD", "PAGES", "C:/t/r7/m-ev1/out/rows-default.json", mdocs, {"variant": "EV1", "profile": "default", "declared": "matched run declaration: default profile, EV1"}),
        ("matched-AI-EV2", "GOLD", "PAGES", "C:/t/r7/m-ev2/out/rows-default.json", mdocs, {"variant": "EV2", "profile": "default", "declared": "matched run declaration: default profile, EV2"})]
for name, lk, pk, rows_path, docs, ctx in RUNS:
    rows = load(rows_path)
    for version, lab in EXP.items():
        labels, pages = lab[lk], lab[pk]
        r = rows
        if docs is not None:
            labels = {**labels, "documents": [d for d in labels["documents"] if d["doc"].replace("\\", "/") in docs]}
            pages = {**pages, "documents": {k: v for k, v in pages["documents"].items() if k.replace("\\", "/") in docs}}
            r = {k: v for k, v in rows.items() if k.replace("\\", "/") in docs}
        res = ev.evaluate(labels, pages, r, pages.get("page1_corrections"), ai_context=ctx)
        (OUT / f"{name}__{version}.json").write_text(json.dumps(res, indent=1, default=str, ensure_ascii=False), encoding="utf-8")
        summary["exposed"][f"{name}__{version}"] = {**headline(res), "critical_list": [{k: c.get(k) for k in ("doc", "page", "field", "value", "outcome")}
                                                                                         for c in res["totals"]["evidence"]["critical"]]}
(OUT / "RESCORE-SUMMARY.json").write_text(json.dumps(summary, indent=1, default=str, ensure_ascii=False) + "\n", encoding="utf-8")


def line(h):
    return f"crit {h['critical']:>2} | " + " | ".join(f"{f} {sum(h[f]['recovery_counts'].get(k, 0) for k in ('recovered_clean', 'recovered_mixed'))}/{h[f]['readable']}" for f in FIELDS)


for k, h in summary["small_batch"].items():
    print(f"{k:34}", line(h), ("| overlay crit " + str(h["overlay"]["critical_after_overlay"]) + " supported obs " + str(h["overlay"]["supported_raw_observations"])
                               + " " + str(collections.Counter(t["type"] for t in h["overlay"]["critical_typed"]))) if "overlay" in h else "")
for k, h in summary["exposed"].items():
    print(f"{k:40}", line(h))
