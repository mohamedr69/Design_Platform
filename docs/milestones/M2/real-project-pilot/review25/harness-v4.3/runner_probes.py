"""Runner integration probes (review 22, R22-03): the ACTUAL document-arm runner (arm_ev.py) under the scripted provider
(dry_provider2, coherent answers) and a fake clock, each scenario in its own isolated dry root (runs, ledger, rolling
counter, allowance). No provider / model request anywhere. Writes runner-evidence/RUNNER-INTEGRATION.json (+ per-scenario logs).
Scenarios:
  S1 baseline        L1 over the synthetic stage: charged == sent per document; the no-trigger control sends nothing
  S2 kill_resume     L3 killed by the provider after the 8th dispatched request (charged, result lost); --resume: the
                     interrupted attempt is visible, the lost request stays charged, the document's attempted sends exceed
                     12 and the durable cap holds at 12 across the restart; completed documents are skipped
  S3 new_tag         after S2: a NEW tag for the same arm is refused before dispatch; with the DRY override the durable
                     cap still holds (the capped document sends nothing more)
  S4 second_writer   a slow L1 holds the sandbox: a concurrent --resume is refused; the document key lock is busy
  S5 cache_hit       --resume --reread over a completed L1: only cache hits, nothing charged, counter unchanged
  S6 scope_exhaust   a declaration variant with the arm's ledger cap at 10: 10 sent, then budget stops; counter == 10
  S7 deferral        the rolling counter seeded with 50 other-track requests for EP-16830 at T0: the project is deferred
                     (zero requests), EP-17428 runs; at T0 + 24 h + 1 s --resume runs EP-16830 without resetting totals
  S8 refusals        --resume of a non-existent sandbox and a repeat without --resume are refused before dispatch
"""
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
PY = sys.executable
CANON = pathlib.Path("C:/t/r2x/dry-runs/r22")
PROBES = pathlib.Path(os.environ.get("R22_PROBES_ROOT", "C:/t/r2x/dry-runs/r25-probes"))
OUT = HERE.parent / "runner-evidence"
DECL = CANON / "R22-DECLARATION.dry.json"
DECL_SHA = (CANON / "DECL.sha").read_text().strip()
assert hashlib.sha256(DECL.read_bytes()).hexdigest() == DECL_SHA
decl = json.loads(DECL.read_text(encoding="utf-8"))
SHA_OF = {p["doc"].split("/")[-1]: p["sha256"] for p in decl["sources"]["sample"]["documents_planned"]}
SIX, ONE, TWO, TXT = SHA_OF["raster-6pages.pdf"], SHA_OF["raster-1page.pdf"], SHA_OF["raster-2pages.pdf"], SHA_OF["text-sheet.pdf"]
CAP = decl["application_limits"]["ai_max_calls_per_document"]
BASE_ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PILOT_DRY": "1", "PILOT_DRY_MODE": "coherent", "TEMP": "C:/t/iso/tmp", "TMP": "C:/t/iso/tmp"}
for k in list(BASE_ENV):
    if k.startswith("AI_EVIDENCE_") or k in ("XTRACK_FAKE_NOW", "PILOT_DRY_KILL_AFTER", "PILOT_DRY_LATENCY_S", "PILOT_DRY_NEW_TAG_OVERRIDE", "PILOT_DRY_FAIL_FROM", "PILOT_DRY_FAIL_COUNT", "PILOT_DRY_FAIL_AT", "PILOT_DRY_KILL_AT_STOP"):
        BASE_ENV.pop(k)


def fresh_root(name: str, *, a_from=CANON / "runs/r22dry-A") -> pathlib.Path:
    root = PROBES / name
    if root.exists():
        shutil.rmtree(root)
    (root / "runs").mkdir(parents=True)
    shutil.copytree(a_from, root / "runs/r22dry-A")
    (root / "logs").mkdir()
    return root


