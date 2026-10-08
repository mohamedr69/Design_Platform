"""R43-42 (review45, new): write BINDING-MANIFEST-R45-HARNESS.json in the R42 form (the same 25 fields as
BINDING-MANIFEST-R42 / -R43-HARNESS / -R32-V4), binding the review45 package, superseding the review43 harness manifest
f35355aa...374a7, carrying every file binding of that manifest (re-hashed now; a difference is a finding, never repaired),
and binding the R43 session-log prefix (lines 1..N at the moment of writing). Written to <out json> once (never over an
existing file); the package copy is placed by the operator. Read-only otherwise.
Usage: <bound python> -B r45_manifest.py <out json> <task card> <facts json>
<facts json> carries the figures the manifest records (tests, drill result, sizes, substitutions), written by the operator
from the evidence files (each of which is bound here by hash)."""
from __future__ import annotations

import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r45common as C  # noqa: E402

UNBOUND = ("BINDING-MANIFEST-R45-HARNESS.json", "SELF-CHECK-1.json", "SELF-CHECK-2.json")
V44 = C.MR / "reviews/M2-review-44"


def log_prefix() -> dict:
    data = C.LOG.read_bytes()
    lines = data.split(b"\n")
    n = len(lines) - 1 if data.endswith(b"\n") else len(lines)
    return {"path": C.LOG.as_posix(), "lines": f"1-{n}", "sha256": C.sha256_bytes(data if data.endswith(b"\n") else data + b"\n"),
            "rule": "sha256 of lines 1..N with their LF terminators (the whole file at binding); later rows are appended, never edited",
            "last_row": next((ln.split("|")[1].strip() for ln in reversed(data.decode("utf-8").splitlines()) if ln.startswith("| R43-")), None)}


