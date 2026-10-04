"""Checker for review31/: manifest (written last) complete and matching; markdown links; candidate commit statements and
reported test counts against the JUnit evidence; every test suite re-run FROM THE PACKAGED COPIES (selector 4, stop / state
/ scorer 26, capture store 21); the binding manifest re-verified entry by entry (packaged copies equal the bound files, code
commits clean, threshold sources, recorded B database, L3 captures); the draft declaration v2 binds the packaged binding
manifest, is not executed or authorised, has equal B / C caps and the 556 ceiling; the dry run made no model request, left
the ledger unchanged, returned PREPARATION BLOCKED, matched the Review 29 replays and passed the resume drill; the cohort is
metadata-only, unpermitted and disjoint from the used EPs; earlier packages, labels, evaluators, trees and the ledger
unchanged; thresholds verbatim in their sources; no authorisation document. Writes evidence/PACKAGE-CHECK.json."""
import hashlib
import json
import os
import pathlib
import re
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review31")
PIL = PKG.parent
WORK = pathlib.Path("C:/t/iso/work/r2x/r31")
PY = "C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"
CAND = "C:/t/iso/cand-r29"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
load = lambda p: json.loads(pathlib.Path(p).read_text(encoding="utf-8"))  # noqa: E731
git = lambda t, *a: subprocess.run(["git", "-C", str(t), *a], capture_output=True, text=True).stdout.strip()  # noqa: E731
sys.path.insert(0, str(PIL / "review30" / "scripts"))
import r30_checks as C  # noqa: E402

res = {}
mf = load(PKG / "evidence/EVIDENCE-MANIFEST.json")
man, final = mf["files"], mf["candidate_head"]
res["manifest"] = {"files": len(man), "mismatched_or_missing": [k for k, v in man.items() if not (PKG / k).exists() or sha(PKG / k) != v["sha256"]],
                   "unlisted": [p.relative_to(PKG).as_posix() for p in PKG.rglob("*") if p.is_file() and p.relative_to(PKG).as_posix() not in man
                                and p.relative_to(PKG).as_posix() not in ("evidence/EVIDENCE-MANIFEST.json", "evidence/PACKAGE-CHECK.json")
                                and "__pycache__" not in p.parts]}
links, broken = 0, []
mds = list(PKG.glob("*.md"))
for md in mds:
    for link in re.findall(r"\]\(([^)#]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
        if not link.startswith(("http:", "https:")):
            links += 1
            if not (md.parent / link).resolve().exists():
                broken.append((md.name, link))
res["markdown_links"] = {"checked": links, "broken": broken}

# ---- tests re-run from the packaged copies ------------------------------------------------------------------------------
env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "TEMP": "C:/t/iso/tmp", "TMP": "C:/t/iso/tmp"}


def pytest(args, cwd, extra=None):
    t = subprocess.run([PY, "-m", "pytest", "-q", *args, "-p", "no:cacheprovider"], capture_output=True, text=True, cwd=str(cwd), env={**env, **(extra or {})})
    last = t.stdout.strip().splitlines()[-1] if t.stdout.strip() else t.stderr[-300:]
    m = re.match(r"(\d+) passed", last)
    return {"exit": t.returncode, "summary": last, "passed": int(m.group(1)) if m else 0}


H = PKG / "scripts" / "harness"
res["tests"] = {"selector": pytest(["test_selector_core.py"], PKG / "scripts"),
                "stop_state_scorer": pytest(["test_stop_rules.py", "test_state_check.py", "test_score_bcr.py"], H),
                "capture_store": pytest([str(H / "test_capture_store.py"), "--rootdir", str(H)], f"{CAND}/backend", {"PYTHONPATH": str(H), "AI_ENABLED": "false"})}
expected = {"selector": 4, "stop_state_scorer": 26, "capture_store": 21}
res["tests_ok"] = all(res["tests"][k]["exit"] == 0 and res["tests"][k]["passed"] == n for k, n in expected.items())

# ---- commit statements and reported counts ------------------------------------------------------------------------------
owner = {p.name: p.read_text(encoding="utf-8") for p in mds}
owner["DRAFT-DECLARATION.v2.json"] = (PKG / "DRAFT-DECLARATION.v2.json").read_text(encoding="utf-8")
junit = {}
for x in ("selector.xml", "harness-pure.xml", "capture-store.xml"):
    junit.update(C.junit_module_counts(PKG / "tests" / x))