def run(root, args, *, env=None, name="run", timeout=600, decl_path=DECL, decl_sha=DECL_SHA, background=False):
    e = {**BASE_ENV, "PILOT_DRY_ROOT": root.as_posix(), **(env or {})}
    cmd = [PY, str(HERE / "arm_ev.py"), *args, "--declaration", str(decl_path), "--declaration-sha", decl_sha]
    log = open(root / "logs" / f"{name}.log", "w", encoding="utf-8")
    p = subprocess.Popen(cmd, env=e, stdout=log, stderr=subprocess.STDOUT, cwd=str(HERE))
    if background:
        return p
    p.wait(timeout=timeout)
    log.close()
    text = (root / "logs" / f"{name}.log").read_text(encoding="utf-8", errors="replace")
    return {"exit": p.returncode, "cmd": " ".join(cmd[1:3] + cmd[3:6]), "tail": text.strip().splitlines()[-3:], "refused": next((l for l in text.splitlines() if l.startswith("REFUSED")), None)}


def run_json(root, tag):
    return json.loads((root / "runs" / tag / "out/RUN.json").read_text(encoding="utf-8"))


def allowance(root, scope, profile):
    con = sqlite3.connect(str(root / "dry-allowance.sqlite"))
    out = {}
    for sha, calls in con.execute("select sha256, calls from allowance where scope = ? and profile = ?", (scope, profile)):
        out[sha] = {"charged": calls, "attempts": [s for (s,) in con.execute("select status from attempts where scope = ? and profile = ? and sha256 = ? order by id", (scope, profile, sha))]}
    con.close()
    return out


def xtrack_used(root, ep, at=None):
    con = sqlite3.connect(str(root / "dry-project-day.sqlite"))
    n = con.execute("select count(*) from calls where ep = ? and at >= ?", (ep, (at or time.time()) - 86400)).fetchone()[0]
    con.close()
    return n


def io_by_doc(root, tag, pid=None):
    f = root / "runs" / tag / "out/io.jsonl"
    out = {}
    if f.exists():
        for l in f.read_text(encoding="utf-8").splitlines():
            x = json.loads(l)
            if pid is None or x["pid"] == pid:
                out[x["sha256"]] = out.get(x["sha256"], 0) + 1
    return out


def progress(root, tag):
    f = root / "runs" / tag / "out/progress.jsonl"
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []


def refusals(root):
    f = root / "runs/refusals/REFUSALS.jsonl"
    return [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines()] if f.exists() else []


def key(arm):
    return decl["ledger"]["scopes"][arm]["scope"], f"{arm}|default|{decl['arms'][arm]['identities']['EVIDENCE_POLICY_VERSION']}"


R = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "declaration_sha256": DECL_SHA, "stage": decl["stage"], "cap_per_document": CAP, "scenarios": {}}

# S1 baseline -------------------------------------------------------------------------------------------------------------
root = fresh_root("s1-baseline")
r1 = run(root, ["r22dry-A", "L1", "L1"], name="L1")
m = run_json(root, "L1")
al = allowance(root, *key("L1"))
io = io_by_doc(root, "L1")
R["scenarios"]["S1_baseline"] = {"run": r1, "status": m["status"], "requests": m["runner_state"]["per_ep"], "cache_hits": m["runner_state"]["cache_hits"],
                                 "charged": {k[-20:]: v["charged"] for k, v in al.items()}, "sent": {k[-20:]: v for k, v in io.items()},
                                 "charged_equals_sent": all(al[s]["charged"] == io.get(s, 0) for s in al), "no_trigger_control_sent": io.get(TXT, 0),
                                 "worst_case_reserved": {ep: v["worst_case_reserved"] for ep, v in m["projects"].items()}, "capacity_before": {ep: v["capacity_before"] for ep, v in m["projects"].items()},
                                 "counter_used": {ep: xtrack_used(root, ep) for ep in ("16830", "17428")}, "tripwire_binding": m["tripwire"]}

