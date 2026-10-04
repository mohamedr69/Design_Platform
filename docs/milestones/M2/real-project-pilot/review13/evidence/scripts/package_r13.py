"""Copy this round's evidence into the owner's docs package review13/ (new folder; earlier packages untouched) and
write evidence/EVIDENCE-MANIFEST.json (sha256 + size of every file in the package). Also exports the ledger scope's
entries (read only) and the cross-track project-day counter as JSON."""
import hashlib
import json
import pathlib
import shutil
import sqlite3

W = pathlib.Path("C:/t/iso/work/r2x")
PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review13")
EV = PKG / "evidence"
RUNS = pathlib.Path("C:/t/r2x/runs")
EV.mkdir(parents=True, exist_ok=True)


def put(src, rel):
    src = pathlib.Path(src)
    if not src.exists():
        print("missing", src)
        return
    dst = PKG / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)


for f in ("EXPLORATION-SELECTION.json", "EXPLORATION-SELECTION.superseded-draft1.json", "EXPLORATION-MANIFEST.json", "SMALL-BATCH.json"):
    put(W / f, f"evidence/manifest/{f}")
for f in ("COUNT-RECONCILIATION.json", "EXPLORATION-INVENTORY.json"):
    put(W / "inventory" / f, f"evidence/manifest/{f}")
put("C:/t/r2x/small-stage/SMALL-STAGE.json", "evidence/manifest/SMALL-STAGE.json")
put("C:/t/r2x/renders/RENDER-INDEX.json", "evidence/manifest/RENDER-INDEX.json")
put("C:/t/r2x/renders/WORD-TEXT.json", "evidence/manifest/WORD-TEXT.json")
for f in ("LABEL-FORMAT.md", "SMALL-BATCH-LABELS.json", "SMALL-BATCH-LABELS.eval.json", "SMALL-BATCH-REGISTER-LABELS.json"):
    put(W / "labels" / f, f"evidence/labels/{f}")
for f in ("FAILURE-INVENTORY.json", "MISSED-DISCOVERY-BREAKDOWN.json"):
    put(W / "failure-inventory" / f, f"evidence/failure-inventory/{f}")
for f in ("holdout-A-r12.json", "holdout-A-r12-extraction.json", "holdout-A-r12.log"):
    put(W / "boq" / f, f"evidence/boq/{f}")
for f in ("EXPERIMENT-DECLARATION-SMALL.json", "EXPERIMENT-DECLARATION-SMALL.addendum-1.json", "RUNNERS-SHA256.txt", "RUN-ATTEMPTS.txt"):
    put(W / "run" / f, f"evidence/run/{f}")
for log in sorted((W / "run").glob("run-small-*.log")):
    put(log, f"evidence/run/logs/{log.name}")
for tag in sorted(p.name for p in RUNS.iterdir() if p.is_dir()):
    for f in sorted((RUNS / tag / "out").glob("*.json")):
        put(f, f"evidence/run/runs/{tag}/{f.name}")
for f in sorted((W / "eval").glob("*.json")):
    put(f, f"evidence/eval/{f.name}")
for f in sorted((W / "regression").glob("*")):
    put(f, f"evidence/regression/{f.name}")
scripts = [p for p in W.rglob("*.py")]
for p in scripts:
    put(p, f"evidence/scripts/{p.relative_to(W).as_posix()}")
put(W / "worklist/HUMAN-REVIEW-WORKLIST.json", "worklist/HUMAN-REVIEW-WORKLIST.json")
for sub in ("findings", "small-batch", "h06", "critical"):
    for f in sorted(pathlib.Path(f"C:/t/r2x/worklist/{sub}").glob("*")):
        put(f, f"worklist/crops/{sub}/{f.name}")
# ledger scope + project-day counter, read only
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
ledger = {"scopes": [dict(r) for r in con.execute("select * from scopes")], "entries": [dict(r) for r in con.execute("select * from entries order by id")],
          "limit_amendments": [dict(r) for r in con.execute("select * from limit_amendments")] if con.execute(
              "select count(*) from sqlite_master where name = 'limit_amendments'").fetchone()[0] else []}
con.close()
(EV / "run/LEDGER-r2x-small.json").write_text(json.dumps(ledger, indent=1, default=str) + "\n", encoding="utf-8")
con = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
con.row_factory = sqlite3.Row
xt = [dict(r) for r in con.execute("select * from calls order by id")]
con.close()
(EV / "run/PROJECT-DAY-COUNTER.json").write_text(json.dumps(xt, indent=1, default=str) + "\n", encoding="utf-8")
man = {}
for p in sorted(PKG.rglob("*")):
    if p.is_file() and p.name != "EVIDENCE-MANIFEST.json":
        man[p.relative_to(PKG).as_posix()] = {"sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "bytes": p.stat().st_size}
(EV / "EVIDENCE-MANIFEST.json").write_text(json.dumps({"package": "review13", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files;", round(sum(v["bytes"] for v in man.values()) / 1e6, 1), "MB")
