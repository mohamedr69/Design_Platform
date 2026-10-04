# DERIVED from review21/arm_ev.py (harness v4, review 22) -- the document-arm runner with the declared execution contract:
#   * a DURABLE per-(ledger scope, arm profile, document) allowance (the reviewed r16.1 DocAllowance / DurableBudget) charged
#     BEFORE dispatch, bound to scope / arm / document / policy, surviving restarts and tags; interrupted attempts stay visible;
#   * --resume over the same sandbox (no new copy of the A base): completed documents (bound by the scoring contract) are
#     skipped, the remaining allowance of an interrupted document is all that can be used; a new tag for an arm whose
#     allowance already exists is refused (PILOT_DRY_NEW_TAG_OVERRIDE=1 lets a DRY probe show the cap holding across tags);
#   * one writer per sandbox (exclusive lock) and per document (the allowance's key lock);
#   * WHOLE-PROJECT deferral: before a project-arm batch, the project's rolling-day capacity (60 minus the last 24 h across
#     all tracks) must cover the batch's worst case (the remaining allowance of every pending PDF); otherwise the project is
#     persisted as deferred and ZERO requests are sent; a later --resume takes deferred projects in declared order;
#   * the tripwire scores only evidence bound by the same eligibility contract as the final scorer (coverage_v4);
#   * the per-arm static share (R21 arm_shares.py) is withdrawn: the rolling counter and the durable allowance replace it.
"""Usage: arm_ev.py <A_tag> <tag> <L1|L2|L3|L4> --declaration D --declaration-sha SHA [--resume] [--reread (dry only)]"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
import sys
import time

HARNESS_CONTRACT = "harness-contract-2026-09-30.v4"
RUNNER_VERSION = "arm-ev-2026-10-01.v4.2"
LIFECYCLE_CONTRACT = "runner-lifecycle-2026-10-01.v2"       # see LIFECYCLE-CONTRACT.md: terminal stops survive --resume (v2: provider stops recovered from the journal)
TERMINAL_PREFIXES = {"stop: critical": "critical_acceptance", "stop: three consecutive provider failures": "provider_failures"}
a = argparse.ArgumentParser()
a.add_argument("a_tag"); a.add_argument("tag"); a.add_argument("arm")
a.add_argument("--declaration", required=True); a.add_argument("--declaration-sha", required=True)
a.add_argument("--resume", action="store_true", help="continue the existing sandbox of this tag (no new copy of A)")
a.add_argument("--reread", action="store_true", help="DRY ONLY: re-run the evidence stage over completed documents too (cache-hit control)")
args = a.parse_args()
assert hashlib.sha256(pathlib.Path(args.declaration).read_bytes()).hexdigest() == args.declaration_sha, "the declaration changed"
decl = json.loads(pathlib.Path(args.declaration).read_text(encoding="utf-8"))
assert args.arm in decl["doc_arms"], args.arm
arm = decl["arms"][args.arm]
HERE = pathlib.Path(__file__).resolve().parent
PILOT_DIR = pathlib.Path(decl["harness_dir"])
for n, h in decl["labels"]["files"].items():
    assert hashlib.sha256((PILOT_DIR / decl["labels"]["dir"] / n).read_bytes()).hexdigest() == h, f"label file {n} changed"
sys.path.insert(0, str(HERE))
sys.path.insert(0, "C:/t/iso/work/r2x/r16")
import coverage_v4 as cv  # noqa: E402
import provider_journal as pj  # noqa: E402
import dry_provider2 as dry  # noqa: E402
import xtrack2 as xtrack  # noqa: E402
from boq_harness import AllowanceBusy, DocAllowance, DurableBudget, _lock_file  # noqa: E402

assert cv.CONTRACT_VERSION == HARNESS_CONTRACT
assert decl.get("harness_contract") == HARNESS_CONTRACT, "the declaration is not on this harness contract"
if args.reread:
    assert dry.DRY, "--reread is a dry-run device only"
if os.environ.get("XTRACK_FAKE_NOW"):
    assert dry.DRY, "a fake clock is a dry-run device only"
RUNS = pathlib.Path(dry.DRY_RUNS if dry.DRY else "C:/t/r2x/runs")
SRC = RUNS / args.a_tag
ROOT = RUNS / args.tag
DB = ROOT / "db" / "default.db"
OUT = ROOT / "out"
ALLOW_PATH = dry.DRY_ALLOWANCE if dry.DRY else "C:/t/r2x/ledger/doc-allowance.sqlite"
scope = decl["ledger"]["scopes"][args.arm]
if dry.DRY:
    scope = {**scope, "env": {**scope["env"], "AI_LEDGER_PATH": dry.DRY_LEDGER}}
    xtrack.PATH = dry.DRY_XTRACK
ALLOW_SCOPE = scope["scope"]                                    # the arm's own ledger scope: experiment + arm
ALLOW_PROFILE = f"{args.arm}|default|{arm['identities']['EVIDENCE_POLICY_VERSION']}"   # arm + reader profile + policy identity
CAP = decl["application_limits"]["ai_max_calls_per_document"]
LIMIT = decl["application_limits"]["ai_max_calls_per_project_per_day"]
ALLOW = DocAllowance(ALLOW_PATH)


def _allowance_rows():
    con = sqlite3.connect(ALLOW_PATH)
    try:
        return con.execute("select count(*), coalesce(sum(calls), 0) from allowance where scope = ? and profile = ?", (ALLOW_SCOPE, ALLOW_PROFILE)).fetchone()
    finally:
        con.close()


def refuse(msg: str) -> None:
    """Refuse BEFORE any dispatch, leaving a record beside the sandbox."""
    (RUNS / "refusals").mkdir(parents=True, exist_ok=True)
    rec = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "arm": args.arm, "resume": args.resume, "refused": msg, "requests_sent": 0}
    with open(RUNS / "refusals" / "REFUSALS.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    sys.exit("REFUSED: " + msg)


if args.resume:
    if not (ROOT.exists() and DB.exists() and (OUT / "RUN.json").exists()):
        refuse(f"{ROOT} has no run to resume")
else:
    if ROOT.exists():
        refuse(f"{ROOT} exists: a run is never repeated over its own sandbox (use --resume to continue it)")
    n_docs, n_calls = _allowance_rows()
    if n_docs and not (dry.DRY and os.environ.get("PILOT_DRY_NEW_TAG_OVERRIDE") == "1"):
        refuse(f"the allowance of {ALLOW_SCOPE} / {ALLOW_PROFILE} already exists ({n_docs} documents, {n_calls} requests charged): "
               "resume the existing sandbox; a new tag never recreates an allowance")
    for d in ("db", "out", "out/io"):
        (ROOT / d).mkdir(parents=True, exist_ok=True)
try:
    _runner_lock = _lock_file(str(OUT / "RUNNER.lock"))     # one writer per sandbox; released by the OS when the holder dies
except AllowanceBusy:
    refuse(f"another writer holds {ROOT}")
a_run = json.loads((SRC / "out" / "RUN.json").read_text(encoding="utf-8"))
assert a_run["track"] == "A" and a_run["declaration_sha256"] == args.declaration_sha, "the source is not this declaration's A base"
if not args.resume:
    _src = sqlite3.connect(f"file:{(SRC / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
    _dst = sqlite3.connect(str(DB))
    _src.backup(_dst)
    _dst.close()
    _src.close()
    for d in ("cache", "library", "uploads"):        # each arm its own copy of A's file caches: no arm writes into another's state
        shutil.copytree(SRC / d, ROOT / d)
for k in ("AI_EVIDENCE_GUARD", "AI_EVIDENCE_TARGETED", "AI_EVIDENCE_EFFICIENT", "AI_EVIDENCE_SUPPORT", "AI_EVIDENCE_SCHEDULING", "AI_EVIDENCE_DEADLINE", "AI_EVIDENCE_ROI"):
    os.environ.pop(k, None)
env = {"DATABASE_URL": f"sqlite:///{DB.as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads"),
       "AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "EXTRACTION_PROMOTE_OBSERVATIONS": "false", "DATASHEET_LIBRARIES": "{}",
       "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
       "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0", **decl["provider"]["env"], **scope["env"], **arm["env"]}
os.environ.update(env)
B = pathlib.Path(arm["tree"]) / "backend"
sys.path.insert(0, str(B)); os.chdir(B)
assert subprocess.run(["git", "-C", str(B.parent), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() == arm["commit"]
assert not subprocess.run(["git", "-C", str(B.parent), "status", "--porcelain"], capture_output=True, text=True).stdout.strip(), "the arm's tree is dirty"
from app.core.config import Settings, get_settings  # noqa: E402
st = get_settings()
assert DB.as_posix() in st.database_url and st.ai_enabled and st.ai_evidence_variant == "EV1" and st.ai_ledger_scope == scope["scope"]
for k, v in decl["application_limits"].items():
    assert getattr(st, k) == v == Settings.model_fields[k].default, f"application limit {k} is not the frozen default"
from app.ai import evidence_reader as er  # noqa: E402
if dry.DRY:
    dry.install()
assert pathlib.Path(er.__file__).resolve().is_relative_to(B.resolve())
for k, v in arm["identities"].items():
    assert getattr(er, k, None) == v, f"{k} differs from the declaration"
assert er.MAX_CALLS_PER_DOCUMENT <= CAP, (er.MAX_CALLS_PER_DOCUMENT, CAP)   # the reader stops a single reading at its own constant (8); the durable cap is the application limit (12)
READER_CAP_PER_READING = er.MAX_CALLS_PER_DOCUMENT
from app.database import SessionLocal  # noqa: E402
from app.models import Project, ProjectDocument  # noqa: E402
from scripts import m2_eval5 as EV  # noqa: E402
assert hashlib.sha256(pathlib.Path(EV.__file__).read_bytes()).hexdigest() == decl["code"]["evaluator"]["sha256"], "evaluator differs"
track = f"r22-{args.arm}"
REG = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["register"]).read_text(encoding="utf-8"))
PAGE = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["page"]).read_text(encoding="utf-8"))
UNC = json.loads((PILOT_DIR / decl["labels"]["dir"] / decl["labels"]["uncertainty"]).read_text(encoding="utf-8"))
unresolved = {u["doc"] for u in UNC["uncertainty"]} | {d["doc"] for d in REG["documents"] if d.get("confidence") != "high"}
CONTEXT = {"variant": "EV1", "profile": "default", "policies": [arm["identities"]["EVIDENCE_POLICY_VERSION"]], "declared": f"pilot arm {args.arm}"}
BCTX = {"variant": "EV1", "profile": "default", "policy": arm["identities"]["EVIDENCE_POLICY_VERSION"]}
PLANNED = decl["sources"]["sample"]["documents_planned"]
planned_by_sha = {p["sha256"]: p for p in PLANNED}
ep_of = {}
state = {"consecutive_failures": 0, "recent_failures": [], "stopped": None, "terminal_stop": None, "xtrack_refusals": 0, "allowance_refusals": 0, "allowance_busy": 0, "ledger_precheck_refusals": 0, "per_ep": {}, "requests_io": 0,
         "cache_hits": 0, "deferred": [], "skipped_completed": [], "skipped_projects": [], "interrupted_seen": []}
IO = OUT / "io"
IO.mkdir(exist_ok=True)


STOP_FILE = OUT / "TERMINAL-STOP.json"
JOURNAL_BINDING = {"declaration_sha256": args.declaration_sha, "arm": args.arm, "tag": args.tag, "a_tag": args.a_tag, "allowance_scope": ALLOW_SCOPE,
                   "allowance_profile": ALLOW_PROFILE, "policy": arm["identities"]["EVIDENCE_POLICY_VERSION"]}
JOURNAL = pj.Journal(OUT / "PROVIDER-OUTCOMES.jsonl", JOURNAL_BINDING)


def load_terminal_stop():
    return json.loads(STOP_FILE.read_text(encoding="utf-8")) if STOP_FILE.exists() else None


def persist_terminal_stop(kind: str, reason: str, evidence, *, reconstructed: bool = False) -> dict:
    """Persist a TERMINAL stop atomically, before anything else is written; the first stop is never overwritten."""
    existing = load_terminal_stop()
    if existing:
        return existing
    if dry.DRY and os.environ.get("PILOT_DRY_KILL_AT_STOP") == "before_file":
        os._exit(98)                          # the stop was decided, nothing persisted yet (recovery must reconstruct it)
    rec = {"lifecycle": LIFECYCLE_CONTRACT, "terminal": True, "kind": kind, "reason": reason, "evidence": evidence, "reconstructed": reconstructed,
           "at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "pid": os.getpid(), "clock": xtrack.now(),
           "tag": args.tag, "arm": args.arm, "declaration_sha256": args.declaration_sha, "allowance_key": {"scope": ALLOW_SCOPE, "profile": ALLOW_PROFILE}}
    tmp = OUT / "TERMINAL-STOP.json.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(rec, f, indent=1, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, STOP_FILE)
    if dry.DRY and os.environ.get("PILOT_DRY_KILL_AT_STOP") == "after_file":
        os._exit(98)                          # the stop file exists, the manifest does not know yet
    return rec


def progress(event: str, **kw) -> None:
    rec = {"at": time.time(), "clock": xtrack.now(), "event": event, "pid": os.getpid(), "tag": args.tag, "arm": args.arm, **kw}
    with open(OUT / "progress.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())


# ---- request accounting: cross-track rolling counter, io capture, failure stop ---------------------------------------------
_original_call = er.EvidenceRun.call


def _save_io(kw, data, entries):
    state["requests_io"] += 1
    n = state["requests_io"]
    parts = []
    for i, p in enumerate(kw.get("parts") or []):
        if hasattr(p, "png"):
            name = f"{os.getpid()}-{n:03d}-{kw.get('task')}-p{kw.get('page')}-{i}-{p.label}.png"
            (IO / name).write_bytes(p.png)
            parts.append({"label": p.label, "image": name, "sha256": hashlib.sha256(p.png).hexdigest()})
        else:
            parts.append({"label": p.label, "text": p.text})
    rec = {"pid": os.getpid(), "n": n, "sha256": kw.get("sha256"), "task": kw.get("task"), "page": kw.get("page"), "reason": kw.get("reason"), "tier": kw.get("tier", "small"),
           "schema": kw.get("schema"), "parts": parts, "answer": data, "log": entries}
    with open(OUT / "io.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def _guarded_call(self, **kw):
    ep = ep_of.get(self.project_id)
    if state["stopped"] and not self.exhausted:
        self.exhausted = state["stopped"]
    took = False
    led = getattr(self.provider, "ledger", None)
    if not self.exhausted and led is not None:
        # the arm's ledger scope is checked BEFORE the durable document allowance is charged: a request the scope would
        # refuse is never charged to the document (other ledger limits refuse after the charge; that charge stays)
        lim, tot = led.effective_limits(), led.totals()
        if tot.get("breaker") or (lim.requests is not None and tot["requests"] + 1 > lim.requests):
            state["ledger_precheck_refusals"] += 1
            self.exhausted = f"ledger scope cap ({lim.requests} requests)" if not tot.get("breaker") else f"ledger breaker: {tot['breaker']}"
    if not self.exhausted:
        took = xtrack.take(ep, track, kw.get("task", ""), LIMIT)
        if not took:
            state["xtrack_refusals"] += 1
            self.exhausted = "calls_per_project_per_day (across tracks)"
    before, n_log, hits = self.calls, len(self.log), self.cache_hits
    jseq = None if self.exhausted else JOURNAL.attempt(pid=os.getpid(), sha256=kw.get("sha256"), task=kw.get("task"), page=kw.get("page"), tier=kw.get("tier", "small"))
    out = _original_call(self, **kw)
    new = self.log[n_log:]
    if jseq is not None:
        JOURNAL.result(jseq, pid=os.getpid(), entry=new[-1] if new else None)     # durable BEFORE the streak decision below
    if took and self.calls == before:
        xtrack.release_last(ep, track)          # a cache hit or a refusal: no request was made
    if self.cache_hits > hits:
        state["cache_hits"] += self.cache_hits - hits
    if self.calls > before:
        state["per_ep"][ep] = state["per_ep"].get(ep, 0) + (self.calls - before)
    if any(not e.get("cache_hit") and not str(e.get("outcome", "")).startswith("budget") for e in new):
        _save_io(kw, out, new)
    for entry in new:
        if str(entry.get("outcome", "")).startswith("budget: calls_per_document"):
            state["allowance_refusals"] += 1
        if entry.get("cache_hit") or str(entry.get("outcome", "")).startswith("budget"):
            continue
        if entry.get("outcome") == "ok":
            state["consecutive_failures"] = 0
            state["recent_failures"] = []
        else:
            state["consecutive_failures"] += 1
            state["recent_failures"].append({"seq": jseq, "pid": os.getpid(), "sha256": kw.get("sha256"), **{k: entry.get(k) for k in ("task", "page", "outcome", "error_detail", "model")}})
            if state["consecutive_failures"] >= 3 and not state["stopped"]:
                state["stopped"] = "stop: three consecutive provider failures"
                state["terminal_stop"] = persist_terminal_stop("provider_failures", state["stopped"], state["recent_failures"][-3:])
                manifest["terminal_stop"] = state["terminal_stop"]
    return out


er.EvidenceRun.call = _guarded_call

# ---- the durable document allowance around the reader's document entry point ------------------------------------------------
_original_read = er.read_document


def _durable_read(run, pdf, *, sha256, **kw):
    key = (ALLOW_SCOPE, ALLOW_PROFILE, sha256)
    ep = ep_of.get(run.project_id)
    try:
        lock = ALLOW.acquire(*key)
    except AllowanceBusy:
        state["allowance_busy"] += 1
        run.exhausted = "allowance busy: another writer holds this document"
        progress("document_busy", ep=ep, sha256=sha256)
        return _original_read(run, pdf, sha256=sha256, **kw)
    try:
        saved = ALLOW.load(*key)
        attempt_id, interrupted = ALLOW.begin_attempt(*key, saved["calls"])
        if interrupted:
            state["interrupted_seen"].append({"sha256": sha256, "attempts": interrupted, "calls_already_charged": saved["calls"]})
        run.budget = DurableBudget(run.budget, ALLOW, key, CAP)
        run.budget.calls = saved["calls"]        # the application's own per-document limit continues from the durable count
        progress("document_start", ep=ep, sha256=sha256, attempt_id=attempt_id, calls_charged_before=saved["calls"], resumed=saved["resumed"], interrupted=interrupted)
        status = "completed"
        try:
            return _original_read(run, pdf, sha256=sha256, **kw)
        except BaseException:
            status = "failed"
            raise
        finally:
            after = ALLOW.load(*key)["calls"]
            ALLOW.end_attempt(attempt_id, status if not run.exhausted else f"{status}:budget_stop", after)
            progress("document_end", ep=ep, sha256=sha256, attempt_id=attempt_id, status=status, exhausted=run.exhausted, calls_charged_after=after)
    finally:
        from boq_harness import _unlock_file
        _unlock_file(lock)


er.read_document = _durable_read


def dump_rows():
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = {}
    for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.system_code, d.extracted "
                         "from project_documents d join projects p on p.id = d.project_id"):
        rows[f"EP-{r['ep_number']}/{r['relative_path']}".replace("\\", "/")] = {
            "id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
            "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
            "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
    con.close()
    return rows


def completed(rowdict: dict) -> bool:
    """A document counts as done for this arm exactly when the scoring contract binds it (same source, this arm's context)."""
    p = planned_by_sha.get(rowdict.get("sha256"))
    if p is None:
        return False
    att, reason = cv.select_attempt(rowdict, p, BCTX)
    return att is not None and reason == "bound"


def tripwire(done_eps: set) -> list:
    """Critical automatic acceptances by this arm's AI on resolved labels, over the projects done so far -- on ELIGIBLE evidence only."""
    docs = [d for d in REG["documents"] if d["ep"] in done_eps]
    planned = [p for p in PLANNED if p["doc"].split("/")[0][3:] in done_eps]
    ok_rows, elig, rejected = cv.eligible_rows(dump_rows(), planned, BCTX)
    ev = EV.evaluate({**REG, "documents": docs}, PAGE, ok_rows, PAGE.get("page1_corrections"), ai_context=CONTEXT)
    return [c for c in ev["totals"]["introduced_ai_errors"] if c["doc"] not in unresolved], {"eligibility": {k: v["state"] for k, v in elig.items()}, "rejected": len(rejected)}


def worst_case(pending_rows) -> tuple[int, list]:
    """The batch's worst case: the REMAINING durable allowance of every pending PDF (12 each before any request)."""
    per = []
    for r in pending_rows:
        charged = ALLOW.load(ALLOW_SCOPE, ALLOW_PROFILE, r.sha256)["calls"]
        per.append({"sha256": r.sha256, "charged": charged, "remaining": max(0, CAP - charged)})
    return sum(x["remaining"] for x in per), per


def write_manifest(final: bool) -> None:
    manifest.update({"seconds": round(time.perf_counter() - started, 1), "runner_state": state, "final": final,
                     "allowance": {p["doc"]: {"charged": ALLOW.load(ALLOW_SCOPE, ALLOW_PROFILE, p["sha256"])["calls"], "attempts": ALLOW.attempts(ALLOW_SCOPE, ALLOW_PROFILE, p["sha256"])}
                                   for p in PLANNED if p["extension"] == ".pdf"}})
    tmp = OUT / "RUN.json.tmp"
    json.dump(manifest, open(tmp, "w", encoding="utf-8"), indent=1, default=str)
    os.replace(tmp, OUT / "RUN.json")


def run_recorded_requests() -> bool:
    """Read-only: did this sandbox already record a request, a charge or a document start?"""
    if (OUT / "io.jsonl").exists() and (OUT / "io.jsonl").stat().st_size > 0:
        return True
    if (OUT / "progress.jsonl").exists() and any(json.loads(l).get("event") == "document_start" for l in (OUT / "progress.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()):
        return True
    con = sqlite3.connect(f"file:{pathlib.Path(ALLOW_PATH).as_posix()}?mode=ro", uri=True)
    try:
        n = con.execute("select coalesce(sum(calls), 0) from allowance where scope = ? and profile = ? and sha256 in (%s)" % ",".join("?" * len(planned_by_sha)),
                        (ALLOW_SCOPE, ALLOW_PROFILE, *planned_by_sha)).fetchone()[0]
    finally:
        con.close()
    return n > 0


def refuse_indeterminate(info: dict) -> None:
    """Fail closed: the persisted provider evidence cannot establish that continuing is allowed. Nothing is dispatched,
    no stop is fabricated and the run record is left as it was; the refusal is recorded beside the runs."""
    (RUNS / "refusals").mkdir(parents=True, exist_ok=True)
    with open(RUNS / "refusals" / "REFUSALS.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps({"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "arm": args.arm, "resume": True,
                            "refused": f"indeterminate provider state: {info.get('why')}", "requests_sent": 0}) + "\n")
    progress("runner_refused_indeterminate", why=info.get("why"))
    print(f"REFUSED (indeterminate provider state): {info.get('why')} -- zero requests sent; the run record is left untouched")
    sys.exit(5)


started = time.perf_counter()
if args.resume:
    manifest = json.loads((OUT / "RUN.json").read_text(encoding="utf-8"))
    assert manifest["arm"] == args.arm and manifest["declaration_sha256"] == args.declaration_sha and manifest["a_tag"] == args.a_tag, "resume of another run"
    manifest.setdefault("resumes", []).append({"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "pid": os.getpid(), "clock": xtrack.now(), "reread": args.reread})
    manifest["deferred_before_resume"] = manifest.get("deferred", [])
    # ---- lifecycle: a terminal stop is loaded, validated and enforced before anything is written or dispatched ----
    saved_stop = load_terminal_stop()
    if saved_stop is None and manifest.get("terminal_stop"):
        saved_stop = manifest["terminal_stop"]                                  # the manifest knew the stop; the file was lost
    if saved_stop is None:
        reason = (manifest.get("runner_state") or {}).get("stopped")
        kind = next((k for pfx, k in TERMINAL_PREFIXES.items() if str(reason or "").startswith(pfx)), None)
        if kind:                                                                # a v4 run record: the reason alone is terminal
            saved_stop = persist_terminal_stop(kind, reason, [t for t in manifest.get("tripwire", []) if t.get("critical_on_resolved")], reconstructed=True)
    if saved_stop is None:
        jinfo = pj.load(JOURNAL.path, JOURNAL_BINDING, planned_sha256=set(planned_by_sha))
        if jinfo["state"] == "absent" and run_recorded_requests():
            jinfo = {"state": "indeterminate", "why": "no provider-outcome journal although this run recorded requests or charges"}
        if jinfo["state"] == "indeterminate":
            refuse_indeterminate(jinfo)
        manifest["resumes"][-1]["provider_journal"] = {k: jinfo.get(k) for k in ("state", "streak", "unresolved", "last_seq", "result_counts", "processes")}
        if jinfo["state"] == "ok" and jinfo["streak"] >= 3:
            # the provider-failure stop had been REACHED (its failures are durable) but not persisted: reconstruct it offline
            saved_stop = persist_terminal_stop("provider_failures", "stop: three consecutive provider failures", jinfo["trailing_failures"][-3:], reconstructed=True)
        elif jinfo["state"] == "ok":
            state["consecutive_failures"], state["recent_failures"] = jinfo["streak"], jinfo["trailing_failures"]   # a restart does not reset the breaker
            JOURNAL.continue_from(jinfo)
    if saved_stop is None:
        # OFFLINE reconstruction from the saved evidence (no dispatch): the same tripwire over every project whose
        # documents this arm already read (bound by the scoring contract), before any call can leave
        read_eps = {rd["ep"] for rd in dump_rows().values() if rd.get("sha256") in planned_by_sha and completed(rd)}
        if read_eps:
            crit0, binding0 = tripwire(read_eps)
            if crit0:
                saved_stop = persist_terminal_stop("critical_acceptance", f"stop: critical acceptance on a resolved label (reconstructed on resume from the saved evidence of EP-{', EP-'.join(sorted(read_eps))})", crit0, reconstructed=True)
    if saved_stop is not None:
        assert saved_stop.get("declaration_sha256") in (None, args.declaration_sha) and saved_stop.get("arm") in (None, args.arm), "the saved stop belongs to another binding"
        state["stopped"], state["terminal_stop"] = saved_stop["reason"], saved_stop
        manifest["terminal_stop"] = saved_stop
        manifest["status"] = "stopped"
        manifest["deferred"] = manifest.get("deferred_before_resume", [])
        manifest["resumes"][-1].update({"refused": "terminal stop preserved (plain --resume is not approval to clear it)", "requests_sent": 0, "terminal_kind": saved_stop["kind"]})
        progress("runner_refused_terminal_stop", kind=saved_stop["kind"], reason=saved_stop["reason"], reconstructed=saved_stop.get("reconstructed"))
        write_manifest(final=True)
        (RUNS / "refusals").mkdir(parents=True, exist_ok=True)
        with open(RUNS / "refusals" / "REFUSALS.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "tag": args.tag, "arm": args.arm, "resume": True,
                                "refused": f"terminal stop preserved: {saved_stop['reason']}", "requests_sent": 0}) + "\n")
        print(f"STOPPED (terminal, preserved): {saved_stop['reason']} -- zero requests sent; a separate explicit decision and binding are required to reopen this arm")
        sys.exit(4)
else:
    manifest = {"at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "a_tag": args.a_tag, "tag": args.tag, "arm": args.arm,
                "track": track, "dry_run": dry.DRY, "declaration_sha256": args.declaration_sha, "identities": arm["identities"], "commit": arm["commit"], "tree": arm["tree"],
                "context": CONTEXT, "harness_contract": HARNESS_CONTRACT, "runner_version": RUNNER_VERSION, "allowance_key": {"scope": ALLOW_SCOPE, "profile": ALLOW_PROFILE, "path": ALLOW_PATH}, "caps": {"durable_per_document": CAP, "reader_per_reading": READER_CAP_PER_READING, "project_rolling_day": LIMIT},
                "projects": {}, "not_attempted": [], "deferred": [], "tripwire": [], "resumes": []}
if not args.resume:
    JOURNAL.create(lifecycle=LIFECYCLE_CONTRACT, pid=os.getpid())   # before any request can leave
manifest["deferred"] = []
progress("runner_start", resume=args.resume, reread=args.reread, clock=xtrack.now())
write_manifest(final=False)        # the run record exists BEFORE any dispatch: an interrupted first project can still be resumed
with SessionLocal() as db:
    done = set(manifest["projects"])
    for project in db.query(Project).order_by(Project.id).all():
        ep_of[project.id] = project.ep_number
        rows = [r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.state == "fresh").order_by(ProjectDocument.id)
                if (r.path or "").lower().endswith(".pdf")]
        if project.ep_number in done and not args.reread:
            state["skipped_projects"].append(project.ep_number)
            continue
        if state["terminal_stop"] or (state["stopped"] and any(state["stopped"].startswith(p) for p in TERMINAL_PREFIXES)):
            manifest["not_attempted"].append({"ep": project.ep_number, "documents": [r.relative_path for r in rows], "reason": state["stopped"]})
            continue
        current = dump_rows()
        pending = []
        for r in rows:
            rd = current.get(f"EP-{project.ep_number}/{r.relative_path}".replace("\\", "/"))
            if rd and completed(rd) and not args.reread:
                state["skipped_completed"].append(rd["sha256"])
                continue
            pending.append(r)
        need, per_doc = worst_case(pending)
        cap_now = xtrack.capacity(project.ep_number, LIMIT)
        if pending and cap_now < need:
            rec = {"ep": project.ep_number, "needed_worst_case": need, "capacity": cap_now, "clock": xtrack.now(), "pending": per_doc, "requests_sent": 0}
            manifest["deferred"].append(rec)
            state["deferred"].append(project.ep_number)
            progress("project_deferred", **rec)
            write_manifest(final=False)
            print(project.ep_number, args.arm, "DEFERRED: needs", need, "capacity", cap_now, flush=True)
            continue
        t0 = time.perf_counter()
        n_before = state["per_ep"].get(project.ep_number, 0)
        progress("project_start", ep=project.ep_number, pending=[x["sha256"] for x in per_doc], worst_case=need, capacity=cap_now)
        counts = er.evidence_stage(db, project, [(r, pathlib.Path(r.path)) for r in pending], variant="EV1")
        db.commit()
        done.add(project.ep_number)
        manifest["projects"][project.ep_number] = {**counts, "seconds": round(time.perf_counter() - t0, 1), "documents_in": len(pending), "documents_skipped_completed": len(rows) - len(pending),
                                                   "requests": state["per_ep"].get(project.ep_number, 0) - n_before, "worst_case_reserved": need, "capacity_before": cap_now, "pid": os.getpid()}
        crit, binding = tripwire(done)
        manifest["tripwire"].append({"after": project.ep_number, "critical_on_resolved": crit, "binding": binding})
        if crit and not state["stopped"]:
            state["stopped"] = f"stop: critical acceptance on a resolved label after EP-{project.ep_number}"
            state["terminal_stop"] = persist_terminal_stop("critical_acceptance", state["stopped"], crit)
            manifest["terminal_stop"] = state["terminal_stop"]
        progress("project_end", ep=project.ep_number, requests=manifest["projects"][project.ep_number]["requests"], critical=len(crit))
        write_manifest(final=False)
        print(project.ep_number, args.arm, counts, manifest["projects"][project.ep_number]["requests"], "req", round(time.perf_counter() - t0, 1), "s",
              "| critical", len(crit), flush=True)
