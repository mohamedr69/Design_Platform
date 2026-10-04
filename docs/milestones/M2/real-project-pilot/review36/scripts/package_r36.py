"""ORCH-06C (R36HARNESS-IMPL): write PILOT/review36/evidence/EVIDENCE-MANIFEST.json LAST (sha256 and bytes of every package
file except the manifest itself), refusing unless evidence/PACKAGE-CHECK.json reports ok (with the tests re-run).
Usage: package_r36.py"""
import datetime
import hashlib
import json
import pathlib

PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PKG = PILOT / "review36"
MANIFEST = PKG / "evidence" / "EVIDENCE-MANIFEST.json"
REFERENCE_SET_STATEMENT = "reference set independently AI-reviewed (Claude agents), not human-signed"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    check = json.loads((PKG / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not check.get("ok") or check.get("skip_tests"):
        raise SystemExit(f"refused: the package check is not ok (or skipped the tests): {check.get('problems')}")
    if MANIFEST.exists():
        raise SystemExit("refused: the evidence manifest is written once")
    files = {}
    for p in sorted(PKG.rglob("*")):
        if p.is_file() and p != MANIFEST:
            files[p.relative_to(PKG).as_posix()] = {"sha256": sha(p), "bytes": p.stat().st_size}
    c = check["checks"]
    w = c["h1_whatif"]
    man = {"package": "review36 (ORCH-06C, R36HARNESS-IMPL): bounded harness fix for H1 (Independent Verification 36, finding R36-08) -- "
                      "literal_compare_r32.norm_revision removes every whitespace character after the optional prefix before the number is parsed",
           "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "written": "last; lists every package file except itself",
           "files": files, "file_count": len(files),
           "package_check_sha256": files["evidence/PACKAGE-CHECK.json"]["sha256"], "package_check_ok": True,
           "binding_manifest_sha256": files["BINDING-MANIFEST-R36.json"]["sha256"],
           "h1_whatif_result_sha256": files["H1-WHATIF-RESULT.json"]["sha256"],
           "literal_compare_r32": c["harness"]["literal_compare_r32"],
           "test_literal_compare_r32": {k: c["harness"]["test_literal_compare_r32"][k] for k in ("review34", "r36")},
           "modules_differing_from_review34": c["harness"]["modules_differing_from_review34"],
           "tests": {"whole_suite_twin": {k: c["junit_packaged"]["whole_suite_twin"][k] for k in ("modules", "tests", "failures", "errors")},
                     "bound_copy": {k: c["junit_packaged"]["bound_copy_sandbox_free_modules"][k] for k in ("modules", "tests", "failures", "errors")}},
           "h1_effect": {"rows_changed_per_state": w["rows_changed"], "cases_changed": w["cases_changed"], "rows_in_run_set": w["changed_rows_in_run_set"],
                         "wrong_value_control_verdicts_changed": w["wrong_value_controls"]["verdict_changed"],
                         "not_scorable_read_as_absent": w["not_scorable"]["harness_read_as_absent_after"]},
           "review34_manifest_sha256": "64d5ba0dda43fc86736eb56558a8eaa2e083231e28c4efd52eceb06abe5d7a86",
           "review34_binding_sha256": "3d0f8bfe37d55a4c0490e054c0d710f4bb1d2ac839dffd08daaafca19063ea27",
           "evaluator_offline_r32_manifest_sha256": "86dd81d3dcbc139f35495946b400c82d50c65feb21dda6fa0ab2558e1d634db7",
           "fixtures_sha256": "9f3e0e56bace4ae5fe2724d259ab657ef63490f0a5afc2f5291d78fbb4d1f774",
           "parity_matrix_sha256": "73e189f2d0cfe05e55ba58837e991c008eaaf11fb928c300cf0670ead60aaccc",
           "verification36_sha256": "f698c2ffebc44df0487edce762a3f1bd561b2cbbda7b3d844dbd7d6c15173a00",
           "candidate_head": "a8aacedd21cceb751a2f55ac07d1dc55b5fbaa1d", "baseline_head": "3d5607d99fcebf08ac45f5df937ad615ecc16fb3",
           "ai_ledger": c["ledger"], "model_requests": 0, "ledger_scope_created": False, "owner_dispatch_authorization_exists": False,
           "reference_set_statement": REFERENCE_SET_STATEMENT}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(MANIFEST, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(hashlib.sha256(text.encode("utf-8")).hexdigest(), len(files))


if __name__ == "__main__":
    main()
