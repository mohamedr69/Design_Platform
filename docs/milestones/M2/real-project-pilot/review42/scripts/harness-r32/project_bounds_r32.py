"""ORCH-08 (A-09 point 1; R38-08, R35-09): the maximum number of requests per project across the complete declared lane
sequence B -> C -> R -> P, from the run set and the HARD bounds of the bound code paths, and the explicit compatible
limits a declaration must bind (PROJECT-REQUEST-BOUNDS.json).

The hard bounds (each read from the bound source file, whose sha256 is checked first -- PACKET MISMATCH otherwise):
  candidate evidence_reader.py   MAX_PAGES_PER_DOCUMENT 4 (pages read: min(page_count, 4)); MAX_CALLS_PER_DOCUMENT 8 is
                                 checked only BETWEEN pages (read_document) and before optional reads, so it is no bound;
                                 DECISION_READS_PER_PAGE 3 (with AI_EVIDENCE_DECISION_REGION: one locate_decision + at
                                 most 3 read_decision per page)
  config.py (both trees)          AI_MAX_CALLS_PER_DOCUMENT 12 and AI_MAX_ELAPSED_S_PER_JOB 120 s: ONE JobBudget per
                                 document in evidence_stage -- the hard per-document bound of C and R (12 reservations);
                                 AI_MAX_CALLS_PER_PROJECT_PER_DAY 60 and AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY 600: the
                                 application's own per-project limits (rolling 24 h over AiUsage rows in the lane's
                                 database); AI_READ_MAX_CALLS_PER_DOCUMENT 60 (B's per-run call limit); AI_CLI_TIMEOUT_S
  budget.py (both trees)          reserve(): calls + 1 > max_calls_per_document; calls_today_before + calls + 1 >
                                 max_calls_per_project_per_day (calls_today counts every non-cache AiUsage row of the project)
  baseline submittal_reader.py    B: one read_submittal_form request per form-like document in the AI stage (read_form ->
                                 one call_task); the reconcile check (submittal_reader.check) repeats it only when that
                                 read stored no reading -- ORCH-08C (R39-16): a repeat of a FAILED read is no longer served
                                 its failure, it is dispatched again (the application's own retry path, charged); a repeat of
                                 an answered read finds the stored reading and makes no call. Hence B <= 2 dispatches and 2
                                 AiUsage rows per document per invocation
  baseline document_processing.py, shop_drawings.py, drawing_ai_review.py (ORCH-08C, R39-04): B's processing ends with
                                 shop_drawings.reconcile -> _ai_review -> drawing_ai_review._ask, up to
                                 drawings_ai_max_calls_per_sync (10) requests per project per B invocation when
                                 DRAWINGS_AI_REVIEW_ENABLED is true. The declaration's application_env sets it to false in
                                 every lane, so the path is DISABLED and counted 0; the 'drawings_ai' block states the
                                 alternative (enabled) for the record. No AiUsage row is written by that path.
Per page under the declared switches (the call sites of _read_page_required / _decision_region_read / _finish_page):
  discovery 1 + read_identity 1 + read_revision 1 + decision (DECISION_REGION: locate_decision 1 + read_decision <= 3;
  otherwise read_decision 1) + optional targeted context reads (TARGETED: <= 2) [+ EV2 escalations <= 2 per document].
  C (L3 + IG/CA/DR/PA): 9 per page; R (L3): 6 per page.
Per document (dispatches per invocation):  B 2 (the read and its retry in the reconcile check);  C and R min(12, per_page x
  pages_read [+2 for EV2]) -- the JobBudget counts served and dispatched calls alike, so a retry inside one invocation
  stays within the 12.
Retries across resumes (ORCH-08C, R39-16): a resume dispatches again every fingerprint whose dispatches all failed; such
  retries are NOT in the totals below (the totals count one dispatch per request per invocation); they are bounded only by
  the lane allowances, the parent total and the window (each retry is a charge the window counts). Stated in the file.
Per project:  P <= min(P cap, C maximum of the project) (the probe re-sends a seeded 15 % of C's answered dispatches).
Planning (the frozen ORCH-07 model, kept for comparison): B one form read per decision-bearing document; C min(8, 2 x
pages read) per document; R 10 x the project's share of C planning; P 0.15 x C planning.

Compatible limits (the harness project rolling-window limit GOVERNS; the application's own per-project limits must be
unable to refuse before it):
  * every request the harness counts per project is a charge in the ONE allowance, across all lanes, in a rolling
    window (project_window.limit per project_window.window_s);
  * the application counts AiUsage rows of the project in ONE lane database per invocation (fresh sandboxes each
    invocation; C and R are copies of B's database, so they hold B's rows; served answers write rows too):
      B database: 2 x documents;  C database: B + C maximum;  R database: B + R maximum;  P has no application database.
    required_application_project_limit = max over projects of those -- AI_MAX_CALLS_PER_PROJECT_PER_DAY and
    AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY (B's form reading uses max(read limit, project limit)) must be >= it, so the
    application's per-project counter can never refuse: only the harness window can, and it does so visibly
    (DEFERRED, then INCOMPLETE if the deferral cannot complete within the elapsed bound);
  * windows needed per project = ceil(all-lane structural maximum / window limit); the earliest completion needs
    (windows - 1) x window_s, which must fit the declared elapsed bound.
Pure apart from the hash-checked reads; writes only the output file of main()."""
from __future__ import annotations

