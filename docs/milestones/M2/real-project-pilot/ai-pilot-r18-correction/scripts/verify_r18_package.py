"""Checker for the ai-pilot-r18-correction package (run after the final edit): manifest (no missing / changed /
unlisted file), relative Markdown links, declaration hash and bindings (accepted tree, successor commit and files,
labels, sample, stage, H-06 sources, evaluator, r16.1 harness), earlier packages unchanged (ai-accuracy-pilot and
review13-16), reviewer probes as required on the successor and identical to the reviewer's on e5a0a94, recorded test
results, ledger (<= 150 over pilot + continuation, 24 still free for H-06), business hashes equal, zero criticals, and the
H-06 pending refusal. Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import pathlib
import re
import subprocess

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/ai-pilot-r18-correction")
MR = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap")
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
git = lambda t, *a: subprocess.run(["git", "-C", t, *a], capture_output=True, text=True).stdout.strip()
res = {}
man = json.loads((PKG / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.name not in ("EVIDENCE-MANIFEST.json", "PACKAGE-CHECK.json")]}
links, broken = 0, []
for md in PKG.rglob("*.md"):
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists():
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}
D = PKG / "declaration/CONT-DECLARATION.json"
decl = json.loads(D.read_text(encoding="utf-8"))
res["declaration_sha256"] = sha(D)
res["accepted_tree"] = {"head": git("C:/t/iso/frozen-r12", "rev-parse", "HEAD"), "clean": not git("C:/t/iso/frozen-r12", "status", "--porcelain")}
res["successor"] = {"head": git("C:/t/iso/cand-ai2", "rev-parse", "HEAD"), "clean": not git("C:/t/iso/cand-ai2", "status", "--porcelain"),
                    "files_match": all(sha(pathlib.Path("C:/t/iso/cand-ai2") / f) == v for f, v in decl["code"]["successor"]["changed_files_vs_accepted"].items()),
                    "packaged_reader_matches": sha(PKG / "candidate/files/backend/app/ai/evidence_reader.py") == decl["code"]["successor"]["changed_files_vs_accepted"]["backend/app/ai/evidence_reader.py"]}
res["labels_match"] = all(sha(PKG / "labels-continuation" / n) == v for n, v in decl["labels"]["files"].items()) and \
    all(sha(PKG / "labels-v2" / n) == v for n, v in decl["labels"]["v2"].items())
res["sample_match"] = sha(PKG / "sample/CONTINUATION-SAMPLE.json") == decl["sources"]["sample"]["sha256"]
res["stage_match"] = sha(PKG / "sample/CONT-STAGE.json") == decl["stage"]["manifest_sha256"]
res["h06_sources_match"] = sha(decl["sources"]["boq_sheet"]["staged_path"]) == decl["sources"]["boq_sheet"]["sha256"] and \
    sha(decl["sources"]["boq_extraction_A"]["file"]) == decl["sources"]["boq_extraction_A"]["sha256"] and sha(decl["sources"]["h06_labels"]["file"]) == decl["sources"]["h06_labels"]["sha256"]
res["evaluator_unchanged"] = sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py") == decl["code"]["evaluator"]["sha256"]
res["r16_harness_unchanged"] = all(sha(pathlib.Path("C:/t/iso/work/r2x/r16") / f) == v for f, v in decl["code"]["boq_harness_r16"].items())
earlier = {}
for pk in ("review13", "review14", "review15", "review16", "ai-accuracy-pilot"):
    m = json.loads((PKG.parent / pk / "evidence/EVIDENCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]
    earlier[pk] = all(sha(PKG.parent / pk / k) == v["sha256"] for k, v in m.items())
res["earlier_packages_unchanged"] = earlier
old = json.loads((PKG / "probes/on-e5a0a94/TARGETED-PROBES.json").read_text(encoding="utf-8"))
reviewer = json.loads((MR / "reviews/M2-review-18/TARGETED-PROBES.json").read_text(encoding="utf-8"))
new = json.loads((PKG / "probes/on-successor/TARGETED-PROBES.json").read_text(encoding="utf-8"))
res["probes"] = {"e5a0a94_reproduces_reviewer": old == reviewer,
                 "successor_rescue_illegible_completed": new["targeted_rescue_after_illegible_blind"]["fields"]["own:identity"] == "completed",
                 "successor_rescue_empty_completed": new["targeted_rescue_after_empty_blind"]["fields"]["own:identity"] == "completed",
                 "successor_no_read_after_failed_escalation": ["read_field_context", "small"] not in new["targeted_after_failed_escalation"]["requests"],
                 "successor_primary_timeout_control": ["read_field_context", "small"] not in new["primary_timeout_control"]["requests"]}
T = PKG / "tests"
res["junit"] = {}
for x in sorted(T.glob("*.xml")):
    s = x.read_text(encoding="utf-8")
    res["junit"][x.stem] = {k: int(re.search(fr'{k}="(\d+)"', s).group(1)) for k in ("tests", "failures", "errors", "skipped")}
led = json.loads((PKG / "ledger/LEDGER-EXPORT.json").read_text(encoding="utf-8"))
res["ledger"] = led["original_150"]
met = json.loads((PKG / "results/CONT-METRICS.json").read_text(encoding="utf-8"))
res["no_business_change"] = met["no_business_change"]
res["critical"] = {a: (len(v["critical"]["resolved"]), len(v["critical"]["unresolved_label"])) for a, v in met["arms"].items() if "critical" in v}
res["h06"] = {"pending_refusal_logged": "cannot fit this arm now" in (PKG / "logs/run-h06-S-blocked-check.log").read_text(encoding="utf-8"),
              "h06_scopes_unused": not any(k.startswith("ai-pilot-r18-2026-09-30-H06") for k in led["settled_by_scope"])}
j = res["junit"]
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken
             and res["accepted_tree"] == {"head": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3", "clean": True}
             and res["successor"]["head"] == decl["code"]["successor"]["commit"] and res["successor"]["clean"] and res["successor"]["files_match"]
             and res["successor"]["packaged_reader_matches"] and res["labels_match"] and res["sample_match"] and res["stage_match"]
             and res["h06_sources_match"] and res["evaluator_unchanged"] and res["r16_harness_unchanged"] and all(earlier.values())
             and all(res["probes"].values())
             and all(j[k]["failures"] == 0 and j[k]["errors"] == 0 for k in ("FOCUSED-off", "FOCUSED-G", "FOCUSED-T", "FOCUSED-TE-shim", "R16-HARNESS", "BOQ-QUEUE"))
             and j["FOCUSED-TE-noshim"]["failures"] == 19
             and res["ledger"]["total_settled"] <= 150 and res["ledger"]["left"] >= res["ledger"]["reserved_for_h06"]
             and all(res["no_business_change"].values()) and set(res["critical"].values()) == {(0, 0)} and all(res["h06"].values()))
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1)[:3000])
