"""ORCH-05C: write <package>/evidence/EVIDENCE-MANIFEST.json LAST (sha256 and bytes of every package file except the manifest
itself), refusing unless evidence/PACKAGE-CHECK.json reports ok. Usage: package_r34.py"""
import datetime
import hashlib
import json
import pathlib
import sys

R34 = pathlib.Path("C:/t/iso/work/r2x/r34")
sys.path.insert(0, str(R34 / "harness-r32"))
import concentration_r32 as K  # noqa: E402
import inputs_r32 as I  # noqa: E402

PKG = I.PILOT / "review34"
MANIFEST = PKG / "evidence" / "EVIDENCE-MANIFEST.json"


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    check = json.loads((PKG / "evidence" / "PACKAGE-CHECK.json").read_text(encoding="utf-8"))
    if not check.get("ok"):
        raise SystemExit(f"refused: the package check is not ok: {check.get('problems')}")
    if MANIFEST.exists():
        raise SystemExit("refused: the evidence manifest is written once")
    files = {}
    for p in sorted(PKG.rglob("*")):
        if p.is_file() and p != MANIFEST:
            files[p.relative_to(PKG).as_posix()] = {"sha256": sha(p), "bytes": p.stat().st_size}
    dry = json.loads((PKG / "dry-run" / "DRY-RUN-REPORT.json").read_text(encoding="utf-8"))
    man = {"package": "review34 (ORCH-05C, R34HARNESS-IMPL): correction package answering Independent Review 34 RC-1 to RC-6 -- concentration rule "
                      "v2 (no net-gain floor), candidate-level outcome, pinned one-run dispatch guard, per-declaration allowance / capture store / "
                      "resume, live lane verification, failures once per document; dry run only",
           "written_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "written": "last; lists every package file except itself",
           "files": files, "file_count": len(files),
           "package_check_sha256": files["evidence/PACKAGE-CHECK.json"]["sha256"], "package_check_ok": True,
           "binding_manifest_sha256": files["BINDING-MANIFEST-R34.json"]["sha256"],
           "concentration_rule_version": K.RULE_VERSION,
           "run_set_proposal_sha256": files["RUN-SET-PROPOSAL.json"]["sha256"],
           "truth_r32_sha256": files["dry-run/TRUTH-R32.json"]["sha256"],
           "labels_eval_input_sha256": files["LABELS-R32-EVAL-INPUT.json"]["sha256"],
           "dry_run_report_sha256": files["dry-run/DRY-RUN-REPORT.json"]["sha256"],
           "reviewed2_labels_sha256": I.INPUTS["reviewed2_labels"][1], "reviewed2_package_manifest_sha256": I.INPUTS["reviewed2_manifest"][1],
           "packet_manifest_sha256": I.INPUTS["packet_manifest"][1], "review31_manifest_sha256": I.INPUTS["review31_manifest"][1],
           "review33_manifest_sha256": "c5001c95420ac76150f320f04b1edfc5785264d00662d97e8f92ec83c6c95919",
           "review33_binding_sha256": "d1a8a40100fc05a937ccf40f6fb02a5788bfbea8a74adafcfc68b0f01a53936e",
           "review34_sha256": "75061210ff7af6b3619d86563af308caf65d706b4b5dc760288899524bbc8f47",
           "review34_findings_sha256": "af99a772cafac9ef24be67902e6769fb92f544be76df3ed2f25969c1642f9fd8",
           "policy_sha256": I.INPUTS["policy"][1], "policy_amendment_sha256": I.INPUTS["policy_amendment"][1],
           "candidate_head": I.CANDIDATE_HEAD, "baseline_head": I.BASELINE_HEAD,
           "ai_ledger": {"before": dry["ledger_before"], "after": dry["ledger_after"]}, "model_requests": 0, "ledger_scope_created": False,
           "owner_dispatch_authorization_exists": False,
           "reference_set_statement": I.REFERENCE_SET_STATEMENT}
    text = json.dumps(man, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print(hashlib.sha256(text.encode("utf-8")).hexdigest(), len(files))


if __name__ == "__main__":
    main()
