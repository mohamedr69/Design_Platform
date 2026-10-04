"""runner_r32 / lane_r32: preflight refusals, the dry pipeline on the real reference set (reader 'none', no prediction),
and the application readers' path in dry mode on SYNTHETIC documents only (B tripwire to INVALID, C from B, R served
from C, resume). Sandboxes only under C:/t/r2x/r33-sandbox/tests/. Run: python -m pytest -q test_runner_r32.py"""
import hashlib
import json
import pathlib
import uuid

import pytest

import runner_r32 as RN
import synthetic_r32 as SY

TEST_BASE = RN.SANDBOX_BASE / "tests"
def _stamp():
    return f"tests/run-{uuid.uuid4().hex[:10]}"


def _binding(tmp_path, files=None):
    f = tmp_path / "bound.txt"
    f.write_text("bound", encoding="utf-8", newline="\n")
    man = {"files": {"g": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()} | (files or {})}}
    p = tmp_path / "BINDING.json"
    p.write_text(json.dumps(man), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest(), f


def _run_set(tmp_path, ids=("F045", "F051", "F066")):
    import inputs_r32 as I
    import labels_adapter_r32 as A

    x = I.load_all()
    T = A.build_truth(x["reviewed2"], renders=x["renders"], source_manifest=x["source_manifest"], selection=x["selection"], verification=x["verification"])
    rs = {"documents": [{"pool_id": p, "doc_key": T["documents"][p]["doc_key"], "ep": T["documents"][p]["ep"]} for p in ids]}
    p = tmp_path / "RUN-SET.json"
    p.write_text(json.dumps(rs), encoding="utf-8", newline="\n")
    return p, T


def test_a_wrong_binding_hash_refuses(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="binding manifest"):
        RN.main(["--mode", "dry", "--stamp", _stamp(), "--run-set", str(rs), "--binding", str(b), "--binding-sha", "0" * 64, "--out", str(tmp_path / "o")])


def test_a_changed_bound_file_refuses(tmp_path):
    b, sha, f = _binding(tmp_path)
    f.write_text("changed", encoding="utf-8", newline="\n")
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="bound file"):
        RN.main(["--mode", "dry", "--stamp", _stamp(), "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha, "--out", str(tmp_path / "o")])


def test_live_mode_without_the_declaration_or_the_authorization_refuses(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    with pytest.raises(RN.Refused, match="declaration"):
        RN.main(["--mode", "live", "--stamp", _stamp(), "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha, "--out", str(tmp_path / "o1")])
    decl = tmp_path / "DECL.json"
    decl.write_text(json.dumps({"binding_manifest_sha256": sha, "run_set_sha256": hashlib.sha256(rs.read_bytes()).hexdigest()}), encoding="utf-8", newline="\n")
    dsha = hashlib.sha256(decl.read_bytes()).hexdigest()
    with pytest.raises(RN.Refused, match="no owner dispatch authorization"):
        RN.main(["--mode", "live", "--stamp", _stamp(), "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha, "--declaration", str(decl),
                 "--declaration-sha", dsha, "--auth-path", str(tmp_path / "missing-auth.json"), "--out", str(tmp_path / "o2")])
    report = json.loads((tmp_path / "o2" / "RUN-REPORT.json").read_text(encoding="utf-8"))
    assert report["model_requests"] == 0 and report["ledger_unchanged"] and "lanes" not in report


def test_folders_are_never_reused(tmp_path):
    """A run never reuses its sandbox or out folder (the WRITER.lock created with O_EXCL is defence in depth)."""
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    stamp = _stamp()
    (RN.SANDBOX_BASE / stamp).mkdir(parents=True)
    with pytest.raises(RN.Refused, match="never reuses"):
        RN.main(["--mode", "dry", "--stamp", stamp, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha, "--out", str(tmp_path / "o3")])


def test_the_dry_pipeline_on_the_reference_set_reads_no_document_and_sends_nothing(tmp_path):
    b, sha, _ = _binding(tmp_path)
    rs, _ = _run_set(tmp_path)
    out = tmp_path / "dry"
    assert RN.main(["--mode", "dry", "--stamp", _stamp(), "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha, "--out", str(out),
                    "--resume-drill"]) == 0
    r = json.loads((out / "RUN-REPORT.json").read_text(encoding="utf-8"))
    assert r["model_requests"] == 0 and r["ledger_unchanged"] and r["dispatch_guard"]["authorized"] is False
    assert all(v["reader"] == "none" and not v["live_provider_attempts_blocked"] for v in r["lanes"].values())
    assert r["lanes"]["B"]["application_processing_run"] is False and r["lanes"]["C"]["application_reader_run"] is False
    assert r["state_check_C"]["ok"] and r["state_check_R"]["ok"] and r["resume_drill"]["passes"]
    assert r["store"]["reference_serves"] == 3 and r["store"]["duplicate_bound_keys"] == []
    rows = json.loads((out / "rows-B.json").read_text(encoding="utf-8"))
    assert all(v["state"] == "pending" and v["extracted"] is None for v in rows.values()), "no cohort document was read"


def _synthetic(tmp_path, truth_spec):
    files = tmp_path / "syn-files"
    T = SY.build(files, truth_spec)
    out = tmp_path / "syn-out"
    out.mkdir()
    tp = out / "TRUTH.json"
    tp.write_text(json.dumps(T), encoding="utf-8", newline="\n")
    sbx = RN.SANDBOX_BASE / _stamp()
    sbx.mkdir(parents=True)
    rs = [{"pool_id": p, "doc_key": d["doc_key"], "ep": d["ep"]} for p, d in T["documents"].items()]
    cfg = {"mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(tp), "run_set": rs,
           "store": str(sbx / "capture.sqlite"), "allowance": str(sbx / "allowance.sqlite"), "caps": RN.CAPS, "trees": RN.TREES,
           "sandbox": {k: str(sbx / k) for k in "BCR"}, "declaration_sha256": None, "auth_path": str(tmp_path / "no-auth.json"),
           "policies": {"B": "B:accepted-path:evidence-off"}}
    return T, cfg, rs, out, sbx, files


SHEET = ["SHOP DRAWING", "DRAWING NO: SYN-0001", "REV: 00", "TITLE: SYNTHETIC TEST SHEET ONE"]
FORM = ["MATERIAL SUBMITTAL", "SUBMITTAL NO: SYN-MAT-002", "REVISION: 01", "APPROVED AS NOTED"]
NS = ("not_scorable", None)


def test_application_path_on_synthetic_documents_b_then_c_from_b_then_r_and_resume(tmp_path):
    T, cfg, rs, out, sbx, files = _synthetic(tmp_path, [
        {"pool_id": "SYN001", "lines": SHEET, "truth": {"identity": NS, "revision": NS, "decision": NS}},
        {"pool_id": "SYN002", "lines": FORM, "truth": {"identity": ("value", "SYN-MAT-002"), "revision": ("value", "01"), "decision": ("absent", None)}}])
    rep = RN.execute(cfg, T, rs, out, sbx, stage_files=files, resume_drill_flag=True)
    assert rep["lanes"]["B"]["application_processing_run"] is True and rep["lanes"]["C"]["application_reader_run"] is True
    assert rep["model_requests"] == 0 and all(not v["live_provider_attempts_blocked"] for v in rep["lanes"].values())
    lb = json.loads((out / "LANE-B.json").read_text(encoding="utf-8"))
    assert {t["when"] for t in lb["tripwire"]} >= {"after_document", "final"}
    assert rep["stop_controller"]["comparison"] == "PENDING" and rep["state_check_C"]["ok"] and rep["resume_drill"]["passes"]
    assert "SCORE-BCR-R32.json" in {p.name for p in out.iterdir()}


def test_the_b_tripwire_stops_b_and_c_never_starts(tmp_path):
    T, cfg, rs, out, sbx, files = _synthetic(tmp_path, [
        {"pool_id": "SYN002", "lines": FORM, "truth": {"identity": ("value", "SYN-MAT-999"), "revision": NS, "decision": NS}}])
    rep = RN.execute(cfg, T, rs, out, sbx, stage_files=files)
    assert rep["stop_controller"]["comparison"].startswith("INVALID") and rep["C_not_started"].startswith("INVALID")
    assert "C" not in rep["lanes"] and rep["model_requests"] == 0
    lb = json.loads((out / "LANE-B.json").read_text(encoding="utf-8"))
    hit = [c for t in lb["tripwire"] for c in t["resolved"]]
    assert hit and hit[0]["pool_id"] == "SYN002" and hit[0]["field"] == "identity"


def test_dry_mode_refuses_to_run_a_reader_on_a_cohort_document(tmp_path):
    rsp, T = _run_set(tmp_path, ("F045",))
    out = tmp_path / "coh"
    out.mkdir()
    tp = out / "TRUTH.json"
    tp.write_text(json.dumps(T), encoding="utf-8", newline="\n")
    sbx = RN.SANDBOX_BASE / _stamp()
    sbx.mkdir(parents=True)
    rs = json.loads(rsp.read_text(encoding="utf-8"))["documents"]
    cfg = {"mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(tp), "run_set": rs,
           "store": str(sbx / "capture.sqlite"), "allowance": str(sbx / "allowance.sqlite"), "caps": RN.CAPS, "trees": RN.TREES,
           "sandbox": {k: str(sbx / k) for k in "BCR"}, "declaration_sha256": None, "auth_path": str(tmp_path / "no-auth.json"),
           "policies": {"B": "B:accepted-path:evidence-off"}}
    with pytest.raises(RuntimeError, match="lane B failed"):
        RN.execute(cfg, T, rs, out, sbx)
    assert "never runs a reader on a cohort document" in (out / "lane-B.log").read_text(encoding="utf-8")