# S2 kill / resume ------------------------------------------------------------------------------------------------------------
root = fresh_root("s2-kill-resume")
k = run(root, ["r22dry-A", "L3", "L3"], env={"PILOT_DRY_KILL_AFTER": "8"}, name="L3-killed")
al_k = allowance(root, *key("L3"))
io_k = io_by_doc(root, "L3")
prog_k = progress(root, "L3")
open_attempt = [p for p in prog_k if p["event"] == "document_start" and not any(q["event"] == "document_end" and q.get("attempt_id") == p["attempt_id"] for q in prog_k)]
res = run(root, ["r22dry-A", "L3", "L3", "--resume"], name="L3-resumed")
m = run_json(root, "L3")
al_r = allowance(root, *key("L3"))
io_r = io_by_doc(root, "L3")
R["scenarios"]["S2_kill_resume"] = {
    "killed": {"run": k, "exit_97_expected": k["exit"] == 97, "charged_at_kill": {s[:8]: v["charged"] for s, v in al_k.items()}, "sent_recorded_at_kill": {s[:8]: n for s, n in io_k.items()},
               "lost_request_charged": al_k.get(SIX, {}).get("charged", 0) == io_k.get(SIX, 0) + 1, "open_attempt_visible_after_kill": [p["sha256"][:8] for p in open_attempt],
               "attempt_statuses_at_kill": {s[:8]: v["attempts"] for s, v in al_k.items()}},
    "resumed": {"run": res, "status": m["status"], "interrupted_seen": m["runner_state"]["interrupted_seen"], "skipped_completed": [s[:8] for s in m["runner_state"]["skipped_completed"]],
                "charged_final": {s[:8]: v["charged"] for s, v in al_r.items()}, "attempt_statuses": {s[:8]: v["attempts"] for s, v in al_r.items()},
                "sent_total_by_doc": {s[:8]: n for s, n in io_r.items()}, "allowance_refusals_in_resume": m["runner_state"]["allowance_refusals"],
                "six_page_doc": {"charged": al_r[SIX]["charged"], "sent_recorded": io_r.get(SIX, 0), "cap": CAP, "capped_at_12": al_r[SIX]["charged"] == CAP,
                                 "attempted_beyond_cap": m["runner_state"]["allowance_refusals"] > 0, "sent_plus_lost_equals_charged": io_r.get(SIX, 0) + 1 == al_r[SIX]["charged"]},
                "one_page_doc_not_resent": io_r.get(ONE, 0) == io_k.get(ONE, 0) and al_r[ONE]["charged"] == al_k[ONE]["charged"], "resumes": m.get("resumes")}}

# S3 new tag (same root as S2) ---------------------------------------------------------------------------------------------------
nt = run(root, ["r22dry-A", "L3-newtag", "L3"], name="L3-newtag-refused")
al_nt = allowance(root, *key("L3"))
six_before_override = al_nt[SIX]["charged"]
ov = run(root, ["r22dry-A", "L3-newtag2", "L3"], env={"PILOT_DRY_NEW_TAG_OVERRIDE": "1"}, name="L3-newtag-override")
m2 = run_json(root, "L3-newtag2")
al_ov = allowance(root, *key("L3"))
io_ov = io_by_doc(root, "L3-newtag2")
R["scenarios"]["S3_new_tag"] = {"refused": {"run": nt, "refused_before_dispatch": nt["exit"] != 0 and bool(nt["refused"]), "charged_unchanged": al_nt == al_r, "sandbox_created": (root / "runs/L3-newtag").exists()},
                                "override_dry_only": {"run": ov, "status": m2["status"], "six_page_doc_sent": io_ov.get(SIX, 0), "six_page_doc_charged": al_ov[SIX]["charged"],
                                                      "six_page_doc_charged_before_override": six_before_override,
                                                      "cap_holds_across_tags": al_ov[SIX]["charged"] <= CAP and io_ov.get(SIX, 0) == CAP - six_before_override,
                                                      "other_docs_charged_total": {s[:8]: v["charged"] for s, v in al_ov.items()}, "all_within_cap": all(v["charged"] <= CAP for v in al_ov.values()),
                                                      "allowance_refusals": m2["runner_state"]["allowance_refusals"]},
                                "refusal_records": refusals(root)}

