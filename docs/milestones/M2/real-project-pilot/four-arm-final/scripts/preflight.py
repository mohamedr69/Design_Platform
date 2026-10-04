"""Runbook v2 step 1: read-only preflight. Writes PREFLIGHT-<utc>.json. No model request."""
import hashlib, json, pathlib, sqlite3, subprocess, sys, datetime
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True).stdout.strip()
D = pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json")
d = json.loads(D.read_text(encoding="utf-8"))
r = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
r["declaration"] = sha(D) == "6c0189b3dc30e721c318a5df44fac3507c5804430c85d3bdf6f23615002a70c1"
r["authorization_sha256"] = sha("C:/t/iso/work/r2x/r27/AUTHORIZATION-2026-10-01.md")
H = pathlib.Path(d["code"]["harness"]["dir"])
r["harness"] = all(sha(H / f) == h for f, h in d["code"]["harness"]["files"].items())
r["a_runner_imports"] = all(sha(p) == h for p, h in d["code"]["a_runner_imports"].items())
r["evaluator"] = sha(d["code"]["evaluator"]["file"]) == d["code"]["evaluator"]["sha256"]
other = {k: v for k, v in d["code"].items() if k not in ("harness", "a_runner_imports", "evaluator")}
r["other_code_keys"] = list(other)
def chk(v):
    if isinstance(v, dict) and "file" in v and "sha256" in v: return sha(v["file"]) == v["sha256"]
    if isinstance(v, dict) and "path" in v and "sha256" in v: return sha(v["path"]) == v["sha256"]
    return None
r["other_code"] = {k: chk(v) for k, v in other.items()}
r["trees"] = {t: (git(t, "rev-parse", "HEAD"), not git(t, "status", "--porcelain")) for t in ("C:/t/iso/frozen-r12", "C:/t/iso/cand-ai4")}
r["trees_ok"] = r["trees"]["C:/t/iso/frozen-r12"] == ("3d5607d99fcebf08ac45f5df937ad615ecc16fb3", True) and r["trees"]["C:/t/iso/cand-ai4"] == ("719e8de661b8b10427ef6cff5d2d277a53b64dc6", True)
L = pathlib.Path(d["harness_dir"]) / d["labels"]["dir"]
r["labels"] = all(sha(L / n) == h for n, h in d["labels"]["files"].items()) and sha(L / d["labels"]["manifest"]) == d["labels"]["manifest_sha256"]
st = json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))
r["stage"] = sha("C:/t/r2x/r21-stage/R21-STAGE.json") == d["stage"]["manifest_sha256"] and all(sha(f["path"]) == f["sha256"] for f in st["files"])
r["stage_files"] = len(st["files"])
c = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
fam = {s: json.loads(l) for (s, l) in c.execute("select scope, limits from scopes") if s.startswith(d["ledger"]["scope_family"])}
declared = {v["scope"]: v["limits"] for v in d["ledger"]["scopes"].values()}
r["family_scopes"] = sorted(fam)
r["family_scopes_declared_with_declared_limits"] = all(s in declared and fam[s] == declared[s] for s in fam)   # runbook step 1.6 (later starts)
r["new_family_scopes"] = [s for s in fam if s not in declared]                                                    # an undeclared scope is a failure
r["ledger_entries"] = c.execute("select count(*) from entries").fetchone()[0]
r["in_flight_any"] = c.execute("select count(*) from entries where state not in ('settled','released','refused')").fetchone()[0]
c.close()
r["PILOT_DRY_unset"] = "PILOT_DRY" not in __import__("os").environ
r["ok"] = all(r[k] for k in ("declaration", "harness", "a_runner_imports", "evaluator", "trees_ok", "labels", "stage", "PILOT_DRY_unset", "family_scopes_declared_with_declared_limits")) and not r["new_family_scopes"] and all(v is not False for v in r["other_code"].values())
out = pathlib.Path(__file__).parent / f"PREFLIGHT-{r['utc'][:19].replace(':','')}.json"
out.write_text(json.dumps(r, indent=1) + "\n", encoding="utf-8")
print(json.dumps(r, indent=1)); print("PREFLIGHT", "OK" if r["ok"] else "FAILED")
