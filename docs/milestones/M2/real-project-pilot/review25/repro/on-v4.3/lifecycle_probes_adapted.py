"""Runner lifecycle probes (review 23, R23-01) through the ACTUAL runner (arm_ev.py v4.1) with the scripted provider, in
isolated dry roots under C:/t/r2x/dry-runs/r23-lifecycle/<scenario>. Each root holds a private copy of the synthetic A
baseline, a private copy of the synthetic labels made to DISAGREE with the scripted answer (X-DRY-1 -> X-DRY-9, the
reviewer's device) for the chosen projects, and a privately rebound declaration; nothing else is touched. No model call.
  T1 critical stop with pending work, then plain --resume: zero sends, the original stop and evidence preserved
  T2 a second plain --resume of the same stopped run: still zero sends, unchanged reason / evidence
  T3 terminal stop after the LAST project: stays `stopped` on resume, never relabelled `completed`
  T4 three consecutive scripted provider failures: a terminal stop; --resume cannot clear it;
     T4b one scripted failure then normal answers: NOT terminal (the run completes; a resume is ordinary)
  T5 interruption at the persistence boundary: (a) killed after the stop was decided but BEFORE the stop file was
     written -> recovery reconstructs the stop offline from the saved evidence and refuses before any dispatch;
     (b) killed AFTER the stop file, before the manifest update -> recovery refuses on the file
  T6 positive controls are the eight R22 runner scenarios rerun with the v4.1 runner (runner_probes.py): daily deferral
     resumes when eligible (S7) and kill/resume uses only the remaining durable allowance (S2)
Writes lifecycle-evidence/LIFECYCLE.json (+ per-scenario logs)."""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PY = sys.executable
CANON = pathlib.Path("C:/t/r2x/dry-runs/r22")
ROOTS = pathlib.Path(os.environ.get("R23_LIFECYCLE_ROOT", "C:/t/r2x/dry-runs/r24-lifecycle"))
OUT = HERE / "lifecycle-evidence"
DECL0 = json.loads((CANON / "R22-DECLARATION.dry.json").read_text(encoding="utf-8"))
BASE_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PILOT_DRY": "1", "PILOT_DRY_MODE": "coherent", "TEMP": os.environ["TEMP"], "TMP": os.environ["TMP"]}
for k in list(BASE_ENV):
    if k.startswith("AI_EVIDENCE_") or k in ("XTRACK_FAKE_NOW", "PILOT_DRY_KILL_AFTER", "PILOT_DRY_LATENCY_S", "PILOT_DRY_NEW_TAG_OVERRIDE", "PILOT_DRY_FAIL_FROM", "PILOT_DRY_FAIL_COUNT", "PILOT_DRY_FAIL_AT", "PILOT_DRY_KILL_AT_STOP"):
        BASE_ENV.pop(k)


def changed(value, eps):
    """The reviewer's device: the synthetic expected identity disagrees with the scripted answer, for the given projects."""
    if isinstance(value, dict):
        ep = value.get("ep") or (str(value.get("doc", "")).split("/")[0][3:] if str(value.get("doc", "")).startswith("EP-") else None)
        if ep and ep not in eps:
            return value
        return {k: changed(v, eps) for k, v in value.items()}
    if isinstance(value, list):
        return [changed(v, eps) for v in value]
    return value.replace("X-DRY-1", "X-DRY-9") if isinstance(value, str) else value


def make_root(name: str, disagree_eps) -> tuple[pathlib.Path, pathlib.Path, str]:
    root = ROOTS / name
    assert root.resolve().is_relative_to(ROOTS.resolve())
    assert not root.exists(), "independent scenario must be new; no deletion"
    (root / "labels").mkdir(parents=True)
    (root / "runs").mkdir()
    (root / "logs").mkdir()
    d = json.loads(json.dumps(DECL0))
    home = pathlib.Path(d["harness_dir"]) / d["labels"]["dir"]
    for n in d["labels"]["files"]:
        payload = json.loads((home / n).read_text(encoding="utf-8"))
        if n in (d["labels"]["register"], d["labels"]["page"]):
            if n == d["labels"]["page"]:
                payload = {**payload, "documents": {k: (changed(v, disagree_eps) if k.split("/")[0][3:] in disagree_eps else v) for k, v in payload["documents"].items()}}
            else:
                payload = changed(payload, disagree_eps)
        (root / "labels" / n).write_text(json.dumps(payload), encoding="utf-8")
        d["labels"]["files"][n] = hashlib.sha256((root / "labels" / n).read_bytes()).hexdigest()
    d["harness_dir"], d["labels"]["dir"] = root.as_posix(), "labels"
    decl = root / "DECLARATION.json"
    decl.write_text(json.dumps(d, indent=1), encoding="utf-8")
    digest = hashlib.sha256(decl.read_bytes()).hexdigest()
    shutil.copytree(CANON / "runs/r22dry-A", root / "runs/r22dry-A")
    a_file = root / "runs/r22dry-A/out/RUN.json"
    a = json.loads(a_file.read_text(encoding="utf-8"))
    a["declaration_sha256"] = digest
    a_file.write_text(json.dumps(a), encoding="utf-8")
    return root, decl, digest