import hashlib
import json
import math
import pathlib
import re
import sys

CANDIDATE = pathlib.Path("C:/t/iso/cand-r29/backend")
BASELINE = pathlib.Path("C:/t/iso/frozen-r12/backend")
SOURCES = {
    "candidate/app/ai/evidence_reader.py": (CANDIDATE / "app/ai/evidence_reader.py", "d74397b374fc91a69ed6b4d2ba4306e5fe89682144b2cf5275c7c4091c7ca07a"),
    "candidate/app/core/config.py": (CANDIDATE / "app/core/config.py", "b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155"),
    "candidate/app/ai/budget.py": (CANDIDATE / "app/ai/budget.py", "da647b1c67ef59252cf336bd771add9d3d211cf6d74368f29c9130e3f75cb23c"),
    "baseline/app/core/config.py": (BASELINE / "app/core/config.py", "b4fbc07f5a50e147b3ca0d9ca70c5b52a062f2aab7b56c5ce9e468257e361155"),
    "baseline/app/ai/budget.py": (BASELINE / "app/ai/budget.py", "da647b1c67ef59252cf336bd771add9d3d211cf6d74368f29c9130e3f75cb23c"),
    "baseline/app/ai/submittal_reader.py": (BASELINE / "app/ai/submittal_reader.py", "7127640681241387b1fdd538180c11aa9eb0d347859ee7b806aa7503b8e0d5bd"),
    "baseline/app/ai/sheet_reader.py": (BASELINE / "app/ai/sheet_reader.py", "900e159f131b293b48a36a433362e0b252b38c0538df8dce85b18fcb98a507f0"),
    "baseline/app/services/document_processing.py": (BASELINE / "app/services/document_processing.py",
                                                     "5f5b25940ad0677f655febf14d6af8ccd6b038232bc1c800efa4496a0f31bf0f"),
    "baseline/app/services/shop_drawings.py": (BASELINE / "app/services/shop_drawings.py", "ae9eb36eaded3a782a37e750c1f0732a7882093c8293387f026c0ace6421392e"),
    "baseline/app/services/drawing_ai_review.py": (BASELINE / "app/services/drawing_ai_review.py",
                                                   "04c6af5ef7908f23b06035e36cc6a6aedda6786301325f5c325a7c354bfb3d7d"),
}
VERSION = "project-bounds-r39-2026-10-04.1"
LANES = ("B", "C", "R", "P")
CAPS = {"B": 240, "C": 240, "R": 40, "P": 36}
PROBE_RATE = 0.15
PLAN_R_TOTAL = 10
B_APP_ROWS_PER_DOCUMENT = 2          # the AI-stage read + the reconcile-check repeat per form document (AiUsage rows)
B_DISPATCHES_PER_DOCUMENT = 2        # ORCH-08C (R39-16): the repeat of a FAILED read is dispatched again (r38: 1, the repeat was served)
DRAWINGS_AI_ENABLE_KEY = "DRAWINGS_AI_REVIEW_ENABLED"   # the application setting drawings_ai_review_enabled (config.py, both trees)


