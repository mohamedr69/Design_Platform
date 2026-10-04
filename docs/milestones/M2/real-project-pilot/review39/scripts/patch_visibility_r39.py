"""One-off patch of the r39 development copy of visibility_r38.py (exact replacements; refuses on a missing anchor)."""
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/r39/harness-r32/visibility_r38.py")
s = P.read_text(encoding="utf-8")

REPL = [
    ("""Every scenario is dry: no provider exists, no model request is possible (DryStub), the AI ledger must read the same before
and after; breaker and ledger refusals come from the APPLICATION's Ledger / LedgerProvider on a FAKE ledger file inside
the dry run folder. Used by test_visibility_r38.py and by the package's visibility exercise. Writes only under the
sandbox base and the given work folder.\"\"\"""",
     """Every scenario is dry: no provider exists, no model request is possible (DryStub), the AI ledger must read the same before
and after; breaker and ledger refusals come from the APPLICATION's Ledger / LedgerProvider on a FAKE ledger file inside
the dry run folder. Used by test_visibility_r38.py and by the package's visibility exercise. Writes only under the
sandbox base and the given work folder.
ORCH-08C adds five scenarios (Verification 39): an undeclared task kind (R39-04: the drawings-AI task name sent by B), a
request without a document context (R39-04), pages the application leaves unread under its own per-document limits and
a reader exception (R39-06), the 'full' resume policy with retry_at_full (R39-08), and the retry of a failed form read
(R39-16). Resumes wait for the invocation's resume_not_before (the declared policy's time).\"\"\""""),
    ("""    {"pool_id": "SYN003", "lines": ["SHOP DRAWING", "DRAWING NO: SYN-0003", "REV: 02", "TITLE: SYNTHETIC TEST SHEET THREE"],
     "truth": {"identity": ["value", "SYN-0003"], "revision": ["value", "02"], "decision": ["absent", None]}}]}""",
     """    {"pool_id": "SYN003", "lines": ["SHOP DRAWING", "DRAWING NO: SYN-0003", "REV: 02", "TITLE: SYNTHETIC TEST SHEET THREE"],
     "truth": {"identity": ["value", "SYN-0003"], "revision": ["value", "02"], "decision": ["absent", None]}}]}
SYN4 = {"documents": [dict(d, pages=4) if d["pool_id"] != "SYN002" else dict(d) for d in SYN["documents"]]}"""),
    ("""    "project_window": {"docs": ("F037", "F009", "F032"), "inject": {"project_window": {"limit": 2, "window_s": 12}}, "resume": "until_finished",
                       "what": "3 EP-27331 documents, a rolling window of 2 per 12 s: deferrals, retry times, resumes until finished"},""",
     """    "project_window": {"docs": ("F037", "F009", "F032"), "inject": {"project_window": {"limit": 2, "window_s": 12}, "resume_policy": "earliest"},
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
                                   "again (a retry with its ordinal, charged), never served the failure")},"""),
    ("""         "application_path": ["provider_timeout", "lane_allowance"], "application_project_limit": ["application_project_limit"]}""",
     """         "application_path": ["provider_timeout", "lane_allowance"], "application_project_limit": ["application_project_limit"],
         "retry_policy_full": ["project_window"], "undeclared_task_kind": ["undeclared_task_kind", "contract_breach_invalid"],
         "missing_context": ["missing_context"], "unread_pages": ["application_document_limit", "application_reader_exception", "application_reader_cap"],
         "failed_read_retry": ["retry_dispatched", "provider_timeout"]}"""),
    ("""            early = _call("resume", stamp, p)                    # before the retry time: refused, nothing created
            steps.append(early | {"early": True})
            time.sleep(max(0.0, float(last["earliest_retry"]) - time.time()) + 1.0)
            steps.append(_call("resume", stamp, p))""",
     """            early = _call("resume", stamp, p)                    # before the policy's time: refused, nothing created
            steps.append(early | {"early": True, "resume_policy": last.get("resume_policy"), "earliest_retry_utc": last.get("earliest_retry_utc"),
                                  "retry_at_full_utc": last.get("retry_at_full_utc"), "resume_not_before_utc": last.get("resume_not_before_utc")})
            if last.get("resume_policy") == "full" and last.get("resume_not_before") and float(last["resume_not_before"]) > float(last["earliest_retry"]) + 0.5:
                time.sleep(max(0.0, float(last["earliest_retry"]) - time.time()) + 0.5)
                between = _call("resume", stamp, p)              # after the earliest retry, before the full time: refused under 'full'
                steps.append(between | {"between_earliest_and_full": True})
            time.sleep(max(0.0, float(last.get("resume_not_before") or last["earliest_retry"]) - time.time()) + 1.0)
            steps.append(_call("resume", stamp, p))"""),
    ("""        out["invocations"].append({k: inv.get(k) for k in ("n", "kind", "status", "run_state", "comparison_state", "earliest_retry_utc", "deferred",
                                                            "deferred_now_incomplete")})""",
     """        out["invocations"].append({k: inv.get(k) for k in ("n", "kind", "status", "run_state", "comparison_state", "earliest_retry_utc", "deferred",
                                                            "deferred_now_incomplete", "retry_at_full_utc", "resume_policy", "resume_not_before_utc")})"""),
    ("""        rep = _load(o / "RUN-REPORT.json") or {}
        for lane, docs in (rep.get("documents") or {}).items():""",
     """        rep = _load(o / "RUN-REPORT.json") or {}
        if rep.get("contract_breach") and set(kinds) & {"undeclared_task_kind", "missing_context", "contract_breach_invalid"}:
            out["run_state"].append({"invocation": n, "where": f"inv-{n}/out/RUN-REPORT.json contract_breach (and RUN-STATE / CONTRACT-BREACH.json)",
                                     "comparison_state": rep.get("comparison_state"), "kind": rep["contract_breach"].get("kind"),
                                     "task": rep["contract_breach"].get("task"), "context": rep["contract_breach"].get("context"),
                                     "lane": rep["contract_breach"].get("lane")})
        if rep.get("retry_at_full") and "project_window" in kinds:
            out["run_state"].append({"invocation": n, "where": f"inv-{n}/out/RUN-REPORT.json retry_at_earliest / retry_at_full / resume_not_before",
                                     "retry_at_earliest_utc": rep.get("retry_at_earliest_utc"), "retry_at_full_utc": rep.get("retry_at_full_utc"),
                                     "resume_policy": rep.get("resume_policy"), "resume_not_before_utc": rep.get("resume_not_before_utc")})
        for lane, docs in (rep.get("documents") or {}).items():"""),
    ("""                if set(d.get("limit_kinds") or []) & set(kinds) or d.get("status") == "DEFERRED":
                    out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/lane-{lane}.r32.json documents.{pid}", "status": d["status"],
                                          "classes": d.get("status_classes"), "pages": d.get("limit_pages"), "in_denominator": True})""",
     """                if set(d.get("limit_kinds") or []) & set(kinds) or d.get("status") == "DEFERRED":
                    out["scorer"].append({"invocation": n, "where": f"inv-{n}/out/lane-{lane}.r32.json documents.{pid}", "status": d["status"],
                                          "classes": d.get("status_classes"), "pages": d.get("limit_pages"), "in_denominator": True,
                                          "unread_pages": d.get("unread_pages") or None, "retries": d.get("retries")})"""),
    ("""        sc = _load(o / "SCORE-BCR-R32.json")
        if sc:""",
     """        sc = _load(o / "SCORE-BCR-R32.json")
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
        if sc:"""),
    ("""            for c in a.get("charges") or []:
                if c["outcome"] in ("timeout", "budget", "identity_mismatch", "dispatched"):""",
     """            for c in a.get("retries") or []:
                if "retry_dispatched" in kinds:
                    out["audit"].append({"invocation": n, "where": f"inv-{n}/out/ALLOWANCE-AUDIT.json retries[{c['id']}]", "lane": c["lane"],
                                         "outcome": c["outcome"], "note": c["note"], "task": c["task"]})
            for c in a.get("charges") or []:
                if c["outcome"] in ("timeout", "budget", "identity_mismatch", "dispatched"):"""),
]


def main():
    global s
    for old, new in REPL:
        n = s.count(old)
        if n != 1:
            print(f"ANCHOR NOT UNIQUE ({n}): {old[:160]!r}")
            return 1
        s = s.replace(old, new)
    P.write_text(s, encoding="utf-8", newline="\n")
    print("patched", len(REPL))
    return 0


if __name__ == "__main__":
    sys.exit(main())
