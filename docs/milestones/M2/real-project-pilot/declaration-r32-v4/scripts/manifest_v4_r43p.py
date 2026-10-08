"""R43-40 (new): the binding manifest of the v4 declaration package, in the R42 / R43 form (the same 25 fields as
BINDING-MANIFEST-R43-HARNESS, sorted keys), written ONCE and LAST, and its self-check (the method of tasks 37 / 38: every bound
entry and every binds hash re-hashed, the field set, the log prefix, the statement, the supersedes hash, the package's unbound
files).
Usage: manifest_v4_r43p.py manifest --log-lines N      -> BINDING-MANIFEST-R32-V4.json (refuses if it exists)
       manifest_v4_r43p.py selfcheck <n>               -> SELF-CHECK-<n>.json (read-only apart from that file)
Bound: everything in this package except the manifest itself, IMPLEMENTATION-REPORT.md and SELF-CHECK-*.json (written after the
manifest), plus the chain (the review43 harness manifest, the executed v3 declaration and its record files, Verification 43, the
v4 preparation inputs, RUNBOOK-ADDENDUM-R42) and the R43 session log prefix (lines 1..N). It authorizes nothing."""
from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

NAME = "BINDING-MANIFEST-R32-V4.json"
AFTER = ("IMPLEMENTATION-REPORT.md",)
LOG = C.EP / "docs/R43-SESSION-LOG.md"
REV43 = C.MR / "reviews/M2-review-43-harness"
FIELDS = ["answers", "baseline", "binds", "candidate", "changed_from_review39", "cli_pin", "contract", "files", "global_provider", "harness_files",
          "immutable", "interpreter", "name", "new_in_review42", "not_bound_but_recorded", "r39_rehash", "reference_set", "reference_set_statement",
          "run_set_sha256", "sandbox_base", "statement", "supersedes", "truth_sha256", "unchanged_from_review39", "written_at_utc"]
STATEMENT = ("binds code and inputs only; it authorizes nothing (no run, budget, scope, token, nonce or default); it is not signed and not bound to "
             "a nonce; M4 (historical M2) CHANGES STILL REQUIRED; M3 accepted (7 October 2026); the declaration v4 bound here is FROZEN and NOT "
             "AUTHORIZED; its dry rehearsal did not exercise real baseline facts on F009, F020 and F030 (finding R43-40-F1, "
             "rehearsal/REAL-BASELINE-FACTS-FINDING.md), so condition (b) of the owner's conditional decision A-13 item 3 is not demonstrated by "
             "this package")


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
            if rel == NAME or rel in AFTER or rel.startswith("SELF-CHECK-"):
                continue
            out[rel] = p
    return out


def group(paths) -> dict:
    return {pathlib.Path(p).as_posix(): C.sha256_file(p) for p in paths}