# S4 second writer ---------------------------------------------------------------------------------------------------------------
root = fresh_root("s4-second-writer")
slow = run(root, ["r22dry-A", "L1", "L1"], env={"PILOT_DRY_LATENCY_S": "0.6"}, name="L1-slow", background=True)
busy_doc, deadline = None, time.time() + 60
while time.time() < deadline and busy_doc is None:
    pr = progress(root, "L1")
    starts = [p for p in pr if p["event"] == "document_start"]
    ends = {p.get("attempt_id") for p in pr if p["event"] == "document_end"}
    open_ = [p for p in starts if p["attempt_id"] not in ends]
    if open_:
        busy_doc = open_[-1]["sha256"]
    else:
        time.sleep(0.2)
second = run(root, ["r22dry-A", "L1", "L1", "--resume"], name="L1-second-writer")
sys.path.insert(0, "C:/t/iso/work/r2x/r16")
from boq_harness import AllowanceBusy, DocAllowance  # noqa: E402
lock_busy = None
if busy_doc:
    try:
        fh = DocAllowance(str(root / "dry-allowance.sqlite")).acquire(*key("L1"), busy_doc)
        lock_busy = False
        from boq_harness import _unlock_file
        _unlock_file(fh)
    except AllowanceBusy:
        lock_busy = True
slow.wait(timeout=600)
m = run_json(root, "L1")
R["scenarios"]["S4_second_writer"] = {"slow_writer_exit": slow.returncode, "slow_writer_status": m["status"], "slow_writer_requests": sum(m["runner_state"]["per_ep"].values()),
                                      "second_writer": second, "second_refused_before_dispatch": second["exit"] != 0 and "another writer" in (second["refused"] or ""),
                                      "document_lock_probe": {"doc": (busy_doc or "")[:8], "busy_while_held": lock_busy}, "refusal_records": refusals(root)}

# S5 cache hit -----------------------------------------------------------------------------------------------------------------
root = fresh_root("s5-cache-hit")
first = run(root, ["r22dry-A", "L1", "L1"], name="L1")
shutil.copyfile(root / "runs/L1/out/RUN.json", root / "runs/L1/out/RUN.json.first")
al_1 = allowance(root, *key("L1"))
used_1 = {ep: xtrack_used(root, ep) for ep in ("16830", "17428")}
io_1 = io_by_doc(root, "L1")
re = run(root, ["r22dry-A", "L1", "L1", "--resume", "--reread"], name="L1-reread")
m = run_json(root, "L1")
pid2 = m["resumes"][-1]["pid"]
al_2 = allowance(root, *key("L1"))
first_state = json.loads((root / "runs/L1/out/RUN.json.first").read_text(encoding="utf-8"))["runner_state"]
first_rows = json.loads((root / "runs/L1/out/rows.json").read_text(encoding="utf-8"))
io_2 = io_by_doc(root, "L1", pid=pid2)
per_doc = {}
for s_ in al_1:
    att = next((v["extracted"]["ai_evidence"]["attempts"][-1] for v in first_rows.values() if v.get("sha256") == s_ and (v.get("extracted") or {}).get("ai_evidence")), None)
    stopped = bool(att and any(str(c.get("outcome", "")).startswith("budget") for c in att.get("calls") or []))
    per_doc[s_[:8]] = {"first_reading_budget_stopped": stopped, "charged_before": al_1[s_]["charged"], "charged_after": al_2[s_]["charged"], "fresh_sends_in_reread": io_2.get(s_, 0),
                       "fresh_equals_charge_delta": io_2.get(s_, 0) == al_2[s_]["charged"] - al_1[s_]["charged"], "completed_doc_unchanged": (not stopped) and io_2.get(s_, 0) == 0 and al_1[s_]["charged"] == al_2[s_]["charged"]}
