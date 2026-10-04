"""Checker for review26/ (four-arm readiness): manifest complete, markdown links, the declaration hash and its bindings
(trees, reviewed v4.3 harness files equal to the review25 package, A-runner imports, evaluator, allowance, labels and label
manifest, stage and the 27 staged files), label completeness (27 register / 42 in-scope pages / every PDF's in-scope
pages labelled), label files equal to the packaged copies, R21 skeletons unchanged, Review 26 reviewer files unchanged,
earlier packages unchanged, enforcement cases, preflight exits and scorer output, the proposal figures (688 / 509 / 1,256,
96 h elapsed), the declaration NOT EXECUTED with no approved budget, and the live ledger untouched (128 settled; no scope of
the new family). Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review26")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))
res = {}
man = load(PKG / "evidence/EVIDENCE-MANIFEST.json")["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.glob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists() and link != "evidence/PACKAGE-CHECK.json":
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
D = PKG / "declaration/FINAL-DECLARATION.json"
d = load(D)
res["declaration"] = {"sha256": sha(D), "equals_workspace": sha(D) == sha("C:/t/iso/work/r2x/r26/FINAL-DECLARATION.json"),
                      "not_executed": d["executed"] is False and "NOT EXECUTED" in d["status"] and d["new_model_budget_approved"] is False,
                      "candidate": d["arms"]["L1"]["commit"] == "719e8de661b8b10427ef6cff5d2d277a53b64dc6", "baseline": d["code"]["accepted_app"]["commit"] == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3",
                      "caps": d["ledger"]["caps"], "sum_caps": d["ledger"]["sum_caps"],
                      "elapsed": {k: v["limits"]["elapsed_s"] for k, v in d["ledger"]["scopes"].items()}, "tokens_per_scope": {k: (v["limits"]["input_tokens"], v["limits"]["output_tokens"]) for k, v in d["ledger"]["scopes"].items()},
                      "figures": d["workload"]["three_request_figures"], "scope_family": d["ledger"]["scope_family"], "n_planned": d["sources"]["sample"]["n_planned"]}
b = load(PKG / "bindings/SOURCE-BINDINGS.json")
H = pathlib.Path(d["code"]["harness"]["dir"])
res["bindings_now"] = {"trees": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD") == "719e8de661b8b10427ef6cff5d2d277a53b64dc6" and not git("C:/t/iso/cand-ai4", "status", "--porcelain")
                       and git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3" and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                       "harness": all(sha(H / f) == h == sha(PKG.parent / "review25/harness-v4.3" / f) for f, h in d["code"]["harness"]["files"].items()),
                       "a_runner_imports": all(sha(p) == h for p, h in d["code"]["a_runner_imports"].items()),
                       "evaluator": sha(d["code"]["evaluator"]["file"]) == d["code"]["evaluator"]["sha256"],
                       "allowance": sha(d["code"]["durable_allowance"]["file"]) == d["code"]["durable_allowance"]["sha256"],
                       "labels_workspace": all(sha(pathlib.Path(d["harness_dir"]) / d["labels"]["dir"] / n) == h for n, h in d["labels"]["files"].items()),
                       "labels_packaged": all(sha(PKG / "labels-r26" / n) == h for n, h in d["labels"]["files"].items()),
                       "label_manifest": sha(PKG / "labels-r26/LABEL-MANIFEST.r26.json") == d["labels"]["manifest_sha256"],
                       "stage": b["stage_and_27_files_equal"] and sha("C:/t/r2x/r21-stage/R21-STAGE.json") == d["stage"]["manifest_sha256"],
                       "r21_skeletons_unchanged": all(sha(pathlib.Path("C:/t/iso/work/r2x/review21/labels-r21") / n) == h for n, h in b["r21_label_skeletons"].items())
                       and all(sha(PKG.parent / "review21/labels-r21" / n) == h for n, h in b["r21_label_skeletons"].items() if (PKG.parent / "review21/labels-r21" / n).exists())}
REG, PAGE = load(PKG / "labels-r26/R26-REGISTER-LABELS.json"), load(PKG / "labels-r26/R26-PAGE-LABELS.json")
planned = d["sources"]["sample"]["documents_planned"]
pdfs = [p for p in planned if p["extension"] == ".pdf"]
res["labels"] = {"register_docs": len(REG["documents"]), "register_covers_planned": {x["doc"] for x in REG["documents"]} == {p["doc"] for p in planned},
                 "page_docs": len(PAGE["documents"]), "every_pdf_page_labelled": all(PAGE["documents"][p["doc"]]["pages_labelled"] == list(range(1, min(p["pages"], 4) + 1)) for p in pdfs),
                 "in_scope_pages": sum(len(v["pages_labelled"]) for v in PAGE["documents"].values()), "records": sum(len(v["records"]) for v in PAGE["documents"].values()),
                 "frozen_before_prediction": load(PKG / "labels-r26/LABEL-MANIFEST.r26.json")["frozen_before_any_prediction"],
                 "provenance": REG["provenance"]}
res["reviewer_files_unchanged"] = all((MR / "reviews/M2-review-26" / n).exists() and sha(MR / "reviews/M2-review-26" / n) == h for n, h in b["reviewer_files_review26"].items())
earlier = {}
for pk, h in b["earlier_package_manifests"].items():
    mp = PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json"
    earlier[pk] = sha(mp) == h and all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in load(mp)["files"].items())
res["earlier_packages_unchanged"] = earlier
enf = load(PKG / "enforcement/ENFORCEMENT.json")
res["enforcement"] = {k: v["ok"] for k, v in enf["cases"].items()}
log = (PKG / "preflight/PREFLIGHT.log").read_text(encoding="utf-8")
metrics = load(PKG / "preflight/score/ARMS-METRICS.v4.json")
res["preflight"] = {"exits": re.findall(r"(\w[\w ]*) exit (\d+)", log), "all_zero": all(e == "0" for e in re.findall(r"exit (\d+)", log)),
                    "scorer_planned": len(metrics["planned"]), "valid_claims": metrics["valid_accuracy_claims"],
                    "extra_facts": {a: len(c["extra_facts_outside_scope"]) for a, c in metrics["coverage"].items()},
                    "dry_declaration_differs_only_by_status_time_and_scope_names": None}
_dry = load(PKG / "preflight/FINAL-DECLARATION.dry.json")
_strip = lambda x: {k: v for k, v in x.items() if k not in ("status", "declared_at_utc", "ledger")}
_lim = lambda x: {k: v["limits"] for k, v in x["ledger"]["scopes"].items()}
res["preflight"]["dry_declaration_differs_only_by_status_time_and_scope_names"] = _strip(_dry) == _strip(d) and _lim(_dry) == _lim(d) and _dry["ledger"]["caps"] == d["ledger"]["caps"]
Lg = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = Lg.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
fam = [s for (s,) in Lg.execute("select scope from scopes") if s.startswith("m2-four-arm-final")]
Lg.close()
res["ledger"] = {"settled_original_experiment": settled, "new_family_scopes": fam}
dd = res["declaration"]
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and dd["equals_workspace"] and dd["not_executed"] and dd["candidate"] and dd["baseline"]
             and dd["sum_caps"] == 688 and dd["caps"] == {"A": 8, "L1": 160, "L2": 160, "L3": 180, "L4": 180}
             and dd["elapsed"] == {"A": 14400, "L1": 345600, "L2": 345600, "L3": 345600, "L4": 345600}
             and dd["figures"]["expected_workload_requests"] == 509 and dd["figures"]["uncapped_structural_maximum_requests"] == 1256 and dd["n_planned"] == 27
             and all(res["bindings_now"].values()) and res["labels"]["register_docs"] == 27 and res["labels"]["register_covers_planned"] and res["labels"]["every_pdf_page_labelled"]
             and res["labels"]["in_scope_pages"] == 42 and res["labels"]["frozen_before_prediction"] and res["reviewer_files_unchanged"] and all(earlier.values())
             and all(res["enforcement"].values()) and res["preflight"]["all_zero"] and res["preflight"]["dry_declaration_differs_only_by_status_time_and_scope_names"] and res["preflight"]["scorer_planned"] == 27 and all(v == 0 for v in res["preflight"]["extra_facts"].values())
             and settled == 128 and not fam)
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k not in ("earlier_packages_unchanged",)}, indent=1, default=str)[:3000])
print("OK" if res["ok"] else "NOT OK")
