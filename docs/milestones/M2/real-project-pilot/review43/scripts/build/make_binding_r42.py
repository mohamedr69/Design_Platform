"""ORCH-10 (R42PORT-IMPL): write PILOT/review42/BINDING-MANIFEST-R42.json ONCE.

The same groups as BINDING-MANIFEST-R39 (a6f703b4...) with every Desktop path re-pointed to the merged installation and
every bound file RE-HASHED: each carried hash must equal R39's (the merged copies are byte-identical); a difference is
recorded as a finding (r39_rehash.differ) and NOT repaired. The runnable harness is bound from PILOT/review42/scripts/
harness-r32 only (group harness_r42_package); review39's harness stays bound as lineage. New groups: outputs_r42 (the
review42 outputs), contracts_r42, declaration_r32_v2_superseded, interpreter. Usage: make_binding_r42.py [--check-only]"""
import datetime
import difflib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

REVIEWS_NEW = ["reviews/M2-review-40/FINDINGS.json", "reviews/M2-review-40/INDEPENDENT-PACKAGE-CHECK.json", "reviews/M2-review-40/INDEPENDENT-VERIFICATION.md",
               "reviews/M2-review-41/FINDINGS.json", "reviews/M2-review-41/INDEPENDENT-PACKAGE-CHECK.json", "reviews/M2-review-41/INDEPENDENT-VERIFICATION.md",
               "orchestrator/RUNBOOK-ADDENDUM-R41.md"]


def repoint(p: str) -> str:
    return p.replace(C.DESKTOP_EP, C.MERGED_EP)


def lines(path) -> list:
    return pathlib.Path(path).read_text(encoding="utf-8").splitlines()