def build(n: int) -> dict:
    h = json.loads(C.BINDING43.read_text(encoding="utf-8"))
    if C.sha256_file(C.BINDING43) != C.BINDING43_SHA:
        raise SystemExit("PACKET MISMATCH: harness manifest")
    pf = pkg_files()
    top = [r for r in pf if "/" not in r]
    files = {
        "declaration_r32_v4": group(pf[r] for r in top),
        "v4_build_scripts": group(pf[r] for r in pf if r.startswith("scripts/")),
        "v4_rehearsal": group(pf[r] for r in pf if r.startswith(("dry-run/", "rehearsal/", "scope/"))),
        "v4_evidence": group(pf[r] for r in pf if r.startswith("evidence/")),
        "chain_r43_harness": group([C.BINDING43]),
        "chain_v3": group([C.V3 / C.V3_NAME, C.V3 / "DECLARATION.sha256", C.V3 / "FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json", C.V3 / C.AUTH_NAME,
                           C.V3 / "evidence/EVIDENCE-MANIFEST.json"]),
        "verification43": group([REV43 / "INDEPENDENT-VERIFICATION.md", REV43 / "FINDINGS.json", REV43 / "INDEPENDENT-PACKAGE-CHECK.json"]),
        "v4_preparation_inputs": group([C.EP / "docs/R32-V4-PREPARATION-LIST.md", pathlib.Path("C:/t/r2x/r42-sandbox/R43-REVIEW-PACKAGE/R43-RESIDUAL-F021-P4.md"),
                                        pathlib.Path("C:/t/r2x/r42-sandbox/R43-RESIDUALS-ADDENDUM-2026-10-07.md"),
                                        pathlib.Path("C:/t/r2x/r42-sandbox/REVIEW-43-REPORT-2026-10-07.md"),
                                        pathlib.Path("C:/t/r2x/r42-sandbox/R43-REVIEW-PACKAGE/R43-HARNESS-JUDGE-OUTPUT.json")]),
        "runbook_addendum_r42": group([C.MR / "orchestrator/RUNBOOK-ADDENDUM-R42.md"]),
    }
    bad = [p for fs in h["files"].values() for p, w in fs.items() if not pathlib.Path(p).is_file() or C.sha256_file(p) != w]
    decl = C.PACKAGE / C.DECLARATION_NAME
    snaps = {k: json.loads((C.PACKAGE / f"evidence/SNAPSHOT-{k}.json").read_text(encoding="utf-8")) for k in ("BEFORE", "AFTER")}
    git = {}
    for side, (repo, head) in (("baseline", C.BASELINE), ("candidate", C.CANDIDATE)):
        g = C.git_state(repo)
        git[side] = {"clean": g["clean"], "expected": head, "head": g["head"], "tree": repo}
    man = {
        "answers": ("Owner task R43-40 (A-13 item 2; card orchestrator/tasks/R43-40-TASK.md a6e54229...): declaration v4 of the R32 fresh "
                    "validation on the review43 harness and the R43 trees, its build scripts (the v3 scripts copied byte-identically and changed "
                    "only where V4-BUILD-DIFF.md lists), the v3 -> v4 field diff, the no-request preflight, dry exercise and scripted-provider "
                    "demonstrations, the rehearsal finding R43-40-F1, chained to BINDING-MANIFEST-R43-HARNESS (Verification 43) and to the "
                    "executed v3 declaration"),
        "baseline": git["baseline"], "candidate": git["candidate"],
        "binds": {
            "declaration_r32_v4": {"declaration": C.sha256_file(decl), "declaration_sha256_file": C.sha256_file(C.PACKAGE / "DECLARATION.sha256"),
                                   "declaration_diff_json": C.sha256_file(C.PACKAGE / "DECLARATION-DIFF.json"),
                                   "declaration_diff_md": C.sha256_file(C.PACKAGE / "DECLARATION-DIFF.md"),
                                   "v4_build_diff": C.sha256_file(C.PACKAGE / "V4-BUILD-DIFF.md"), "status": "frozen, NOT authorized"},
            "harness_r43": {"manifest": C.BINDING43_SHA, "entries": sum(len(v) for v in h["files"].values())},
            "declaration_r32_v3": {"declaration": C.V3_SHA, "manifest": C.V3_MANIFEST_SHA, "run_declaration": C.V3_RUN_SHA, "authorization_file": C.V3_AUTH_SHA},
            "verification43": {"verification": C.sha256_file(REV43 / "INDEPENDENT-VERIFICATION.md"), "findings": C.sha256_file(REV43 / "FINDINGS.json"),
                               "package_check": C.sha256_file(REV43 / "INDEPENDENT-PACKAGE-CHECK.json"), "verdict": "VERIFIED WITH CONDITIONS"},
            "rehearsal": {"preflight": C.sha256_file(C.PACKAGE / "dry-run/PREFLIGHT-RESULTS.json"), "dry_exercise": C.sha256_file(C.PACKAGE / "dry-run/DRY-EXERCISE.json"),
                          "demos": C.sha256_file(C.PACKAGE / "rehearsal/demos/DEMOS-R42.json"),
                          "finding_r43_40_f1": C.sha256_file(C.PACKAGE / "rehearsal/REAL-BASELINE-FACTS-FINDING.md")},
            "r43_session_log_prefix": log_prefix(n)},
        "changed_from_review39": h["changed_from_review39"], "cli_pin": h["cli_pin"], "contract": h["contract"], "files": files,
        "global_provider": h["global_provider"], "harness_files": h["harness_files"],
        "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
        "interpreter": h["interpreter"],
        "name": ("R32 v4 declaration binding manifest: the frozen declaration v4 (not authorized), its build scripts and diffs and the dry rehearsal "
                 "evidence, chained to the review43 harness manifest and the executed v3 declaration (declaration-r32-v4)"),
        "new_in_review42": h["new_in_review42"],
        "not_bound_but_recorded": {
            "authority_register": {"path": (C.MR / "orchestrator/AUTHORITY-REGISTER.md").as_posix(), "sha256_at_binding": C.sha256_file(C.MR / "orchestrator/AUTHORITY-REGISTER.md"),
                                   "why": "append-only, updated by the orchestrator"},
            "task_file": {"path": C.TASK_FILE.as_posix(), "sha256_at_binding": C.sha256_file(C.TASK_FILE)},
            "carried_fields": "baseline and candidate re-read now; changed_from_review39, cli_pin, contract, global_provider, harness_files, interpreter, new_in_review42, reference_set, reference_set_statement, run_set_sha256, truth_sha256 and unchanged_from_review39 are carried from BINDING-MANIFEST-R43-HARNESS (the harness is unchanged); r39_rehash is that manifest's every entry re-hashed now",
            "protected_state": {k: {"ai_ledger": v["ai_ledger"], "v4_scope_present": v["v4_scope_present"], "pip_freeze": v["pip_freeze"]["sha256"],
                                    "folders": {f: x["sha256"] for f, x in v["folders"].items()}, "v4_run_folder_exists": v["v4_run_folder_exists"],
                                    "named_files": v["authorization_run_token_named_files"], "c_free_bytes": v["c_free_bytes"]} for k, v in snaps.items()},
            "protected_state_unchanged": {"ai_ledger": snaps["BEFORE"]["ai_ledger"] == snaps["AFTER"]["ai_ledger"],
                                          "pip_freeze": snaps["BEFORE"]["pip_freeze"]["sha256"] == snaps["AFTER"]["pip_freeze"]["sha256"],
                                          "folders": snaps["BEFORE"]["folders"] == snaps["AFTER"]["folders"],
                                          "trees": snaps["BEFORE"]["trees"] == snaps["AFTER"]["trees"],
                                          "named_files": snaps["BEFORE"]["authorization_run_token_named_files"] == snaps["AFTER"]["authorization_run_token_named_files"]},
            "written_after_this_manifest": list(AFTER) + ["SELF-CHECK-<n>.json"],
            "work_folder": {"path": C.WORK.as_posix(), "rule": "every file this task created outside the package lies under it (scripts' run copies, dry and demonstration run folders, logs)"},
            "substitutions": "V4-BUILD-DIFF.md section 4 (S-RUN, S-HERE, S-BASE, S-GUARD, S-ENV)"},
        "r39_rehash": {"rule": "every file binding of BINDING-MANIFEST-R43-HARNESS re-hashed at its path when this manifest was written",
                       "equal": sum(len(v) for v in h["files"].values()) - len(bad), "differ": bad, "missing": [p for p in bad if not pathlib.Path(p).is_file()]},
        "reference_set": h["reference_set"], "reference_set_statement": h["reference_set_statement"], "run_set_sha256": h["run_set_sha256"],
        "sandbox_base": "declared by the declaration (run.sandbox_base C:/t/r2x/r42-sandbox, run.folder C:/t/r2x/r42-sandbox/r32-v4, never created here); this task's dry base C:/t/r2x/r42-sandbox/r43p/sb",
        "statement": STATEMENT,
        "supersedes": {"file": (C.V3 / "evidence/EVIDENCE-MANIFEST.json").as_posix(), "sha256": C.V3_MANIFEST_SHA,
                       "for": "the declaration package of the R32 fresh validation (v3 executed 2026-10-07, INVALID and terminal; v4 is its successor, not authorized)"},
        "truth_sha256": h["truth_sha256"], "unchanged_from_review39": h["unchanged_from_review39"],
        "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    assert sorted(man) == FIELDS and len(man) == 25
    return man


def selfcheck(n: str) -> int:
    out = C.PACKAGE / f"SELF-CHECK-{n}.json"
    if out.exists():
        raise SystemExit(f"refused: {out.name} exists")
    mp = C.PACKAGE / NAME
    man = json.loads(mp.read_text(encoding="utf-8"))
    checks, fails = [], []

    def ck(name, ok, detail=None):
        checks.append(name)
        if not ok:
            fails.append({"check": name, "detail": detail})
    ck("fields: 25 in the R42/R43 set", sorted(man) == FIELDS and len(man) == 25, sorted(man))
    ck("fields: equal to the harness manifest's", sorted(man) == sorted(json.loads(C.BINDING43.read_text(encoding="utf-8"))))
    entries = [(g, p, w) for g, fs in man["files"].items() for p, w in fs.items()]
    for g, p, w in entries:
        ok = pathlib.Path(p).is_file() and C.sha256_file(p) == w
        ck(f"file {g}: {p}", ok, None if ok else ("missing" if not pathlib.Path(p).is_file() else C.sha256_file(p)))
    b = man["binds"]
    d4 = b["declaration_r32_v4"]
    for k, f in (("declaration", C.DECLARATION_NAME), ("declaration_sha256_file", "DECLARATION.sha256"), ("declaration_diff_json", "DECLARATION-DIFF.json"),
                 ("declaration_diff_md", "DECLARATION-DIFF.md"), ("v4_build_diff", "V4-BUILD-DIFF.md")):
        ck(f"binds declaration_r32_v4.{k}", C.sha256_file(C.PACKAGE / f) == d4[k])
    ck("binds DECLARATION.sha256 names the declaration", (C.PACKAGE / "DECLARATION.sha256").read_text(encoding="utf-8").split()[0] == d4["declaration"])
    decl = json.loads((C.PACKAGE / C.DECLARATION_NAME).read_text(encoding="utf-8"))
    ck("declaration binds the harness manifest", decl["binding_manifest_sha256"] == b["harness_r43"]["manifest"] == C.sha256_file(C.BINDING43))
    ck("declaration not executed, not approved", decl["executed"] is False and decl["budget_approved"] is False)
    v3 = b["declaration_r32_v3"]
    for k, f in (("declaration", C.V3_NAME), ("manifest", "evidence/EVIDENCE-MANIFEST.json"), ("run_declaration", "FRESH-VALIDATION-DECLARATION-R32-V3.RUN.json"),
                 ("authorization_file", C.AUTH_NAME)):
        ck(f"binds declaration_r32_v3.{k}", C.sha256_file(C.V3 / f) == v3[k])
    for k, f in (("verification", "INDEPENDENT-VERIFICATION.md"), ("findings", "FINDINGS.json"), ("package_check", "INDEPENDENT-PACKAGE-CHECK.json")):
        ck(f"binds verification43.{k}", C.sha256_file(REV43 / f) == b["verification43"][k])
    for k, f in (("preflight", "dry-run/PREFLIGHT-RESULTS.json"), ("dry_exercise", "dry-run/DRY-EXERCISE.json"), ("demos", "rehearsal/demos/DEMOS-R42.json"),
                 ("finding_r43_40_f1", "rehearsal/REAL-BASELINE-FACTS-FINDING.md")):
        ck(f"binds rehearsal.{k}", C.sha256_file(C.PACKAGE / f) == b["rehearsal"][k])
    lp = b["r43_session_log_prefix"]
    nlines = int(lp["lines"].split("-")[1])
    ck("binds r43_session_log_prefix", log_prefix(nlines)["sha256"] == lp["sha256"])
    h = json.loads(C.BINDING43.read_text(encoding="utf-8"))
    hbad = [p for fs in h["files"].values() for p, w in fs.items() if not pathlib.Path(p).is_file() or C.sha256_file(p) != w]
    ck("harness manifest: every entry re-hashes equal now", not hbad, hbad[:5])
    ck("r39_rehash recorded 0 differ", not man["r39_rehash"]["differ"] and not man["r39_rehash"]["missing"])
    ck("supersedes hash", C.sha256_file(man["supersedes"]["file"]) == man["supersedes"]["sha256"])
    ck("statement: authorizes nothing", "it authorizes nothing" in man["statement"])
    ck("statement: M4 CHANGES STILL REQUIRED; M3 accepted", "M4 (historical M2) CHANGES STILL REQUIRED" in man["statement"] and "M3 accepted" in man["statement"])
    bound = {p for fs in man["files"].values() for p in fs}
    unbound = sorted(rel for rel, p in pkg_files().items() if p.as_posix() not in bound)
    ck("package: every file bound (except the manifest, the report and the self-checks)", not unbound, unbound)
    ck("package: no RUN or authorization file in v4", not (C.PACKAGE / C.RUN_NAME).exists() and not (C.PACKAGE / C.AUTH_NAME).exists())
    ck("v4 run folder absent", not C.RUN_FOLDER.exists())
    led = C.ledger_state()
    ck("AI ledger 484 / 18 / 0, no v4 scope", {k: led[k] for k in C.LEDGER_EXPECTED} == C.LEDGER_EXPECTED and C.SCOPE not in led["scope_names"])
    res = {"manifest": {"path": mp.as_posix(), "sha256": C.sha256_file(mp)}, "checks": len(checks), "failures": fails,
           "entries": len(entries), "unique_paths": len({p for _g, p, _w in entries}),
           "taken_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "log_lines_now": len(LOG.read_bytes().split(b"\n")) - 1}
    C.write_json_once(out, res)
    print(json.dumps({"manifest_sha256": res["manifest"]["sha256"], "checks": len(checks), "failures": len(fails), "entries": len(entries)}))
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
