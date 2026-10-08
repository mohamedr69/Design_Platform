"""R43-42 (review45, new): the dry-only BASELINE-FACTS drill of lane B (Verification 44 option 1; A-13 item 2).

  runner_r32.py run --mode dry --dry-baseline-facts SPEC.json --stamp S --run-set RS.json --binding BM.json --binding-sha SHA
                    [--sandbox-base D]
SPEC.json is exactly {"drill": "baseline-facts", "lane": "B", "tree": "C:/t/iso/frozen-r13",
                      "documents": [{"pool_id": "F009", "staged_sha256": ...}, {"pool_id": "F020", ...}, {"pool_id": "F030", ...}]}.

What it is. One lane-B pass of the REAL application processing (frozen-r13, reader 'application') over exactly the three
run-set documents F009, F020 and F030 of EP-27331 (ALLOW: pool id AND staged sha256), with AI off and the refusing global
provider (run_control_r38.RefusingGlobalProvider) installed right after the application's provider module is imported and
before any other application module; the lane's OWN code path does the reading, the fact extraction and the tripwire
input (lane_r32: document_processing.run with its process / read_form_or_raise / apply_form_reading hooks, row_dict,
b_tripwire -> tripwire_r32.py -> lane_judge_r32 rule CP-R38, 'after_document' and 'final'), so the tripwire judges the
real facts against the resolved truth exactly as live B would. Everything is written under ONE drill folder
<sandbox base>/r32-drill-<stamp> (never r32-v<N>): out/ (TRUTH-R32.json, DRILL-CONFIG.json, LANE-B.json, rows-B.json,
DRILL-TRACE.json, DRILL-FACTS.json, DRILL-REPORT.json, the lane log) and B/ (the lane's sandbox).

What it never does. No live mode, no other lane, tree, document or drill flag (--dry-fault / --dry-inject /
--dry-synthetic), no resume, no declaration. It never creates, opens or consults a run state, allowance, capture store,
ledger (real or fake), ledger scope, authorization, nonce, token or RUN file: in the runner the functions that would do so
are replaced by refusals for the drill's duration (forbid), and in the lane the allowance / capture-store objects are
Forbidden sentinels that refuse (and record) any use; a configuration that names any of them is refused before the lane
imports the application (check_config). 0 model requests: AI is off; the refusing provider and the dry stub must record
0 calls; live provider classes are blocked by the lane (unchanged dry rule).

Evidence of the path (call tracing). The lane installs a profiler (Tracer, sys.setprofile / threading.setprofile) for the
whole drill and records every call of the lane's own B functions, of document_processing.run, document_sync's process /
read path, the submittal reader's availability and form read, the OCR probe, and every provider complete(); the
tripwire inputs are captured from b_tripwire's own arguments. DRILL-TRACE.json is that record; the tests assert on it.

The pass criterion (DRILL-CRITERION.md, declared before the first run) is evaluated by criterion(); a critical acceptance
on resolved truth is a FAIL that is reported, never fixed. The other dry rules are unchanged: reader 'none' over the real
cohort, --dry-synthetic over SYN* documents only, and the lane assertion that dry mode never reads a cohort document
except under this drill's allow-list."""
from __future__ import annotations

import contextlib
import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import threading
import time

HERE = pathlib.Path(__file__).resolve().parent
NAME = "baseline-facts"
FLAG = "--dry-baseline-facts"
LANE = "B"
TREE = "C:/t/iso/frozen-r13"
BASELINE_BACKEND = "C:/t/iso/frozen-r13/backend"
EP = "27331"
RUN_SET_SHA256 = "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"
TRUTH_SHA256 = "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"
ALLOW = {"F009": "970ddb0f5b59199b41f33bee8356dd87418d9daff26ec9a9b8a72a3538bab415",
         "F020": "599d36be15e6eded0fcbe4226afdb49c9b282f6bcbbd13c3c3376872da1891db",
         "F030": "feec64cdcb0b7a95262c9991fd09830d810f88e75d87be05ac308c106047010a"}
FOLDER_PREFIX = "r32-drill-"
FIELDS = ("identity", "revision", "decision")
STOP_CONDITION = "INVALID: baseline incomplete (critical acceptance on resolved truth in B)"
CONFIG_NAME = "DRILL-CONFIG.json"
# never in a drill configuration (or only as None): the run's allowance / capture store / run key, every ledger and
# declaration value, every dry injection, the provider environment and the run budgets
FORBIDDEN_KEYS = ("store", "allowance", "run_key", "ledger", "dry_ledger", "dry_inject", "dry_application_limits", "declaration_path",
                  "declaration_sha256", "auth_path", "provider_env", "caps", "parent", "project_window", "project_totals")
