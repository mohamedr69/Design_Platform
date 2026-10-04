"""Review 31 dry run, one lane, NO model request. Runs the frozen candidate a8aaced (C:/t/iso/cand-r29) through the
capture store (capture_store.StoreProvider) and the per-lane stop guard, with an inner provider that REPLAYS the frozen
four-arm L3 captures (io.jsonl) and answers anything unrecorded with the failure 'unrecorded' (the Review 29 replay
label; never an invented answer). Such a failure is a dry-run artefact and is not fed to the stop guard. Every live provider class is replaced by one that raises, so a model request is impossible in this process.

  C  sandbox copy of B (final-A) -> C-from-B state check -> L3 switch set + IG, CA, DR, PA -> lane C of the store
  R  sandbox copy of B (final-A) -> C-from-B state check -> L3 switch set (reference)      -> lane R, served from the
     capture of C by content key; a request C never made goes to the inner provider once, in lane R
  P  no sandbox: the seeded 15 % variation probe over the answered lane-C dispatches, in lane P

Usage: run_lane.py <C|R|P> <sandbox_root_abs> <capture_store_abs> <out_dir_abs> [output tag, default the lane]
All paths are absolute: this process changes directory into the candidate tree and must never write there."""
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import sys
import time

lane, ROOT, STORE, OUT = sys.argv[1], pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3]), pathlib.Path(sys.argv[4])
TAG = sys.argv[5] if len(sys.argv) > 5 else lane
for p in (ROOT, STORE, OUT):
    assert p.is_absolute(), p
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
DECL = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
B_RUN = pathlib.Path("C:/t/r2x/runs/final-A")
B_RECORDED = json.loads(pathlib.Path("C:/t/iso/work/r2x/run-final/POST-RUN-BINDINGS.json").read_text(encoding="utf-8"))["sandbox_databases"]["A"]
L3 = pathlib.Path("C:/t/r2x/runs/final-L3")
C_SWITCHES = {"AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1", "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"}
C_MARKERS = ["identity-role-guard-2026-10-02.2", "conflict-adjudication-2026-10-02.2", "decision-region-2026-10-02.1", "page-association-2026-10-02.1"]
OUT.mkdir(parents=True, exist_ok=True)
CAND = pathlib.Path("C:/t/iso/cand-r29/backend")