def run(root, decl, digest, args, *, env=None, name="run"):
    e = {**BASE_ENV, "PILOT_DRY_ROOT": root.as_posix(), **(env or {})}
    cmd = [PY, str(HERE / "arm_ev.py"), "r22dry-A", "L1", "L1", *args, "--declaration", str(decl), "--declaration-sha", digest]
    with open(root / "logs" / f"{name}.log", "w", encoding="utf-8") as log:
        p = subprocess.run(cmd, env=e, stdout=log, stderr=subprocess.STDOUT, cwd=str(HERE), timeout=600)
    text = (root / "logs" / f"{name}.log").read_text(encoding="utf-8", errors="replace")
    return {"exit": p.returncode, "tail": text.strip().splitlines()[-2:], "printed": next((l for l in text.splitlines() if l.startswith(("STOPPED", "REFUSED"))), None)}


def snapshot(root):
    m = json.loads((root / "runs/L1/out/RUN.json").read_text(encoding="utf-8"))
    stop = root / "runs/L1/out/TERMINAL-STOP.json"
    io = root / "runs/L1/out/io.jsonl"
    sends = [json.loads(l) for l in io.read_text(encoding="utf-8").splitlines()] if io.exists() else []
    return {"status": m.get("status"), "stopped": m["runner_state"]["stopped"], "requests_this_invocation": m["runner_state"]["per_ep"], "projects": list(m["projects"]),
            "not_attempted": m["not_attempted"], "deferred": m.get("deferred"), "tripwire_errors": [len(t["critical_on_resolved"]) for t in m["tripwire"]],
            "terminal_stop": m.get("terminal_stop"), "stop_file": json.loads(stop.read_text(encoding="utf-8")) if stop.exists() else None,
            "resumes": m.get("resumes"), "sends_total_recorded": len(sends), "sends_by_pid": {str(x["pid"]): sum(1 for y in sends if y["pid"] == x["pid"]) for x in sends},
            "declaration_sha256": m["declaration_sha256"], "arm": m["arm"], "tag": m["tag"], "allowance_key": m["allowance_key"]}


def refusals(root):
    f = root / "runs/refusals/REFUSALS.jsonl"
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []


R = {"lifecycle_contract": "runner-lifecycle-2026-10-01.v1", "scenarios": {}}
same_stop = lambda a, b: a and b and (a["reason"], a["kind"], a["evidence"], a["at_utc"], a["pid"]) == (b["reason"], b["kind"], b["evidence"], b["at_utc"], b["pid"])

