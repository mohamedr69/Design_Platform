"""ORCH-09 (R40DECL-IMPL): every difference between the superseded declaration (38e08df9...76b0) and the corrected
declaration of this package, mechanically: both files are flattened to leaf paths (dicts recursed, lists compared whole),
every top-level key is classified (unchanged / changed / added / removed) with the reason it changed, and every changed,
added or removed leaf path is listed. Writes DECLARATION-DIFF.json and DECLARATION-DIFF.md (once each). Read-only otherwise.

Usage: diff_declaration_r40.py"""
from __future__ import annotations

import json
import sys

sys.dont_write_bytecode = True
import r40common as C  # noqa: E402

REASONS = {
    "schema": "new schema id for the corrected declaration",
    "contract": "ADDED: contract 4 (review39 preflight_r32.CONTRACT 'r39-live-contract-4'); the superseded file predates the key",
    "name": "names the corrected declaration v2",
    "task": "ORCH-09 / R40DECL-IMPL",
    "supersedes": "ADDED: names the superseded declaration and its manifest (A-09)",
    "declared_at_utc": "the time of this freeze",
    "status": "adds 'no run file' and 'Verification 41' to the not-authorized status",
    "authorities": "A-09 and A-10 applied and summarised; register hash 346597d3... (A-09 and A-10 present)",
    "binding_manifest_sha256": "bound harness review39 (BINDING-MANIFEST-R39 a6f703b4...) instead of review36 (5a1a6aad...)",
    "run": "contract 4: declared sandbox_base; base C:/t/r2x/r40-sandbox and stamp r32-v2 (short paths, justified); the superseded folder was under r34-sandbox",
    "authorization": "pinned path beside this declaration; two-hash procedure (R38-07) with the RUN file and who verifies the RUN hash; review39 contract section 3 carried verbatim; invocation from the review39 harness",
    "caps": "REMOVED: contract 4 names the lane allowances budget.lane_allowances (same values B 240 / C 240 / R 40 / P 36)",
    "caps_detail": "REMOVED: replaced by budget_detail",
    "budget": "ADDED: contract 4 parent budget {total 556, input 16,300,000, output 3,260,000, elapsed 604,800 s} and lane allowances (A-09 point 3)",
    "budget_detail": "ADDED: A-09 point 3 rule, enforcement, no borrowing, charges never refunded",
    "project_day_limit": "REMOVED: the UTC day limit 60 is replaced by the rolling project window (A-09 point 1)",
    "project_day_limit_detail": "REMOVED: replaced by project_window_detail (deferral, not a permanent refusal)",
    "project_window": "ADDED: contract 4 harness rolling window {limit 60, window_s 86,400}, all lanes",
    "project_window_detail": "ADDED: deferral rule, lane gating, what it replaces",
    "project_request_bounds": "ADDED: contract 4 binding of PROJECT-REQUEST-BOUNDS.json (99be01fb...)",
    "project_request_bounds_detail": "ADDED: EP-27331 planning 63.0 / structural 160 / 170 with the drawings path; required minimum 84",
    "resume_policy": "ADDED: contract 4 resume_policy 'full' (R39-08)",
    "resume_detail": "ADDED: RESUME-INVOCATIONS-R39 (9791fa89...) bound; 2 / 3 invocations under 'full'",
    "lane_switches": "unchanged",
    "lane_task_kinds": "ADDED: contract 4 task kinds per lane = task_kinds_for(lane_switches) (R39-04)",
    "lane_task_kinds_detail": "ADDED: explanation",
    "application_env": "ADDED: contract 4 exactly {DRAWINGS_AI_REVIEW_ENABLED: false} (R39-04)",
    "application_env_detail": "ADDED: explanation",
    "provider_env": "full model ids (A-09 point 2); new scope name; per-project limit 96 >= 84 (compatible limits); integer strings for every count and time limit (R40-08: '120', '1800', prices '0')",
    "application_ai_limits": "compatible limits with margins and justification; integer strings (R40-08); the 'silent stops' replaced by recorded unread pages",
    "model_identity": "ADDED: contract 4 pinned full ids, provider, CLI path and version line '2.1.263 (Claude Code)' (A-09 point 2, A-10)",
    "model_identity_detail": "ADDED: served-model identity UNRESOLVED, the runtime check fail-closed with its two limits, the CLI file hash, the probe pointer",
    "ledger": "new scope name m2-fresh-validation-r32-v2-2026-10-04; limits unchanged (equal to the parent, contract 4)",
    "ledger_detail": "creation by create_scope_r40.py (R38-11); two elapsed clocks; reconciliation before every resume",
    "decision_coverage_gate": "ADDED: contract 4 'C_GE_B_ONLY' (A-10): a change from plan v2",
    "decision_coverage_gate_detail": "ADDED: the bound text, the change from plan v2, the plan v2 definition, the mandatory diagnostic, contract v4 section 12 verbatim",
    "lanes": "task kinds per lane; B's drawings-AI review off; R no credit and never eligibility (A-09 point 7, A-10); P's population drawn at its first run (R40-12)",
    "switch_names": "unchanged",
    "dispatch_order": "owner steps before invocation 1; CLI version and nonce consumption; lane gating on deferral; frozen P sample; DEFERRED / resume",
    "probe_population": "ADDED: R40-12",
    "r_and_p": "ADDED: A-09 point 7 (no credit; diagnostic INCOMPLETE)",
    "retry_rule": "ADDED: R40-13 -- the failed-read retry named as a change from plan v2 section 4",
    "unread_page_rule": "ADDED: R39-06 rule, the no_trigger exclusion and two unguarded corners (R40-10), the R40-15 acknowledgement",
    "request_path_coverage": "ADDED: R40-04 -- the corrected claim, the proof bound by hash, the residual risk, the owner's two options",
    "cross_page_identity": "ADDED: rule CP-R38 (A-09 point 5)",
    "scope_limitations": "ADDED: the shortfall as a declared scope limitation and what is not claimed (A-09 point 6)",
    "controls": "the shortfall entry gains its A-09 point 6 statement",
    "estimated_usage": "structural maxima and per-project figures from PROJECT-REQUEST-BOUNDS replace the superseded 'conservative' 8-per-document maxima (R38-08); tokens at the structural maximum",
    "token_thresholds": "enforcement restated (the allowance also enforces the parent token bounds); breaker margins (R38-13)",
    "elapsed_bounds": "two clocks (allowance and scope); waiting times under 'full'",
    "cost": "unchanged",
    "provider": "owner-confirmable fields restated for full ids, the CLI pin, the scope name and the per-project limit; owner_confirmable 'project_day_limit' removed",
    "stop_rules": "review39 contract v4 sections 4, 5, 6 and 13 verbatim REPLACE the review34 resume rules (R40-13); terminal states INCOMPLETE / DEFERRED / INVALID / CLOSED / RESULT / FINISHED; the stop-and-safety table unchanged",
    "harness": "review39 (manifest 2430fa2b..., binding a6f703b4..., 239 bound files) replaces review36; modules and contracts re-bound; lineage; review39 SNAPSHOT-BEFORE 09:55:49Z (R40-19); work records bound (R40-20)",
    "evaluator": "judging statement names the review39 lane_judge (rule CP-R38)",
    "trees": "adds config.py of the baseline, the application ledger.py and provider.py hashes",
    "run_set": "selector re-bound to the review39 copy (ec5025d2..., its selection code unchanged since review36; the replacement refusal appended in review38); frozen_by restated",
    "reference_set": "unchanged",
    "cohort": "unchanged",
    "reviews": "Verifications 38, 39 and 40 added",
    "policy": "unchanged",
    "plan_sources": "unchanged",
    "revision_comparison_rule": "implementation re-bound to the review39 copy of literal_compare_r32.py (same hash c23ba577...)",
    "emission_rules": "unchanged",
    "interpretations": "the .10-parity cross-page items and the H4 gap are superseded by rule CP-R38 (A-09 point 5)",
    "concentration_on_proposal": "ADDED: the superseded package's concentration results carried by hash (module and run set unchanged)",
    "primary_outcomes": "unchanged",
    "thresholds_verbatim": "unchanged (re-verified verbatim at build time)",
    "gates": "decision_coverage CHANGED to C >= B only (A-10; a change from plan v2); comparison_state (A-09 point 1) and other_gates added; every other gate verbatim",
    "verification40_items": "ADDED: where each Verification 40 item is answered",
    "disclosures": "stale items replaced (day limit, silent stops, H4, H5, the twin); new disclosures for R40-04/08/10/12/13, the CLI-version dead-end, identity UNRESOLVED, tokens at the structural maximum, path length, the dry exercise",
    "forbidden_after_authorization": "four items added (the frozen hash never with the runner; the scope once; the probe outside the harness; no direct lane)",
    "what_this_run_can_show": "unchanged",
    "reference_set_statement": "unchanged",
    "standing_status": "unchanged",
    "executed": "unchanged",
    "budget_approved": "unchanged",
    "authorization_status": "unchanged",
    "run_set_sha256": "unchanged",
}


