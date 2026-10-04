"""Offline replay of one frozen four-arm arm under a flag configuration of the Review 29 candidate (C:/t/iso/cand-r29).
NO model request: a ReplayProvider answers only requests whose exact fingerprint (task, tier, prompt text and image
hashes) was recorded in the arm's io.jsonl; a request the original run refused before dispatch (its cache-key prefix in
the stored attempt log) is refused the same way; anything else fails as 'unrecorded' (never an invented answer).
The sandbox is a NEW copy of the frozen A base (final-A) under C:/t/r2x/r29-replay/<arm>-<config>; nothing frozen is written.
Usage: replay_arm.py <L1|L2|L3|L4> <config: off|IG|CA|DR|PA|ALL> -> <sandbox>/out/rows.json, REPLAY.json"""
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import sys
import time

arm, config = sys.argv[1], sys.argv[2]
CONFIGS = {"off": {}, "IG": {"AI_EVIDENCE_IDGUARD": "1"}, "CA": {"AI_EVIDENCE_ADJUDICATE": "1"}, "DR": {"AI_EVIDENCE_DECISION_REGION": "1"},
           "PA": {"AI_EVIDENCE_ASSOC": "1"},
           "ALL": {"AI_EVIDENCE_IDGUARD": "1", "AI_EVIDENCE_ADJUDICATE": "1", "AI_EVIDENCE_DECISION_REGION": "1", "AI_EVIDENCE_ASSOC": "1"}}
DECL = json.loads(pathlib.Path("C:/t/iso/work/r2x/r27/FINAL-DECLARATION.v2.json").read_text(encoding="utf-8"))
RUNS = pathlib.Path("C:/t/r2x/runs")
SRC_A, SRC_ARM = RUNS / "final-A", RUNS / f"final-{arm}"
ROOT = pathlib.Path("C:/t/r2x/r29-replay") / f"{arm}-{config}"
if ROOT.exists():
    sys.exit(f"{ROOT} exists: a replay never reuses a sandbox")
for d in ("db", "out"):
    (ROOT / d).mkdir(parents=True)