def main(argv) -> int:
    check_only = "--check-only" in argv
    r39 = json.loads(C.BINDING39.read_text(encoding="utf-8"))
    if C.sha256_file(C.BINDING39) != C.BINDING39_SHA:
        raise SystemExit("PACKET MISMATCH: BINDING-MANIFEST-R39")
    files, rehash = {}, {"equal": 0, "differ": [], "missing": []}
    for group, entries in r39["files"].items():
        name = "outputs_r39" if group == "outputs" else group
        files[name] = {}
        for p, want in entries.items():
            q = repoint(p)
            try:
                got = C.sha256_file(q)
            except OSError:
                rehash["missing"].append(q)
                continue
            files[name][q] = got
            if got == want:
                rehash["equal"] += 1
            else:
                rehash["differ"].append({"group": group, "path": q, "r39": want, "now": got})
    # the runnable harness: the review42 PACKAGE copy only
    h42 = sorted(C.HARNESS42.glob("*.py"))
    files["harness_r42_package"] = {p.as_posix(): C.sha256_file(p) for p in h42}
    files["outputs_r42"] = {(C.REVIEW42 / n).as_posix(): C.sha256_file(C.REVIEW42 / n)
                            for n in ("PROJECT-REQUEST-BOUNDS.json", "RESUME-INVOCATIONS-R42.json", "REQUEST-PATHS-STATIC.json")}
    files["contracts_r42"] = {(C.REVIEW42 / n).as_posix(): C.sha256_file(C.REVIEW42 / n) for n in ("LIVE-RUN-CONTRACT.md", "REQUEST-PATHS.md")}
    files["declaration_r32_v2_superseded"] = {(C.V2 / C.V2_NAME).as_posix(): C.sha256_file(C.V2 / C.V2_NAME),
                                              (C.V2 / "evidence/EVIDENCE-MANIFEST.json").as_posix(): C.sha256_file(C.V2 / "evidence/EVIDENCE-MANIFEST.json"),
                                              (C.REVIEW39 / "evidence/EVIDENCE-MANIFEST.json").as_posix(): C.sha256_file(C.REVIEW39 / "evidence/EVIDENCE-MANIFEST.json"),
                                              C.BINDING39.as_posix(): C.sha256_file(C.BINDING39)}
    files["reviews"].update({(C.MR / r).as_posix(): C.sha256_file(C.MR / r) for r in REVIEWS_NEW})
    base = pathlib.Path(sys.base_prefix)
    files["interpreter"] = {C.PY: C.sha256_file(C.PY), (base / "python.exe").as_posix(): C.sha256_file(base / "python.exe"),
                            (base / "python312.dll").as_posix(): C.sha256_file(base / "python312.dll")}
    # the harness file table against review39
    table = {}
    for p in h42:
        old = C.HARNESS39 / p.name
        new_sha = C.sha256_file(p)
        if not old.exists():
            table[p.name] = {"status": "new", "r42_sha256": new_sha, "lines": len(lines(p))}
            continue
        old_sha = C.sha256_file(old)
        if old_sha == new_sha:
            table[p.name] = {"status": "unchanged", "r39_sha256": old_sha, "r42_sha256": new_sha}
            continue
        d = list(difflib.unified_diff(lines(old), lines(p), lineterm="", n=0))
        table[p.name] = {"status": "changed", "r39_sha256": old_sha, "r42_sha256": new_sha,
                         "lines_added": sum(1 for x in d if x.startswith("+") and not x.startswith("+++")),
                         "lines_removed": sum(1 for x in d if x.startswith("-") and not x.startswith("---"))}
    heads = {r: C.git_state(r) for r in (C.CANDIDATE[0], C.BASELINE[0])}
    man = {
        "name": "ORCH-10 (R42PORT-IMPL) binding manifest: the r32 harness corrected for portability and safety in the merged installation (review42)",
        "answers": ("A-11 / ORCH-10: portability (2.1), R40-04 by option 2 (2.2), R41-09 / R41-10 / R41-11 (2.3), one approval for all planned "
                    "resumptions (2.4); every carried binding re-pointed to the merged installation and re-hashed"),
        "contract": "r42-live-contract-5",
        "files": files,
        "harness_files": table,
        "changed_from_review39": sorted(k for k, v in table.items() if v["status"] == "changed"),
        "new_in_review42": sorted(k for k, v in table.items() if v["status"] == "new"),
        "unchanged_from_review39": sorted(k for k, v in table.items() if v["status"] == "unchanged"),
        "r39_rehash": rehash | {"rule": "every carried file re-hashed at its merged path must equal BINDING-MANIFEST-R39; a difference is a finding, never repaired"},
        "supersedes": {"file": C.BINDING39.as_posix(), "sha256": C.BINDING39_SHA,
                       "for": "the harness-r32 code (now bound from review42); every carried group re-pointed and re-hashed"},
        "binds": {"review39": {"binding": C.BINDING39_SHA, "manifest": C.REVIEW39_MANIFEST_SHA}, "declaration_r32_v2": {"declaration": C.V2_SHA,
                                                                                                                     "manifest": C.V2_MANIFEST_SHA}},
        "interpreter": {"path": C.PY, "sha256": C.sha256_file(C.PY), "version": sys.version.split()[0], "base": (base / "python.exe").as_posix()},
        "cli_pin": {"path": C.CLI_EXE.as_posix(), "sha256": C.CLI_EXE_SHA, "bytes": C.CLI_EXE_BYTES, "version_line": C.CLI_VERSION_LINE,
                    "bound_in": "the declaration (model_identity.cli); verified by preflight_r32.verify_cli before any lane (read as bytes)",
                    "not_used": C.BUNDLED_CLI_NOT_USED.as_posix()},
        "candidate": {"tree": C.CANDIDATE[0], "expected": C.CANDIDATE[1], "head": heads[C.CANDIDATE[0]]["head"], "clean": heads[C.CANDIDATE[0]]["clean"]},
        "baseline": {"tree": C.BASELINE[0], "expected": C.BASELINE[1], "head": heads[C.BASELINE[0]]["head"], "clean": heads[C.BASELINE[0]]["clean"]},
        "run_set_sha256": C.RUN_SET_SHA, "truth_sha256": C.TRUTH_SHA,
        "reference_set": {"name": "r32-labels-reviewed-2", "sha256": C.LABELS_SHA, "populations": {"identity": 57, "revision": 38, "decision": 38}},
        "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed",
        "sandbox_base": "declared by the declaration (run.sandbox_base); dry / tests default C:/t/r2x/r42-sandbox",
        "global_provider": {"B": "harness_chain", "C": "refusing", "R": "refusing", "P": "refusing"},
        "immutable": "written once per freeze; a changed file is a new manifest with a new hash, never an edit",
        "not_bound_but_recorded": {"authority_register": {"path": (C.MR / "orchestrator/AUTHORITY-REGISTER.md").as_posix(),
                                                          "sha256_at_binding": C.sha256_file(C.MR / "orchestrator/AUTHORITY-REGISTER.md"),
                                                          "why": "append-only, updated by the orchestrator"},
                                   "task_file": {"path": C.TASK_FILE.as_posix(), "sha256_at_binding": C.sha256_file(C.TASK_FILE)}},
        "statement": "binds code and inputs only; it authorizes nothing (no run, budget, scope, token or default); M2 CHANGES STILL REQUIRED; M3 not started",
        "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    }
    ok = not rehash["differ"] and not rehash["missing"] and all(h["clean"] for h in heads.values())
    print(json.dumps({"groups": {k: len(v) for k, v in files.items()}, "entries": sum(len(v) for v in files.values()), "r39_rehash_equal": rehash["equal"],
                      "differ": rehash["differ"], "missing": rehash["missing"], "changed": man["changed_from_review39"], "new": man["new_in_review42"]}, indent=1))
    if check_only:
        return 0 if ok else 3
    if C.BINDING42.exists():
        raise SystemExit("refused: BINDING-MANIFEST-R42.json is written once")
    sha = C.write_json_once(C.BINDING42, man)
    print(json.dumps({"written": C.BINDING42.as_posix(), "sha256": sha}))
    return 0 if ok else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