MOD = re.compile(r"\b(selector_core|stop_rules|state_check|score_bcr|capture_store)\.py`?[^|\n]{0,40}?\b(\d+) tests\b")
count_v = []
for name, text in owner.items():
    for n, line in enumerate(text.splitlines(), 1):
        for m in MOD.finditer(line):
            mod, cnt = "test_" + m.group(1), int(m.group(2))
            if junit.get(mod) != cnt:
                count_v.append({"doc": name, "line": n, "module": mod, "reported": cnt, "junit": junit.get(mod)})
        for m in re.finditer(r"\ball (\d+) tests\b", line):
            if int(m.group(1)) != sum(junit.values()):
                count_v.append({"doc": name, "line": n, "module": "total", "reported": int(m.group(1)), "junit": sum(junit.values())})
res["statements"] = {"junit_counts": junit, "junit_total": sum(junit.values()),
                     "commit_violations": C.check_commit_statements(owner, final, ["a4ce6a3", final, "719e8de"]), "count_violations": count_v}

# ---- binding manifest ---------------------------------------------------------------------------------------------------
bm = load(PKG / "BINDING-MANIFEST.json")
packaged = {**{f: f"scripts/{f}" for f in ("selector_core.py", "used_sets.py", "select_fresh_projects_r31.py", "reconcile_r30_picks.py", "test_selector_core.py", "feasibility_r31.py")},
            "FRESH-PROJECTS-R31.json": "cohort/FRESH-PROJECTS-R31.json", "R30-PICKS-RECONCILED.json": "cohort/R30-PICKS-RECONCILED.json",
            "FEASIBILITY-R31.json": "field-population/FEASIBILITY-R31.json",
            **{f"harness/{f}": f"scripts/harness/{f}" for f in ("capture_store.py", "test_capture_store.py", "state_check.py", "test_state_check.py", "run_lane.py",
                                                               "dry_run.py", "stop_rules.py", "test_stop_rules.py", "score_bcr.py", "test_score_bcr.py", "score_lane.py")},
            **{f"tests/{f}": f"tests/{f}" for f in ("selector.xml", "harness-pure.xml", "capture-store.xml")}}
bad = []
for group, files in bm["files"].items():
    for f, h in files.items():
        if (WORK / f).exists() and sha(WORK / f) != h:
            bad.append(("work", f))
        if f in packaged and sha(PKG / packaged[f]) != h:
            bad.append(("package", f))
        if f.startswith("dry-run/t3/") and not pathlib.Path(f).name.startswith("rows-") and sha(PKG / "dry-run" / pathlib.Path(f).name) != h:
            bad.append(("package", f))
MR = "C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap"
M2 = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2"
TH = {"AI-ACCURACY-POLICY.md": f"{MR}/AI-ACCURACY-POLICY.md", "MASTER-ROADMAP.md": f"{MR}/MASTER-ROADMAP.md", "M2-ACCEPTANCE-REPORT.md": f"{M2}/M2-ACCEPTANCE-REPORT.md",
      "review21/ANALYSIS-PLAN.md": f"{M2}/real-project-pilot/review21/ANALYSIS-PLAN.md"}
res["binding_manifest"] = {"sha256": sha(PKG / "BINDING-MANIFEST.json"), "file_mismatches": bad,
                           "candidate": bm["code"]["candidate"]["commit"] == final == git(CAND, "rev-parse", "HEAD") and not git(CAND, "status", "--porcelain"),
                           "candidate_reader": sha(f"{CAND}/backend/app/ai/evidence_reader.py") == bm["code"]["candidate"]["evidence_reader.py"],
                           "evaluator_10": sha(f"{CAND}/backend/scripts/m2_eval6.py") == bm["code"]["candidate"]["evaluator .10 scripts/m2_eval6.py"],
                           "baseline": bm["code"]["baseline"]["commit"] == git("C:/t/iso/frozen-r12", "rev-parse", "HEAD") and not git("C:/t/iso/frozen-r12", "status", "--porcelain"),
                           "evaluator_9": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py") == bm["code"]["baseline"]["evaluator .9 scripts/m2_eval5.py"],
                           "coverage_contract": sha(bm["code"]["coverage_contract"]["file"]) == bm["code"]["coverage_contract"]["sha256"],
                           "threshold_sources": all(sha(TH[k]) == v for k, v in bm["threshold_sources"].items()),
                           "b_database": sha("C:/t/r2x/runs/final-A/db/default.db") == bm["dry_run_inputs"]["B database (final-A), recorded after the four-arm run"],
                           "l3_captures": sha("C:/t/r2x/runs/final-L3/out/io.jsonl") == bm["dry_run_inputs"]["L3 captures io.jsonl"]}
