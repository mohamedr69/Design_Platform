"""Source bindings of the four-arm readiness package (read-only): trees, the reviewed v4.3 harness files equal to the
review25 package and to the declaration, the A runner's imports, the labels (manifest and files), the stage and sample,
the evaluator, the Review 26 reviewer files, earlier package manifests, the R21 label skeletons (unchanged) and the live
ledger state (read-only: original experiment settled count, no scope of the new family). Writes bindings/SOURCE-BINDINGS.json."""
import hashlib
import json
import pathlib
import sqlite3
import subprocess

R = pathlib.Path(__file__).resolve().parent
PKGROOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True).stdout.strip()
decl = json.loads((R / "FINAL-DECLARATION.json").read_text(encoding="utf-8"))
trees = {"accepted": {"tree": "C:/t/iso/frozen-r12", "commit": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD"), "clean": not git("C:/t/iso/frozen-r12", "status", "--porcelain")},
         "candidate": {"tree": "C:/t/iso/cand-ai4", "commit": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD"), "clean": not git("C:/t/iso/cand-ai4", "status", "--porcelain")}}
H = pathlib.Path(decl["code"]["harness"]["dir"])
harness = {f: {"declared": h, "workspace": sha(H / f), "review25_package": sha(PKGROOT / "review25/harness-v4.3" / f)} for f, h in decl["code"]["harness"]["files"].items()}
a_imports = {p: {"declared": h, "now": sha(p)} for p, h in decl["code"]["a_runner_imports"].items()}
labels = {n: {"declared": h, "now": sha(R / "labels-r26" / n)} for n, h in decl["labels"]["files"].items()}
st = json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))
stage_ok = sha("C:/t/r2x/r21-stage/R21-STAGE.json") == decl["stage"]["manifest_sha256"] and all(
    sha(f["path"]) == f["sha256"] == decl["sources"]["sample"]["documents"][f["doc_key"]] for f in st["files"])
rev = MR / "reviews/M2-review-26"
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
ledger = {"settled_original_experiment": con.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0],
          "total_entries": con.execute("select count(*) from entries").fetchone()[0],
          "scopes_of_new_family": [s for (s,) in con.execute("select scope from scopes") if s.startswith(decl["ledger"]["scope_family"])]}
con.close()
out = {"declaration_sha256": sha(R / "FINAL-DECLARATION.json"), "trees": trees,
       "harness_files": harness, "harness_all_equal": all(v["declared"] == v["workspace"] == v["review25_package"] for v in harness.values()),
       "review25_frozen_harness_sha256": sha(PKGROOT / "review25/bindings/FROZEN-HARNESS.json"),
       "a_runner_imports": a_imports, "a_runner_imports_equal": all(v["declared"] == v["now"] for v in a_imports.values()),
       "evaluator": {"declared": decl["code"]["evaluator"]["sha256"], "now": sha(decl["code"]["evaluator"]["file"])},
       "durable_allowance": {"declared": decl["code"]["durable_allowance"]["sha256"], "now": sha(decl["code"]["durable_allowance"]["file"])},
       "labels": labels, "labels_equal": all(v["declared"] == v["now"] for v in labels.values()),
       "label_manifest": {"declared": decl["labels"]["manifest_sha256"], "now": sha(R / "labels-r26/LABEL-MANIFEST.r26.json")},
       "r21_label_skeletons": {p.name: sha(p) for p in sorted(pathlib.Path("C:/t/iso/work/r2x/review21/labels-r21").glob("*.json"))},
       "stage_and_27_files_equal": stage_ok,
       "reviewer_files_review26": {p.name: sha(p) for p in sorted(rev.iterdir()) if p.is_file()},
       "earlier_package_manifests": {pk: sha(PKGROOT / pk / "evidence/EVIDENCE-MANIFEST.json") for pk in
                                     ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction", "review19", "review20", "review21", "review22", "review23", "review24", "review25")},
       "ledger_read_only": ledger,
       "response_file": {"path": "docs/milestones/M2/M2-REVIEW-RESPONSE.md", "sha256_at_task_start": "182e655607d5c084fb38e1c1da5ea47888b6f613ff7dbef1b4aa3c0793547374"}}
(R / "bindings").mkdir(exist_ok=True)
(R / "bindings/SOURCE-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print("harness equal", out["harness_all_equal"], "| a imports", out["a_runner_imports_equal"], "| labels", out["labels_equal"], "| stage", stage_ok, "| trees", trees, "| ledger", ledger)
