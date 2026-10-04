"""Copy one arm's evidence (read-only sources) into evidence-<arm>/ with a sha256 manifest. Never overwrites a saved set.
Usage: save_evidence.py <arm> <tag> <score_dir>"""
import hashlib, json, pathlib, shutil, sqlite3, sys
arm, tag, score = sys.argv[1], sys.argv[2], pathlib.Path(sys.argv[3])
HERE = pathlib.Path(__file__).resolve().parent
E = HERE / f"evidence-{arm}"
if E.exists():
    sys.exit(f"{E} exists; never overwritten")
E.mkdir()
OUT = pathlib.Path("C:/t/r2x/runs") / tag / "out"
for n in ("RUN.json", "PROVIDER-OUTCOMES.jsonl", "io.jsonl", "progress.jsonl", "usage.json", "rows.json", "TERMINAL-STOP.json"):
    if (OUT / n).exists():
        shutil.copyfile(OUT / n, E / f"run-{n}")
if score.name != "-":
    shutil.copytree(score, E / "interim-score")
for n in [x for x in (f"{arm}.log", f"REPORT-{arm}-FULL.json", "RUN-LOG.jsonl", f"REPORT-{arm}-EXTRA.json", f"{arm}-REPORT.md") if (HERE / x).exists()] + sorted(p.name for p in HERE.glob(f"REPORT-{arm}-[0-9]*.json")):
    shutil.copyfile(HERE / n, E / n)
d = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
scope = d["ledger"]["scopes"][arm]["scope"]
c = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True); c.row_factory = sqlite3.Row
(E / "ledger-scope.json").write_text(json.dumps({"scope": dict(c.execute("select * from scopes where scope = ?", (scope,)).fetchone()),
    "entries": [dict(r) for r in c.execute("select * from entries where scope = ? order by id", (scope,))]}, indent=1) + "\n", encoding="utf-8")
c.close()
pc = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
(E / "rolling-counter-calls-last-48h.json").write_text(json.dumps([list(r) for r in pc.execute("select id, ep, at, track, task, source from calls where at >= strftime('%s','now') - 172800 order by id")], indent=0) + "\n", encoding="utf-8")
pc.close()
man = {p.relative_to(E).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(E.rglob("*")) if p.is_file()}
(E / "EVIDENCE-MANIFEST.json").write_text(json.dumps({"arm": arm, "tag": tag, "declaration_sha256": d and "6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1", "files": man}, indent=1) + "\n", encoding="utf-8")
print(len(man), "files saved to", E, "| manifest", hashlib.sha256((E / "EVIDENCE-MANIFEST.json").read_bytes()).hexdigest())