src = sqlite3.connect(f"file:{(SRC_A / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
dst = sqlite3.connect(str(ROOT / "db" / "default.db"))
src.backup(dst)
dst.close()
src.close()
for d in ("cache", "library", "uploads"):
    shutil.copytree(SRC_A / d, ROOT / d)
for k in [k for k in os.environ if k.startswith("AI_EVIDENCE_") or k.startswith("AI_LEDGER")]:
    os.environ.pop(k)
env = {"DATABASE_URL": f"sqlite:///{(ROOT / 'db' / 'default.db').as_posix()}", "CACHE_ROOT": str(ROOT / "cache"), "LIBRARY_ROOT": str(ROOT / "library"),
       "UPLOADS_ROOT": str(ROOT / "uploads"), "AI_ENABLED": "true", "PROJECTS_ROOT": "", "PROJECTS_ROOT_AUTODETECT": "false",
       "EXTRACTION_PROMOTE_OBSERVATIONS": "false", "DATASHEET_LIBRARIES": "{}", "ARCHIVE_DATASHEET_LIBRARIES": "{}", "COMPLIANCE_KNOWLEDGE_SOURCE": "",
       "COMPLIANCE_KNOWLEDGE_AUTODETECT": "false", "COMPLIANCE_KNOWLEDGE_IMPORT_ON_START": "false", "LIBRARY_RESCAN_SECONDS": "0",
       **DECL["provider"]["env"], **DECL["arms"][arm]["env"], **CONFIGS[config],
       # the replay is not subject to the wall clock: the original run's time-budget refusals are reproduced from its record
       # (the refusal map); a slow replay machine must not add refusals of its own (replay sandbox only)
       "AI_MAX_ELAPSED_S_PER_JOB": "86400"}
os.environ.update(env)
B = pathlib.Path("C:/t/iso/cand-r29/backend")
sys.path.insert(0, str(B))
os.chdir(B)
from app.ai import evidence_reader as er  # noqa: E402
from app.ai.provider import AiResponse, Usage  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.models import Project, ProjectDocument  # noqa: E402
from app.ai import submittal_reader  # noqa: E402

assert pathlib.Path(er.__file__).resolve().is_relative_to(B.resolve())

# ---- the recorded answers (fingerprint -> queue) and the recorded refusals (cache-key prefix -> log entry) ----------------
recorded: dict = {}
for line in open(SRC_ARM / "out" / "io.jsonl", encoding="utf-8"):
    x = json.loads(line)
    fp = hashlib.sha256(json.dumps([[p["label"], p["text"] if "text" in p else p["sha256"]] for p in x["parts"]]).encode()).hexdigest()
    log = (x.get("log") or [{}])[-1]
    recorded.setdefault((x["task"], x.get("tier") or "small", fp), []).append({"answer": x.get("answer"), "log": log})
stored = json.loads((SRC_ARM / "out" / "rows.json").read_text(encoding="utf-8"))
refused = {}            # a request the original run refused before dispatch, by (document, task, page): the same refusal under any
for r in stored.values():   # switch set (a switch changes the cache key, never which request the budget / breaker refused there)
    for a in (((r.get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or []):
        for c in a.get("calls") or []:
            if str(c.get("outcome", "")).startswith("budget"):
                refused.setdefault((r.get("sha256"), c.get("task"), c.get("page")), c)
stats = {"served": 0, "served_timeout_or_failure": 0, "refused_as_recorded": 0, "unrecorded": 0, "unrecorded_requests": []}


class ReplayProvider:
    name = "replay"
    ready = True
    status = "offline replay of recorded answers (no model request)"

    def complete(self, request):
        fp = hashlib.sha256(json.dumps([[p.label, p.text if hasattr(p, "text") else hashlib.sha256(p.png).hexdigest()] for p in request.parts]).encode()).hexdigest()
        queue = recorded.get((request.task, request.tier or "small", fp))
        if queue:
            rec = queue.pop(0) if len(queue) > 1 else queue[0]
            log = rec["log"]
            usage = Usage(input_tokens=log.get("input_tokens") or 0, output_tokens=log.get("output_tokens") or 0)
            if rec["answer"] is None:
                stats["served_timeout_or_failure"] += 1
                return AiResponse(data=None, usage=usage, model=log.get("model") or "", error=str(log.get("outcome") or "transport"),
                                  error_detail=log.get("error_detail"), latency_ms=log.get("latency_ms") or 0)
            stats["served"] += 1
            return AiResponse(data=rec["answer"], usage=usage, model=log.get("model") or "", latency_ms=log.get("latency_ms") or 0)
        stats["unrecorded"] += 1
        stats["unrecorded_requests"].append({"task": request.task, "fingerprint": fp[:16]})
        return AiResponse(data=None, model="replay", error="unrecorded", error_detail="replay: no recorded answer for this exact request")


# ---- refusals exactly as the original run made them (before any provider call) ---------------------------------------------
_original_call = er.EvidenceRun.call


def _replay_call(self, **kw):
    from app.ai import cache as result_cache
    from app.core.config import get_settings

    if not self.exhausted:
        settings = get_settings()
        tier = kw.get("tier", "small")
        model = settings.ai_model_standard if tier == "standard" else settings.ai_model_small
        fingerprint = hashlib.sha256(json.dumps([[p.label, p.text if hasattr(p, "text") else hashlib.sha256(p.png).hexdigest()]
                                                 for p in kw["parts"]]).encode()).hexdigest()
        key = result_cache.cache_key(scope="evidence", document_sha256=kw["sha256"], evidence_fingerprint=fingerprint, task=kw["task"],
                                     context={"variant": self.variant, "profile": self.profile, "policy": er.EVIDENCE_POLICY_VERSION, "tier": tier},
                                     parser_version=er.READER_VERSION, prompt_version=er.PROMPTS[kw["task"]], schema_version=er.SCHEMA_VERSION, model=model)
        c = refused.get((kw["sha256"], kw["task"], kw.get("page", 0)))
        if c is not None and not recorded.get((kw["task"], tier, fingerprint)):
            outcome = c["outcome"]
            reason = outcome[len("budget: "):]
            self.exhausted = "elapsed_time" if reason.startswith("elapsed_time") else reason
            self.log.append({"task": kw["task"], "page": kw.get("page", 0), "reason": kw.get("reason", ""), "tier": tier, "model_requested": model,
                             "key": key[:16], "cache_hit": False, "outcome": outcome})
            stats["refused_as_recorded"] += 1
            return None
    return _original_call(self, **kw)


er.EvidenceRun.call = _replay_call
submittal_reader.available = lambda project, provider=None: None
provider = ReplayProvider()
t0 = time.perf_counter()
per_project = {}
with SessionLocal() as db:
    for project in db.query(Project).order_by(Project.id).all():
        rows = [r for r in db.query(ProjectDocument).filter(ProjectDocument.project_id == project.id, ProjectDocument.state == "fresh").order_by(ProjectDocument.id)
                if (r.path or "").lower().endswith(".pdf")]
        counts = er.evidence_stage(db, project, [(r, pathlib.Path(r.path)) for r in rows], provider=provider, variant="EV1")
        db.commit()
        per_project[project.ep_number] = counts
con = sqlite3.connect(f"file:{(ROOT / 'db' / 'default.db').as_posix()}?mode=ro", uri=True)
con.row_factory = sqlite3.Row
out = {}
for r in con.execute("select d.id, p.ep_number, d.relative_path, d.role, d.state, d.error, d.sha256, d.reference, d.revision, d.status, d.system_code, d.extracted "
                     "from project_documents d join projects p on p.id = d.project_id"):
    out[f"EP-{r['ep_number']}/{r['relative_path']}".replace("\\", "/")] = {
        "id": r["id"], "ep": r["ep_number"], "role": r["role"], "state": r["state"], "error": r["error"], "sha256": r["sha256"],
        "mirror": {"reference": r["reference"], "revision": r["revision"], "status": r["status"], "system_code": r["system_code"]},
        "extracted": json.loads(r["extracted"]) if r["extracted"] else None}
business = {t: hashlib.sha256(json.dumps([list(x) for x in con.execute(f"select * from {t} order by id")], default=str).encode()).hexdigest()
            for t in ("project_submittals", "project_shop_drawings", "project_actions")}
business["project_documents_role"] = hashlib.sha256(json.dumps([list(x) for x in con.execute("select id, role from project_documents order by id")]).encode()).hexdigest()
con.close()
(ROOT / "out" / "rows.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
manifest = {"arm": arm, "config": config, "flags": CONFIGS[config], "env_switches": {k: v for k, v in env.items() if k.startswith("AI_EVIDENCE_")},
            "reader_version": er.READER_VERSION, "policy_version": er.EVIDENCE_POLICY_VERSION, "prompts": er.PROMPTS,
            "candidate_tree": str(B), "replay_job_elapsed_limit_s": 86400, "seconds": round(time.perf_counter() - t0, 1), "per_project": per_project, "provider": stats,
            "business_hashes": business, "model_requests": 0}
(ROOT / "out" / "REPLAY.json").write_text(json.dumps(manifest, indent=1, default=str), encoding="utf-8")
print(json.dumps({k: manifest[k] for k in ("arm", "config", "policy_version", "seconds")}), json.dumps({k: v for k, v in stats.items() if k != "unrecorded_requests"}))
