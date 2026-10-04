"""Review 07 (A): every stored output re-scored with the frozen evaluator .5 -- nothing overwritten (new files under
C:/t/iso/work/r7/eval5). Real-model runs are scored on the projects they ran on (labels restricted to them)."""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, r"C:\t\iso\ep-platform\backend")
from scripts import m2_eval5 as ev5  # noqa: E402

P = Path(r"C:\Users\moham\Desktop\dev\dev\ep-platform\docs\milestones\M2\real-project-pilot")
R5 = P / "review05"
OUT = Path(r"C:\t\iso\work\r7\eval5")
OUT.mkdir(parents=True, exist_ok=True)
GOLD = json.load(open(P / "GOLDEN-LABELS.json", encoding="utf-8"))
PAGES = json.load(open(R5 / "labels" / "GOLDEN-LABELS-v2-PAGES.json", encoding="utf-8"))
HOLD = json.load(open(R5 / "holdout" / "HOLDOUT-LABELS.json", encoding="utf-8"))
HOLD_PAGES = json.load(open(R5 / "holdout" / "HOLDOUT-PAGE-LABELS.json", encoding="utf-8"))
ELIGIBLE = ["29076", "30088", "30784"]


def restrict(labels, pages, eps):
    lab = {**labels, "documents": [d for d in labels["documents"] if d["ep"] in eps]}
    pg = {**pages, "documents": {k: v for k, v in pages["documents"].items() if any(k.startswith(f"EP-{e}/") for e in eps)}}
    return lab, pg


RUNS = []
for p in ("default", "promoted"):
    RUNS += [(f"r5-candidateA-{p}", GOLD, PAGES, P / "outputs" / "candidateA" / f"rows-{p}.json", None),
             (f"r5-candidateB-{p}", GOLD, PAGES, P / "outputs" / "candidateB" / f"rows-{p}.json", None),
             (f"r5-candC0-{p}", GOLD, PAGES, R5 / "outputs" / "candidateC-intermediate" / "C0" / f"rows-{p}.json", None),
             (f"r5-candC1-{p}", GOLD, PAGES, R5 / "outputs" / "candidateC-intermediate" / "C1" / f"rows-{p}.json", None),
             (f"r5-candidateC-{p}", GOLD, PAGES, R5 / "outputs" / "candidateC" / f"rows-{p}.json", None),
             (f"r5-holdout-{p}", HOLD, HOLD_PAGES, R5 / "holdout" / f"rows-{p}.json", None),
             (f"r6-det7-pilot-{p}", GOLD, PAGES, Path(rf"C:\t\r6\det-pilot-parse7-superseded\out\rows-{p}.json"), None),
             (f"r6-det7-holdout-{p}", HOLD, HOLD_PAGES, Path(rf"C:\t\r6\det-holdout-parse7-superseded\out\rows-{p}.json"), None),
             (f"r6-det8-pilot-{p}", GOLD, PAGES, Path(rf"C:\t\r6\det-pilot\out\rows-{p}.json"), None),
             (f"r6-det8-holdout-{p}", HOLD, HOLD_PAGES, Path(rf"C:\t\r6\det-holdout\out\rows-{p}.json"), None)]
RUNS += [("r6-det7-eligible-default", GOLD, PAGES, Path(r"C:\t\r6\det-pilot-parse7-superseded\out\rows-default.json"), ELIGIBLE),
         ("r6-ai-ev0-eligible-default", GOLD, PAGES, Path(r"C:\t\r6\ai-ev0\out\rows-default.json"), ELIGIBLE),
         ("r6-ai-ev1-eligible-default", GOLD, PAGES, Path(r"C:\t\r6\ai-ev1\out\rows-default.json"), ELIGIBLE),
         ("r6-ai-ev2-ep29076-default", GOLD, PAGES, Path(r"C:\t\r6\ai-ev2\out\rows-default.json"), ["29076"]),
         ("r6-ai-ev1-ep29076-default", GOLD, PAGES, Path(r"C:\t\r6\ai-ev1\out\rows-default.json"), ["29076"]),
         ("r6-ai-ev0-ep29076-default", GOLD, PAGES, Path(r"C:\t\r6\ai-ev0\out\rows-default.json"), ["29076"])]
extra = sys.argv[1:]          # name=rows.json:eps  (replays)
for arg in extra:
    name, rest = arg.split("=", 1)
    path, eps = rest.rsplit(":", 1)
    RUNS.append((name, GOLD, PAGES, Path(path), eps.split(",")))

summary = {}
for name, labels, pages, rows_path, eps in RUNS:
    if not rows_path.exists():
        summary[name] = {"not_run": f"no stored output ({rows_path})"}
        print(name.ljust(32), "NOT RUN (no stored output)")
        continue
    rows = json.load(open(rows_path, encoding="utf-8"))
    if eps:
        labels_, pages_ = restrict(labels, pages, eps)
        rows = {k: v for k, v in rows.items() if any(k.replace("\\", "/").startswith(f"EP-{e}/") for e in eps)}
    else:
        labels_, pages_ = labels, pages
    result = ev5.evaluate(labels_, pages_, rows, (pages_ or {}).get("page1_corrections"))
    json.dump(result, open(OUT / f"{name}.json", "w", encoding="utf-8"), indent=1, default=str)
    t = result["totals"]
    row = {"register_critical": len(t["register"]["critical"])}
    for layer in ("raw", "evidence", "ai"):
        row[layer] = {"critical": len(t[layer]["critical"]), "observed_errors": len(t[layer]["observed_errors"]),
                      "critical_kinds": dict(collections.Counter(f"{c['field']}:{c['outcome']}" for c in t[layer]["critical"])),
                      **{f: {k: t[layer]["fields"][f][k] for k in ("asserted_distinct", "accepted_precision", "recovery", "readable")}
                         for f in ev5.FIELDS}}
    row["introduced_ai_errors"] = len(t["introduced_ai_errors"])
    summary[name] = row
    print(name.ljust(32), "reg", row["register_critical"], "| raw crit", row["raw"]["critical"], "obs-err", row["raw"]["observed_errors"], "| evid crit", row["evidence"]["critical"],
          "| ai crit", row["ai"]["critical"], "| introduced", row["introduced_ai_errors"],
          "| raw id", row["raw"]["identity"]["recovery"], "prec", row["raw"]["identity"]["accepted_precision"])
json.dump(summary, open(OUT / "SUMMARY.json", "w", encoding="utf-8"), indent=1)