R["scenarios"]["S5_cache_hit"] = {"first": first, "reread": re, "fresh_sends_in_reread": sum(io_by_doc(root, "L1", pid=pid2).values()), "cache_hits_in_reread": m["runner_state"]["cache_hits"],
                                  "fresh_sends_first_run": sum(io_1.values()), "cache_hits_first_run": first_state["cache_hits"],
                                  "charged_unchanged": {s: v["charged"] for s, v in al_1.items()} == {s: v["charged"] for s, v in al_2.items()}, "attempts_after_reread": {s[:8]: v["attempts"] for s, v in al_2.items()},
                                  "per_document": per_doc, "counter_delta": sum(xtrack_used(root, ep) for ep in ("16830", "17428")) - sum(used_1.values()), "counter_unchanged": used_1 == {ep: xtrack_used(root, ep) for ep in ("16830", "17428")},
                                  "charged": {s[:8]: v["charged"] for s, v in al_2.items()}, "requests_in_reread_process": m["runner_state"]["per_ep"]}

# S6 scope exhaustion ---------------------------------------------------------------------------------------------------------
root = fresh_root("s6-scope-exhaust")
shutil.rmtree(root / "runs/r22dry-A")
e6 = {**BASE_ENV, "PILOT_DRY_ROOT": root.as_posix(), "PILOT_DRY_CAP": "10", "PILOT_SCOPE_FAMILY": "r22-probe-exhaust-2026-09-30"}
d6 = subprocess.run([PY, str(HERE / "declare_r22.py")], env=e6, capture_output=True, text=True, cwd=str(HERE))
assert d6.returncode == 0, d6.stdout[-2000:] + d6.stderr[-2000:]
decl6 = root / "R22-DECLARATION.dry.json"
sha6 = hashlib.sha256(decl6.read_bytes()).hexdigest()
a6 = subprocess.run([PY, str(HERE / "arm_a.py"), "r22dry-A", "--declaration", str(decl6), "--declaration-sha", sha6], env=e6, capture_output=True, text=True, cwd=str(HERE))
assert a6.returncode == 0, a6.stdout[-2000:] + a6.stderr[-2000:]
x6 = run(root, ["r22dry-A", "L1", "L1"], name="L1-exhaust", decl_path=decl6, decl_sha=sha6)
m = run_json(root, "L1")
d6j = json.loads(decl6.read_text(encoding="utf-8"))
k6 = (d6j["ledger"]["scopes"]["L1"]["scope"], f"L1|default|{d6j['arms']['L1']['identities']['EVIDENCE_POLICY_VERSION']}")
al6 = allowance(root, *k6)
con = sqlite3.connect(str(root / "dry-ledger.sqlite"))
ledger_rows = con.execute("select count(*) from requests where scope = ?", (k6[0],)).fetchone()[0] if con.execute("select name from sqlite_master where name = 'requests'").fetchone() else None
con.close()
budget_stops = sum(1 for e in progress(root, "L1") if e["event"] == "document_end" and e.get("exhausted"))
R["scenarios"]["S6_scope_exhaust"] = {"run": x6, "status": m["status"], "arm_cap": d6j["ledger"]["caps"]["L1"], "requests_sent": sum(m["runner_state"]["per_ep"].values()), "sent_by_doc": {s[:8]: n for s, n in io_by_doc(root, "L1").items()},
                                      "charged_total": sum(v["charged"] for v in al6.values()), "ledger_scope_rows": ledger_rows, "counter_used": {ep: xtrack_used(root, ep) for ep in ("16830", "17428")},
                                      "documents_budget_stopped": budget_stops, "ledger_precheck_refusals": m["runner_state"]["ledger_precheck_refusals"], "exhaustion_is_a_budget_stop": m["status"] == "completed" and sum(m["runner_state"]["per_ep"].values()) == d6j["ledger"]["caps"]["L1"],
                                      "counter_equals_sent": sum(xtrack_used(root, ep) for ep in ("16830", "17428")) == sum(m["runner_state"]["per_ep"].values())}