def main(out: str, card: str, facts_path: str) -> int:
    out = pathlib.Path(out)
    if out.exists():
        raise SystemExit("refused: the manifest is written once")
    facts = json.loads(pathlib.Path(facts_path).read_text(encoding="utf-8"))
    m43 = json.loads(C.BINDING43.read_text(encoding="utf-8"))
    if C.sha256_file(C.BINDING43) != C.BINDING43_SHA:
        raise SystemExit("refused: the review43 harness manifest is not f35355aa...")
    # carried groups, re-hashed
    equal, differ, missing = 0, [], []
    for g, fs in m43["files"].items():
        for p, want in fs.items():
            try:
                got = C.sha256_file(p)
            except OSError:
                missing.append(p)
                continue
            if got == want:
                equal += 1
            else:
                differ.append({"group": g, "path": p, "bound": want, "now": got})
    files = {g: dict(v) for g, v in m43["files"].items()}
    pkg = {}
    for p in sorted(C.REVIEW45.rglob("*")):
        if p.is_file() and p.name not in UNBOUND and "__pycache__" not in p.parts:
            pkg[p.as_posix()] = C.sha256_file(p)
    files["harness_r45_package"] = pkg
    files["chain_r43_harness"] = {C.BINDING43.as_posix(): C.BINDING43_SHA}
    files["verification44"] = {(V44 / n).as_posix(): C.sha256_file(V44 / n) for n in ("INDEPENDENT-VERIFICATION.md", "FINDINGS.json", "INDEPENDENT-PACKAGE-CHECK.json")}
    files["r45_task_card"] = {pathlib.Path(card).as_posix(): C.sha256_file(card)}
    files["r45_staged_documents"] = {f"C:/t/r2x/r32-stage/files/{p}.pdf": C.sha256_file(f"C:/t/r2x/r32-stage/files/{p}.pdf") for p in ("F009", "F020", "F030")}
    files["r45_v4_package_read_only"] = {(C.PILOT / "declaration-r32-v4" / n).as_posix(): C.sha256_file(C.PILOT / "declaration-r32-v4" / n)
                                         for n in ("FRESH-VALIDATION-DECLARATION-R32-V4.json", "BINDING-MANIFEST-R32-V4.json",
                                                   "rehearsal/REAL-BASELINE-FACTS-FINDING.md")}
    h43 = C.REVIEW43 / "scripts" / "harness-r32"
    h45 = C.REVIEW45 / "scripts" / "harness-r32"
    hf = {}
    for p in sorted(set(x.name for x in h43.glob("*.py")) | set(x.name for x in h45.glob("*.py"))):
        a = C.sha256_file(h43 / p) if (h43 / p).exists() else None
        b = C.sha256_file(h45 / p) if (h45 / p).exists() else None
        changed = facts["lines_changed"].get(p, 0)
        hf[p] = {"r43_sha256": a, "r45_sha256": b, "status": "unchanged" if a == b else ("new_in_review45" if a is None else "changed_in_review45"),
                 "lines_changed": 0 if a == b else changed}
    binds = dict(m43["binds"])
    binds["r43_harness"] = {"manifest": C.BINDING43_SHA, "supersedes_by_this_manifest": True}
    binds["verification44"] = {pathlib.Path(k).name: v for k, v in files["verification44"].items()}
    binds["r45_drill"] = facts["drill_binds"]
    binds["r45_tests"] = facts["test_binds"]
    binds["r45_session_log_prefix"] = log_prefix()
    binds["r45_task_card"] = {"path": pathlib.Path(card).as_posix(), "sha256": C.sha256_file(card)}
    trees = {"baseline": C.tree_state("C:/t/iso/frozen-r13"), "candidate": C.tree_state("C:/t/iso/cand-r30n")}
    rec = {
        "answers": ("Owner task R43-42 (A-13 item 2; Verification 44 ruling R44-06 and its recommendation, option 1 scoped to F009, F020 and F030; "
                    "card MR/orchestrator/tasks/R43-42-TASK.md, bound in files.r45_task_card): the review45 harness = the review43 harness copied "
                    "byte-identically plus the dry-only baseline-facts drill (runner_r32 --dry-baseline-facts, drill_r45.py, the lane_r32 drill "
                    "branch, test_dry_baseline_drill_r45.py), its tests, the one drill run and its evidence, DRILL-DIFF.md, DRILL-CRITERION.md "
                    "(declared before the first run) and DISCLOSURE-AMENDMENT-DRAFT.md, chained to BINDING-MANIFEST-R43-HARNESS (superseded)"),
        "baseline": {"clean": trees["baseline"]["status_lines"] == 0, "expected": "7ec3d2cf983b70a604844beda8eb6b1ec6173d34",
                     "head": trees["baseline"]["head"], "tree": "C:/t/iso/frozen-r13"},
        "binds": binds,
        "candidate": {"clean": trees["candidate"]["status_lines"] == 0, "expected": "436daef215c72fbe2429dcd783e087bf39756ad7",
                      "head": trees["candidate"]["head"], "tree": "C:/t/iso/cand-r30n"},
        "changed_from_review39": m43["changed_from_review39"],
        "cli_pin": m43["cli_pin"],
        "contract": m43["contract"],
        "files": files,
        "global_provider": m43["global_provider"] | {"B_in_the_baseline_facts_drill": "refusing (run_control_r38.RefusingGlobalProvider; dry drill only)"},
        "harness_files": hf,
        "immutable": m43["immutable"],
        "interpreter": m43["interpreter"] | {"sha256_now": C.sha256_file(C.PY)},
        "name": ("R45 harness binding manifest: the review45 harness (the review43 harness plus the dry-only baseline-facts drill of lane B on "
                 "F009, F020 and F030), its tests and the drill evidence, superseding the review43 harness manifest (review45)"),
        "new_in_review42": m43["new_in_review42"],
        "not_bound_but_recorded": {
            "authority_register": {"path": (C.MR / "orchestrator/AUTHORITY-REGISTER.md").as_posix(),
                                   "sha256_at_binding": C.sha256_file(C.MR / "orchestrator/AUTHORITY-REGISTER.md"), "why": "append-only, updated by the orchestrator"},
            "carried_fields": ("changed_from_review39, cli_pin, contract, new_in_review42, reference_set, reference_set_statement, run_set_sha256, "
                               "truth_sha256 and unchanged_from_review39 are carried from BINDING-MANIFEST-R43-HARNESS (historical lists; the review45 "
                               "changes are in harness_files); baseline, candidate and the interpreter hash are re-read now"),
            "changed_in_review45": sorted(k for k, v in hf.items() if v["status"] != "unchanged"),
            "evidence_counts": facts["evidence_counts"],
            "log_prefix_placement": {"where": "binds.r45_session_log_prefix", "why": "every files entry is a real file (verify_binding opens each)"},
            "run_copy_substitutions": facts["substitutions"],
            "unbound": list(UNBOUND),
            "v4": "declaration-r32-v4 untouched (three of its files re-hashed in files.r45_v4_package_read_only); r32-v4 does not exist"},
        "r39_rehash": {"differ": differ, "equal": equal, "missing": missing,
                       "rule": "every file binding of BINDING-MANIFEST-R43-HARNESS re-hashed at its path when this manifest was written; a difference is a finding, never repaired"},
        "reference_set": m43["reference_set"],
        "reference_set_statement": m43["reference_set_statement"],
        "run_set_sha256": m43["run_set_sha256"],
        "sandbox_base": ("declared by a declaration (run.sandbox_base); dry / tests default C:/t/r2x/r42-sandbox; the drill writes only "
                         "<base>/r32-drill-<stamp> (this task's evidence run: C:/t/r2x/r42-sandbox/r45p/sb/r32-drill-<stamp>, driver-side S-BASE)"),
        "statement": ("binds code and inputs only; it authorizes nothing (no run, budget, scope, token, nonce, RUN or authorization file, no "
                      "default); it is not signed and not bound to a nonce; M4 (historical M2) CHANGES STILL REQUIRED; M3 accepted (7 October 2026); "
                      "declaration v4 is untouched, frozen and NOT authorized; the drill bound here is dry only (0 model requests) and its result "
                      f"is {facts['drill_result']} against DRILL-CRITERION.md; a v5 declaration, Verification 45 and an owner decision are needed "
                      "before anything uses this harness"),
        "supersedes": {"file": C.BINDING43.as_posix(), "sha256": C.BINDING43_SHA,
                       "for": "the harness-r32 code of a later declaration (review45 = review43 + the dry-only baseline-facts drill); the carried inputs and chains stay bound here"},
        "truth_sha256": m43["truth_sha256"],
        "unchanged_from_review39": m43["unchanged_from_review39"],
        "written_at_utc": C.now_utc()}
    assert len(rec) == 25 and list(rec) == sorted(m43), sorted(set(rec) ^ set(m43))
    out.write_text(json.dumps(rec, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"fields": len(rec), "entries": sum(len(v) for v in files.values()), "rehash_equal": equal, "differ": len(differ),
                      "missing": len(missing), "log_prefix": binds["r45_session_log_prefix"]["lines"], "sha256": C.sha256_file(out)}))
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:4]))