state = None
if lane in ("C", "R"):
    if ROOT.exists():
        sys.exit(f"{ROOT} exists: a lane never reuses a sandbox")
    for d in ("db", "out"):
        (ROOT / d).mkdir(parents=True)
    src = sqlite3.connect(f"file:{(B_RUN / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
    dst = sqlite3.connect(str(ROOT / "db" / "default.db"))
    src.backup(dst)
    dst.close()
    src.close()
    for d in ("cache", "library", "uploads"):
        shutil.copytree(B_RUN / d, ROOT / d)
    import state_check  # noqa: E402

    state = state_check.check_c_start(B_RUN / "db" / "default.db", B_RECORDED, ROOT / "db" / "default.db", C_MARKERS,
                                      list(DECL["arms"]["L3"]["identities"]["PROMPTS"]))
    (OUT / f"STATE-CHECK-{TAG}.json").write_text(json.dumps(state, indent=1) + "\n", encoding="utf-8")
    if not state["ok"]:
        sys.exit(f"refused: {lane} does not start from the intended B state: {state['problems']}")

for k in [k for k in os.environ if k.startswith("AI_EVIDENCE_") or k.startswith("AI_LEDGER")]:
    os.environ.pop(k)
env = {"AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false", "EXTRACTION_PROMOTE_OBSERVATIONS": "false",
       "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "", "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false",
       "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0", **DECL["provider"]["env"], **DECL["arms"]["L3"]["env"],
       **(C_SWITCHES if lane in ("C", "P") else {}), "AI_MAX_ELAPSED_S_PER_JOB": "86400"}
if lane in ("C", "R"):
    env |= {"DATABASE_URL": f"sqlite:///{(ROOT / 'db' / 'default.db').as_posix()}", "CACHE_ROOT": str(ROOT / "cache"),
            "LIBRARY_ROOT": str(ROOT / "library"), "UPLOADS_ROOT": str(ROOT / "uploads")}
else:
    env |= {"DATABASE_URL": "sqlite:///C:/t/iso/tmp/r31-probe-no-db.db"}
os.environ.update(env)
sys.path.insert(0, str(CAND))
os.chdir(CAND)
from app.ai import provider as prov  # noqa: E402
from app.ai.provider import AiResponse, Usage  # noqa: E402

blocked_attempts = []


def _forbidden(self, request):
    blocked_attempts.append(type(self).__name__)
    raise RuntimeError("dry run: a live provider request is forbidden")


for cls in (prov.ClaudeProvider, prov.OpenAiProvider, prov.ClaudeCodeProvider):
    cls.complete = _forbidden
from app.ai import evidence_reader as er  # noqa: E402
from app.core.config import get_settings  # noqa: E402

assert pathlib.Path(er.__file__).resolve().is_relative_to(CAND.resolve())
import capture_store as CS  # noqa: E402
import stop_rules  # noqa: E402

settings = get_settings()
alias = lambda tier: settings.ai_model_standard if tier == "standard" else settings.ai_model_small  # noqa: E731
fp_of = lambda parts: hashlib.sha256(json.dumps([[p.label, p.text if hasattr(p, "text") else hashlib.sha256(p.png).hexdigest()] for p in parts]).encode()).hexdigest()  # noqa: E731

recorded: dict = {}
for line in open(L3 / "out" / "io.jsonl", encoding="utf-8"):
    x = json.loads(line)
    fp = hashlib.sha256(json.dumps([[p["label"], p["text"] if "text" in p else p["sha256"]] for p in x["parts"]]).encode()).hexdigest()
    recorded.setdefault((x["task"], x.get("tier") or "small", fp), []).append({"answer": x.get("answer"), "log": (x.get("log") or [{}])[-1]})
stats = {"inner_served": 0, "inner_served_failure": 0, "dry_unrecorded": 0, "refused_as_recorded": 0, "stopped_by_guard": 0}


class ReplayInner:
    """The inner provider of the dry run: recorded L3 answers only."""
    name, ready, status = "replay", True, "replay of the frozen L3 captures (no model request)"

    def complete(self, request):
        queue = recorded.get((request.task, request.tier or "small", fp_of(request.parts)))
        if queue:
            rec = queue.pop(0) if len(queue) > 1 else queue[0]
            log = rec["log"]
            usage = Usage(input_tokens=log.get("input_tokens") or 0, output_tokens=log.get("output_tokens") or 0)
            if rec["answer"] is None:
                stats["inner_served_failure"] += 1
                return AiResponse(data=None, usage=usage, model=log.get("model") or "", error=str(log.get("outcome") or "transport"), latency_ms=0)
            stats["inner_served"] += 1
            return AiResponse(data=rec["answer"], usage=usage, model=log.get("model") or "", latency_ms=0)
        stats["dry_unrecorded"] += 1
        return AiResponse(data=None, model="replay", error="unrecorded", error_detail="dry run: no recorded answer for this exact request")


store = CS.CaptureStore(STORE)
ctl = stop_rules.StopController()
events = []


class Guarded:
    """Per-lane stop guard in front of the store: refuses once the lane is stopped; reports every outcome."""
    name, ready, status = "guarded", True, "stop guard"

    def __init__(self, inner):
        self.inner = inner

    def complete(self, request):
        if not ctl.can_dispatch(lane):
            stats["stopped_by_guard"] += 1
            return AiResponse(data=None, model="guard", error="stopped", error_detail=f"lane {lane} stopped: {ctl.lanes[lane]['reason']}")
        resp = self.inner.complete(request)
        kind = "ok" if resp.ok else ("dry_unrecorded" if resp.error == "unrecorded" else "provider_failure")
        events.append({"lane": lane, "kind": kind, "task": request.task, "error": resp.error})
        if kind != "dry_unrecorded":
            ctl.observe(lane, kind)
        return resp


t0 = time.perf_counter()
manifest = {"lane": lane, "tag": TAG, "candidate_tree": str(CAND), "state_check": state, "model_requests": 0}
if lane == "P":
    cpol = json.loads((OUT / "LANE-C.json").read_text(encoding="utf-8"))["policy_version"]
    result = CS.probe(store, Guarded(ReplayInner()), "probe:" + cpol, alias, rate=0.15, seed="m2-r30-variation-2026-10-02")
    manifest |= {"probe": result}
else:
    rmap = {}
    for r in json.loads((L3 / "out" / "rows.json").read_text(encoding="utf-8")).values():
        for a in (((r.get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or []):
            for c in a.get("calls") or []:
                if str(c.get("outcome", "")).startswith("budget"):
                    rmap.setdefault((r.get("sha256"), c.get("task"), c.get("page")), c)
    _orig = er.EvidenceRun.call

    def _refusal_as_recorded(self, **kw):
        """The frozen L3 run refused these requests before dispatch (budget / time): the dry run refuses them the same way."""
        if not self.exhausted:
            tier = kw.get("tier", "small")
            c = rmap.get((kw["sha256"], kw["task"], kw.get("page", 0)))
            if c is not None and not recorded.get((kw["task"], tier, fp_of(kw["parts"]))):
                reason = c["outcome"][len("budget: "):]
                self.exhausted = "elapsed_time" if reason.startswith("elapsed_time") else reason
                self.log.append({"task": kw["task"], "page": kw.get("page", 0), "reason": kw.get("reason", ""), "tier": tier,
                                 "model_requested": alias(tier), "key": "", "cache_hit": False, "outcome": c["outcome"]})
                stats["refused_as_recorded"] += 1
                return None
        return _orig(self, **kw)

    er.EvidenceRun.call = _refusal_as_recorded
    CS.install_context(er)
    from app.ai import submittal_reader  # noqa: E402
    from app.database import SessionLocal  # noqa: E402
    from app.models import Project, ProjectDocument  # noqa: E402

    submittal_reader.available = lambda project, provider=None: None
    sp = CS.StoreProvider(store, lane, ReplayInner(), lambda: er.EVIDENCE_POLICY_VERSION, alias, reference_from="C" if lane == "R" else None)
    provider = Guarded(sp)
    per_project = {}
    with SessionLocal() as db:
        for project in db.query(Project).order_by(Project.id).all():
            rows = [r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.state == "fresh").order_by(ProjectDocument.id)
                    if (r.path or "").lower().endswith(".pdf")]
            per_project[project.ep_number] = er.evidence_stage(db, project, [(r, pathlib.Path(r.path)) for r in rows], provider=provider, variant="EV1")
            db.commit()
    con = sqlite3.connect(f"file:{(ROOT / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    out = {}
    for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.system_code, d.extracted "
                         "from project_documents d join projects p on p.id = d.project_id"):
        out[f"EP-{r['ep_number']}/{r['relative_path']}".replace("\\", "/")] = {
            "id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
            "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
            "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
    con.close()
    (OUT / f"rows-{TAG}.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    manifest |= {"policy_version": er.EVIDENCE_POLICY_VERSION, "reader_version": er.READER_VERSION,
                 "env_switches": {k: v for k, v in env.items() if k.startswith("AI_EVIDENCE_")}, "per_project": per_project,
                 "store_dispatched_to_inner": sp.dispatched}
manifest |= {"seconds": round(time.perf_counter() - t0, 1), "inner": stats, "events": events, "lane_stop_state": ctl.state()["lanes"][lane],
             "live_provider_attempts_blocked": blocked_attempts}
assert not blocked_attempts, "a live provider was reached"
(OUT / f"LANE-{TAG}.json").write_text(json.dumps(manifest, indent=1, default=str) + "\n", encoding="utf-8")
print(json.dumps({k: manifest.get(k) for k in ("lane", "policy_version", "seconds", "inner", "store_dispatched_to_inner", "lane_stop_state")}, default=str))
