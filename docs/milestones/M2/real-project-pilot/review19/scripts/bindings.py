"""Frozen source bindings of the Review 19 correction (read-only): commits and file hashes of the accepted tree, the
reviewed candidate and the successor; the H-06 declaration and everything it binds (unchanged: the R19 reader change
does not rebind the BOQ control); labels; the result-v2 scorer; the reviewer's files. Writes bindings/SOURCE-BINDINGS.json
and candidate/c216206-to-69ee759.diff."""
import hashlib
import json
import pathlib
import subprocess

W = pathlib.Path("C:/t/iso/work/r2x/review19")
R18 = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True, check=True).stdout.strip()
SUC = "C:/t/iso/cand-ai3"
assert git(SUC, "rev-parse", "HEAD") == "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6" and not git(SUC, "status", "--porcelain")
assert git("C:/t/iso/cand-ai2", "rev-parse", "HEAD") == "c216206df6812fb17b32719a28cdd4300d44a5c1" and not git("C:/t/iso/cand-ai2", "status", "--porcelain")
assert git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not git("C:/t/iso/frozen-r12", "status", "--porcelain")
diff = subprocess.run(["git", "-C", SUC, "diff", "--binary", "c216206", "69ee759"], capture_output=True).stdout
(W / "pkg-src/candidate").mkdir(parents=True, exist_ok=True)
(W / "pkg-src/candidate/c216206-to-69ee759.diff").write_bytes(diff)
(W / "pkg-src/candidate/69ee759.patch").write_bytes(subprocess.run(["git", "-C", SUC, "format-patch", "-1", "--stdout", "69ee759"], capture_output=True).stdout)
changed = git(SUC, "diff", "--name-only", "c216206", "69ee759").splitlines()
decl = json.loads((R18 / "CONT-DECLARATION.json").read_text(encoding="utf-8"))
out = {"accepted": {"commit": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "tree": "C:/t/iso/frozen-r12", "clean": True},
       "reviewed_candidate": {"commit": "c216206df6812fb17b32719a28cdd4300d44a5c1", "tree": "C:/t/iso/cand-ai2", "clean": True,
                              "evidence_reader_sha256": sha("C:/t/iso/cand-ai2/backend/app/ai/evidence_reader.py")},
       "successor": {"commit": "69ee75937bf190a0bf605dc0b79eecf29b0f3dc6", "tree": SUC, "branch": git(SUC, "rev-parse", "--abbrev-ref", "HEAD"),
                     "parent": "c216206df6812fb17b32719a28cdd4300d44a5c1", "clean": True, "changed_files": {f: sha(f"{SUC}/{f}") for f in changed},
                     "diff_sha256": hashlib.sha256(diff).hexdigest(), "repository": "C:/t/iso/ep-platform (scratch clone; not the owner checkout)"},
       "h06_control_binding_unchanged": {"declaration": str(R18 / "CONT-DECLARATION.json").replace("\\", "/"), "sha256": sha(R18 / "CONT-DECLARATION.json"),
                                         "runner_cont_boq_sha256": sha(R18 / "cont_boq.py"), "runner_matches_declaration": sha(R18 / "cont_boq.py") == decl["code"]["scripts"]["cont_boq.py"],
                                         "boq_arm_reader": decl["arms"]["S"]["commit"], "boq_queue_sha256": decl["code"]["boq_queue_sha256"],
                                         "h06_sheet_sha256": decl["sources"]["boq_sheet"]["sha256"], "note": "the R19 document-reader change is not bound into the BOQ control"},
       "labels": {"continuation": decl["labels"]["files"], "v2": decl["labels"]["v2"], "unchanged": all(sha(R18 / decl["labels"]["dir"] / n) == h for n, h in decl["labels"]["files"].items())},
       "evaluator": decl["code"]["evaluator"], "result_v2_scorer_sha256": sha(W / "score_cont_v2.py"),
       "reviewer_files": {p.name: sha(p) for p in sorted((MR / "reviews/M2-review-19").glob("*")) if p.is_file()}}
(W / "bindings").mkdir(exist_ok=True)
(W / "bindings/SOURCE-BINDINGS.json").write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: out[k] for k in ("successor", "h06_control_binding_unchanged")}, indent=1)[:1800])
