"""Checker for review27/: manifest complete, markdown links, declaration v2 (hash, binding to labels r26.2 and the review
artifacts, limits / caps identical to v1, NOT EXECUTED, supersedes v1), v1 and r26.1 labels and R21 skeletons unchanged,
r26.2 rulings present and limited, document-level uncertainty unchanged, every planned document / in-scope page bound,
the budget arithmetic, the owner documents' required statements (application-visible, estimates + breaker, no hard
actual-token bound, unknown cost, 96 h proposal, ROI limitation, new declaration hash) and the absence of the removed
claims, the re-score delta, the ROI population, reviewer files and earlier packages unchanged, the live ledger untouched.
Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import sqlite3

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review27")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
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
D2 = PKG / "declaration/FINAL-DECLARATION.v2.json"
d2 = load(D2)
d1 = load("C:/t/iso/work/r2x/r26/FINAL-DECLARATION.json")
b = load(PKG / "bindings/SOURCE-BINDINGS.json")
L = pathlib.Path(d2["harness_dir"]) / d2["labels"]["dir"]
res["declaration"] = {"sha256": sha(D2), "equals_workspace": sha(D2) == sha("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json"),
                      "v1_unchanged": sha("C:/t/iso/work/r2x/r26/FINAL-DECLARATION.json") == "aec4d4df3d400126b95c17938aafe267d9444baba04a8bb4ddedce088edef998",
                      "supersedes_v1": d2["supersedes"]["declaration_sha256"] == "aec4d4df3d400126b95c17938aafe267d9444baba04a8bb4ddedce088edef998",
                      "not_executed": d2["executed"] is False and "NOT EXECUTED" in d2["status"] and d2["new_model_budget_approved"] is False,
                      "limits_identical_to_v1": {k: v["limits"] for k, v in d2["ledger"]["scopes"].items()} == {k: v["limits"] for k, v in d1["ledger"]["scopes"].items()} and d2["ledger"]["caps"] == d1["ledger"]["caps"],
                      "caps": d2["ledger"]["caps"], "sum_caps": d2["ledger"]["sum_caps"], "arithmetic": sum(d2["ledger"]["caps"].values()) == 688 == d2["ledger"]["sum_caps"],
                      "limit_semantics_present": all(k in d2["ledger"]["limit_semantics"] for k in ("requests", "tokens", "elapsed", "cost")),
                      "labels_bound": all(sha(L / n) == h == sha(PKG / "labels-r26.2" / n) for n, h in d2["labels"]["files"].items()) and sha(L / d2["labels"]["manifest"]) == d2["labels"]["manifest_sha256"] == sha(PKG / "labels-r26.2" / d2["labels"]["manifest"]),
                      "review_artifacts_bound": all(sha(MR / "reviews/M2-review-27" / n) == h for n, h in d2["labels"]["independent_review_bindings"].items()),
                      "same_design_as_v1": all(d2[k] == d1[k] for k in ("arms", "doc_arms", "sources", "stage", "application_limits", "project_day", "lifecycle", "stop_rules", "provider", "authorization", "code"))}
REG, PAGE, UNC = (load(PKG / "labels-r26.2" / d2["labels"][k]) for k in ("register", "page", "uncertainty"))
CH = load(PKG / "labels-r26.2/R26.2-CHANGES.json")
old_unc = load("C:/t/iso/work/r2x/r26/labels-r26/R26-UNCERTAINTY-AND-EXPOSURE.json")
planned = d2["sources"]["sample"]["documents_planned"]
pg = lambda did, n: next(r for r in PAGE["documents"][next(x["doc"] for x in REG["documents"] if x["draft_id"] == did)]["records"] if r["page"] == n)
res["labels"] = {"version": REG["labels_version"], "register_covers_planned": {x["doc"] for x in REG["documents"]} == {p["doc"] for p in planned},
                 "every_pdf_page_bound": all(PAGE["documents"][p["doc"]]["pages_labelled"] == list(range(1, min(p["pages"], 4) + 1)) and PAGE["documents"][p["doc"]]["sha256"] == p["sha256"] for p in planned if p["extension"] == ".pdf"),
                 "r26_1_unchanged": b["labels_r26_1_files_unchanged"] and b["labels_r26_1_manifest"]["sha256"] == b["labels_r26_1_manifest"]["expected"],
                 "r21_skeletons_unchanged": all(sha(pathlib.Path("C:/t/iso/work/r2x/review21/labels-r21") / n) == h for n, h in b["r21_label_skeletons"].items()),
                 "changes": [(c["id"], c["field"]) for c in CH["changes"]],
                 "D17_value_kept_actor_uncertain": pg("D17", 1)["decision"] == "approved as noted" and pg("D17", 1)["actor_attribution"]["state"] == "inferred_unresolved",
                 "D19_literal_and_normalized": pg("D19", 1)["decision"] == "rejected" and "Revise & Resubmit" in pg("D19", 1)["decision_literal"] and all(pg("D19", n)["decision"] == "UR" for n in (2, 3, 4)),
                 "D05_stage": pg("D05", 1)["stage_printed"].startswith("ASBUILT") and pg("D05", 1)["decision"] == "UR",
                 "D27_not_verified": "not visually verified" in next(x for x in REG["documents"] if x["draft_id"] == "D27")["verification"],
                 "doc_level_uncertainty_unchanged": sorted({u["doc"] for u in UNC["uncertainty"]}) == sorted({u["doc"] for u in old_unc["uncertainty"]}),
                 "D17_field_uncertainty": [u["draft_id"] for u in UNC["field_uncertainty"]] == ["D17"] and not any(c["draft_id"] == "D17" for c in UNC["labelling_conventions"]),
                 "independent_review_credited": "independent AI source review" in REG["provenance"]["independent_review"] and REG["provenance"]["human_signoff"] == "none"}
txt = {n: (PKG / n).read_text(encoding="utf-8") for n in ("BUDGET-PROPOSAL.md", "DECISION-CARD.md", "RUNBOOK.md", "CORRECTION-REPORT.md")}
need = {"application-visible": ["BUDGET-PROPOSAL.md", "DECISION-CARD.md", "CORRECTION-REPORT.md"], "estimates": ["BUDGET-PROPOSAL.md", "DECISION-CARD.md", "RUNBOOK.md"],
        "breaker": ["BUDGET-PROPOSAL.md", "DECISION-CARD.md", "RUNBOOK.md"], "no hard actual-token bound": ["DECISION-CARD.md"], "unknown": ["BUDGET-PROPOSAL.md", "DECISION-CARD.md"],
        "96 h": ["BUDGET-PROPOSAL.md", "DECISION-CARD.md"], "D16": ["BUDGET-PROPOSAL.md", "DECISION-CARD.md"], "6c0189b3": ["BUDGET-PROPOSAL.md", "DECISION-CARD.md", "RUNBOOK.md", "CORRECTION-REPORT.md"]}
res["owner_text_required"] = {k: all(k in txt[f] for f in fs) for k, fs in need.items()}
removed = ["never an overspend", "at most 20 M input and 3 M output", "Tokens, enforced per scope"]
CLAIM_DOCS = ("BUDGET-PROPOSAL.md", "DECISION-CARD.md", "RUNBOOK.md")      # the documents that make claims; the correction report / diff quote removed claims as removed
res["owner_text_removed_claims_absent"] = {c: not any(c in txt[n] for n in CLAIM_DOCS) for c in removed}
delta = load(PKG / "evidence/RESCORE-DELTA.json")
res["rescore_identical"] = all(all(v) for v in delta["identical_recovery_coverage_eligibility"].values())
roi = load(PKG / "evidence/ROI-POPULATION.json")
res["roi"] = {"crop_eligible": roi["decision_pages_crop_eligible"], "whole_page": roi["decision_pages_whole_page_discovery"],
              "ok": roi["decision_pages_crop_eligible"] == ["D16 p1", "D17 p1", "D18 p1"] and sorted(roi["decision_pages_whole_page_discovery"]) == ["D04 p1", "D19 p1", "D22 p1", "D22 p2"]}
res["bindings_now"] = {k: b[k] for k in ("harness_equal", "a_runner_imports_equal", "evaluator_equal", "stage_equal")}
res["reviewer_files_unchanged"] = all(sha(MR / "reviews/M2-review-27" / n) == h for n, h in b["reviewer_files_review27"].items())
earlier = {}
for pk, h in b["earlier_package_manifests"].items():
    mp = PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json"
    earlier[pk] = sha(mp) == h and all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in load(mp)["files"].items())
res["earlier_packages_unchanged"] = earlier
Lg = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
settled = Lg.execute("select count(*) from entries where scope like 'ai-pilot%' and state = 'settled'").fetchone()[0]
fam = [s for (s,) in Lg.execute("select scope from scopes") if s.startswith("m2-four-arm-final")]
Lg.close()
res["ledger"] = {"settled_original_experiment": settled, "new_family_scopes": fam}
dd, ll = res["declaration"], res["labels"]
EXPECTED_CHANGES = [("D17", "decision_actor"), ("D19", "decision_literal (added)"), ("D05", "stage_printed (added, descriptive)"), ("D27", "verification (added)")]
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken
             and all(v for k, v in dd.items() if isinstance(v, bool)) and all(v for k, v in ll.items() if isinstance(v, bool))
             and [tuple(x) for x in ll["changes"]] == EXPECTED_CHANGES
             and all(res["owner_text_required"].values()) and all(res["owner_text_removed_claims_absent"].values()) and res["rescore_identical"] and res["roi"]["ok"]
             and all(res["bindings_now"].values()) and res["reviewer_files_unchanged"] and all(earlier.values()) and settled == 128 and not fam)
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in res.items() if k not in ("earlier_packages_unchanged",)}, indent=1, default=str)[:3500])
print("OK" if res["ok"] else "NOT OK")