def flatten(obj, prefix=""):
    out = {}
    if isinstance(obj, dict):
        if not obj:
            out[prefix or "."] = {}
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    else:
        out[prefix] = obj
    return out


def short(v, n=150):
    s = json.dumps(v, ensure_ascii=False, sort_keys=True)
    return s if len(s) <= n else s[: n - 3] + "..."


def main() -> int:
    old_path, new_path = C.SUPERSEDED / "FRESH-VALIDATION-DECLARATION-R32.json", C.PACKAGE / C.DECLARATION_NAME
    old_sha, new_sha = C.sha256_file(old_path), C.sha256_file(new_path)
    if old_sha != C.SUPERSEDED_SHA:
        raise C.PacketMismatch("PACKET MISMATCH: the superseded declaration")
    old, new = json.loads(old_path.read_text(encoding="utf-8")), json.loads(new_path.read_text(encoding="utf-8"))
    fo, fn = flatten(old), flatten(new)
    keys = sorted(set(old) | set(new))
    top = {}
    for k in keys:
        ko = {p: v for p, v in fo.items() if p == k or p.startswith(k + ".")}
        kn = {p: v for p, v in fn.items() if p == k or p.startswith(k + ".")}
        added = sorted(set(kn) - set(ko))
        removed = sorted(set(ko) - set(kn))
        changed = sorted(p for p in set(ko) & set(kn) if ko[p] != kn[p])
        status = "added" if k not in old else "removed" if k not in new else ("unchanged" if not (added or removed or changed) else "changed")
        reason = REASONS.get(k)
        if reason is None:
            raise SystemExit(f"no reason recorded for top-level key {k!r}")
        top[k] = {"status": status, "reason": reason, "added": [{"path": p, "new": fn[p]} for p in added],
                  "removed": [{"path": p, "old": fo[p]} for p in removed], "changed": [{"path": p, "old": fo[p], "new": fn[p]} for p in changed]}
        if status == "unchanged" and not reason.startswith("unchanged"):
            raise SystemExit(f"{k}: unchanged but the reason says {reason!r}")
        if status != "unchanged" and reason.startswith("unchanged"):
            raise SystemExit(f"{k}: {status} but the reason says unchanged")
    counts = {s: sum(1 for v in top.values() if v["status"] == s) for s in ("unchanged", "changed", "added", "removed")}
    leaf = {"added": sum(len(v["added"]) for v in top.values()), "removed": sum(len(v["removed"]) for v in top.values()),
            "changed": sum(len(v["changed"]) for v in top.values())}
    res = {"name": "DECLARATION-DIFF (ORCH-09): every difference from the superseded declaration", "superseded": {"path": old_path.as_posix(), "sha256": old_sha},
           "corrected": {"path": new_path.as_posix(), "sha256": new_sha}, "method": __doc__.split("\n\n")[0].replace("\n", " "),
           "top_level_counts": counts, "leaf_counts": leaf, "top_level": top}
    C.write_json_once(C.PACKAGE / "DECLARATION-DIFF.json", res)
    lines = ["# Declaration diff: superseded `38e08df9…76b0` → corrected `" + new_sha[:8] + "…" + new_sha[-4:] + "`", "",
             f"- **Superseded:** `{old_path.as_posix()}` sha256 `{old_sha}` (A-09: never authorized, never run, never to be run).",
             f"- **Corrected:** `{new_path.as_posix()}` sha256 `{new_sha}`.",
             "- **Method:** both files are flattened to leaf paths (objects recursed, lists compared whole). Every top-level key is listed with its status "
             "and the reason; every added, removed or changed leaf path is listed below it. The machine-readable version, with full values, is "
             "`DECLARATION-DIFF.json` (written by `scripts/diff_declaration_r40.py`).",
             f"- **Top-level keys:** {counts['unchanged']} unchanged, {counts['changed']} changed, {counts['added']} added, {counts['removed']} removed.",
             f"- **Leaf paths:** {leaf['changed']} changed, {leaf['added']} added, {leaf['removed']} removed.",
             "- **Reference set:** reference set independently AI-reviewed (Claude agents), not human-signed.", "",
             "## 1. Top-level keys", "", "| Key | Status | Why |", "|---|---|---|"]
    for k in keys:
        lines.append(f"| `{k}` | {top[k]['status']} | {top[k]['reason']} |")
    lines += ["", "## 2. Every changed, added or removed leaf path", ""]
    for k in keys:
        t = top[k]
        if t["status"] == "unchanged":
            continue
        lines += [f"### `{k}` ({t['status']})", ""]
        for e in t["changed"]:
            lines.append(f"- changed `{e['path']}`: {short(e['old'])} → {short(e['new'])}")
        for e in t["added"]:
            lines.append(f"- added `{e['path']}`: {short(e['new'])}")
        for e in t["removed"]:
            lines.append(f"- removed `{e['path']}`: {short(e['old'])}")
        lines.append("")
    C.write_once(C.PACKAGE / "DECLARATION-DIFF.md", "\n".join(lines).rstrip() + "\n")
    print(json.dumps({"top_level_counts": counts, "leaf_counts": leaf}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