_STAMP = re.compile(r"[A-Za-z0-9._-]{3,40}")
_LIVE_RUN = re.compile(r"r32-v\d", re.IGNORECASE)
VIOLATIONS: list[str] = []
TRACER = None                                                      # the lane's Tracer (set by lane_r32 in the drill only)


def _refused():
    import preflight_r32 as PF
    return PF.Refused


def refuse(msg: str):
    raise _refused()(msg)


def _norm(p) -> str:
    return str(p).replace("\\", "/").rstrip("/").lower()


def sha256_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def sha256_file(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


# ---- the allow-list, the folder and the configuration -----------------------------------------------------------------
def spec_documents(spec) -> list[dict]:
    """The drill's SPEC: exactly lane B, the frozen-r13 tree and the three allowed documents by id AND staged sha256."""
    if not isinstance(spec, dict) or set(spec) != {"drill", "lane", "tree", "documents"} or spec.get("drill") != NAME:
        refuse(f"refused: a baseline-facts drill spec is exactly {{drill: {NAME!r}, lane, tree, documents}} ({sorted(spec) if isinstance(spec, dict) else spec!r})")
    if spec["lane"] != LANE:
        refuse(f"refused: the baseline-facts drill runs lane B only (lane {spec['lane']!r})")
    if _norm(spec["tree"]) != _norm(TREE):
        refuse(f"refused: the baseline-facts drill runs on {TREE} only (tree {spec['tree']!r})")
    docs = spec["documents"]
    if not isinstance(docs, list) or any(not isinstance(d, dict) or set(d) != {"pool_id", "staged_sha256"} for d in docs):
        refuse("refused: every drill document is exactly {pool_id, staged_sha256}")
    ids = [d["pool_id"] for d in docs]
    if len(ids) != len(ALLOW) or sorted(ids) != sorted(ALLOW):
        refuse(f"refused: the baseline-facts drill takes exactly {sorted(ALLOW)} (given {ids})")
    for d in docs:
        if d["staged_sha256"] != ALLOW[d["pool_id"]]:
            refuse(f"refused: {d['pool_id']} staged sha256 {d['staged_sha256']} is not the allowed {ALLOW[d['pool_id']]}")
    return docs


def drill_folder(base, stamp) -> pathlib.Path:
    """<sandbox base>/r32-drill-<stamp>: never a live run folder name (r32-v<N>), never an existing folder."""
    if not stamp or not _STAMP.fullmatch(str(stamp)) or _LIVE_RUN.search(str(stamp)):
        refuse(f"refused: a drill stamp is 3-40 characters A-Z a-z 0-9 . _ - and never names a live run (r32-v<N>) ({stamp!r})")
    folder = pathlib.Path(base) / f"{FOLDER_PREFIX}{stamp}"
    if folder.exists():
        refuse(f"refused: {folder.as_posix()} exists (a drill folder is never reused)")
    return folder


def select(run_set: list, truth: dict, docs: list) -> list:
    """The three run-set entries, in run-set order; the truth's staged sha256 must be the allowed one."""
    out = [d for d in run_set if d["pool_id"] in ALLOW]
    if sorted(d["pool_id"] for d in out) != sorted(ALLOW):
        refuse(f"refused: the run set does not hold {sorted(ALLOW)}")
    for d in out:
        t = truth["documents"][d["pool_id"]]
        if t["staged_sha256"] != ALLOW[d["pool_id"]] or str(t["ep"]) != EP or str(d["ep"]) != EP:
            refuse(f"refused: {d['pool_id']} in the truth is not the allowed document (sha256 {t['staged_sha256']}, ep {t['ep']})")
    return out


def check_config(cfg: dict, lane: str | None = None) -> dict:
    """The runner (before the lane starts) and the lane (before it imports the application) refuse any drill configuration
    that is not exactly: dry mode, reader 'application', lane B, the frozen-r13 tree, the three allowed documents, a
    r32-drill-<stamp> folder, a B sandbox only, and NO allowance / capture store / run key / ledger / declaration /
    injection / provider environment / budget value."""
    if cfg.get("drill") != NAME:
        refuse(f"refused: not a baseline-facts drill configuration ({cfg.get('drill')!r})")
    if lane is not None and lane != LANE:
        refuse(f"refused: the baseline-facts drill runs lane B only (lane {lane})")
    if cfg.get("mode") != "dry":
        refuse(f"refused: the baseline-facts drill is dry mode only (mode {cfg.get('mode')!r})")
    if cfg.get("reader") != "application":
        refuse("refused: the baseline-facts drill runs the application reader")
    bad = [k for k in FORBIDDEN_KEYS if cfg.get(k) is not None]
    if bad:
        refuse(f"refused: the baseline-facts drill never consults or writes {bad} (run state, allowance, capture store, ledger, scope, "
               "authorization, nonce, RUN or provider values)")
    name = pathlib.PurePosixPath(str(cfg.get("run_folder") or "").replace("\\", "/")).name
    if not name.startswith(FOLDER_PREFIX) or _LIVE_RUN.search(name):
        refuse(f"refused: the drill folder is r32-drill-<stamp> ({cfg.get('run_folder')!r})")
    if set(cfg.get("sandbox") or {}) != {LANE}:
        refuse(f"refused: the baseline-facts drill has a B sandbox only ({sorted(cfg.get('sandbox') or {})})")
    if _norm((cfg.get("trees") or {}).get("baseline") or "") != _norm(BASELINE_BACKEND):
        refuse(f"refused: the baseline-facts drill runs on {BASELINE_BACKEND} only ({(cfg.get('trees') or {}).get('baseline')!r})")
    ids = sorted(d["pool_id"] for d in cfg.get("run_set") or [])
    if ids != sorted(ALLOW):
        refuse(f"refused: the baseline-facts drill takes exactly {sorted(ALLOW)} (given {ids})")
    return {"drill": NAME, "lane": LANE, "documents": ids, "forbidden_keys_absent": list(FORBIDDEN_KEYS)}


def check_cohort(run_set: list, truth: dict, truth_path) -> list:
    """lane_r32's dry-mode cohort assertion, extended for this drill only: the documents are exactly the allow-list by id
    AND staged sha256, judged against the declared truth file."""
    if sha256_file(truth_path) != TRUTH_SHA256:
        refuse(f"refused: the drill's truth file is not the declared truth {TRUTH_SHA256}")
    ids = sorted(d["pool_id"] for d in run_set)
    if ids != sorted(ALLOW) or any(truth["documents"][p]["staged_sha256"] != ALLOW[p] for p in ids):
        refuse(f"refused: dry mode reads a cohort document only in the baseline-facts drill and only {sorted(ALLOW)} ({ids})")
    return ids


def check_provider(prov, expected) -> dict:
    """The application's global provider must be the drill's refusing provider (run_control_r38.RefusingGlobalProvider)."""
    got = prov.get_provider()
    if expected is None or type(expected).__name__ != "RefusingGlobalProvider" or got is not expected:
        refuse(f"refused: the drill's global provider is {type(got).__name__}, not the refusing global provider")
    return {"global_provider": type(got).__name__, "name": getattr(got, "name", None), "calls": getattr(got, "calls", None)}


class Forbidden:
    """Stands for the run's allowance / capture store in the drill lane: any use refuses and is recorded (VIOLATIONS), so a
    use caught by the application's own exception handling still fails the lane at its end."""

    def __init__(self, what: str):
        object.__setattr__(self, "_what", what)

    def __getattr__(self, name):
        msg = f"refused: the baseline-facts drill never consults {object.__getattribute__(self, '_what')} (.{name})"
        VIOLATIONS.append(msg)
        refuse(msg)

    def __setattr__(self, name, value):
        self.__getattr__(name)


@contextlib.contextmanager
def forbid(RN):
    """Runner side: for the drill's duration every function that creates, opens or consults a run state, allowance, capture
    store, ledger, ledger scope, declaration, authorization, nonce or model identity record refuses."""
    import allowance_r32 as AL
    import dispatch_guard_r32 as DG
    import model_identity_r38 as MI
    import preflight_r32 as PF

    targets = [(AL, n) for n in ("LaneAllowance", "AllowanceProvider", "bind_store", "bound_key")] + \
              [(DG, n) for n in ("check", "authorize", "GuardedProvider")] + \
              [(PF, n) for n in ("verify_ledger_scope", "ledger_counts", "ledger_snapshot", "ledger_live_check", "load_declaration", "live_preflight",
                                 "verify_bounds", "verify_cli")] + \
              [(MI, n) for n in ("record_invocation", "check_version", "cli_version")] + \
              [(RN, n) for n in ("ledger_state", "reentry_proof", "create_allowance_atomic", "open_allowance", "allowance_state", "store_counts",
                                 "execute", "_state_write", "_state_of_reentry", "_close")]
    saved = []

    def stop(label):
        def _f(*_a, **_k):
            msg = f"refused: the baseline-facts drill never consults {label}"
            VIOLATIONS.append(msg)
            raise PF.Refused(msg)
        return _f

    for mod, name in targets:
        if hasattr(mod, name):
            saved.append((mod, name, getattr(mod, name)))
            setattr(mod, name, stop(f"{mod.__name__}.{name}"))
    try:
        yield [f"{m.__name__}.{n}" for m, n, _ in saved]
    finally:
        for mod, name, fn in saved:
            setattr(mod, name, fn)


# ---- call tracing (lane side) --------------------------------------------------------------------------------------------
WATCH = {"lane_r32": {"process", "read_form_or_raise", "apply_form_reading", "_after", "b_tripwire", "row_dict", "_run_call", "dump_rows",
                      "observe_trip", "_forbidden"},
         "document_processing": {"run", "read_task"},
         "document_sync": {"process", "apply_form_reading", "read_form_or_raise", "read_in_completion_order"},
         "submittal_reader": {"available", "read_form", "check"},
         "submittal_scanner": {"ocr_available"},
         "run_control_r38": {"complete"},
         "app_provider": {"complete"}}
RETURNS = {("submittal_reader", "available"), ("submittal_scanner", "ocr_available")}


class Tracer:
    """sys.setprofile / threading.setprofile over the drill lane: every call of the watched functions (WATCH) with its
    caller; b_tripwire's arguments (when, and the rows exactly as the tripwire receives them) are captured."""

    def __init__(self, harness_dir, tree_backend):
        h, t = _norm(harness_dir), _norm(tree_backend)
        self.files = {f"{h}/lane_r32.py": "lane_r32", f"{h}/run_control_r38.py": "run_control_r38",
                      f"{t}/app/services/document_processing.py": "document_processing", f"{t}/app/services/document_sync.py": "document_sync",
                      f"{t}/app/ai/submittal_reader.py": "submittal_reader", f"{t}/app/services/submittal_scanner.py": "submittal_scanner",
                      f"{t}/app/ai/provider.py": "app_provider"}
        self.cache: dict[str, str | None] = {}
        self.calls: list[dict] = []
        self.tripwire_inputs: list[dict] = []
        self.started = self.stopped = None

    def _label(self, filename):
        lab = self.cache.get(filename, 0)
        if lab == 0:
            lab = self.files.get(_norm(os.path.abspath(filename))) if filename and not filename.startswith("<") else None
            self.cache[filename] = lab
        return lab

    def _prof(self, frame, event, arg):
        if event not in ("call", "return"):
            return
        try:
            self._record(frame, event, arg)
        except Exception as exc:  # noqa: BLE001 -- a profiler that raises would change the lane; the failure is recorded
            self.calls.append({"seq": len(self.calls) + 1, "event": "trace_error", "error": f"{type(exc).__name__}: {exc}"[:200]})

    def _record(self, frame, event, arg):
        co = frame.f_code
        lab = self._label(co.co_filename)
        if lab is None or co.co_name not in WATCH[lab]:
            return
        if event == "return":
            if (lab, co.co_name) in RETURNS:
                self.calls.append({"seq": len(self.calls) + 1, "event": "return", "file": lab, "function": co.co_name, "returned": repr(arg)[:200]})
            return
        back = frame.f_back
        rec = {"seq": len(self.calls) + 1, "event": "call", "file": lab, "function": co.co_name, "thread": threading.current_thread().name,
               "caller": f"{self._label(back.f_code.co_filename) or pathlib.PurePath(back.f_code.co_filename).name}:{back.f_code.co_name}" if back else None}
        loc = frame.f_locals
        try:
            if lab == "lane_r32" and co.co_name == "b_tripwire":
                rows = json.loads(json.dumps(loc.get("rows_by_pid"), default=str, ensure_ascii=False))
                rec |= {"when": loc.get("when"), "pool_ids": sorted(rows or {})}
                self.tripwire_inputs.append({"seq": rec["seq"], "when": loc.get("when"), "rows": rows})
            elif co.co_name in ("process", "apply_form_reading") and lab in ("lane_r32", "document_sync"):
                row, project = loc.get("row"), loc.get("project")
                rec |= {"relative_path": getattr(row, "relative_path", None), "ep": getattr(project, "ep_number", None)}
            elif lab == "document_processing" and co.co_name == "run":
                rec |= {"ep": getattr(loc.get("project"), "ep_number", None)}
            elif co.co_name == "complete":
                rec |= {"self": type(loc.get("self")).__name__, "task": getattr(loc.get("request"), "task", None)}
        except Exception as exc:  # noqa: BLE001 -- tracing never changes the lane; the failure is recorded
            rec["trace_error"] = f"{type(exc).__name__}: {exc}"[:200]
        self.calls.append(rec)

    def start(self):
        self.started = time.time()
        threading.setprofile(self._prof)
        sys.setprofile(self._prof)

    def stop(self):
        sys.setprofile(None)
        threading.setprofile(None)
        self.stopped = time.time()

    def summary(self) -> dict:
        n = {}
        for c in self.calls:
            if c["event"] == "call":
                k = f"{c['file']}.{c['function']}"
                n[k] = n.get(k, 0) + 1
        return {"calls_by_function": dict(sorted(n.items())), "tripwire_calls": [{"seq": t["seq"], "when": t["when"], "pool_ids": sorted(t["rows"])}
                                                                                  for t in self.tripwire_inputs],
                "provider_complete_calls": [c for c in self.calls if c["event"] == "call" and c["function"] == "complete"]}

    def record(self) -> dict:
        return {"method": "sys.setprofile and threading.setprofile in the lane process for the whole drill (call and return events of the "
                          "watched functions; b_tripwire's arguments captured as the tripwire receives them)",
                "watched": {k: sorted(v) for k, v in WATCH.items()}, "files": self.files, "started": self.started, "stopped": self.stopped,
                "summary": self.summary(), "calls": self.calls, "tripwire_inputs": self.tripwire_inputs}


def lane_manifest(*, recorder, ctl, trip, provider, prov, stub, blocked, isolation, app_env, env_check, task_kinds, stopped, seconds,
                  install, tracer) -> dict:
    """The drill lane's manifest (LANE-B.json): no allowance, store, gate or ledger figure exists to report."""
    docs = recorder.documents()
    return {"drill": NAME, "documents": docs, "tripwire": trip, "stop_state": ctl.state(), "lane_stop_state": ctl.state()["lanes"][LANE],
            "stopped": stopped, "seconds": seconds, "limit_events": recorder.events, "application_env_check": app_env, "environment_check": env_check,
            "task_kinds": sorted(task_kinds), "isolation_check": isolation, "live_provider_attempts_blocked": blocked,
            "dry_stub_calls": stub.calls, "model_requests": 0,
            "global_provider": {"lane_kind": "refusing (baseline-facts drill)", "installed": install,
                                "at_end": type(prov.get_provider()).__name__, "still_installed_at_end": prov.get_provider() is provider,
                                "requests_refused": provider.calls, "records": provider.records, "events": provider.events},
            "violations": list(VIOLATIONS), "trace": tracer.summary(),
            "not_consulted": "run state, allowance, capture store, gate, ledger (real or fake), ledger scope, authorization, nonce, token, RUN file"}


def finish_lane(out, manifest, tracer) -> int:
    """Writes LANE-B.json and DRILL-TRACE.json; a drill rule broken in the lane (a forbidden object used, the provider
    replaced, a live provider reached, isolation lost) fails the lane (exit 3) AFTER its evidence is written."""
    out = pathlib.Path(out)
    (out / "DRILL-TRACE.json").write_text(json.dumps(tracer.record(), indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n",
                                          encoding="utf-8", newline="\n")
    (out / "LANE-B.json").write_text(json.dumps(manifest, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n",
                                     encoding="utf-8", newline="\n")
    problems = list(manifest["violations"])
    if not manifest["global_provider"]["still_installed_at_end"]:
        problems.append("the refusing global provider was replaced during the drill")
    if manifest["live_provider_attempts_blocked"]:
        problems.append(f"a live provider was reached: {manifest['live_provider_attempts_blocked']}")
    if not (manifest["isolation_check"].get("end") or {}).get("ok"):
        problems.append(f"isolation at the end: {(manifest['isolation_check'].get('end') or {}).get('refused')}")
    print(json.dumps({"drill": NAME, "lane": LANE, "documents": {p: v["status"] for p, v in manifest["documents"].items()},
                      "stop": manifest["stop_state"]["comparison"], "refusing_provider_calls": manifest["global_provider"]["requests_refused"],
                      "dry_stub_calls": manifest["dry_stub_calls"], "problems": problems}, default=str))
    if problems:
        print(f"refused: baseline-facts drill rule broken in the lane: {problems}", file=sys.stderr)
        return 3
    return 0


# ---- the runner side -----------------------------------------------------------------------------------------------------
def run(args, RN) -> int:
    """`runner_r32.py run --mode dry --dry-baseline-facts SPEC.json ...` (called by runner_r32.main before anything else)."""
    import dispatch_guard_r32 as DG
    import preflight_r32 as PF
    import sandbox_ingest_r32 as SI

    if args.mode != "dry":
        refuse("refused: --dry-baseline-facts is a dry-mode drill only")
    if args.command != "run":
        refuse("refused: the baseline-facts drill is one fresh run of its own folder; it is never resumed")
    if args.dry_fault or args.dry_inject or args.dry_synthetic:
        refuse("refused: the baseline-facts drill takes no other drill (--dry-fault / --dry-inject / --dry-synthetic)")
    if args.declaration or args.declaration_sha or args.out:
        refuse("refused: the baseline-facts drill takes no declaration and no --out (its folder is r32-drill-<stamp>)")
    if os.environ.get(DG.TOKEN_ENV) is not None:
        refuse(f"refused: {DG.TOKEN_ENV} is set; the drill never reads an owner token (nothing was created)")
    VIOLATIONS.clear()
    started = time.time()
    with forbid(RN) as forbidden:
        spec = json.loads(pathlib.Path(args.dry_baseline_facts).read_text(encoding="utf-8"))
        docs = spec_documents(spec)
        binding = PF.verify_binding(args.binding, args.binding_sha)
        rs_sha = sha256_file(args.run_set)
        if rs_sha != RUN_SET_SHA256:
            refuse(f"refused: the run set {rs_sha} is not the declared run set {RUN_SET_SHA256}")
        base = PF.sandbox_base(args.sandbox_base)
        folder = drill_folder(base, args.stamp)
        disk = PF.verify_free_disk(PF.dry_disk_precondition(base.as_posix()))
        heads = PF.heads()
        truth = PF.build_truth()
        if sha256_text(PF.truth_text(truth)) != TRUTH_SHA256:
            refuse(f"refused: the built truth is not the declared truth {TRUTH_SHA256}")
        gate = PF.population(truth)
        run_set = select(PF.load_run_set(args.run_set, truth), truth, docs)
        folder.mkdir(parents=True)
        out = folder / "out"
        out.mkdir()
        truth_path = out / "TRUTH-R32.json"
        truth_path.write_text(PF.truth_text(truth), encoding="utf-8", newline="\n")
        SI.SANDBOX_BASE = pathlib.Path(base)
        ing = SI.ingest(folder / LANE, [d["pool_id"] for d in run_set], truth)
        if not ing["ok"]:
            refuse("refused: the drill's B sandbox ingestion check failed")
        cfg = {"drill": NAME, "mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(truth_path),
               "run_set": run_set, "run_set_path": str(args.run_set), "run_folder": folder.as_posix(), "run_key": None, "stamp": args.stamp,
               "invocation": 1, "sandbox_base": pathlib.Path(base).as_posix(), "trees": dict(RN.TREES), "sandbox": {LANE: str(folder / LANE)},
               "binding": str(args.binding), "binding_sha256": binding["sha256"], "lane_switches": {LANE: dict(RN.DRY_LANE_SWITCHES[LANE])},
               "model_identity": dict(RN.DRY_PINS), "cli_version": RN.DRY_CLI_VERSION, "switch_source": PF.DRY_LANE_SWITCHES_LABEL,
               "policies": {LANE: "B:accepted-path:evidence-off"}, "application_env": dict(PF.APPLICATION_ENV),
               "lane_task_kinds": {LANE: PF.task_kinds_for(RN.DRY_LANE_SWITCHES)[LANE]}, "ai_enabled": False}
        check_config(cfg, LANE)
        cfg_path = out / CONFIG_NAME
        cfg_path.write_text(json.dumps(cfg, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        env = RN.lane_env("dry", folder / LANE, LANE, cfg)
        env["AI_ENABLED"] = "false"                                   # AI off: the application reads deterministically
        env.pop(DG.TOKEN_ENV, None)
        lane = RN.run_lane(LANE, cfg_path, out, env, RN.TREES["baseline"])
        facts = facts_of(out, truth_path, env)
        report = build_report(lane, facts, json.loads((out / "rows-B.json").read_text(encoding="utf-8")), run_set)
        report |= {"drill": NAME, "folder": folder.as_posix(), "stamp": args.stamp, "binding": binding, "run_set_sha256": rs_sha,
                   "truth_sha256": sha256_file(truth_path), "heads": heads, "free_disk": disk, "population_gate": gate.get("action"),
                   "ingest": {k: ing[k] for k in ("ok", "documents", "projects", "registration", "b_database_sha256")},
                   "forbidden_in_runner": forbidden, "violations": list(VIOLATIONS), "seconds": round(time.time() - started, 1),
                   "spec_sha256": sha256_file(args.dry_baseline_facts), "statement": "a dry drill: 0 model requests; it authorizes nothing"}
        report["criterion"] = criterion(report)
        (out / "DRILL-REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n",
                                               encoding="utf-8", newline="\n")
    print(json.dumps({"drill": NAME, "folder": folder.as_posix(), "criterion": report["criterion"]["result"],
                      "documents": {p: {k: v.get(k) for k in ("exercised", "facts_final", "resolved_criticals", "unresolved_criticals")}
                                    for p, v in report["per_document"].items()},
                      "stop_condition_fired": report["stop_condition_fired"], "requests": report["requests"]}, default=str))
    return 0


def facts_of(out, truth_path, env) -> dict:
    """The facts of every tripwire input the lane gave (captured in DRILL-TRACE.json), by the SAME functions the tripwire
    uses (tripwire_r32.facts_from_row, tripwire, lane_judge_r32.judge_document), in a subprocess like b_tripwire's."""
    o = pathlib.Path(out) / "DRILL-FACTS.json"
    r = subprocess.run([sys.executable, str(HERE / "drill_r45.py"), "facts", str(truth_path), str(pathlib.Path(out) / "DRILL-TRACE.json"), str(o)],
                       cwd=str(HERE), env={**env, "PYTHONDONTWRITEBYTECODE": "1", "AI_ENABLED": "false"}, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"drill facts failed: {r.stderr[-2000:]}")
    return json.loads(o.read_text(encoding="utf-8"))


def build_report(lane: dict, facts: dict, rows: dict, run_set: list) -> dict:
    trip = lane.get("tripwire") or []
    lane_pairs = [(t["pool_id"], t["when"], json.dumps(t["resolved"], sort_keys=True), json.dumps(t["unresolved"], sort_keys=True)) for t in trip]
    re_pairs = [(pid, c["when"], json.dumps(v["resolved"], sort_keys=True), json.dumps(v["unresolved"], sort_keys=True))
                for c in facts["calls"] for pid, v in c["documents"].items()]
    per = {}
    for d in run_set:
        pid = d["pool_id"]
        row = rows.get(d["doc_key"]) or {}
        evals = [{"when": c["when"], "seq": c["seq"], "facts": len(c["documents"][pid]["facts"]),
                  "resolved_criticals": c["documents"][pid]["resolved"], "unresolved_criticals": c["documents"][pid]["unresolved"],
                  "fields": c["documents"][pid]["fields"]} for c in facts["calls"] if pid in c["documents"]]
        final = next((c["documents"][pid] for c in reversed(facts["calls"]) if pid in c["documents"] and c["when"] == "final"), None)
        status = (lane.get("documents") or {}).get(pid) or {}
        n_facts = max([e["facts"] for e in evals] or [0])
        read = row.get("extracted") is not None and row.get("state") in ("fresh", "processing")
        res = [c for e in evals for c in e["resolved_criticals"]]
        unres = [c for e in evals for c in e["unresolved_criticals"]]
        reason = None
        if not read:
            reason = f"not read by the application (row state {row.get('state')!r}, error {row.get('error')!r}, lane status {status.get('status')!r}: {status.get('reason')!r})"
        elif n_facts == 0:
            reason = "read, but the tripwire evaluated no fact"
        per[pid] = {"doc_key": d["doc_key"], "staged_sha256": ALLOW[pid], "lane_status": status.get("status"), "lane_reason": status.get("reason"),
                    "row": {k: row.get(k) for k in ("role", "state", "error", "sha256", "mirror")}, "extracted_present": row.get("extracted") is not None,
                    "evaluations": evals, "facts_final": len((final or {}).get("facts") or []), "facts": (final or {}).get("facts"),
                    "judged_rows_final": (final or {}).get("rows"), "resolved_criticals": res, "unresolved_criticals": unres,
                    "exercised": read and n_facts > 0, "unread_reason": reason,
                    "staged_sha_equals_row_sha": row.get("sha256") == ALLOW[pid]}
    comp = (lane.get("stop_state") or {}).get("comparison")
    gp = lane.get("global_provider") or {}
    return {"per_document": per, "stop_state": lane.get("stop_state"), "stop_condition": STOP_CONDITION,
            "stop_condition_fired": comp == STOP_CONDITION, "lane_stopped": lane.get("stopped"),
            "tripwire_consistency": {"lane_entries": len(lane_pairs), "recomputed_entries": len(re_pairs), "equal": lane_pairs == re_pairs},
            "requests": {"refusing_provider_calls": gp.get("requests_refused"), "dry_stub_calls": lane.get("dry_stub_calls"),
                         "live_provider_attempts_blocked": lane.get("live_provider_attempts_blocked"),
                         "provider_complete_calls_traced": len((lane.get("trace") or {}).get("provider_complete_calls") or []),
                         "model_requests": lane.get("model_requests")},
            "global_provider": {k: gp.get(k) for k in ("installed", "at_end", "still_installed_at_end", "requests_refused")},
            "trace": lane.get("trace"), "lane_violations": lane.get("violations"), "evaluator": facts.get("evaluator")}


def criterion(report: dict) -> dict:
    """DRILL-CRITERION.md section 3, as declared before the first run."""
    per = report["per_document"]
    req = report["requests"]
    zero_requests = (req["refusing_provider_calls"] == 0 and req["dry_stub_calls"] == 0 and not req["live_provider_attempts_blocked"]
                     and req["provider_complete_calls_traced"] == 0)
    resolved = {p: v["resolved_criticals"] for p, v in per.items() if v["resolved_criticals"]}
    not_exercised = {p: v["unread_reason"] for p, v in per.items() if not v["exercised"]}
    fields_ok = all(c.get("field") in FIELDS for v in resolved.values() for c in v)
    if resolved or report["stop_condition_fired"] or not zero_requests:
        result = "FAIL"
    elif not_exercised:
        result = "NOT PASS (incomplete)"
    else:
        result = "PASS"
    return {"result": result, "declared_in": "DRILL-CRITERION.md (sha256 recorded in the R43 session log before the first run)",
            "zero_resolved_criticals": not resolved, "resolved_criticals": resolved, "criticals_in_the_three_fields": fields_ok,
            "stop_condition_fired": report["stop_condition_fired"], "all_exercised": not not_exercised, "not_exercised": not_exercised,
            "zero_requests": zero_requests, "rule": "a critical is reported, never fixed here"}


# ---- the facts subcommand (a subprocess, like the lane's tripwire) ---------------------------------------------------------
def facts_main(truth_path, trace_path, out_path) -> int:
    import lane_judge_r32 as J
    import tripwire_r32 as TW

    truth = json.loads(pathlib.Path(truth_path).read_text(encoding="utf-8"))
    trace = json.loads(pathlib.Path(trace_path).read_text(encoding="utf-8"))
    EV = TW.load_evaluator()
    calls = []
    for t in trace["tripwire_inputs"]:
        docs = {}
        for pid, row in (t["rows"] or {}).items():
            facts = TW.facts_from_row(EV, row, None, None)
            res = TW.tripwire(truth, pid, facts, (row or {}).get("sha256"))
            jd = J.judge_document(truth, pid, {"facts": facts, "source_sha256": (row or {}).get("sha256")})
            docs[pid] = {"facts": facts, "resolved": res["resolved"], "unresolved": res["unresolved"], "fields": res["fields"],
                         "rows": [{k: j.get(k) for k in ("page", "field", "truth_kind", "outcome", "accepted_correct", "accepted_wrong")} for j in jd["rows"]]}
        calls.append({"seq": t["seq"], "when": t["when"], "documents": docs})
    pathlib.Path(out_path).write_text(json.dumps({"evaluator": EV.EVALUATOR_VERSION, "calls": calls}, indent=1, sort_keys=True, ensure_ascii=False,
                                                 default=str) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "facts":
        sys.exit(facts_main(sys.argv[2], sys.argv[3], sys.argv[4]))
    raise SystemExit("usage: drill_r45.py facts <truth json> <DRILL-TRACE.json> <out json>")