# T1 / T2 ----------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("t1-critical-stop-resume", {"16830", "17428"})
r0 = run(root, decl, dg, [], name="initial")
s0 = snapshot(root)
r1 = run(root, decl, dg, ["--resume"], name="resume-1")
s1 = snapshot(root)
r2 = run(root, decl, dg, ["--resume"], name="resume-2")
s2 = snapshot(root)
R["scenarios"]["T1_critical_stop_then_plain_resume"] = {
    "initial": {"run": r0, **{k: s0[k] for k in ("status", "stopped", "requests_this_invocation", "projects", "not_attempted", "tripwire_errors", "sends_total_recorded")}, "stop_file": s0["stop_file"]},
    "resume": {"run": r1, **{k: s1[k] for k in ("status", "stopped", "requests_this_invocation", "projects", "not_attempted", "tripwire_errors", "sends_total_recorded", "resumes")}},
    "checks": {"initial_stopped_with_pending_work": s0["status"] == "stopped" and s0["tripwire_errors"] == [1] and [x["ep"] for x in s0["not_attempted"]] == ["17428"] and s0["stop_file"] is not None and s0["stop_file"]["kind"] == "critical_acceptance",
               "resume_zero_sends": sum(s1["requests_this_invocation"].values()) == 0 and s1["sends_total_recorded"] == s0["sends_total_recorded"],
               "resume_exit_4_and_refusal_recorded": r1["exit"] == 4 and any(x.get("resume") and x["requests_sent"] == 0 and "terminal stop preserved" in x["refused"] for x in refusals(root)),
               "stop_reason_and_evidence_preserved": s1["stopped"] == s0["stopped"] and same_stop(s1["stop_file"], s0["stop_file"]) and same_stop(s1["terminal_stop"], s0["stop_file"]),
               "lists_consistent": s1["projects"] == s0["projects"] and s1["not_attempted"] == s0["not_attempted"] and s1["tripwire_errors"] == s0["tripwire_errors"] and s1["status"] == "stopped",
               "same_binding": (s0["declaration_sha256"], s0["arm"], s0["tag"], s0["allowance_key"]) == (s1["declaration_sha256"], s1["arm"], s1["tag"], s1["allowance_key"])}}
R["scenarios"]["T2_repeated_resume"] = {"run": r2, **{k: s2[k] for k in ("status", "stopped", "requests_this_invocation", "sends_total_recorded", "resumes")},
                                        "checks": {"still_zero_sends": r2["exit"] == 4 and sum(s2["requests_this_invocation"].values()) == 0 and s2["sends_total_recorded"] == s0["sends_total_recorded"],
                                                   "unchanged_reason_and_evidence": s2["stopped"] == s0["stopped"] and same_stop(s2["stop_file"], s0["stop_file"]),
                                                   "two_refusals_recorded": len([x for x in refusals(root) if x.get("resume")]) == 2}}

# T3 ------------------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("t3-stop-after-last-project", {"17428"})
r0 = run(root, decl, dg, [], name="initial")
s0 = snapshot(root)
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
R["scenarios"]["T3_terminal_stop_no_remaining_project"] = {
    "initial": {"run": r0, **{k: s0[k] for k in ("status", "stopped", "requests_this_invocation", "projects", "not_attempted", "tripwire_errors")}},
    "resume": {"run": r1, **{k: s1[k] for k in ("status", "stopped", "requests_this_invocation", "projects", "not_attempted", "sends_total_recorded")}},
    "checks": {"stopped_after_last_project": s0["status"] == "stopped" and s0["projects"] == ["16830", "17428"] and s0["not_attempted"] == [] and s0["tripwire_errors"][-1] >= 1,
               "resume_stays_stopped_never_completed": r1["exit"] == 4 and s1["status"] == "stopped" and s1["stopped"] == s0["stopped"] and sum(s1["requests_this_invocation"].values()) == 0 and s1["sends_total_recorded"] == s0["sends_total_recorded"]}}

# T4 / T4b ----------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("t4-provider-failures", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "1"}, name="initial-failing-provider")
s0 = snapshot(root)
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
R["scenarios"]["T4_three_consecutive_provider_failures"] = {
    "initial": {"run": r0, **{k: s0[k] for k in ("status", "stopped", "requests_this_invocation", "projects", "not_attempted")}, "stop_file": s0["stop_file"]},
    "resume": {"run": r1, **{k: s1[k] for k in ("status", "stopped", "requests_this_invocation", "sends_total_recorded")}},
    "checks": {"terminal_failure_stop_persisted": s0["status"] == "stopped" and s0["stop_file"] is not None and s0["stop_file"]["kind"] == "provider_failures" and len(s0["stop_file"]["evidence"]) == 3
               and all(e["outcome"] == "transport" for e in s0["stop_file"]["evidence"]),
               "remaining_project_not_attempted": [x["ep"] for x in s0["not_attempted"]] == ["17428"],
               "resume_cannot_clear_it": r1["exit"] == 4 and sum(s1["requests_this_invocation"].values()) == 0 and s1["stopped"] == s0["stopped"] and s1["status"] == "stopped"}}