res["binding_manifest_ok"] = not bad and all(v for k, v in res["binding_manifest"].items() if k not in ("sha256", "file_mismatches"))

# ---- draft declaration v2 -----------------------------------------------------------------------------------------------
dd = load(PKG / "DRAFT-DECLARATION.v2.json")
src_ok = []
for th in dd["thresholds_verbatim"]:
    texts = th["text"] if isinstance(th["text"], list) else [th["text"]]
    path = {"AI-ACCURACY-POLICY.md section 1": TH["AI-ACCURACY-POLICY.md"], "M2-ACCEPTANCE-REPORT.md Correction 5 targets": TH["M2-ACCEPTANCE-REPORT.md"],
            "MASTER-ROADMAP.md M2": TH["MASTER-ROADMAP.md"], "review21/ANALYSIS-PLAN.md section 5": TH["review21/ANALYSIS-PLAN.md"]}[th["source"]]
    body = pathlib.Path(path).read_text(encoding="utf-8")
    src_ok.append({"source": th["source"], "hash_matches": sha(path) == th["sha256"], "verbatim": all(x in body for x in texts)})
res["thresholds_verbatim"] = src_ok
caps = dd["limits"]["caps"]
res["declaration"] = {"sha256": sha(PKG / "DRAFT-DECLARATION.v2.json"),
                      "binds_packaged_binding_manifest": dd["binding_manifest"]["sha256"] == sha(PKG / "BINDING-MANIFEST.json"),
                      "not_executed_or_authorised": dd["executed"] is False and dd["budget_approved"] is False and dd["authorization"] is None,
                      "candidate": dd["code"]["candidate"]["commit"] == final,
                      "equal_caps": caps["B"] == caps["C"] and dd["limits"]["scope_estimate_thresholds"]["B"] == dd["limits"]["scope_estimate_thresholds"]["C"]
                      and dd["limits"]["elapsed_s"]["B"] == dd["limits"]["elapsed_s"]["C"],
                      "ceiling_556": dd["limits"]["total_cap"] == sum(caps.values()) == 556,
                      "gate_at_equal_caps_only": "no unequal-cap variant" in dd["analysis"]["request_normalised_gate"]["no_natural_policy_gate"],
                      "population_gate_12_all_fields": dd["selection"]["population_gate"]["minimum_resolved_independently_reviewed_per_field"] == 12
                      and dd["selection"]["population_gate"]["fields"] == ["identity", "revision", "decision"] and "no partial closure run" in dd["selection"]["population_gate"]["rule"],
                      "label_review_recorded_as_ai": "never as human sign-off" in dd["labels"]["review"],
                      "gpt_bridge_disabled": dd["gpt_bridge"].startswith("disabled"),
                      "dry_run_bound": dd["dry_run"]["sha256"] == sha(PKG / "dry-run" / "DRY-RUN-REPORT.json"),
                      "supersedes_review30": dd["supersedes"]["sha256"] == sha(PIL / "review30" / "DRAFT-DECLARATION.json")}

# ---- dry run ------------------------------------------------------------------------------------------------------------
dr = load(PKG / "dry-run" / "DRY-RUN-REPORT.json")
sc = load(PKG / "dry-run" / "SCORE-BCR.json")
res["dry_run"] = {"model_requests_0": dr["model_requests"] == 0 and all(not dr["lanes"][k]["live_provider_attempts_blocked"] for k in "CRP"),
                  "ledger_unchanged": dr["ledger_before"] == dr["ledger_after"] == {"entries": 483, "scopes": 17},
                  "population_gate_blocked": dr["population_gate"]["action"] == "PREPARATION BLOCKED" and sc["outcome"] == "PREPARATION BLOCKED" and bool(sc.get("exercise_only")),
                  "state_checks_ok": all(dr["lanes"][k]["state_check"]["ok"] for k in "CR"),
                  "transparency_identical": all(not dr["transparency"][k]["documents_with_different_observations"] for k in "CR"),
                  "store_isolation": not dr["store"]["duplicate_bound_keys"] and dr["store"]["r_rows_served_to_c"] == 0 and dr["store"]["b_or_c_served_from_p"] == 0,
                  "resume_drill": dr["resume_drill"]["passes"] is True and dr["resume_drill"]["dispatched_to_inner"] == 0,
                  "unequal_caps_refused": "R31-03" in dr["unequal_caps_check"], "no_default": sc["default_selected"] is None}

