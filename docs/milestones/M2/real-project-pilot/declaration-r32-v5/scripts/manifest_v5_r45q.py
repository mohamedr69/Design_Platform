"""R43-44 (new): the binding manifest of the v5 declaration package, in the R42 / R43 form (the same 25 fields as
BINDING-MANIFEST-R45-HARNESS, sorted keys), written ONCE and LAST, and its self-check (the method of tasks 37 / 38 / R43-40:
every bound entry and every binds hash re-hashed, the field set, the log prefix, the statement, the supersedes hash, the package's
unbound files; plus preflight_r32.verify_binding on THIS manifest and validate_declaration on the frozen file and an in-memory copy).
Usage: manifest_v5_r45q.py manifest --log-lines N      -> BINDING-MANIFEST-R32-V5.json (refuses if it exists)
       manifest_v5_r45q.py selfcheck <n>               -> SELF-CHECK-<n>.json (read-only apart from that file)
Bound: everything in this package except the manifest itself and SELF-CHECK-*.json (written after it); IMPLEMENTATION-REPORT.md
is written BEFORE the manifest and bound by it (the v4 ordering gap fixed); plus the chain (the review45 harness manifest, the
superseded v4 declaration and its manifest, the executed v3 declaration and its record files, Verifications 43, 44 and 45,
RUNBOOK-ADDENDUM-R42) and the R43 session log prefix (lines 1..N). It authorizes nothing."""
from __future__ import annotations

import copy
import datetime
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

NAME = "BINDING-MANIFEST-R32-V5.json"
LOG = C.EP / "docs/R43-SESSION-LOG.md"
REV = {"verification43": C.MR / "reviews/M2-review-43-harness", "verification44": C.MR / "reviews/M2-review-44",
       "verification45": C.MR / "reviews/M2-review-45"}
REV_FILES = (("verification", "INDEPENDENT-VERIFICATION.md"), ("findings", "FINDINGS.json"), ("package_check", "INDEPENDENT-PACKAGE-CHECK.json"))
DOCS = (("declaration", C.DECLARATION_NAME), ("declaration_sha256_file", "DECLARATION.sha256"), ("declaration_diff_json", "DECLARATION-DIFF-V4-V5.json"),
        ("declaration_diff_md", "DECLARATION-DIFF-V4-V5.md"), ("v5_build_diff", "V5-BUILD-DIFF.md"), ("runbook", "RUNBOOK-R32-V5.md"),
        ("scope_creation_command", "SCOPE-CREATION-COMMAND.md"), ("summary", "SUMMARY-R32-V5.md"), ("budget_card", "BUDGET-CARD-V6.md"),
        ("implementation_report", "IMPLEMENTATION-REPORT.md"))
REHEARSAL = (("preflight_steps_1_7", "dry-run/PREFLIGHT-RESULTS.json"), ("dry_exercise_single", "dry-run/DRY-EXERCISE.json"),
             ("demos", "rehearsal/demos/DEMOS-R42.json"), ("drill_v5_report", "evidence/drill-v5/out/DRILL-REPORT.json"),
             ("drill_v5_run", "evidence/drill-v5/DRILL-RUN-V5.json"), ("drill_v5_compare", "evidence/drill-v5/DRILL-COMPARE-V5.json"))
FIELDS = ["answers", "baseline", "binds", "candidate", "changed_from_review39", "cli_pin", "contract", "files", "global_provider", "harness_files",
          "immutable", "interpreter", "name", "new_in_review42", "not_bound_but_recorded", "r39_rehash", "reference_set", "reference_set_statement",
          "run_set_sha256", "sandbox_base", "statement", "supersedes", "truth_sha256", "unchanged_from_review39", "written_at_utc"]
STATEMENT = ("binds code and inputs only; it authorizes nothing (no run, budget, scope, token, nonce, RUN or authorization file, no default); it is "
             "not signed and not bound to a nonce; M4 (historical M2) CHANGES STILL REQUIRED; M3 accepted (7 October 2026); the declaration v5 "
             "bound here is FROZEN and NOT AUTHORIZED; declaration v4 is untouched, frozen, never authorized and superseded; the review45 drill "
             "reproduced on v5's bindings is dry (0 model requests) and PASS against DRILL-CRITERION.md 8b183053...d918; the AI-on form reading "
             "of F009 and F020 is not rehearsed (R45-08); a run needs Verification 46, the owner's option-1 entry and a fresh D1/D2 naming the "
             "v5 hash (owner_decision_required)")