root, decl, dg = make_root("t4b-single-failure", set())
r0 = run(root, decl, dg, [], env={"PILOT_DRY_FAIL_FROM": "2", "PILOT_DRY_FAIL_COUNT": "1"}, name="initial-one-failure")
s0 = snapshot(root)
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
R["scenarios"]["T4b_single_failed_request_is_not_terminal"] = {
    "initial": {"run": r0, **{k: s0[k] for k in ("status", "stopped", "requests_this_invocation", "projects")}, "stop_file": s0["stop_file"]},
    "resume": {"run": r1, **{k: s1[k] for k in ("status", "stopped", "requests_this_invocation")}},
    "checks": {"one_failure_no_stop": s0["status"] == "completed" and s0["stopped"] is None and s0["stop_file"] is None and s0["projects"] == ["16830", "17428"],
               "ordinary_resume_not_refused": r1["exit"] == 0 and s1["status"] == "completed" and not any(x.get("resume") for x in refusals(root))}}

# T5a / T5b ---------------------------------------------------------------------------------------------------------------
root, decl, dg = make_root("t5a-kill-before-stop-file", {"16830", "17428"})
r0 = run(root, decl, dg, [], env={"PILOT_DRY_KILL_AT_STOP": "before_file"}, name="initial-killed-before-file")
stop_after_kill = (root / "runs/L1/out/TERMINAL-STOP.json").exists()
m_after_kill = json.loads((root / "runs/L1/out/RUN.json").read_text(encoding="utf-8"))
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
R["scenarios"]["T5a_killed_before_stop_persisted"] = {
    "killed": {"run": r0, "exit_98_expected": r0["exit"] == 98, "stop_file_after_kill": stop_after_kill, "manifest_knows_stop_after_kill": bool(m_after_kill.get("terminal_stop") or m_after_kill["runner_state"].get("stopped")),
               "manifest_projects_after_kill": list(m_after_kill["projects"])},
    "resume": {"run": r1, **{k: s1[k] for k in ("status", "stopped", "requests_this_invocation", "sends_total_recorded", "projects", "not_attempted")}, "stop_file": s1["stop_file"]},
    "checks": {"state_was_indeterminate": not stop_after_kill and not (m_after_kill.get("terminal_stop") or m_after_kill["runner_state"].get("stopped")),
               "recovery_reconstructed_offline_and_refused": r1["exit"] == 4 and s1["stop_file"] is not None and s1["stop_file"]["reconstructed"] is True and s1["stop_file"]["kind"] == "critical_acceptance"
               and len(s1["stop_file"]["evidence"]) >= 1 and sum(s1["requests_this_invocation"].values()) == 0 and s1["status"] == "stopped",
               "no_dispatch_on_recovery": s1["sends_total_recorded"] == 12}}
root, decl, dg = make_root("t5b-kill-after-stop-file", {"16830", "17428"})
r0 = run(root, decl, dg, [], env={"PILOT_DRY_KILL_AT_STOP": "after_file"}, name="initial-killed-after-file")
stop_after_kill = json.loads((root / "runs/L1/out/TERMINAL-STOP.json").read_text(encoding="utf-8")) if (root / "runs/L1/out/TERMINAL-STOP.json").exists() else None
m_after_kill = json.loads((root / "runs/L1/out/RUN.json").read_text(encoding="utf-8"))
r1 = run(root, decl, dg, ["--resume"], name="resume")
s1 = snapshot(root)
R["scenarios"]["T5b_killed_after_stop_file_before_manifest"] = {
    "killed": {"run": r0, "exit_98_expected": r0["exit"] == 98, "stop_file_after_kill": stop_after_kill is not None, "manifest_knows_stop_after_kill": bool(m_after_kill.get("terminal_stop") or m_after_kill["runner_state"].get("stopped"))},
    "resume": {"run": r1, **{k: s1[k] for k in ("status", "stopped", "requests_this_invocation", "sends_total_recorded")}, "stop_file": s1["stop_file"]},
    "checks": {"file_written_manifest_not": stop_after_kill is not None and not (m_after_kill.get("terminal_stop") or m_after_kill["runner_state"].get("stopped")),
               "recovery_refused_on_file": r1["exit"] == 4 and same_stop(s1["stop_file"], stop_after_kill) and s1["stopped"] == stop_after_kill["reason"] and sum(s1["requests_this_invocation"].values()) == 0 and s1["status"] == "stopped",
               "no_dispatch_on_recovery": s1["sends_total_recorded"] == 12}}

OUT.mkdir(exist_ok=True)
(OUT / "LIFECYCLE.json").write_text(json.dumps(R, indent=1, default=str) + "\n", encoding="utf-8")
for n, s in R["scenarios"].items():
    print(n, s["checks"])