# S7 deferral with a fake clock ----------------------------------------------------------------------------------------------
root = fresh_root("s7-deferral")
T0 = time.time()
sys.path.insert(0, str(HERE))
import xtrack2  # noqa: E402
xtrack2.PATH = str(root / "dry-project-day.sqlite")
xtrack2.record("16830", "seed-other-track", [(T0 - 60, "seed")] * 50)
d1 = run(root, ["r22dry-A", "L1", "L1"], env={"XTRACK_FAKE_NOW": str(T0)}, name="L1-T0")
m1 = run_json(root, "L1")
cap_T0 = 60 - xtrack_used(root, "16830", T0)          # read BEFORE the resume: the resumed run's requests are stamped a day later
al_d1 = allowance(root, *key("L1"))
io_d1 = io_by_doc(root, "L1")
d2 = run(root, ["r22dry-A", "L1", "L1", "--resume"], env={"XTRACK_FAKE_NOW": str(T0 + 86401)}, name="L1-T0+24h")
m2 = run_json(root, "L1")
al_d2 = allowance(root, *key("L1"))
io_d2 = io_by_doc(root, "L1")
R["scenarios"]["S7_deferral"] = {"T0": T0, "seeded_other_track_requests": {"16830": 50}, "first": {"run": d1, "status": m1["status"], "deferred": m1["deferred"], "requests": m1["runner_state"]["per_ep"],
                                 "sent_16830": sum(n for s, n in io_d1.items() if s in (SIX, ONE)), "zero_requests_for_deferred_project": sum(n for s, n in io_d1.items() if s in (SIX, ONE)) == 0,
                                 "capacity_16830_at_T0": cap_T0},
                                 "resumed": {"run": d2, "status": m2["status"], "deferred_before_resume": m2.get("deferred_before_resume"), "deferred_after": m2["deferred"], "requests": m2["runner_state"]["per_ep"],
                                             "skipped_completed": [s[:8] for s in m2["runner_state"]["skipped_completed"]], "skipped_projects": m2["runner_state"]["skipped_projects"], "charged_17428_unchanged": {s: al_d1[s]["charged"] for s in al_d1 if s in (TWO, TXT)} == {s: al_d2[s]["charged"] for s in al_d2 if s in (TWO, TXT)},
                                             "sent_17428_unchanged": {s: io_d1.get(s, 0) for s in (TWO, TXT)} == {s: io_d2.get(s, 0) for s in (TWO, TXT)}, "charged_final": {s[:8]: v["charged"] for s, v in al_d2.items()},
                                             "capacity_16830_at_resume": 60 - xtrack_used(root, "16830", T0 + 86401) + sum(n for s, n in io_d2.items() if s in (SIX, ONE))}}

# S8 refusals ----------------------------------------------------------------------------------------------------------------
root = fresh_root("s8-refusals")
r_a = run(root, ["r22dry-A", "L1", "L1", "--resume"], name="resume-nonexistent")
r_b = run(root, ["r22dry-A", "L1", "L1"], name="L1")
r_c = run(root, ["r22dry-A", "L1", "L1"], name="repeat-without-resume")
R["scenarios"]["S8_refusals"] = {"resume_nonexistent": r_a, "first_run_exit": r_b["exit"], "repeat_without_resume": r_c, "both_refused_before_dispatch": r_a["exit"] != 0 and r_c["exit"] != 0 and bool(r_a["refused"]) and bool(r_c["refused"]),
                                 "refusal_records": refusals(root), "counter_after": {ep: xtrack_used(root, ep) for ep in ("16830", "17428")}, "requests_first_run": sum(run_json(root, "L1")["runner_state"]["per_ep"].values())}

OUT.mkdir(exist_ok=True)
(OUT / "RUNNER-INTEGRATION.json").write_text(json.dumps(R, indent=1, default=str) + "\n", encoding="utf-8")
for n, s in R["scenarios"].items():
    print(n, json.dumps({k: v for k, v in s.items() if isinstance(v, (bool, int)) or (isinstance(v, dict) and any(isinstance(x, bool) for x in v.values()))}, default=str)[:400])
