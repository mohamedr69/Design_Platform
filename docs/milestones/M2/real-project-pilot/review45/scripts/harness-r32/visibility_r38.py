"""ORCH-08 (A-09 point 7; task item 8): the VISIBILITY drill -- dry runs with the refusing stub in which every kind of
refusal, deferral, failure and identity mismatch is injected, and a locator that shows where each one is recorded:
  run state     <run folder>/RUN-STATE.json and the invocation's RUN-REPORT.json (comparison / run state, deferred
                documents, the per-lane document statuses);
  lane rows     <out>/LANE-<lane>.json (limit_events per document and page, document statuses);
  scorer        <out>/lane-<lane>.r32.json (document status, classes, pages) and <out>/SCORE-BCR-R32.json (limit_incomplete,
                matched_exclusions, coverage status_rows, diagnostics) -- the documents stay in every denominator;
  audit view    <out>/ALLOWANCE-AUDIT.json (charges with outcome and ledger entry, refusals, durable stops, reconciliation).
Scenarios run over the REAL run-set documents with reader 'none' (no document is read: the adapter's real reviewed-2
truth scores empty lanes) or over SYNTHETIC EP-990001 documents with the application readers (the application path).
Every scenario is dry: no provider exists, no model request is possible (DryStub), the AI ledger must read the same before
and after; breaker and ledger refusals come from the APPLICATION's Ledger / LedgerProvider on a FAKE ledger file inside
the dry run folder. Used by test_visibility_r38.py and by the package's visibility exercise. Writes only under the
sandbox base and the given work folder.
ORCH-08C adds five scenarios (Verification 39): an undeclared task kind (R39-04: the drawings-AI task name sent by B), a
request without a document context (R39-04), pages the application leaves unread under its own per-document limits and
a reader exception (R39-06), the 'full' resume policy with retry_at_full (R39-08), and the retry of a failed form read
(R39-16). Resumes wait for the invocation's resume_not_before (the declared policy's time)."""
from __future__ import annotations

import hashlib
import json
import pathlib
import sqlite3
import time
import uuid

import preflight_r32 as PF
import runner_r32 as RN

REAL = ("F037", "F009", "F051", "F066")
SYN = {"documents": [
    {"pool_id": "SYN001", "lines": ["SHOP DRAWING", "DRAWING NO: SYN-0001", "REV: 00", "TITLE: SYNTHETIC TEST SHEET ONE"],
     "truth": {"identity": ["value", "SYN-0001"], "revision": ["value", "00"], "decision": ["absent", None]}},
    {"pool_id": "SYN002", "lines": ["MATERIAL SUBMITTAL", "SUBMITTAL NO: SYN-MAT-002", "REVISION: 01", "APPROVED AS NOTED"],
     "truth": {"identity": ["value", "SYN-MAT-002"], "revision": ["value", "01"], "decision": ["absent", None]}},
    {"pool_id": "SYN003", "lines": ["SHOP DRAWING", "DRAWING NO: SYN-0003", "REV: 02", "TITLE: SYNTHETIC TEST SHEET THREE"],
     "truth": {"identity": ["value", "SYN-0003"], "revision": ["value", "02"], "decision": ["absent", None]}}]}
