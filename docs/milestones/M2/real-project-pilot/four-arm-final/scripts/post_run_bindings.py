"""Post-run bindings (read-only): declaration, authorization, harness, A-runner imports, evaluator, allowance module, trees,
labels r26.2 (and r26.1 unchanged), stage, ledger family scopes (declared only, declared limits, nothing in flight), the
original 150-request experiment's settled count, business hashes of every arm equal the A base, sandbox databases.
Writes POST-RUN-BINDINGS.json."""
import hashlib
import json
import pathlib
import sqlite3
import subprocess

R = pathlib.Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True).stdout.strip()
DP = pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json")
d = json.loads(DP.read_text(encoding="utf-8"))
H = pathlib.Path(d["code"]["harness"]["dir"])
L = pathlib.Path(d["harness_dir"]) / d["labels"]["dir"]
st = json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))
c = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
fam = {s: json.loads(l) for (s, l) in c.execute("select scope, limits from scopes") if s.startswith(d["ledger"]["scope_family"])}
declared = {v["scope"]: v["limits"] for v in d["ledger"]["scopes"].values()}
inflight = c.execute("select count(*) from entries where state not in ('settled','released','refused')").fetchone()[0]
per_scope = {s: c.execute("select count(*) from entries where scope = ?", (s,)).fetchone()[0] for s in declared}
orig = c.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
c.close()
runs = pathlib.Path("C:/t/r2x/runs")
a_db = runs / "final-A/db/default.db"
ac = sqlite3.connect(f"file:{a_db.as_posix()}?mode=ro", uri=True)
bh = {t: hashlib.sha256(json.dumps([list(r) for r in ac.execute(f"select * from {t} order by id")], default=str).encode()).hexdigest() for t in ("project_submittals", "project_shop_drawings", "project_actions")}
bh["project_documents_role"] = hashlib.sha256(json.dumps([list(r) for r in ac.execute("select id, role from project_documents order by id")]).encode()).hexdigest()
ac.close()
caps = {v["scope"]: d["ledger"]["caps"][k] for k, v in d["ledger"]["scopes"].items()}
out = {"declaration_sha256": sha(DP), "declaration_ok": sha(DP) == "6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1",
       "authorization_sha256": sha("C:/t/iso/work/r2x/r27/AUTHORIZATION-2026-10-01.md"),
       "harness": all(sha(H / f) == h for f, h in d["code"]["harness"]["files"].items()),
       "a_runner_imports": all(sha(p) == h for p, h in d["code"]["a_runner_imports"].items()),
       "evaluator": sha(d["code"]["evaluator"]["file"]) == d["code"]["evaluator"]["sha256"],
       "durable_allowance": sha(d["code"]["durable_allowance"]["file"]) == d["code"]["durable_allowance"]["sha256"] if "file" in d["code"]["durable_allowance"] else None,
       "trees": {t: [git(t, "rev-parse", "HEAD"), not git(t, "status", "--porcelain")] for t in ("C:/t/iso/frozen-r12", "C:/t/iso/cand-ai4")},
       "labels_r26_2": all(sha(L / n) == h for n, h in d["labels"]["files"].items()) and sha(L / d["labels"]["manifest"]) == d["labels"]["manifest_sha256"],
       "labels_r26_1_manifest": sha("C:/t/iso/work/r2x/r26/labels-r26/LABEL-MANIFEST.r26.json") == "b29d93d162a375ca8d1d2a648c8522af8c3d132a6957c93a2b21e96c63812509",
       "stage": sha("C:/t/r2x/r21-stage/R21-STAGE.json") == d["stage"]["manifest_sha256"] and all(sha(f["path"]) == f["sha256"] for f in st["files"]),
       "family_scopes": sorted(fam), "family_scopes_declared_with_declared_limits": all(s in declared and fam[s] == declared[s] for s in fam),
       "dispatched_per_scope": per_scope, "within_caps": all(per_scope[s] <= caps[s] for s in per_scope), "in_flight_any": inflight,
       "original_experiment_settled": orig,
       "business_hashes_equal_A": {a: json.loads((runs / f"final-{a}/out/RUN.json").read_text(encoding="utf-8")).get("business_hashes") == bh for a in ("L1", "L2", "L3", "L4")},
       "sandbox_databases": {a: sha(runs / f"final-{a}/db/default.db") for a in ("A", "L1", "L2", "L3", "L4")}}
out["ok"] = (out["declaration_ok"] and out["harness"] and out["a_runner_imports"] and out["evaluator"] and out["labels_r26_2"] and out["labels_r26_1_manifest"] and out["stage"]
             and out["family_scopes_declared_with_declared_limits"] and out["within_caps"] and inflight == 0 and orig == 128 and all(out["business_hashes_equal_A"].values())
             and all(v == ["3d5607d99fcebf08ac45f5df937ad615ecc16fb3", True] if "frozen" in k else v == ["719e8de661b8b10427ef6cff5d2d277a53b64dc6", True] for k, v in out["trees"].items()))
(R / "POST-RUN-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps(out, indent=1))