class PacketMismatch(RuntimeError):
    pass


def _sha(path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _src(name) -> str:
    path, want = SOURCES[name]
    got = _sha(path)
    if got != want:
        raise PacketMismatch(f"PACKET MISMATCH: {name} {got} != {want}")
    return pathlib.Path(path).read_text(encoding="utf-8")


def _int(text, pattern) -> int:
    m = re.search(pattern, text, re.M)
    if not m:
        raise PacketMismatch(f"bound constant not found: {pattern}")
    return int(float(m.group(1)))


def code_constants() -> dict:
    er, cfg, bud = _src("candidate/app/ai/evidence_reader.py"), _src("candidate/app/core/config.py"), _src("candidate/app/ai/budget.py")
    bcfg, bbud, sub, sheet = (_src("baseline/app/core/config.py"), _src("baseline/app/ai/budget.py"), _src("baseline/app/ai/submittal_reader.py"),
                              _src("baseline/app/ai/sheet_reader.py"))
    dproc, shop, dar = (_src("baseline/app/services/document_processing.py"), _src("baseline/app/services/shop_drawings.py"),
                        _src("baseline/app/services/drawing_ai_review.py"))
    for text, needle in ((bud, "self.calls + 1 > self.limits.max_calls_per_document"),
                         (bud, "self.calls_today_before + self.calls + 1 > self.limits.max_calls_per_project_per_day"),
                         (er, "budget=open_budget(db, project.id)"),
                         (er, "if run.calls - calls_before >= MAX_CALLS_PER_DOCUMENT or run.exhausted:"),
                         (sheet, "max_calls_per_project_per_day=max(settings.ai_read_max_calls_per_project_per_day,"),
                         (sub, "result = assist.call_task(session, TASK, SYSTEM_READ, parts, FORM_SCHEMA, 1500"),
                         (sub, "existing = stored(db, document_sha)"),
                         (dproc, "counts[\"drawings\"] = shop_drawings.reconcile(db, project, user=user)"),
                         (shop, "_ai_review(db, project, systems, rows, shop_all, integrated, registry)"),
                         (dar, "if not settings.drawings_ai_review_enabled:"),
                         (dar, "if report.calls >= settings.drawings_ai_max_calls_per_sync:"),
                         (dar, "response = get_provider().complete(request)")):
        if needle not in text:
            raise PacketMismatch(f"bound code path changed: {needle!r}")
    c = {"max_pages_per_document": _int(er, r"^MAX_PAGES_PER_DOCUMENT = (\d+)"), "reader_soft_calls_per_document": _int(er, r"^MAX_CALLS_PER_DOCUMENT = (\d+)"),
         "decision_reads_per_page": _int(er, r"^DECISION_READS_PER_PAGE = (\d+)"),
         "ai_max_calls_per_document": _int(cfg, r"^\s+ai_max_calls_per_document: int = (\d+)"),
         "ai_max_elapsed_s_per_job": _int(cfg, r"^\s+ai_max_elapsed_s_per_job: float = ([\d.]+)"),
         "ai_max_calls_per_project_per_day": _int(cfg, r"^\s+ai_max_calls_per_project_per_day: int = (\d+)"),
         "ai_read_max_calls_per_project_per_day": _int(cfg, r"^\s+ai_read_max_calls_per_project_per_day: int = (\d+)"),
         "ai_read_max_calls_per_document": _int(cfg, r"^\s+ai_read_max_calls_per_document: int = (\d+)"),
         "ai_cli_timeout_s": _int(cfg, r"^\s+ai_cli_timeout_s: float = ([\d.]+)"),
         "ai_max_escalations_per_document": _int(cfg, r"^\s+ai_max_escalations_per_document: int = (\d+)"),
         "b_pages_to_read": _int(sub, r"^PAGES_TO_READ = (\d+)"),
         "drawings_ai_max_calls_per_sync": _int(bcfg, r"^\s+drawings_ai_max_calls_per_sync: int = (\d+)"),
         "drawings_ai_review_enabled_default": bool(re.search(r"^\s+drawings_ai_review_enabled: bool = True", bcfg, re.M))}
    if _int(bcfg, r"^\s+ai_max_calls_per_project_per_day: int = (\d+)") != c["ai_max_calls_per_project_per_day"] or bbud != bud:
        raise PacketMismatch("the baseline and candidate limits differ")
    c["sources"] = {k: v[1] for k, v in SOURCES.items()}
    return c


def per_page_max(switches: dict, c: dict) -> int:
    """Requests one page can take under a lane's AI_EVIDENCE_* switches (EV1 / EV2; 0 when the evidence reader is off)."""
    if switches.get("AI_EVIDENCE_VARIANT", "off") == "off":
        return 0
    decision = (1 + c["decision_reads_per_page"]) if switches.get("AI_EVIDENCE_DECISION_REGION") == "1" else 1
    targeted = 2 if switches.get("AI_EVIDENCE_TARGETED") == "1" else 0
    return 1 + 1 + 1 + decision + targeted


def document_max(pages: int, switches: dict, c: dict) -> int:
    per = per_page_max(switches, c)
    if per == 0:
        return 0
    esc = min(2, c["ai_max_escalations_per_document"]) if switches.get("AI_EVIDENCE_VARIANT") == "EV2" else 0
    return min(c["ai_max_calls_per_document"], per * pages + esc)


def compute(run_set: list[dict], truth: dict, switches: dict, *, window_limit: int, window_s: int, elapsed_s: int,
            caps: dict | None = None, c: dict | None = None) -> dict:
    """run_set: [{"pool_id", "ep", "reason"?}]; truth: the adapter's truth (page_count, decision facts)."""
    c = c or code_constants()
    caps = dict(caps or CAPS)
    docs = []
    for d in run_set:
        td = truth["documents"][d["pool_id"]]
        pages = min(int(td["page_count"]), c["max_pages_per_document"])
        if int(td["in_scope_pages"]) != pages:
            raise PacketMismatch(f"{d['pool_id']}: in-scope pages {td['in_scope_pages']} != min(page_count, {c['max_pages_per_document']})")
        decision_bearing = bool(td["fields"]["decision"]["has_fact"])
        docs.append({"pool_id": d["pool_id"], "project": f"EP-{d['ep']}", "pages_read": pages, "decision_bearing": decision_bearing,
                     "structural": {"B": B_DISPATCHES_PER_DOCUMENT, "C": document_max(pages, switches["C"], c), "R": document_max(pages, switches["R"], c)},
                     "planning": {"B": 1 if decision_bearing else 0, "C": min(c["reader_soft_calls_per_document"], 2 * pages)}})
    projects = sorted({d["project"] for d in docs}, key=lambda p: int(p.split("-")[1]))
    c_plan_total = sum(d["planning"]["C"] for d in docs)
    c_struct_total = sum(d["structural"]["C"] for d in docs)
    probe_k_max = round(PROBE_RATE * min(caps["C"], c_struct_total))
    out_projects = {}
    for p in projects:
        pd = [d for d in docs if d["project"] == p]
        n = len(pd)
        uncapped = {"B": n * B_DISPATCHES_PER_DOCUMENT, "C": sum(d["structural"]["C"] for d in pd), "R": sum(d["structural"]["R"] for d in pd)}
        uncapped["P"] = min(probe_k_max, uncapped["C"])
        s = {lane: min(caps[lane], uncapped[lane]) for lane in LANES}     # a lane never exceeds its own allowance
        cp = sum(d["planning"]["C"] for d in pd)
        pl = {"B": sum(d["planning"]["B"] for d in pd), "C": cp, "R": round(PLAN_R_TOTAL * cp / c_plan_total, 1) if c_plan_total else 0.0,
              "P": round(PROBE_RATE * cp, 1)}
        s_all, p_all = sum(s.values()), round(sum(pl.values()), 1)
        b_app = B_APP_ROWS_PER_DOCUMENT * n
        # application rows count served answers too (R is served C's capture without a charge): never capped by a lane allowance
        app = {"B_database": b_app, "C_database": b_app + uncapped["C"], "R_database": b_app + uncapped["R"], "P": 0}
        windows = math.ceil(s_all / window_limit) if window_limit else None
        dai = c["drawings_ai_max_calls_per_sync"]
        alt_all = s_all - s["B"] + min(caps["B"], uncapped["B"] + dai)
        out_projects[p] = {"documents": n, "pool_ids": [d["pool_id"] for d in pd], "pages_read": sum(d["pages_read"] for d in pd),
                           "planning": pl | {"all_lanes": p_all}, "structural_maximum": s | {"all_lanes": s_all},
                           "structural_before_lane_caps": uncapped,
                           "planning_exceeds_window": p_all > window_limit, "structural_exceeds_window": s_all > window_limit,
                           "windows_needed_structural": windows, "earliest_completion_s_structural": (windows - 1) * window_s if windows else None,
                           "fits_elapsed_bound": (windows - 1) * window_s < elapsed_s if windows else None,
                           "application_rows_maximum": app | {"max": max(app.values())},
                           "change_from_r38_model": {"B_reconcile_retry": n * (B_DISPATCHES_PER_DOCUMENT - 1),
                                                     "r38_structural_all_lanes": s_all - n * (B_DISPATCHES_PER_DOCUMENT - 1),
                                                     "why": "ORCH-08C (R39-16): the reconcile check's repeat of a failed form read is dispatched again"},
                           "drawings_ai": {"state": f"disabled ({DRAWINGS_AI_ENABLE_KEY}=false in the declared application_env of every lane); counted 0",
                                           "if_enabled": {"B_add_per_invocation": dai, "structural_all_lanes": alt_all,
                                                          "windows_needed": math.ceil(alt_all / window_limit) if window_limit else None,
                                                          "r38_model_all_lanes": alt_all - n * (B_DISPATCHES_PER_DOCUMENT - 1),
                                                          "application_rows_added": 0}}}
    lane_struct = {lane: sum(v["structural_before_lane_caps"][lane] for v in out_projects.values()) for lane in LANES}
    lane_plan = {lane: round(sum(v["planning"][lane] for v in out_projects.values()), 1) for lane in LANES}
    required_app = max(v["application_rows_maximum"]["max"] for v in out_projects.values())
    worst = max(out_projects, key=lambda p: (out_projects[p]["structural_maximum"]["all_lanes"], p))
    return {"version": VERSION, "code_constants": c, "lane_switches": switches, "per_page_maximum": {lane: per_page_max(switches[lane], c) for lane in ("C", "R")},
            "per_document": {d["pool_id"]: {k: d[k] for k in ("project", "pages_read", "decision_bearing", "structural", "planning")} for d in docs},
            "projects": out_projects,
            "lanes": {lane: {"structural_sum_before_cap": lane_struct[lane], "structural_maximum": min(caps[lane], lane_struct[lane]),
                             "planning_sum": lane_plan[lane], "cap": caps[lane], "cap_can_bind": lane_struct[lane] > caps[lane],
                             "if_the_cap_binds": "the lane's allowance refuses visibly: the lane is budget-stopped, its remaining documents are INCOMPLETE"}
                      for lane in LANES},
            "probe_k_maximum": probe_k_max,
            "project_window": {"limit": window_limit, "window_s": window_s, "governs": True, "counts": "harness charges of every lane, rolling window"},
            "elapsed_bound_s": elapsed_s,
            "compatible_limits": {
                "rule": ("the application's per-project counters count AiUsage rows in ONE lane database per invocation; they must be "
                         ">= the largest such count so that only the harness window can refuse (visibly)"),
                "required_minimum": {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": required_app, "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": required_app},
                "tree_defaults": {"AI_MAX_CALLS_PER_PROJECT_PER_DAY": c["ai_max_calls_per_project_per_day"],
                                  "AI_READ_MAX_CALLS_PER_PROJECT_PER_DAY": c["ai_read_max_calls_per_project_per_day"]},
                "binding_project": max(out_projects, key=lambda p: (out_projects[p]["application_rows_maximum"]["max"], p)),
                "kept_at_tree_default": {"AI_MAX_CALLS_PER_DOCUMENT": c["ai_max_calls_per_document"], "AI_MAX_ELAPSED_S_PER_JOB": c["ai_max_elapsed_s_per_job"],
                                         "note": "the per-document job limits are the evaluated arms' own policy; the structural bounds assume them"}},
            "largest_project": worst,
            "drawings_ai": {"enable_key": DRAWINGS_AI_ENABLE_KEY, "tree_default_enabled": c["drawings_ai_review_enabled_default"],
                            "declared": "false (application_env, every lane, every invocation)", "counted": 0,
                            "path": "baseline document_processing.run -> shop_drawings.reconcile -> _ai_review -> drawing_ai_review._ask "
                                    "(tasks drawings_reply_match, drawings_reference_conflict, drawings_floor_alias)",
                            "if_enabled_per_project_per_B_invocation": c["drawings_ai_max_calls_per_sync"]},
            "retries_across_resumes": ("not in the totals: a resume dispatches again every fingerprint whose dispatches all failed (ORCH-08C, "
                                       "R39-16), each a new charge counted by the window; bounded by the lane allowances "
                                       f"{dict(caps)}, the parent total and the window, not by this file"),
            "statement": "bounds and estimates, not measurements; no request was made to compute them"}


def check_compatible(provider_env: dict, bounds: dict) -> list[str]:
    """Problems ([] = compatible): the declared application limits must be >= the required minimum, and the per-document
    limits must equal the values the bounds were computed with."""
    probs = []
    for k, need in bounds["compatible_limits"]["required_minimum"].items():
        v = provider_env.get(k)
        try:
            ok = v is not None and int(str(v)) >= need
        except ValueError:
            ok = False
        if not ok:
            probs.append(f"{k} = {v!r} could refuse before the harness project window (required >= {need})")
    for k, want in (("AI_MAX_CALLS_PER_DOCUMENT", bounds["code_constants"]["ai_max_calls_per_document"]),
                    ("AI_MAX_ELAPSED_S_PER_JOB", bounds["code_constants"]["ai_max_elapsed_s_per_job"])):
        v = provider_env.get(k)
        try:
            ok = v is not None and float(str(v)) == float(want)
        except ValueError:
            ok = False
        if not ok:
            probs.append(f"{k} = {v!r}: the bounds assume {want}")
    for p, v in bounds["projects"].items():
        if v["fits_elapsed_bound"] is False:
            probs.append(f"{p}: {v['windows_needed_structural']} windows cannot complete within the elapsed bound")
    return probs


def text(obj) -> str:
    return json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"


def main(argv) -> int:
    """project_bounds_r32.py <run-set json> <out json> [window_limit window_s elapsed_s] -- with the r32 truth and the
    declared C / R switches of the frozen ORCH-07 arms (DRY_LANE_SWITCHES of runner_r32)."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import preflight_r32 as PF
    import runner_r32 as RN
    rs_path, out = argv[1], pathlib.Path(argv[2])
    lim, win, el = (int(argv[3]), int(argv[4]), int(argv[5])) if len(argv) > 5 else (60, 86400, 604800)
    truth = PF.build_truth()
    run_set = PF.load_run_set(rs_path, truth)
    b = compute(run_set, truth, RN.DRY_LANE_SWITCHES, window_limit=lim, window_s=win, elapsed_s=el)
    b["run_set"] = {"path": str(rs_path), "sha256": _sha(rs_path), "documents": len(run_set)}
    out.write_text(text(b), encoding="utf-8", newline="\n")
    print(json.dumps({"projects": {p: [v["planning"]["all_lanes"], v["structural_maximum"]["all_lanes"]] for p, v in b["projects"].items()},
                      "required": b["compatible_limits"]["required_minimum"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
