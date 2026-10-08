"""R43-40: every difference between the executed v3 declaration (9a55fa7b...1b40) and the v4 declaration of this package,
mechanically (the v2 -> v3 method of ORCH-10, below, with the R43 re-point in place of the Desktop re-point). Each leaf is:
  unchanged            byte-equal value
  repointed            equal once the R43 re-point is applied (frozen-r12 -> frozen-r13, cand-r29 -> cand-r30n, their HEADs, and
                       the harness folder review42/scripts/harness-r32 -> review43/scripts/harness-r32; nothing else)
  rebound              the sha256 of a {path, sha256} node whose path was re-pointed to a review43 harness file, equal to the hash
                       BINDING-MANIFEST-R43-HARNESS binds for it (the 20 re-pointed harness files have new bytes)
  changed / added / removed   an item of task R43-40 (each top-level key carries its reason)
The PROTECTED values (as in v3) must be unchanged, repointed or rebound only; the script exits 3 otherwise. It also lists
every string of v4 that still names an old identifier (frozen-r12, cand-r29, 3d5607d, a8aaced, the review42 harness folder,
r32-v3, declaration-r32-v3) with its JSON path; outside the record keys (supersedes, lineage, reviews, disclosures, ...) none
may remain (Verification 43 R43V-13: validate_declaration does not check trees). Writes DECLARATION-DIFF.json and
DECLARATION-DIFF.md (once each). Usage: diff_declaration_r42.py

ORCH-10 (R42PORT-IMPL): every difference between the frozen v2 declaration (f38fb281...25af) and the v3 declaration of
this package, mechanically. Both files are flattened to leaf paths (dicts recursed, lists compared whole). Each leaf is:
  unchanged            byte-equal value
  repointed            equal once the absent Desktop installation's path prefix is replaced by the merged one (nothing else)
  changed / added / removed   a correction of ORCH-10 (each top-level key carries its reason)
The PROTECTED values -- every number and rule the task says must not change (arms, switches, task kinds, run set, truth,
reference set, parent, lane allowances, window, thresholds, per-project limits "96" / "600" / "12" / "120", the gate,
resume_policy, stop rules, concentration results, the model pins) -- must be unchanged or repointed only; the script exits
3 otherwise. Writes DECLARATION-DIFF.json and DECLARATION-DIFF.md (once each). Usage: diff_declaration_r42.py"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import build_declaration_r42 as BD  # noqa: E402  (R43-40: the R43 re-point map)
import r42common as C  # noqa: E402

PROTECTED_KEYS = ("budget", "budget_detail", "project_window", "project_window_detail", "lane_switches", "lane_task_kinds", "lane_task_kinds_detail",
                  "application_env", "application_env_detail", "application_ai_limits", "decision_coverage_gate", "decision_coverage_gate_detail", "gates",
                  "resume_policy", "stop_rules", "estimated_usage", "token_thresholds", "elapsed_bounds", "cost", "controls", "cross_page_identity",
                  "concentration_on_proposal", "primary_outcomes", "thresholds_verbatim", "scope_limitations", "probe_population", "r_and_p", "retry_rule",
                  "unread_page_rule", "reference_set", "cohort", "evaluator", "emission_rules", "interpretations", "switch_names", "lanes",
                  "what_this_run_can_show", "reference_set_statement", "trees", "run_set_sha256", "policy", "plan_sources", "executed", "budget_approved",
                  "authorization_status", "standing_status")
PROTECTED_LEAVES = ("model_identity.models.small", "model_identity.models.standard", "model_identity.provider", "ledger.limits", "ledger.path",
                    "ledger.wrap_provider", "provider_env.AI_MAX_CALLS_PER_PROJECT_PER_DAY", "provider_env.AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY",
                    "provider_env.AI_MAX_CALLS_PER_DOCUMENT", "provider_env.AI_MAX_ELAPSED_S_PER_JOB", "provider_env.AI_LEDGER_LIMITS",
                    "provider_env.AI_MODEL_SMALL", "provider_env.AI_MODEL_STANDARD", "provider_env.AI_PROVIDER", "provider_env.AI_EFFORT",
                    "provider_env.AI_TIMEOUT_S", "provider_env.AI_CLI_TIMEOUT_S", "provider_env.AI_LEDGER_PATH", "model_identity.cli.version",
                    "run_set.truth", "run_set.labels_eval_input", "project_request_bounds_detail.EP-27331", "project_request_bounds_detail.all_projects_structural",
                    "project_request_bounds_detail.all_projects_planning", "project_request_bounds_detail.required_application_minimum",
                    "resume_detail.invocations_expected", "resume_detail.rule", "resume_detail.resume_invocations.EP-27331_full",
                    "resume_detail.resume_invocations.last_invocation_starts_after_s")
REASONS = {
    "schema": "the v4 schema id", "name": "names declaration v4 (R43 trees, review43 harness)", "task": "R43-40 (A-13 item 2), ep-implementer",
    "supersedes": "supersedes the executed v3 9a55fa7b...1b40 (its RUN file, authorization file and manifest named; the v3 binding R42 and the task-37 manifest named, superseded by the harness manifest f35355aa...); v3's own supersedes record kept as lineage",
    "declared_at_utc": "the time of this freeze", "status": "Verification 44 and the owner's conditional decision pending",
    "authorities": "A-13 applied and summarised; the authority register re-hashed at its current (append-only) state",
    "binding_manifest_sha256": "BINDING-MANIFEST-R43-HARNESS (review43, f35355aa...374a7) instead of BINDING-MANIFEST-R42 (section 0 item 2)",
    "run": "stamp r32-v4, folder C:/t/r2x/r42-sandbox/r32-v4 (same lengths as v3); the dry-base sentence (section 0 item 3)",
    "authorization": "pinned path, RUN file and scope of v4; invocation from review43 with its manifest (harness_copy, working_directory); runbook pointer (section 0 items 2, 3)",
    "provider_env": "AI_LEDGER_SCOPE = the v4 scope; every other value unchanged", "ledger": "the v4 scope name; path and limits unchanged",
    "ledger_detail": "the creation sentence names 484 / 18 / 0 (R43V-04)", "isolation": "the review43 harness folder (section 0 item 1)",
    "isolation_detail": "the lane checks of this package",
    "harness": "review43 (binding manifest, modules re-pointed and rebound, accepted by Verification 43); review42 added to the lineage; the re-point diff added to the contracts",
    "request_path_coverage": "the dynamic proof re-pointed to review43's test_global_provider_r42 junit and result",
    "reviews": "Verification 42 and 43 (with findings and package check), RUNBOOK-ADDENDUM-R42 and the review-43 report added",
    "provider": "owner-confirmable: the v4 scope", "resume_authorization": "the guard module re-pointed to review43 (rebound)",
    "interpreter_detail": "a sentence on the R43 trees added (requirements equal)",
    "disclosures": "the dry-exercise and isolation disclosures restated for review43; ten R43-40 disclosures added (v3 result, V4-01..V4-04, R43V-04/05/09/10, pip freeze)",
    "forbidden_after_authorization": "two items added (the executed v3 artifacts; any harness but review43)",
    "bound_files_rehashed": "the v4 re-hash record (v3 nodes; rebound harness nodes)",
    "owner_conditional_decision": "ADDED (section 2 item 6): A-13 item 3 verbatim, a precondition, not an authorization",
    "ledger_baseline": "ADDED (section 0 item 4, R43V-04): 484 / 18 / 0 at freeze",
    "preconditions": "ADDED (section 0 item 9): pip freeze (R42-09), ledger, conditional decision",
    "test_exceptions": "ADDED (section 0 item 5, R43V-05): the authorization-file test",
    "trees_r43": "ADDED (section 0 item 2, V4-05 corrected): commits, parents, patch-id",
    "verification43_items": "ADDED: the nine readiness items of Verification 43 check 8",
    "v4_preparation_items": "ADDED (section 0 item 9): V4-01..V4-05",
    "standing_status_at_v4_freeze": "ADDED: M4 CHANGES STILL REQUIRED, M3 accepted (standing_status carried unchanged as v3's record)",
}
OLD_IDS = re.compile(r"frozen-r12|cand-r29|3d5607d|a8aaced|review42/scripts/harness-r32|r32-v3|declaration-r32-v3")
RECORD_KEYS = ("supersedes", "harness.lineage", "harness.contracts", "harness.review39_snapshot_before", "harness.review39_work_records", "reviews",
               "disclosures", "forbidden_after_authorization", "authorities", "verification43_items", "verification40_items", "verification41_items",
               "trees_r43", "ledger_baseline", "test_exceptions", "bound_files_rehashed", "preconditions", "v4_preparation_items", "interpreter_detail",
               "portability", "request_path_coverage", "invocation_order", "owner_conditional_decision", "harness.package_check",
               "project_request_bounds_detail", "resume_detail", "run.base_justification", "isolation_detail", "dispatch_order", "model_identity_detail",
               "authorization.authorization_rule_v5", "authorization.placeholder_rule", "authorization.two_hash_procedure.independent_verification")


def flat(o, prefix=""):
    out = {}
    if isinstance(o, dict) and o:
        for k, v in o.items():
            out.update(flat(v, f"{prefix}.{k}" if prefix else k))
    else:
        out[prefix] = o
    return out


def repoint(v):
    return BD.repoint43(v)


def strings(o, path=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield from strings(v, f"{path}.{k}" if path else k)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            yield from strings(v, f"{path}[{i}]")
    elif isinstance(o, str):
        yield path, o


def main(argv=()) -> int:
    v4_path, out_dir = C.PACKAGE / C.DECLARATION_NAME, C.PACKAGE                 # dev mode: --v4 <file> --out <work dir>
    if "--v4" in argv:
        v4_path, out_dir = pathlib.Path(argv[argv.index("--v4") + 1]), pathlib.Path(argv[argv.index("--out") + 1])
    for f in ("DECLARATION-DIFF.json", "DECLARATION-DIFF.md"):
        if (out_dir / f).exists():
            raise SystemExit(f"refused: {f} is written once")
    old_b, new_b = BD.v3_bytes(), v4_path.read_bytes()
    old, new = json.loads(old_b), json.loads(new_b)
    bound = json.loads(C.BINDING43.read_text(encoding="utf-8"))["files"][C.HARNESS_GROUP]
    fo, fn = flat(old), flat(new)
    leaves = {"unchanged": [], "repointed": [], "rebound": [], "changed": [], "added": [], "removed": []}
    for k in sorted(set(fo) | set(fn)):
        if k not in fn:
            leaves["removed"].append(k)
        elif k not in fo:
            leaves["added"].append(k)
        elif fo[k] == fn[k]:
            leaves["unchanged"].append(k)
        elif repoint(fo[k]) == fn[k]:
            leaves["repointed"].append(k)
        elif k.endswith(".sha256") and fn.get(k[:-7] + ".path") in bound and bound[fn[k[:-7] + ".path"]] == fn[k] \
                and repoint(fo.get(k[:-7] + ".path")) == fn[k[:-7] + ".path"]:
            leaves["rebound"].append(k)
        else:
            leaves["changed"].append(k)
    tops = {}
    for k in sorted(set(old) | set(new)):
        mine = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
        rep = [x for cat in ("repointed", "rebound") for x in leaves[cat] if x == k or x.startswith(k + ".")]
        state = ("added" if k not in old else "removed" if k not in new else "changed" if mine else "repointed / rebound only" if rep else "unchanged")
        tops[k] = {"state": state, "reason": REASONS.get(k, "unchanged" if state == "unchanged" else
                                                         "only the R43 re-point (and the harness manifest's hashes)" if state.startswith("repointed") else "SEE LEAVES"),
                   "leaves_changed": sorted(mine), "leaves_repointed_or_rebound": len(rep)}
    prot = {}
    for k in PROTECTED_KEYS + PROTECTED_LEAVES:
        bad = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
        prot[k] = {"ok": not bad, "violations": bad}
    unexplained = [k for k, v in tops.items() if v["state"] in ("changed", "added", "removed") and k not in REASONS]
    counts = {s: sum(1 for v in tops.values() if v["state"] == s) for s in ("unchanged", "repointed / rebound only", "changed", "added", "removed")}
    olds = [(p, sorted(set(OLD_IDS.findall(s)))) for p, s in strings(new) if OLD_IDS.search(s)]
    outside = [(p, ids) for p, ids in olds if not any(p == r or p.startswith(r + ".") or p.startswith(r + "[") for r in RECORD_KEYS)]
    tt = {"trees": new["trees"], "lanes": {k: {x: v.get(x) for x in ("tree", "commit")} for k, v in new["lanes"].items()},
          "evaluator_file": new["evaluator"]["file"]}
    tt["ok"] = (new["trees"]["baseline"]["tree"] == C.BASELINE[0] and new["trees"]["baseline"]["head"] == C.BASELINE[1]
                and new["trees"]["candidate"]["tree"] == C.CANDIDATE[0] and new["trees"]["candidate"]["head"] == C.CANDIDATE[1]
                and all(v.get("tree") in (None, C.BASELINE[0], C.CANDIDATE[0]) for v in new["lanes"].values())
                and all(v.get("commit") in (None, C.BASELINE[1], C.CANDIDATE[1]) for v in new["lanes"].values())
                and new["evaluator"]["file"]["path"].startswith(C.CANDIDATE[0] + "/"))
    res = {"v3": {"path": (C.V3 / C.V3_NAME).as_posix(), "sha256": C.V3_SHA}, "v4": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(),
                                                                                    "sha256": C.sha256_bytes(new_b)},
           "method": (__doc__ or "").strip(), "top_level_counts": counts, "leaf_counts": {k: len(v) for k, v in leaves.items()},
           "top_level": tops, "leaves": leaves, "protected": prot, "protected_all_ok": all(v["ok"] for v in prot.values()),
           "unexplained_top_level_changes": unexplained,
           "old_identifiers_in_v4": {"count": len(olds), "in_record_keys": len(olds) - len(outside), "outside_record_keys": outside, "all": olds},
           "trees_text_check": tt}
    res["ok"] = res["protected_all_ok"] and not unexplained and not outside and tt["ok"]
    C.write_json_once(out_dir / "DECLARATION-DIFF.json", res)
    L = ["# DECLARATION-DIFF: v3 (`9a55fa7b...1b40`, executed 2026-10-07, terminal) -> v4 (this package)", "",
         f"- v4 sha256: `{res['v4']['sha256']}`.", "- Method: both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the R43 re-point: "
         "`frozen-r12`->`frozen-r13`, `cand-r29`->`cand-r30n`, `3d5607d...`->`7ec3d2cf...`, `a8aaced...`->`436daef2...`, `review42/scripts/harness-r32`->"
         "`review43/scripts/harness-r32`), rebound (the sha256 of a re-pointed review43 harness file, equal to the hash BINDING-MANIFEST-R43-HARNESS "
         "binds), changed, added or removed.", f"- Top-level keys: {counts}.", f"- Leaves: {res['leaf_counts']}.",
         f"- **Protected values (every number and rule that must not change): {'ALL UNCHANGED (or re-pointed / rebound only)' if res['protected_all_ok'] else 'VIOLATED'}** "
         f"({len(prot)} keys and leaves checked).",
         f"- Trees in text (R43V-13): {'frozen-r13 7ec3d2cf / cand-r30n 436daef2 in trees, lanes and evaluator' if tt['ok'] else 'NOT OK'}.",
         f"- Old identifiers left in v4: {len(olds)}, {len(olds) - len(outside)} inside record keys, {len(outside)} outside.", "",
         "## Top-level keys", "", "| Key | State | Reason |", "|---|---|---|"]
    for k, v in tops.items():
        L.append(f"| `{k}` | {v['state']} | {v['reason']} |")
    L += ["", "## Changed, added and removed leaves", ""]
    for cat in ("changed", "added", "removed"):
        L.append(f"### {cat} ({len(leaves[cat])})")
        L.append("")
        L += [f"- `{x}`" for x in leaves[cat]] or ["- none"]
        L.append("")
    L += [f"### repointed ({len(leaves['repointed'])}) and rebound ({len(leaves['rebound'])})", ""]
    L += [f"- `{x}` (rebound)" for x in leaves["rebound"]] + [f"- `{x}`" for x in leaves["repointed"]]
    L += ["", "## Old identifiers left in v4 (JSON path: identifiers)", ""]
    L += [f"- `{p}`: {', '.join(ids)}" for p, ids in olds] or ["- none"]
    C.write_once(out_dir / "DECLARATION-DIFF.md", "\n".join(L) + "\n")
    print(json.dumps({"ok": res["ok"], "top_level_counts": counts, "leaf_counts": res["leaf_counts"], "protected_all_ok": res["protected_all_ok"],
                      "violations": {k: v["violations"] for k, v in prot.items() if not v["ok"]}, "unexplained": unexplained,
                      "old_identifiers_outside_record_keys": outside, "trees_text_ok": tt["ok"]}, indent=1))
    return 0 if res["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
