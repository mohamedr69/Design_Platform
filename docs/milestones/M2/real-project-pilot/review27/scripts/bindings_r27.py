"""Bindings of the Review 27 correction package (read-only checks): declaration v2 and the unchanged v1, labels r26.2 and
the unchanged r26.1 / R21 skeletons, the reviewed v4.3 harness and A-runner imports, the evaluator, the stage, the
Review 27 reviewer files, the earlier package manifests (review13..review26) and the live ledger state.
Writes bindings/SOURCE-BINDINGS.json."""
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
d2 = json.loads((R / "FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
H = pathlib.Path(d2["code"]["harness"]["dir"])
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
ledger = {"settled_original_experiment": con.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0],
          "total_entries": con.execute("select count(*) from entries").fetchone()[0],
          "scopes_of_new_family": [s for (s,) in con.execute("select scope from scopes") if s.startswith(d2["ledger"]["scope_family"])]}
con.close()
out = {
    "declaration_v2_sha256": sha(R / "FINAL-DECLARATION.v2.json"),
    "declaration_v1": {"path": "C:/t/iso/work/r2x/r26/FINAL-DECLARATION.json", "sha256": sha("C:/t/iso/work/r2x/r26/FINAL-DECLARATION.json"),
                       "expected": "aec4d4df3d400126b95c17938aafe267d9444baba04a8bb4ddedce088edef998", "superseded_by_v2": d2["supersedes"]["declaration_sha256"]},
    "labels_r26_2": {n: sha(R / "labels-r26.2" / n) for n in sorted(p.name for p in (R / "labels-r26.2").iterdir())},
    "labels_r26_1_manifest": {"sha256": sha("C:/t/iso/work/r2x/r26/labels-r26/LABEL-MANIFEST.r26.json"), "expected": "b29d93d162a375ca8d1d2a648c8522af8c3d132a6957c93a2b21e96c63812509"},
    "labels_r26_1_files_unchanged": all(sha(pathlib.Path("C:/t/iso/work/r2x/r26/labels-r26") / n) == h for n, h in json.loads(pathlib.Path("C:/t/iso/work/r2x/r26/labels-r26/LABEL-MANIFEST.r26.json").read_text(encoding="utf-8"))["files"].items()),
    "r21_label_skeletons": {p.name: sha(p) for p in sorted(pathlib.Path("C:/t/iso/work/r2x/review21/labels-r21").glob("*.json"))},
    "trees": {"accepted": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD"), "accepted_clean": not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
              "candidate": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD"), "candidate_clean": not git("C:/t/iso/cand-ai4", "status", "--porcelain")},
    "harness_equal": all(sha(H / f) == h == sha(PKGROOT / "review25/harness-v4.3" / f) for f, h in d2["code"]["harness"]["files"].items()),
    "a_runner_imports_equal": all(sha(p) == h for p, h in d2["code"]["a_runner_imports"].items()),
    "evaluator_equal": sha(d2["code"]["evaluator"]["file"]) == d2["code"]["evaluator"]["sha256"],
    "stage_equal": sha("C:/t/r2x/r21-stage/R21-STAGE.json") == d2["stage"]["manifest_sha256"] and all(
        sha(f["path"]) == f["sha256"] for f in json.loads(pathlib.Path("C:/t/r2x/r21-stage/R21-STAGE.json").read_text(encoding="utf-8"))["files"]),
    "reviewer_files_review27": {p.name: sha(p) for p in sorted((MR / "reviews/M2-review-27").iterdir()) if p.is_file()},
    "earlier_package_manifests": {pk: sha(PKGROOT / pk / "evidence/EVIDENCE-MANIFEST.json") for pk in
                                  ("review13", "review14", "review15", "review16", "ai-accuracy-pilot", "ai-pilot-r18-correction", "review19", "review20", "review21", "review22", "review23", "review24", "review25", "review26")},
    "ledger_read_only": ledger,
    "response_file_sha256_at_task_start": "e621fa7eb388b01e652bacf8ee78369b306609fff9b7b1412d0f807d1dfa7e62",
}
(R / "bindings").mkdir(exist_ok=True)
(R / "bindings/SOURCE-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print({k: out[k] for k in ("harness_equal", "a_runner_imports_equal", "evaluator_equal", "stage_equal", "labels_r26_1_files_unchanged", "trees", "ledger_read_only")},
      "| v1 unchanged", out["declaration_v1"]["sha256"] == out["declaration_v1"]["expected"])