def log_prefix(n: int) -> dict:
    lines = LOG.read_bytes().split(b"\n")
    if len(lines) - 1 < n:
        raise SystemExit(f"refused: the log has fewer than {n} lines")
    data = b"\n".join(lines[:n]) + b"\n"
    return {"lines": f"1-{n}", "path": LOG.as_posix(), "rule": "sha256 of lines 1..N with their LF terminators; later rows are appended, never edited",
            "sha256": hashlib.sha256(data).hexdigest()}


def pkg_files() -> dict:
    out = {}
    for p in sorted(C.PACKAGE.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts:
            rel = p.relative_to(C.PACKAGE).as_posix()
            if rel == NAME or rel.startswith("SELF-CHECK-"):
                continue
            out[rel] = p
    return out


def group(paths) -> dict:
    return {pathlib.Path(p).as_posix(): C.sha256_file(p) for p in paths}


def harness():
    C.check_run_copy()
    if str(C.HARNESS42) not in sys.path:
        sys.path.insert(0, str(C.HARNESS42))
    import preflight_r32 as PF  # noqa: E402
    C.declared_here(PF)
    return PF


def build(n: int) -> dict:
    h = json.loads(C.BINDING45.read_text(encoding="utf-8"))
    if C.sha256_file(C.BINDING45) != C.BINDING45_SHA:
        raise SystemExit("PACKET MISMATCH: harness manifest")
    pf = pkg_files()
    if "IMPLEMENTATION-REPORT.md" not in pf:
        raise SystemExit("refused: IMPLEMENTATION-REPORT.md is written before the manifest and bound by it")
    top = [r for r in pf if "/" not in r]
    files = {
        "declaration_r32_v5": group(pf[r] for r in top),
        "v5_build_scripts": group(pf[r] for r in pf if r.startswith("scripts/")),
        "v5_rehearsal": group(pf[r] for r in pf if r.startswith(("dry-run/", "rehearsal/"))),
        "v5_evidence": group(pf[r] for r in pf if r.startswith("evidence/")),
        "chain_r45_harness": group([C.BINDING45, C.REVIEW45 / "DRILL-CRITERION.md", C.REVIEW45 / "DISCLOSURE-AMENDMENT-DRAFT.md"]),
        "chain_v4": group([C.V4 / C.V4_NAME, C.V4 / "DECLARATION.sha256", C.V4 / "BINDING-MANIFEST-R32-V4.json", C.V4 / "DECLARATION-DIFF.json",
                           C.V4 / "DECLARATION-DIFF.md", C.V4 / "V4-BUILD-DIFF.md", C.V4 / "IMPLEMENTATION-REPORT.md"]),
        "chain_v3": group([C.V3 / C.V3_NAME, C.V3 / "DECLARATION.sha256", C.V3 / "FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json", C.V3 / C.AUTH_NAME,
                           C.V3 / "evidence/EVIDENCE-MANIFEST.json", C.V3 / "RUNBOOK.md", C.V3 / "SCOPE-CREATION-COMMAND.md",
                           C.V3 / "DECLARATION-SUMMARY.md", C.V3 / "BUDGET-DECISION-CARD.v5.md"]),
        "verifications_43_44_45": group([REV[k] / f for k in REV for _n, f in REV_FILES]),
        "runbook_addendum_r42": group([C.MR / "orchestrator/RUNBOOK-ADDENDUM-R42.md"]),
    }
    bad = [p for fs in h["files"].values() for p, w in fs.items() if not pathlib.Path(p).is_file() or C.sha256_file(p) != w]
    snaps = {k: json.loads((C.PACKAGE / f"evidence/SNAPSHOT-{k}.json").read_text(encoding="utf-8")) for k in ("BEFORE", "AFTER")}
    git = {}
    for side, (repo, head) in (("baseline", C.BASELINE), ("candidate", C.CANDIDATE)):
        g = C.git_state(repo)
        git[side] = {"clean": g["clean"], "expected": head, "head": g["head"], "tree": repo}
    keep = ("ai_ledger", "v3_scope_present", "v4_scope_present", "v5_scope_present", "v4_run_folder_exists", "v5_run_folder_exists", "c_free_bytes")
    man = {
        "answers": ("Owner task R43-44 (A-13 item 2; Verification 44 option 1; Verification 45 section 5 item 2; card "
                    "orchestrator/tasks/R43-44-TASK.md 1cd72eb3...): declaration v5 of the R32 fresh validation = v4 rebound to the review45 "
                    "harness with the corrected disclosures (R45-06, R45-07, R45-08), a new stamp / folder / scope, A-13 item 3 as history and "
                    "owner_decision_required; its build scripts (the v4 scripts copied byte-identically and changed only where V5-BUILD-DIFF.md "
                    "lists), the v4 -> v5 leaf diff, the no-request preflight (steps 1-7), the single dry run, the 8 demonstrations, the review45 "
                    "drill reproduced on v5's bindings, the R44-07 documents (runbook, scope-creation command, summary, budget card) and the "
                    "implementation report, chained to BINDING-MANIFEST-R45-HARNESS (Verification 45), the superseded v4 and the executed v3"),
        "baseline": git["baseline"], "candidate": git["candidate"],
        "binds": {
            "declaration_r32_v5": {k: C.sha256_file(C.PACKAGE / f) for k, f in DOCS} | {"status": "frozen, NOT authorized"},
            "harness_r45": {"manifest": C.BINDING45_SHA, "entries": sum(len(v) for v in h["files"].values()),
                            "drill_criterion": C.sha256_file(C.REVIEW45 / "DRILL-CRITERION.md")},
            "declaration_r32_v4": {"declaration": C.V4_SHA, "manifest": C.V4_MANIFEST_SHA, "status": "frozen, never authorized, never run; superseded by v5"},
            "declaration_r32_v3": {"declaration": C.V3_SHA, "manifest": C.V3_MANIFEST_SHA, "run_declaration": C.V3_RUN_SHA, "authorization_file": C.V3_AUTH_SHA},
            **{k: {n: C.sha256_file(REV[k] / f) for n, f in REV_FILES} for k in REV},
            "rehearsal": {k: C.sha256_file(C.PACKAGE / f) for k, f in REHEARSAL},
            "r43_session_log_prefix": log_prefix(n)},
        "changed_from_review39": h["changed_from_review39"], "cli_pin": h["cli_pin"], "contract": h["contract"], "files": files,
        "global_provider": h["global_provider"], "harness_files": h["harness_files"],
        "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
        "interpreter": h["interpreter"],
        "name": ("R32 v5 declaration binding manifest: the frozen declaration v5 (not authorized), its build scripts, diffs, R44-07 documents, "
                 "implementation report and the dry rehearsal and drill evidence, chained to the review45 harness manifest, the superseded v4 "
                 "and the executed v3 (declaration-r32-v5)"),
        "new_in_review42": h["new_in_review42"],
        "not_bound_but_recorded": {
            "authority_register": {"path": (C.MR / "orchestrator/AUTHORITY-REGISTER.md").as_posix(), "sha256_at_binding": C.sha256_file(C.MR / "orchestrator/AUTHORITY-REGISTER.md"),
                                   "why": "append-only, updated by the orchestrator"},
            "task_file": {"path": C.TASK_FILE.as_posix(), "sha256_at_binding": C.sha256_file(C.TASK_FILE)},
            "carried_fields": ("baseline and candidate re-read now; changed_from_review39, cli_pin, contract, global_provider, harness_files, interpreter, "
                               "new_in_review42, reference_set, reference_set_statement, run_set_sha256, truth_sha256 and unchanged_from_review39 are "
                               "carried from BINDING-MANIFEST-R45-HARNESS (the harness is unchanged); r39_rehash is that manifest's every entry re-hashed now"),
            "protected_state": {k: {x: v.get(x) for x in keep} | {"pip_freeze": v["pip_freeze"]["sha256"],
                                                                  "folders": {f: y.get("sha256") for f, y in v["folders"].items()},
                                                                  "v3_run_folder_stat": v["v3_run_folder_stat"].get("stat_sha256"),
                                                                  "named_files": v["authorization_run_token_named_files"]} for k, v in snaps.items()},
            "protected_state_unchanged": {"ai_ledger": snaps["BEFORE"]["ai_ledger"] == snaps["AFTER"]["ai_ledger"],
                                          "pip_freeze": snaps["BEFORE"]["pip_freeze"]["sha256"] == snaps["AFTER"]["pip_freeze"]["sha256"],
                                          "folders": snaps["BEFORE"]["folders"] == snaps["AFTER"]["folders"],
                                          "v3_run_folder_stat": snaps["BEFORE"]["v3_run_folder_stat"] == snaps["AFTER"]["v3_run_folder_stat"],
                                          "trees": snaps["BEFORE"]["trees"] == snaps["AFTER"]["trees"],
                                          "named_files": snaps["BEFORE"]["authorization_run_token_named_files"] == snaps["AFTER"]["authorization_run_token_named_files"]},
            "written_after_this_manifest": ["SELF-CHECK-<n>.json"],
            "work_folder": {"path": C.WORK.as_posix(), "rule": "every file this task created outside the package lies under it (run copies, dry, demonstration and drill folders, logs, work helpers)"},
            "substitutions": "V5-BUILD-DIFF.md section 4 (S-RUN, S-HERE, S-BASE, S-GUARD, S-ENV, S-R45Q-1) and evidence/drill-v5/RUN-COPY-AND-SUBSTITUTIONS.json"},
        "r39_rehash": {"rule": "every file binding of BINDING-MANIFEST-R45-HARNESS re-hashed at its path when this manifest was written",
                       "equal": sum(len(v) for v in h["files"].values()) - len(bad), "differ": bad, "missing": [p for p in bad if not pathlib.Path(p).is_file()]},
        "reference_set": h["reference_set"], "reference_set_statement": h["reference_set_statement"], "run_set_sha256": h["run_set_sha256"],
        "sandbox_base": ("declared by the declaration (run.sandbox_base C:/t/r2x/r42-sandbox, run.folder C:/t/r2x/r42-sandbox/r32-v5, never created "
                         "here); this task's dry base C:/t/r2x/r42-sandbox/r45q/sb"),
        "statement": STATEMENT,
        "supersedes": {"file": (C.V4 / "BINDING-MANIFEST-R32-V4.json").as_posix(), "sha256": C.V4_MANIFEST_SHA,
                       "for": "the declaration package of the R32 fresh validation (v4 frozen, never authorized, never run; v5 is its successor, not authorized)"},
        "truth_sha256": h["truth_sha256"], "unchanged_from_review39": h["unchanged_from_review39"],
        "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    assert sorted(man) == FIELDS and len(man) == 25
    return man


def selfcheck(n: str) -> int:
    out = C.PACKAGE / f"SELF-CHECK-{n}.json"
    if out.exists():
        raise SystemExit(f"refused: {out.name} exists")
    mp = C.PACKAGE / NAME
    msha = C.sha256_file(mp)
    man = json.loads(mp.read_text(encoding="utf-8"))
    checks, fails = [], []

    def ck(name, ok, detail=None):
        checks.append(name)
        if not ok:
            fails.append({"check": name, "detail": detail})
    ck("fields: 25 in the R42/R43 set", sorted(man) == FIELDS and len(man) == 25, sorted(man))
    ck("fields: equal to the harness manifest's", sorted(man) == sorted(json.loads(C.BINDING45.read_text(encoding="utf-8"))))
    entries = [(g, p, w) for g, fs in man["files"].items() for p, w in fs.items()]
    for g, p, w in entries:
        ok = pathlib.Path(p).is_file() and C.sha256_file(p) == w
        ck(f"file {g}: {p}", ok, None if ok else ("missing" if not pathlib.Path(p).is_file() else C.sha256_file(p)))
    b = man["binds"]
    for k, f in DOCS:
        ck(f"binds declaration_r32_v5.{k}", C.sha256_file(C.PACKAGE / f) == b["declaration_r32_v5"][k])
    ck("binds DECLARATION.sha256 names the declaration", (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0] == b["declaration_r32_v5"]["declaration"])
    decl_bytes = (C.PACKAGE / C.DECLARATION_NAME).read_bytes()
    decl = json.loads(decl_bytes.decode("utf-8"))
    ck("declaration binds the harness manifest", decl["binding_manifest_sha256"] == b["harness_r45"]["manifest"] == C.sha256_file(C.BINDING45) == C.BINDING45_SHA)
    ck("declaration not executed, not approved", decl["executed"] is False and decl["budget_approved"] is False)
    ck("declaration supersedes v4", decl["supersedes"]["declaration"]["sha256"] == C.V4_SHA == C.sha256_file(C.V4 / C.V4_NAME))
    ck("binds declaration_r32_v4", C.sha256_file(C.V4 / C.V4_NAME) == b["declaration_r32_v4"]["declaration"]
       and C.sha256_file(C.V4 / "BINDING-MANIFEST-R32-V4.json") == b["declaration_r32_v4"]["manifest"])
    v3 = b["declaration_r32_v3"]
    for k, f in (("declaration", C.V3_NAME), ("manifest", "evidence/EVIDENCE-MANIFEST.json"), ("run_declaration", "FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json"),
                 ("authorization_file", C.AUTH_NAME)):
        ck(f"binds declaration_r32_v3.{k}", C.sha256_file(C.V3 / f) == v3[k])
    for k in REV:
        for nm, f in REV_FILES:
            ck(f"binds {k}.{nm}", C.sha256_file(REV[k] / f) == b[k][nm])
    for k, f in REHEARSAL:
        ck(f"binds rehearsal.{k}", C.sha256_file(C.PACKAGE / f) == b["rehearsal"][k])
    lp = b["r43_session_log_prefix"]
    nlines = int(lp["lines"].split("-")[1])
    ck("binds r43_session_log_prefix", log_prefix(nlines)["sha256"] == lp["sha256"])
    h = json.loads(C.BINDING45.read_text(encoding="utf-8"))
    hbad = [p for fs in h["files"].values() for p, w in fs.items() if not pathlib.Path(p).is_file() or C.sha256_file(p) != w]
    ck("harness manifest: every entry re-hashes equal now", not hbad, hbad[:5])
    ck("r39_rehash recorded 0 differ", not man["r39_rehash"]["differ"] and not man["r39_rehash"]["missing"])
    ck("supersedes hash", C.sha256_file(man["supersedes"]["file"]) == man["supersedes"]["sha256"] == C.V4_MANIFEST_SHA)
    ck("statement: authorizes nothing", "it authorizes nothing" in man["statement"])
    ck("statement: M4 CHANGES STILL REQUIRED; M3 accepted", "M4 (historical M2) CHANGES STILL REQUIRED" in man["statement"] and "M3 accepted" in man["statement"])
    bound = {p for fs in man["files"].values() for p in fs}
    unbound = sorted(rel for rel, p in pkg_files().items() if p.as_posix() not in bound)
    ck("package: every file bound (except the manifest and the self-checks), the implementation report included", not unbound
       and (C.PACKAGE / "IMPLEMENTATION-REPORT.md").as_posix() in bound, unbound)
    ck("package: no RUN or authorization file in v5", not (C.PACKAGE / C.RUN_NAME).exists() and not (C.PACKAGE / C.AUTH_NAME).exists())
    ck("v5 and v4 run folders absent", not C.RUN_FOLDER.exists() and not C.V4_RUN_FOLDER.exists())
    led = C.ledger_state()
    ck("AI ledger 484 / 18 / 0, no v4 or v5 scope", {k: led[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and C.SCOPE not in led["scope_names"]
       and C.V4_SCOPE not in led["scope_names"])
    PF = harness()
    try:
        vb = PF.verify_binding(mp, msha)
        ck("preflight_r32.verify_binding on THIS manifest", vb["files_verified"] == len(entries), vb)
    except PF.Refused as exc:
        ck("preflight_r32.verify_binding on THIS manifest", False, str(exc))
    try:
        PF.validate_declaration(decl, C.PACKAGE / C.DECLARATION_NAME)
        ck("validate_declaration: the file as written is refused", False, "accepted")
    except PF.Refused as exc:
        ck("validate_declaration: the file as written is refused", "binds no owner token digest" in str(exc), str(exc))
    mem = copy.deepcopy(decl)
    mem["authorization"]["owner_token_sha256"] = C.DUMMY_DIGEST
    try:
        PF.validate_declaration(mem, C.PACKAGE / C.DECLARATION_NAME)
        ck("validate_declaration: an in-memory copy with a dummy digest passes", True)
    except PF.Refused as exc:
        ck("validate_declaration: an in-memory copy with a dummy digest passes", False, str(exc))
    res = {"manifest": {"path": mp.as_posix(), "sha256": msha}, "checks": len(checks), "failures": fails,
           "entries": len(entries), "unique_paths": len({p for _g, p, _w in entries}),
           "taken_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "log_lines_now": len(LOG.read_bytes().split(b"\n")) - 1}
    C.write_json_once(out, res)
    print(json.dumps({"manifest_sha256": msha, "checks": len(checks), "failures": len(fails), "entries": len(entries),
                      "failed": [f["check"] for f in fails][:10]}))
    return 0 if not fails else 1


def main(argv) -> int:
    if argv[0] == "manifest":
        n = int(argv[argv.index("--log-lines") + 1])
        if (C.PACKAGE / NAME).exists():
            raise SystemExit("refused: the manifest is written once")
        sha = C.write_json_once(C.PACKAGE / NAME, build(n))
        print(json.dumps({"manifest": (C.PACKAGE / NAME).as_posix(), "sha256": sha}))
        return 0
    if argv[0] == "selfcheck":
        return selfcheck(argv[1])
    raise SystemExit("usage: manifest --log-lines N | selfcheck <n>")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