SYN4 = {"documents": [dict(d, pages=4) if d["pool_id"] != "SYN002" else dict(d) for d in SYN["documents"]]}
_CAPS_C1 = {"B": 240, "C": 1, "R": 40, "P": 36}
SCENARIOS = {
    "lane_allowance": {"docs": REAL, "inject": {"caps": _CAPS_C1}, "resume": True,
                       "what": "C's own allowance is 1: its 2nd request is refused (C budget-stopped); the resume re-opens the stop"},
    "project_window": {"docs": ("F037", "F009", "F032"), "inject": {"project_window": {"limit": 2, "window_s": 12}, "resume_policy": "earliest"},
                       "resume": "until_finished",
                       "what": "3 EP-27331 documents, a rolling window of 2 per 12 s, resume policy 'earliest': deferrals, retry times, resumes until finished"},
    "retry_policy_full": {"docs": ("F037", "F009", "F032"), "inject": {"project_window": {"limit": 2, "window_s": 12}, "resume_policy": "full"},
                          "resume": "until_finished",
                          "what": ("the same 3 EP-27331 documents under the 'full' resume policy: every DEFERRED record carries retry_at_earliest and "
                                   "retry_at_full (planning / structural); a resume before the policy's time is refused and creates nothing")},
    "undeclared_task_kind": {"docs": REAL, "inject": {"injections": [{"kind": "undeclared_request", "lane": "B", "calls": [1], "task": "drawings_reply_match"}]},
                             "resume": True,
                             "what": ("after its 1st document B sends a 'drawings_reply_match' request (the drawings-AI task, undeclared for B): refused "
                                      "at the gate, recorded with the lane, task and context, CONTRACT-BREACH.json written, the run INVALID, the resume refused")},
    "missing_context": {"docs": REAL, "inject": {"injections": [{"kind": "context_free_request", "lane": "C", "calls": [1]}]},
                        "what": ("after its 1st document C sends a DECLARED task kind with no document context (the context is cleared after each "
                                 "document): refused at the gate as a contract breach, never charged, the run INVALID")},
    "unread_pages": {"synthetic": SYN4, "inject": {"application_limits": {"AI_MAX_CALLS_PER_DOCUMENT": "2"},
                                                   "injections": [{"kind": "reader_exception", "lane": "C", "calls": [2]}]},
                     "what": ("SYNTHETIC 4-page documents, the per-document JobBudget lowered to 2 (dry only): pages left unread or read in part "
                              "by the application's own budget, and an evidence-reader exception on the 2nd document -- every such page "
                              "recorded per page; the documents stay COMPLETE with unread_pages")},
    "failed_read_retry": {"synthetic": SYN, "inject": {"injections": [{"kind": "provider_timeout", "lane": "B", "calls": [1]}]},
                          "what": ("SYNTHETIC: B's first form read times out; the application's reconcile check repeats the read: it is dispatched "
                                   "again (a retry with its ordinal, charged), never served the failure")},
    "deferral_beyond_bound": {"docs": ("F037", "F009"), "inject": {"project_window": {"limit": 1, "window_s": 3600},
                                                                  "parent": {"total": 556, "input_tokens": 16300000, "output_tokens": 3260000, "elapsed_s": 600}},
                              "what": "the window frees after the elapsed bound: the deferral cannot complete, the document is INCOMPLETE"},
    "bound_passed_while_deferred": {"docs": ("F037", "F009"), "inject": {"project_window": {"limit": 1, "window_s": 4},
                                                                         "parent": {"total": 556, "input_tokens": 16300000, "output_tokens": 3260000, "elapsed_s": 40}},
                                    "resume": "after_bound", "what": "deferred, then resumed only after the elapsed bound: the run is CLOSED INCOMPLETE"},
    "breaker": {"docs": REAL, "inject": {"injections": [{"kind": "usage", "lane": "C", "calls": [1], "input_tokens": 200000, "output_tokens": 10}],
                                         "dry_ledger": {"scope": "drill-breaker", "limits": {"requests": 556, "per_request_input": 100000}}},
                "what": "C's 1st response reports 200,000 input tokens to the FAKE ledger (per-request 100,000): its breaker opens; the next request is refused"},
    "ledger": {"docs": REAL, "inject": {"dry_ledger": {"scope": "drill-ledger", "limits": {"requests": 5}}},
               "what": "the FAKE ledger scope allows 5 requests: B takes 4, C's 2nd request is refused by the ledger"},
    "provider_timeout": {"docs": REAL, "inject": {"injections": [{"kind": "provider_timeout", "lane": "C", "calls": [1, 2, 3]}]}, "resume": True,
                         "what": "C's first three requests time out: three consecutive failures make C terminal"},
    "interrupted": {"docs": REAL, "inject": {"injections": [{"kind": "interrupted", "lane": "C", "calls": [2]}]}, "resume": True, "crash": True,
                    "what": "C's process dies inside its 2nd dispatch (no response): the row stays reserved, the charge 'dispatched'"},
    "unsaved": {"docs": REAL, "inject": {"injections": [{"kind": "unsaved", "lane": "C", "calls": [2]}]}, "resume": True, "crash": True,
                "what": "C's 2nd response came back (identity logged) and the process died before saving it"},
    "identity_mismatch": {"docs": REAL, "inject": {"injections": [{"kind": "identity_mismatch", "lane": "C", "calls": [1], "model": "claude-sonnet-5-1"}]},
                          "resume": True, "what": "C's 1st response names claude-sonnet-5-1, not the pinned claude-sonnet-5: the run is INVALID"},
    "application_path": {"synthetic": SYN, "inject": {"injections": [{"kind": "provider_timeout", "lane": "C", "calls": [1]}],
                                                      "caps": {"B": 240, "C": 1, "R": 40, "P": 36}},
                         "what": "SYNTHETIC EP-990001 documents through the application readers: a timeout on a page, then C's allowance"},
    "application_project_limit": {"synthetic": SYN, "inject": {"application_limits": {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": "1"}},
                                  "what": ("SYNTHETIC EP-990001: the application's own per-project limit lowered to 1 (dry drill only) refuses C "
                                           "before the harness -- the R38-08 failure mode -- and is recorded, never silent")},
}
KINDS = {"lane_allowance": ["lane_allowance", "terminal_stop"], "project_window": ["project_window"], "deferral_beyond_bound": ["deferral_beyond_bound"],
         "bound_passed_while_deferred": ["project_window"], "breaker": ["breaker"], "ledger": ["ledger"], "provider_timeout": ["provider_timeout"],
         "interrupted": ["interrupted_charged"], "unsaved": ["interrupted_charged"], "identity_mismatch": ["identity_mismatch", "identity_invalid"],
         "application_path": ["provider_timeout", "lane_allowance"], "application_project_limit": ["application_project_limit"],
         "retry_policy_full": ["project_window"], "undeclared_task_kind": ["undeclared_task_kind", "contract_breach_invalid"],
         "missing_context": ["missing_context"], "unread_pages": ["application_document_limit", "application_reader_exception", "application_reader_cap"],
         "failed_read_retry": ["retry_dispatched", "provider_timeout"]}


def _write(path, obj):
    pathlib.Path(path).write_text(json.dumps(obj, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")


def prepare(work: pathlib.Path, name: str) -> dict:
    sc = SCENARIOS[name]
    work.mkdir(parents=True, exist_ok=True)
    f = work / "bound.txt"
    f.write_text("visibility drill binding (dry)", encoding="utf-8", newline="\n")
    b = work / "BINDING.json"
    _write(b, {"files": {"drill": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()}}})
    T = PF.build_truth()
    docs = sc.get("docs") or ("F045",)
    rs = work / "RUN-SET.json"
    _write(rs, {"documents": [{"pool_id": p, "doc_key": T["documents"][p]["doc_key"], "ep": T["documents"][p]["ep"]} for p in docs]})
    args = []
    if sc.get("inject"):
        _write(work / "INJECT.json", sc["inject"])
        args += ["--dry-inject", str(work / "INJECT.json")]
    if sc.get("synthetic"):
        _write(work / "SYNTHETIC.json", sc["synthetic"])
        args += ["--dry-synthetic", str(work / "SYNTHETIC.json")]
    return {"binding": b, "binding_sha": hashlib.sha256(b.read_bytes()).hexdigest(), "run_set": rs, "args": args}


def _call(cmd, stamp, p, extra=()):
    try:
        RN.main([cmd, "--mode", "dry", "--stamp", stamp, "--run-set", str(p["run_set"]), "--binding", str(p["binding"]),
                 "--binding-sha", p["binding_sha"], *p["args"], *extra])
        return {"command": cmd, "result": "finished"}
    except RN.Refused as exc:
        return {"command": cmd, "result": "refused", "why": str(exc)}
    except RuntimeError as exc:
        return {"command": cmd, "result": "error", "why": str(exc)}


def _state(folder):
    return json.loads((folder / "RUN-STATE.json").read_text(encoding="utf-8"))


def run_scenario(name: str, work: pathlib.Path) -> dict:
    """Run one scenario (dry) and return its invocations; waits for retry times / the bound where the scenario says so."""
    sc = SCENARIOS[name]
    p = prepare(work, name)
    stamp = f"vis-{name.replace('_', '-')[:20]}-{uuid.uuid4().hex[:6]}"
    folder = RN.SANDBOX_BASE / stamp
    steps = [_call("run", stamp, p)]
    if sc.get("resume") == "until_finished":
        for _ in range(12):
            last = _state(folder)["invocations"][-1]
            if last.get("run_state") != "DEFERRED":
                break
            early = _call("resume", stamp, p)                    # before the policy's time: refused, nothing created
            steps.append(early | {"early": True, "resume_policy": last.get("resume_policy"), "earliest_retry_utc": last.get("earliest_retry_utc"),
                                  "retry_at_full_utc": last.get("retry_at_full_utc"), "resume_not_before_utc": last.get("resume_not_before_utc")})
            if last.get("resume_policy") == "full" and last.get("resume_not_before") and float(last["resume_not_before"]) > float(last["earliest_retry"]) + 0.5:
                time.sleep(max(0.0, float(last["earliest_retry"]) - time.time()) + 0.5)
                between = _call("resume", stamp, p)              # after the earliest retry, before the full time: refused under 'full'
                steps.append(between | {"between_earliest_and_full": True})
            time.sleep(max(0.0, float(last.get("resume_not_before") or last["earliest_retry"]) - time.time()) + 1.0)
            steps.append(_call("resume", stamp, p))
    elif sc.get("resume") == "after_bound":
        st = _state(folder)
        import allowance_r32 as AL
        a = AL.LaneAllowance(folder / "allowance.sqlite", st["caps"], st["project_window"], parent=st["parent"], run_key=st["run_key"], create=False)
        time.sleep(max(0.0, a.bound_end() - time.time()) + 1.0)
        steps.append(_call("resume", stamp, p))
        steps.append(_call("resume", stamp, p))
    elif sc.get("resume"):
        steps.append(_call("resume", stamp, p))
    return {"scenario": name, "what": sc["what"], "stamp": stamp, "run_folder": folder.as_posix(), "steps": steps}


def _load(path):
    path = pathlib.Path(path)
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def locate(run_folder, kinds) -> dict:
    """Where every event of the given kinds is recorded, per invocation, in the four places."""
    folder = pathlib.Path(run_folder)
    st = _load(folder / "RUN-STATE.json")
    out = {"run_state": [], "lane_rows": [], "scorer": [], "audit": [], "invocations": []}
    for inv in st["invocations"]:
        n = inv["n"]
        out["invocations"].append({k: inv.get(k) for k in ("n", "kind", "status", "run_state", "comparison_state", "earliest_retry_utc", "deferred",
                                                            "deferred_now_incomplete", "retry_at_full_utc", "resume_policy", "resume_not_before_utc")})
        if inv.get("status") == "closed":
            out["run_state"].append({"invocation": n, "where": "RUN-STATE.json invocations[-1] (closed)", "comparison_state": inv["comparison_state"],
                                     "deferred_now_incomplete": inv.get("deferred_now_incomplete")})
            continue
        o = folder / f"inv-{n}" / "out"
        rep = _load(o / "RUN-REPORT.json") or {}
        if rep.get("contract_breach") and set(kinds) & {"undeclared_task_kind", "missing_context", "contract_breach_invalid"}:
            out["run_state"].append({"invocation": n, "where": f"inv-{n}/out/RUN-REPORT.json contract_breach (and RUN-STATE / CONTRACT-BREACH.json)",
                                     "comparison_state": rep.get("comparison_state"), "kind": rep["contract_breach"].get("kind"),
                                     "task": rep["contract_breach"].get("task"), "context": rep["contract_breach"].get("context"),
                                     "lane": rep["contract_breach"].get("lane")})
        if rep.get("retry_at_full") and "project_window" in kinds:
            out["run_state"].append({"invocation": n, "where": f"inv-{n}/out/RUN-REPORT.json retry_at_earliest / retry_at_full / resume_not_before",
                                     "retry_at_earliest_utc": rep.get("retry_at_earliest_utc"), "retry_at_full_utc": rep.get("retry_at_full_utc"),
                                     "resume_policy": rep.get("resume_policy"), "resume_not_before_utc": rep.get("resume_not_before_utc")})
        for lane, docs in (rep.get("documents") or {}).items():
            for pid, d in docs.items():
                hit = sorted(set(d.get("kinds") or []) & set(kinds))
                if hit or (d.get("status") != "COMPLETE" and ("project_window" in kinds and d.get("status") == "DEFERRED")):
                    out["run_state"].append({"invocation": n, "where": f"inv-{n}/out/RUN-REPORT.json documents.{lane}.{pid}", "status": d.get("status"),
                                             "kinds": d.get("kinds"), "pages": d.get("pages"), "retry_at_utc": d.get("retry_at_utc")})
        for lane in ("B", "C", "R", "P"):
            m = _load(o / f"LANE-{lane}.json")
            if not m:
                continue
            for e in m.get("limit_events") or []:
                if e["kind"] in kinds:
                    out["lane_rows"].append({"invocation": n, "where": f"inv-{n}/out/LANE-{lane}.json limit_events", "kind": e["kind"], "pool_id": e["pool_id"],
                                             "page": e["page"], "class": e["class"], "served": e["served"], "retry_at_utc": e["retry_at_utc"]})
            s = _load(o / f"lane-{lane}.r32.json")
            for pid, d in ((s or {}).get("documents") or {}).items():
                if set(d.get("limit_kinds") or []) & set(kinds) or d.get("status") == "DEFERRED":
                    out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/lane-{lane}.r32.json documents.{pid}", "status": d["status"],
                                          "classes": d.get("status_classes"), "pages": d.get("limit_pages"), "in_denominator": True,
                                          "unread_pages": d.get("unread_pages") or None, "retries": d.get("retries")})
        sc = _load(o / "SCORE-BCR-R32.json")
        if sc and sc.get("unread_pages") and set(kinds) & {"application_document_limit", "application_reader_exception", "application_reader_cap"}:
            for lane, u in sc["unread_pages"].items():
                for pid, v in (u.get("documents") or {}).items():
                    out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/SCORE-BCR-R32.json unread_pages.{lane}.documents.{pid}",
                                          "status": v.get("status"), "unread_page_count": v.get("unread_page_count"), "pages": v.get("pages")})
        if sc and str(sc.get("comparison_state") or "").startswith("INVALID") and set(kinds) & {"undeclared_task_kind", "missing_context"}:
            out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/SCORE-BCR-R32.json comparison_state", "comparison_state": sc.get("comparison_state")})
        if not sc and str(rep.get("comparison_state") or "").startswith("INVALID") and set(kinds) & {"undeclared_task_kind", "missing_context"}:
            out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/RUN-REPORT.json comparison_state (no B/C score: C did not run)",
                                  "comparison_state": rep.get("comparison_state"), "candidate_outcome": rep.get("candidate_outcome")})
        if sc:
            for lane, ls in (sc.get("limit_incomplete") or {}).items():
                for group, docs in ls.items():
                    for pid in docs:
                        out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/SCORE-BCR-R32.json limit_incomplete.{lane}.{group}.{pid}"})
            for f, m in (sc.get("metrics") or {}).get("C", {}).get("fields", {}).items():
                rows = (m.get("coverage_resolved") or {}).get("status_rows")
                if rows:
                    out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/SCORE-BCR-R32.json metrics.C.fields.{f}.coverage_resolved",
                                          "pages_denominator": m["coverage_resolved"]["pages"], "status_rows": rows})
        a = _load(o / "ALLOWANCE-AUDIT.json")
        if a:
            for r in a.get("refusals") or []:
                if r["kind"] in kinds:
                    out["audit"].append({"invocation": n, "where": f"inv-{n}/out/ALLOWANCE-AUDIT.json refusals[{r['id']}]", "kind": r["kind"], "lane": r["lane"],
                                         "project": r["project"], "page": r["page"], "retry_at_utc": r["retry_at_utc"]})
            for c in a.get("retries") or []:
                if "retry_dispatched" in kinds:
                    out["audit"].append({"invocation": n, "where": f"inv-{n}/out/ALLOWANCE-AUDIT.json retries[{c['id']}]", "lane": c["lane"],
                                         "outcome": c["outcome"], "note": c["note"], "task": c["task"]})
            for c in a.get("charges") or []:
                if c["outcome"] in ("timeout", "budget", "identity_mismatch", "dispatched"):
                    out["audit"].append({"invocation": n, "where": f"inv-{n}/out/ALLOWANCE-AUDIT.json charges[{c['id']}]", "lane": c["lane"],
                                         "outcome": c["outcome"], "ledger_entry": c["ledger_entry"], "page": c["page"], "task": c["task"]})
            for lane, s in (a.get("stops") or {}).items():
                out["audit"].append({"invocation": n, "where": f"inv-{n}/out/ALLOWANCE-AUDIT.json stops.{lane}", "kind": s["kind"]})
    return out


def capture_duplicates(run_folder) -> int:
    con = sqlite3.connect(f"file:{(pathlib.Path(run_folder) / 'capture.sqlite').as_posix()}?mode=ro", uri=True)
    try:
        return con.execute("select count(*) from (select bound_key from requests group by bound_key having count(*) > 1)").fetchone()[0]
    finally:
        con.close()