# ---- cohort -------------------------------------------------------------------------------------------------------------
fp = load(PKG / "cohort" / "FRESH-PROJECTS-R31.json")
eps = [r["ep"] for r in fp["picked"] + fp["alternates"]]
res["cohort"] = {"metadata_only": fp["content_read"].startswith("none") and "NOT permitted" in fp["permission"],
                 "disjoint_from_used": not (set(eps) & set(fp["used"]["eps_list"])),
                 "six_picks_four_alternates": len(fp["picked"]) == 6 and len(fp["alternates"]) == 4,
                 "distinct_unused_clusters": len({r["contractor_canonical"] for r in fp["picked"] + fp["alternates"]}) == 10
                 and all(not r["contractor_fresh"]["cluster_used"] and r["contractor_fresh"]["nearest_similarity"] < 0.85 for r in fp["picked"] + fp["alternates"]),
                 "plain_project_one_folder": all(r["topology_class"] == "project" and r["project_fresh"]["folders"] == 1 for r in fp["picked"] + fp["alternates"]),
                 "nothing_hydrated": all(r["placeholders_not_local"] == r["pdf"] for r in fp["picked"] + fp["alternates"]),
                 "no_authorization_document": not any("AUTHORIZATION" in k.upper() or "AUTHORISATION" in k.upper() for k in man)}

# ---- frozen -------------------------------------------------------------------------------------------------------------
frozen = {}
for name, h in (("review30", "453a9d61207c445be864ec96e9b9516517e14ea19813adb5fd46834daf10636c"), ("review29", "ca3f33ad4fadec2072d52b6f90e618c90bfabc16b12bae054c21a8739210d87b"),
                ("four-arm-final", "cf1b95f1e88889c82fa6897507773185d4abbfbeaa1228c0b8ed1a4f981d419b")):
    m = PIL / name / "evidence/EVIDENCE-MANIFEST.json"
    frozen[f"{name}_manifest"] = sha(m) == h
    frozen[f"{name}_files"] = all(sha(PIL / name / k) == v["sha256"] for k, v in load(m)["files"].items())
frozen |= {"labels_r26_2": sha("C:/t/iso/work/r2x/r27/labels-r26.2/LABEL-MANIFEST.r26.2.json") == "ed3c88e40daadaee6e4a7271d7dd9be430773a8c1b0976030d1bfb2a27a9a72d",
           "evaluator_9": sha("C:/t/iso/frozen-r12/backend/scripts/m2_eval5.py") == "38326f149a7f49246413427cf4a661134cc7d31734faa13fe80f8ad967a3e451",
           "cand_ai4_tree": git("C:/t/iso/cand-ai4", "rev-parse", "HEAD") == "719e8de661b8b10427ef6cff5d2d277a53b64dc6" and not git("C:/t/iso/cand-ai4", "status", "--porcelain")}
res["frozen"] = frozen
con = sqlite3.connect("file:C:/t/r2x/ledger/r2x-ledger.sqlite?mode=ro", uri=True)
res["ledger"] = {"entries": con.execute("select count(*) from entries").fetchone()[0], "scopes": con.execute("select count(*) from scopes").fetchone()[0]}
con.close()
res["ledger"]["unchanged"] = (res["ledger"]["entries"], res["ledger"]["scopes"]) == (483, 17)
res["candidate_after_tests"] = {"head": git(CAND, "rev-parse", "HEAD"), "clean": not git(CAND, "status", "--porcelain")}
res["ok"] = (not res["manifest"]["mismatched_or_missing"] and not res["manifest"]["unlisted"] and not broken and res["tests_ok"]
             and not res["statements"]["commit_violations"] and not res["statements"]["count_violations"] and res["binding_manifest_ok"]
             and all(x["hash_matches"] and x["verbatim"] for x in src_ok) and all(v for k, v in res["declaration"].items() if k != "sha256")
             and all(res["dry_run"].values()) and all(res["cohort"].values()) and all(frozen.values()) and res["ledger"]["unchanged"]
             and res["candidate_after_tests"] == {"head": final, "clean": True})
(PKG / "evidence/PACKAGE-CHECK.json").write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps(res, indent=1, default=str)[:5000])
print("OK" if res["ok"] else "NOT OK")
