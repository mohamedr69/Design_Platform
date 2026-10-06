"""ORCH-10 (R42PORT-IMPL): every difference between the frozen v2 declaration (f38fb281...25af) and the v3 declaration of
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
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
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
    "schema": "the v3 schema id", "contract": "contract 5 (review42 preflight_r32.CONTRACT 'r42-live-contract-5')", "name": "names declaration v3 (merged installation)",
    "task": "ORCH-10 / R42PORT-IMPL", "supersedes": "supersedes v2 f38fb281...25af (A-11; never to be run); v2's own supersedes record kept as lineage",
    "declared_at_utc": "the time of this freeze", "status": "Verification 42 and the owner's decision card pending",
    "authorities": "A-11 applied and summarised; the authority register re-hashed at its current (append-only) state",
    "binding_manifest_sha256": "BINDING-MANIFEST-R42 (review42) instead of R39",
    "run": "stamp r32-v3, base C:/t/r2x/r42-sandbox, folder C:/t/r2x/r42-sandbox/r32-v3 (same lengths as v2); the re-entry rule",
    "authorization": "pinned path beside v3; the RUN file v3; the scope v3; invocation from review42 with the bound interpreter; contract v5 section 3 cited; the multi-invocation file fields (A-11 section 4)",
    "model_identity": "the CLI pinned by ABSOLUTE PATH and file sha256 (contract 5); models, provider and version line unchanged",
    "model_identity_detail": "the CLI rule (file hash before anything, version before the folder); the bundled 2.1.289 named as not used",
    "provider_env": "AI_CLAUDE_CLI = the absolute CLI path; AI_LEDGER_SCOPE = the v3 scope; every other value unchanged",
    "ledger": "the v3 scope name; path and limits unchanged", "ledger_detail": "create_scope_r42.py; the C1 disk check",
    "project_request_bounds": "review42 PROJECT-REQUEST-BOUNDS.json (recomputed; equal to review39's in every verified key, the run-set path re-pointed)",
    "project_request_bounds_detail": "adds the equality record with review39", "resume_detail": "review42 RESUME-INVOCATIONS-R42.json (byte-identical to R39's)",
    "interpreter": "ADDED (contract 5): the bound interpreter", "interpreter_detail": "ADDED: requirements and import check of both trees",
    "disk_precondition": "ADDED (contract 5): 2 GiB on C:, only upward (R41-10, C1)", "disk_precondition_detail": "ADDED",
    "isolation": "ADDED (contract 5): the merged installation is forbidden except the venv and the review42 harness", "isolation_detail": "ADDED",
    "resume_authorization": "ADDED (contract 5; A-11 section 4): the separable multi-invocation proposal, max 3",
    "global_provider": "ADDED (contract 5; R40-04 option 2)", "request_path_coverage": "R40-04 closed by option 2: the refusing global provider; static and dynamic proof; v2's proof-based text kept as superseded",
    "invocation_order": "ADDED (R41-09, R41-10, R41-11): the reordered invocation, re-entry and the dead-end cases", "portability": "ADDED: the re-pointing and the path lengths",
    "harness": "review42 (manifest, binding, modules, contracts v5); review39 added to the lineage; the work records referenced in the v2 package",
    "revision_comparison_rule": "implementation re-bound to the review42 copy (same hash)", "run_set": "selector re-bound to the review42 copy (same hash)",
    "reviews": "Verification 41 (and its findings and package check) and RUNBOOK-ADDENDUM-R41 added", "dispatch_order": "the reordered invocation (contract v5 section 14)",
    "provider": "owner-confirmable: the v3 scope, the CLI pin, the disk floor, the resume authorization; AI_CLAUDE_CLI declared absolute",
    "verification40_items": "R40-04 now closed by option 2", "verification41_items": "ADDED: R41-09 to R41-15, R41-18, C1; the four r40 records bound by hash",
    "bound_files_rehashed": "ADDED: the build-time re-hash record", "disclosures": "R40-04, R40-08 (R41-12 correction), the CLI dead-end (R41-09 closed), path length, the dry exercise (R41-13) restated; nine ORCH-10 disclosures added",
    "forbidden_after_authorization": "four items added (v2, the merged installation's CLI / .env / data / code, run-folder records, the floor and the bound)",
}


def flat(o, prefix=""):
    out = {}
    if isinstance(o, dict) and o:
        for k, v in o.items():
            out.update(flat(v, f"{prefix}.{k}" if prefix else k))
    else:
        out[prefix] = o
    return out


def repoint(v):
    return json.loads(json.dumps(v).replace(C.DESKTOP_EP, C.MERGED_EP))


def main(argv=()) -> int:
    v3_path, out_dir = C.PACKAGE / C.DECLARATION_NAME, C.PACKAGE                 # dev mode: --v3 <file> --out <work dir>
    if "--v3" in argv:
        v3_path, out_dir = pathlib.Path(argv[argv.index("--v3") + 1]), pathlib.Path(argv[argv.index("--out") + 1])
    for f in ("DECLARATION-DIFF.json", "DECLARATION-DIFF.md"):
        if (out_dir / f).exists():
            raise SystemExit(f"refused: {f} is written once")
    old_b, new_b = (C.V2 / C.V2_NAME).read_bytes(), v3_path.read_bytes()
    if C.sha256_bytes(old_b) != C.V2_SHA:
        raise SystemExit("PACKET MISMATCH: v2")
    old, new = json.loads(old_b), json.loads(new_b)
    fo, fn = flat(old), flat(new)
    leaves = {"unchanged": [], "repointed": [], "changed": [], "added": [], "removed": []}
    for k in sorted(set(fo) | set(fn)):
        if k not in fn:
            leaves["removed"].append(k)
        elif k not in fo:
            leaves["added"].append(k)
        elif fo[k] == fn[k]:
            leaves["unchanged"].append(k)
        elif repoint(fo[k]) == fn[k]:
            leaves["repointed"].append(k)
        else:
            leaves["changed"].append(k)
    tops = {}
    for k in sorted(set(old) | set(new)):
        mine = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
        rep = [x for x in leaves["repointed"] if x == k or x.startswith(k + ".")]
        state = ("added" if k not in old else "removed" if k not in new else "changed" if mine else "repointed only" if rep else "unchanged")
        tops[k] = {"state": state, "reason": REASONS.get(k, "unchanged" if state == "unchanged" else
                                                         "only the Desktop paths re-pointed" if state == "repointed only" else "SEE LEAVES"),
                   "leaves_changed": sorted(mine), "leaves_repointed": len(rep)}
    prot = {}
    for k in PROTECTED_KEYS:
        bad = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
        prot[k] = {"ok": not bad, "violations": bad}
    for k in PROTECTED_LEAVES:
        bad = [x for cat in ("changed", "added", "removed") for x in leaves[cat] if x == k or x.startswith(k + ".")]
        prot[k] = {"ok": not bad, "violations": bad}
    unexplained = [k for k, v in tops.items() if v["state"] in ("changed", "added", "removed") and k not in REASONS]
    counts = {s: sum(1 for v in tops.values() if v["state"] == s) for s in ("unchanged", "repointed only", "changed", "added", "removed")}
    res = {"v2": {"path": (C.V2 / C.V2_NAME).as_posix(), "sha256": C.V2_SHA}, "v3": {"path": (C.PACKAGE / C.DECLARATION_NAME).as_posix(),
                                                                                    "sha256": C.sha256_bytes(new_b)},
           "method": (__doc__ or "").strip(), "top_level_counts": counts, "leaf_counts": {k: len(v) for k, v in leaves.items()},
           "top_level": tops, "leaves": leaves, "protected": prot, "protected_all_ok": all(v["ok"] for v in prot.values()),
           "unexplained_top_level_changes": unexplained, "desktop_prefix_left_in_v3": C.DESKTOP_EP in new_b.decode("utf-8")}
    res["ok"] = res["protected_all_ok"] and not unexplained and not res["desktop_prefix_left_in_v3"]
    C.write_json_once(out_dir / "DECLARATION-DIFF.json", res)
    L = ["# DECLARATION-DIFF: v2 (`f38fb281…25af`, frozen, superseded, never run) → v3 (this package)", "",
         f"- v3 sha256: `{res['v3']['sha256']}`.", "- Method: both files flattened to leaf paths; a leaf is unchanged, re-pointed (only the absent Desktop "
         "installation's prefix `C:/Users/moham/Desktop/dev/dev/ep-platform` replaced by `G:/dev (2)/dev/ep-platform-merged/ep-platform`), changed, added "
         "or removed.", f"- Top-level keys: {counts}.", f"- Leaves: {res['leaf_counts']}.",
         f"- **Protected values (every number and rule that must not change): {'ALL UNCHANGED (or re-pointed only)' if res['protected_all_ok'] else 'VIOLATED'}** "
         f"({len(prot)} keys and leaves checked: {', '.join(sorted(prot))}).", "", "## Top-level keys", "", "| Key | State | Reason |", "|---|---|---|"]
    for k, v in tops.items():
        L.append(f"| `{k}` | {v['state']} | {v['reason']} |")
    L += ["", "## Changed, added and removed leaves", ""]
    for cat in ("changed", "added", "removed"):
        L.append(f"### {cat} ({len(leaves[cat])})")
        L.append("")
        L += [f"- `{x}`" for x in leaves[cat]] or ["- none"]
        L.append("")
    C.write_once(out_dir / "DECLARATION-DIFF.md", "\n".join(L) + "\n")
    print(json.dumps({"ok": res["ok"], "top_level_counts": counts, "leaf_counts": res["leaf_counts"], "protected_all_ok": res["protected_all_ok"],
                      "violations": {k: v["violations"] for k, v in prot.items() if not v["ok"]}, "unexplained": unexplained}, indent=1))
    return 0 if res["ok"] else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