rows = dump_rows()
con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
usage = [dict(u) for u in con.execute("select u.id, p.ep_number, u.task, u.model, u.input_tokens, u.output_tokens, u.cached_input_tokens, u.reasoning_tokens, "
                                      "u.estimated_cost, u.latency_ms, u.cache_hit, u.escalated, u.outcome, u.at from ai_usage u left join projects p on p.id = u.project_id order by u.id")]
tables = {t: con.execute(f"select count(*) from {t}").fetchone()[0] for t in
          ("project_documents", "project_submittals", "project_shop_drawings", "background_jobs", "project_actions", "ai_usage", "document_readings")}
business = {}
for t in ("project_submittals", "project_shop_drawings", "project_actions"):
    business[t] = hashlib.sha256(json.dumps([list(r) for r in con.execute(f"select * from {t} order by id")], default=str).encode()).hexdigest()
business["project_documents_role"] = hashlib.sha256(json.dumps([list(r) for r in con.execute("select id, role from project_documents order by id")]).encode()).hexdigest()
con.close()
manifest.update({"tables": tables, "business_hashes": business, "ai_usage_rows": len(usage),
                 "fresh_requests_this_arm": sum(1 for u in usage if not u["cache_hit"] and str(u["task"]).startswith("evidence:")),
                 "status": "stopped" if (state["stopped"] or load_terminal_stop()) else ("deferred" if manifest["deferred"] else "completed"), "lifecycle": LIFECYCLE_CONTRACT})
write_manifest(final=True)
json.dump(rows, open(OUT / "rows.json", "w", encoding="utf-8"), indent=1, default=str)
json.dump(usage, open(OUT / "usage.json", "w", encoding="utf-8"), indent=1, default=str)
progress("runner_end", status=manifest["status"], requests=sum(state["per_ep"].values()))
print("done", args.tag, args.arm, manifest["status"], "requests", sum(state["per_ep"].values()), "seconds", manifest["seconds"], "state",
      {k: v for k, v in state.items() if k not in ("per_ep", "skipped_completed")}, state["per_ep"])
