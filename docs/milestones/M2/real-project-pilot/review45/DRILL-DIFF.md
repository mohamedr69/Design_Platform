# DRILL-DIFF: review45/scripts against review43/scripts (task R43-42)

Produced by `scripts/r45/r45_diff.py` (run copy, guard roots r45p only); machine record `evidence/HARNESS-COMPARE-R43.json`.
This record authorizes nothing.

## 1. Summary

- 85 files in `review45/scripts`: **71 byte-identical** to review43 (every build file, the build guard and 59 of the 61
  harness files), **2 changed** (`harness-r32/lane_r32.py`, `harness-r32/runner_r32.py`), **12 new**, 0 removed.
- New harness files: `harness-r32/drill_r45.py` (the drill) and `harness-r32/test_dry_baseline_drill_r45.py` (its tests).
  The test file lives beside the other 26 test modules (the card's `tests/` names its role; `review45/tests/` holds the
  junit results, as in review43).
- New task tooling (not harness; listed, not diffed): `r45/r45common.py`, `r45_snapshot.py`, `r45_launch.py`,
  `r45_run_tests.py`, `r45_prebinding.py`, `r45_drill_run.py`, `r45_diff.py`, `r45_manifest.py`, `r45_selfcheck.py`, and
  `r45/guard/sitecustomize.py` (the declaration-r32-v4 guard with three changes, section 3).
- Nothing in any live path changed meaning: every changed line is either inside an `if DRILL ...` / `DRILL is None`
  branch, or makes the live refusal list one flag longer. With no `drill` key in the configuration (every existing mode),
  the lane executes exactly the review43 statements.

## 2. Table of changes (harness)

| File | Line (review45) | Change | Reason |
|---|---|---|---|
| runner_r32.py | 7-8 | usage line for `--dry-baseline-facts` | document the additional, explicitly named mode |
| runner_r32.py | 514-515 | new argument `--dry-baseline-facts SPEC.json` | the mode's flag (card item 1) |
| runner_r32.py | 616-617 | live refusal list gains `--dry-baseline-facts` | live mode refuses the drill like every dry drill (nothing loosened) |
| runner_r32.py | 620-622 | `if args.dry_baseline_facts: return DR.run(args, module)` | dispatch to the drill before the ordinary dry path; the ordinary dry and live paths are unchanged after it |
| lane_r32.py | 50-53 | docstring paragraph | describes the drill branch |
| lane_r32.py | 70-76 | `DRILL = CFG.get("drill")`; `DR.check_config(CFG, LANE)` | refuse before anything is imported: a lane other than B, live mode, reader not `application`, any run / allowance / store / ledger / declaration / injection / provider / budget value, a folder not `r32-drill-<stamp>`, a tree other than frozen-r13, documents other than F009 / F020 / F030 |
| lane_r32.py | 97-101 | inside the dry cohort assertion (old 84-86): `DR.check_cohort` removes the allow-listed ids only for the drill | card item 3: the assertion is extended for the drill's allow-list (ids AND staged sha256, declared truth file) and is unchanged otherwise (line 102 is the old assertion) |
| lane_r32.py | 112-122 | drill only: AI_ENABLED=false and no owner token required; `app.ai.provider` imported first; `RefusingGlobalProvider` installed with `set_provider`, checked; call tracer started | the refusing global provider before any other application module; the call trace |
| lane_r32.py | 298-313 | drill: allowance / alw / store are `Forbidden` sentinels; the store binding check, the allowance and the capture store are built only when `DRILL is None` (re-indented, identical statements); the drill's provider attached to the recorder and stop controller | no allowance, capture store or ledger is opened or consulted; any use refuses and is recorded |
| lane_r32.py | 450 | `SERVES_BEFORE = serves_by_mode() if DRILL is None else None` | the drill has no capture store |
| lane_r32.py | 464-465 | `G` and `chain` are the gate and stop guard unless the drill, where `chain` is the refusing provider | the B path's provider; `prov.set_provider(chain)` (line 466) and `document_processing.run(..., provider=chain)` are unchanged |
| lane_r32.py | 700-710 | drill only: tracer stopped, isolation re-checked, drill manifest, `finish_lane` (writes LANE-B.json and DRILL-TRACE.json), exit | the drill's own manifest (no allowance, gate or store figures exist); the rest of the file never runs in the drill |

Unchanged on purpose (asserted by `test_static_the_other_dry_rules_and_the_single_application_entry_are_unchanged`):
`runner_r32.py` line 779 (`"reader": "application" if (live or synthetic is not None) else "none"`), the synthetic
SYN*-only refusal (line 872), the lane's cohort assertion text, the one `document_processing.run` call of lane B and the
`set_provider(chain)` line; `lane_r32.py` 470-472 of review43 (reader `none` -> `exercise_no_facts`) is unchanged
(now 502-504).

## 3. The review45 guard (`scripts/r45/guard/sitecustomize.py`, new; from `declaration-r32-v4/scripts/guard`)

Three changes to the v4 guard: (1) `declaration-r32-v4` is DENIED like the other frozen packages; (2) the default and
only roots of this task are `C:/t/r2x/r42-sandbox/r45p`, and the v4 package is never a root; (3) the sandbox base itself
is accepted as a root only with `R45_GUARD_TEST_BASE=1` (the harness test suite creates its sandboxes as siblings at the
base, by design); the deny list (every `r32-v<N>` folder, the owner records, the ledger folder, the trees, the frozen
packages) applies first.

## 4. Unified diff (harness files: the 2 changed and the 2 new)

```diff
--- /dev/null
+++ review45/scripts/harness-r32/drill_r45.py
@@ -0,0 +1,551 @@
+"""R43-42 (review45, new): the dry-only BASELINE-FACTS drill of lane B (Verification 44 option 1; A-13 item 2).
+
+  runner_r32.py run --mode dry --dry-baseline-facts SPEC.json --stamp S --run-set RS.json --binding BM.json --binding-sha SHA
+                    [--sandbox-base D]
+SPEC.json is exactly {"drill": "baseline-facts", "lane": "B", "tree": "C:/t/iso/frozen-r13",
+                      "documents": [{"pool_id": "F009", "staged_sha256": ...}, {"pool_id": "F020", ...}, {"pool_id": "F030", ...}]}.
+
+What it is. One lane-B pass of the REAL application processing (frozen-r13, reader 'application') over exactly the three
+run-set documents F009, F020 and F030 of EP-27331 (ALLOW: pool id AND staged sha256), with AI off and the refusing global
+provider (run_control_r38.RefusingGlobalProvider) installed right after the application's provider module is imported and
+before any other application module; the lane's OWN code path does the reading, the fact extraction and the tripwire
+input (lane_r32: document_processing.run with its process / read_form_or_raise / apply_form_reading hooks, row_dict,
+b_tripwire -> tripwire_r32.py -> lane_judge_r32 rule CP-R38, 'after_document' and 'final'), so the tripwire judges the
+real facts against the resolved truth exactly as live B would. Everything is written under ONE drill folder
+<sandbox base>/r32-drill-<stamp> (never r32-v<N>): out/ (TRUTH-R32.json, DRILL-CONFIG.json, LANE-B.json, rows-B.json,
+DRILL-TRACE.json, DRILL-FACTS.json, DRILL-REPORT.json, the lane log) and B/ (the lane's sandbox).
+
+What it never does. No live mode, no other lane, tree, document or drill flag (--dry-fault / --dry-inject /
+--dry-synthetic), no resume, no declaration. It never creates, opens or consults a run state, allowance, capture store,
+ledger (real or fake), ledger scope, authorization, nonce, token or RUN file: in the runner the functions that would do so
+are replaced by refusals for the drill's duration (forbid), and in the lane the allowance / capture-store objects are
+Forbidden sentinels that refuse (and record) any use; a configuration that names any of them is refused before the lane
+imports the application (check_config). 0 model requests: AI is off; the refusing provider and the dry stub must record
+0 calls; live provider classes are blocked by the lane (unchanged dry rule).
+
+Evidence of the path (call tracing). The lane installs a profiler (Tracer, sys.setprofile / threading.setprofile) for the
+whole drill and records every call of the lane's own B functions, of document_processing.run, document_sync's process /
+read path, the submittal reader's availability and form read, the OCR probe, and every provider complete(); the
+tripwire inputs are captured from b_tripwire's own arguments. DRILL-TRACE.json is that record; the tests assert on it.
+
+The pass criterion (DRILL-CRITERION.md, declared before the first run) is evaluated by criterion(); a critical acceptance
+on resolved truth is a FAIL that is reported, never fixed. The other dry rules are unchanged: reader 'none' over the real
+cohort, --dry-synthetic over SYN* documents only, and the lane assertion that dry mode never reads a cohort document
+except under this drill's allow-list."""
+from __future__ import annotations
+
+import contextlib
+import hashlib
+import json
+import os
+import pathlib
+import re
+import subprocess
+import sys
+import threading
+import time
+
+HERE = pathlib.Path(__file__).resolve().parent
+NAME = "baseline-facts"
+FLAG = "--dry-baseline-facts"
+LANE = "B"
+TREE = "C:/t/iso/frozen-r13"
+BASELINE_BACKEND = "C:/t/iso/frozen-r13/backend"
+EP = "27331"
+RUN_SET_SHA256 = "9058f3d6794342db40c76ff9ad79f0e40c171430a616c5eab4b570a2fb057ce8"
+TRUTH_SHA256 = "4e237a4e321949c5138caf1b203e52257499d9ca9739d5b6fa93df474705e064"
+ALLOW = {"F009": "970ddb0f5b59199b41f33bee8356dd87418d9daff26ec9a9b8a72a3538bab415",
+         "F020": "599d36be15e6eded0fcbe4226afdb49c9b282f6bcbbd13c3c3376872da1891db",
+         "F030": "feec64cdcb0b7a95262c9991fd09830d810f88e75d87be05ac308c106047010a"}
+FOLDER_PREFIX = "r32-drill-"
+FIELDS = ("identity", "revision", "decision")
+STOP_CONDITION = "INVALID: baseline incomplete (critical acceptance on resolved truth in B)"
+CONFIG_NAME = "DRILL-CONFIG.json"
+# never in a drill configuration (or only as None): the run's allowance / capture store / run key, every ledger and
+# declaration value, every dry injection, the provider environment and the run budgets
+FORBIDDEN_KEYS = ("store", "allowance", "run_key", "ledger", "dry_ledger", "dry_inject", "dry_application_limits", "declaration_path",
+                  "declaration_sha256", "auth_path", "provider_env", "caps", "parent", "project_window", "project_totals")
+_STAMP = re.compile(r"[A-Za-z0-9._-]{3,40}")
+_LIVE_RUN = re.compile(r"r32-v\d", re.IGNORECASE)
+VIOLATIONS: list[str] = []
+TRACER = None                                                      # the lane's Tracer (set by lane_r32 in the drill only)
+
+
+def _refused():
+    import preflight_r32 as PF
+    return PF.Refused
+
+
+def refuse(msg: str):
+    raise _refused()(msg)
+
+
+def _norm(p) -> str:
+    return str(p).replace("\\", "/").rstrip("/").lower()
+
+
+def sha256_text(s: str) -> str:
+    return hashlib.sha256(s.encode("utf-8")).hexdigest()
+
+
+def sha256_file(p) -> str:
+    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
+
+
+# ---- the allow-list, the folder and the configuration -----------------------------------------------------------------
+def spec_documents(spec) -> list[dict]:
+    """The drill's SPEC: exactly lane B, the frozen-r13 tree and the three allowed documents by id AND staged sha256."""
+    if not isinstance(spec, dict) or set(spec) != {"drill", "lane", "tree", "documents"} or spec.get("drill") != NAME:
+        refuse(f"refused: a baseline-facts drill spec is exactly {{drill: {NAME!r}, lane, tree, documents}} ({sorted(spec) if isinstance(spec, dict) else spec!r})")
+    if spec["lane"] != LANE:
+        refuse(f"refused: the baseline-facts drill runs lane B only (lane {spec['lane']!r})")
+    if _norm(spec["tree"]) != _norm(TREE):
+        refuse(f"refused: the baseline-facts drill runs on {TREE} only (tree {spec['tree']!r})")
+    docs = spec["documents"]
+    if not isinstance(docs, list) or any(not isinstance(d, dict) or set(d) != {"pool_id", "staged_sha256"} for d in docs):
+        refuse("refused: every drill document is exactly {pool_id, staged_sha256}")
+    ids = [d["pool_id"] for d in docs]
+    if len(ids) != len(ALLOW) or sorted(ids) != sorted(ALLOW):
+        refuse(f"refused: the baseline-facts drill takes exactly {sorted(ALLOW)} (given {ids})")
+    for d in docs:
+        if d["staged_sha256"] != ALLOW[d["pool_id"]]:
+            refuse(f"refused: {d['pool_id']} staged sha256 {d['staged_sha256']} is not the allowed {ALLOW[d['pool_id']]}")
+    return docs
+
+
+def drill_folder(base, stamp) -> pathlib.Path:
+    """<sandbox base>/r32-drill-<stamp>: never a live run folder name (r32-v<N>), never an existing folder."""
+    if not stamp or not _STAMP.fullmatch(str(stamp)) or _LIVE_RUN.search(str(stamp)):
+        refuse(f"refused: a drill stamp is 3-40 characters A-Z a-z 0-9 . _ - and never names a live run (r32-v<N>) ({stamp!r})")
+    folder = pathlib.Path(base) / f"{FOLDER_PREFIX}{stamp}"
+    if folder.exists():
+        refuse(f"refused: {folder.as_posix()} exists (a drill folder is never reused)")
+    return folder
+
+
+def select(run_set: list, truth: dict, docs: list) -> list:
+    """The three run-set entries, in run-set order; the truth's staged sha256 must be the allowed one."""
+    out = [d for d in run_set if d["pool_id"] in ALLOW]
+    if sorted(d["pool_id"] for d in out) != sorted(ALLOW):
+        refuse(f"refused: the run set does not hold {sorted(ALLOW)}")
+    for d in out:
+        t = truth["documents"][d["pool_id"]]
+        if t["staged_sha256"] != ALLOW[d["pool_id"]] or str(t["ep"]) != EP or str(d["ep"]) != EP:
+            refuse(f"refused: {d['pool_id']} in the truth is not the allowed document (sha256 {t['staged_sha256']}, ep {t['ep']})")
+    return out
+
+
+def check_config(cfg: dict, lane: str | None = None) -> dict:
+    """The runner (before the lane starts) and the lane (before it imports the application) refuse any drill configuration
+    that is not exactly: dry mode, reader 'application', lane B, the frozen-r13 tree, the three allowed documents, a
+    r32-drill-<stamp> folder, a B sandbox only, and NO allowance / capture store / run key / ledger / declaration /
+    injection / provider environment / budget value."""
+    if cfg.get("drill") != NAME:
+        refuse(f"refused: not a baseline-facts drill configuration ({cfg.get('drill')!r})")
+    if lane is not None and lane != LANE:
+        refuse(f"refused: the baseline-facts drill runs lane B only (lane {lane})")
+    if cfg.get("mode") != "dry":
+        refuse(f"refused: the baseline-facts drill is dry mode only (mode {cfg.get('mode')!r})")
+    if cfg.get("reader") != "application":
+        refuse("refused: the baseline-facts drill runs the application reader")
+    bad = [k for k in FORBIDDEN_KEYS if cfg.get(k) is not None]
+    if bad:
+        refuse(f"refused: the baseline-facts drill never consults or writes {bad} (run state, allowance, capture store, ledger, scope, "
+               "authorization, nonce, RUN or provider values)")
+    name = pathlib.PurePosixPath(str(cfg.get("run_folder") or "").replace("\\", "/")).name
+    if not name.startswith(FOLDER_PREFIX) or _LIVE_RUN.search(name):
+        refuse(f"refused: the drill folder is r32-drill-<stamp> ({cfg.get('run_folder')!r})")
+    if set(cfg.get("sandbox") or {}) != {LANE}:
+        refuse(f"refused: the baseline-facts drill has a B sandbox only ({sorted(cfg.get('sandbox') or {})})")
+    if _norm((cfg.get("trees") or {}).get("baseline") or "") != _norm(BASELINE_BACKEND):
+        refuse(f"refused: the baseline-facts drill runs on {BASELINE_BACKEND} only ({(cfg.get('trees') or {}).get('baseline')!r})")
+    ids = sorted(d["pool_id"] for d in cfg.get("run_set") or [])
+    if ids != sorted(ALLOW):
+        refuse(f"refused: the baseline-facts drill takes exactly {sorted(ALLOW)} (given {ids})")
+    return {"drill": NAME, "lane": LANE, "documents": ids, "forbidden_keys_absent": list(FORBIDDEN_KEYS)}
+
+
+def check_cohort(run_set: list, truth: dict, truth_path) -> list:
+    """lane_r32's dry-mode cohort assertion, extended for this drill only: the documents are exactly the allow-list by id
+    AND staged sha256, judged against the declared truth file."""
+    if sha256_file(truth_path) != TRUTH_SHA256:
+        refuse(f"refused: the drill's truth file is not the declared truth {TRUTH_SHA256}")
+    ids = sorted(d["pool_id"] for d in run_set)
+    if ids != sorted(ALLOW) or any(truth["documents"][p]["staged_sha256"] != ALLOW[p] for p in ids):
+        refuse(f"refused: dry mode reads a cohort document only in the baseline-facts drill and only {sorted(ALLOW)} ({ids})")
+    return ids
+
+
+def check_provider(prov, expected) -> dict:
+    """The application's global provider must be the drill's refusing provider (run_control_r38.RefusingGlobalProvider)."""
+    got = prov.get_provider()
+    if expected is None or type(expected).__name__ != "RefusingGlobalProvider" or got is not expected:
+        refuse(f"refused: the drill's global provider is {type(got).__name__}, not the refusing global provider")
+    return {"global_provider": type(got).__name__, "name": getattr(got, "name", None), "calls": getattr(got, "calls", None)}
+
+
+class Forbidden:
+    """Stands for the run's allowance / capture store in the drill lane: any use refuses and is recorded (VIOLATIONS), so a
+    use caught by the application's own exception handling still fails the lane at its end."""
+
+    def __init__(self, what: str):
+        object.__setattr__(self, "_what", what)
+
+    def __getattr__(self, name):
+        msg = f"refused: the baseline-facts drill never consults {object.__getattribute__(self, '_what')} (.{name})"
+        VIOLATIONS.append(msg)
+        refuse(msg)
+
+    def __setattr__(self, name, value):
+        self.__getattr__(name)
+
+
+@contextlib.contextmanager
+def forbid(RN):
+    """Runner side: for the drill's duration every function that creates, opens or consults a run state, allowance, capture
+    store, ledger, ledger scope, declaration, authorization, nonce or model identity record refuses."""
+    import allowance_r32 as AL
+    import dispatch_guard_r32 as DG
+    import model_identity_r38 as MI
+    import preflight_r32 as PF
+
+    targets = [(AL, n) for n in ("LaneAllowance", "AllowanceProvider", "bind_store", "bound_key")] + \
+              [(DG, n) for n in ("check", "authorize", "GuardedProvider")] + \
+              [(PF, n) for n in ("verify_ledger_scope", "ledger_counts", "ledger_snapshot", "ledger_live_check", "load_declaration", "live_preflight",
+                                 "verify_bounds", "verify_cli")] + \
+              [(MI, n) for n in ("record_invocation", "check_version", "cli_version")] + \
+              [(RN, n) for n in ("ledger_state", "reentry_proof", "create_allowance_atomic", "open_allowance", "allowance_state", "store_counts",
+                                 "execute", "_state_write", "_state_of_reentry", "_close")]
+    saved = []
+
+    def stop(label):
+        def _f(*_a, **_k):
+            msg = f"refused: the baseline-facts drill never consults {label}"
+            VIOLATIONS.append(msg)
+            raise PF.Refused(msg)
+        return _f
+
+    for mod, name in targets:
+        if hasattr(mod, name):
+            saved.append((mod, name, getattr(mod, name)))
+            setattr(mod, name, stop(f"{mod.__name__}.{name}"))
+    try:
+        yield [f"{m.__name__}.{n}" for m, n, _ in saved]
+    finally:
+        for mod, name, fn in saved:
+            setattr(mod, name, fn)
+
+
+# ---- call tracing (lane side) --------------------------------------------------------------------------------------------
+WATCH = {"lane_r32": {"process", "read_form_or_raise", "apply_form_reading", "_after", "b_tripwire", "row_dict", "_run_call", "dump_rows",
+                      "observe_trip", "_forbidden"},
+         "document_processing": {"run", "read_task"},
+         "document_sync": {"process", "apply_form_reading", "read_form_or_raise", "read_in_completion_order"},
+         "submittal_reader": {"available", "read_form", "check"},
+         "submittal_scanner": {"ocr_available"},
+         "run_control_r38": {"complete"},
+         "app_provider": {"complete"}}
+RETURNS = {("submittal_reader", "available"), ("submittal_scanner", "ocr_available")}
+
+
+class Tracer:
+    """sys.setprofile / threading.setprofile over the drill lane: every call of the watched functions (WATCH) with its
+    caller; b_tripwire's arguments (when, and the rows exactly as the tripwire receives them) are captured."""
+
+    def __init__(self, harness_dir, tree_backend):
+        h, t = _norm(harness_dir), _norm(tree_backend)
+        self.files = {f"{h}/lane_r32.py": "lane_r32", f"{h}/run_control_r38.py": "run_control_r38",
+                      f"{t}/app/services/document_processing.py": "document_processing", f"{t}/app/services/document_sync.py": "document_sync",
+                      f"{t}/app/ai/submittal_reader.py": "submittal_reader", f"{t}/app/services/submittal_scanner.py": "submittal_scanner",
+                      f"{t}/app/ai/provider.py": "app_provider"}
+        self.cache: dict[str, str | None] = {}
+        self.calls: list[dict] = []
+        self.tripwire_inputs: list[dict] = []
+        self.started = self.stopped = None
+
+    def _label(self, filename):
+        lab = self.cache.get(filename, 0)
+        if lab == 0:
+            lab = self.files.get(_norm(os.path.abspath(filename))) if filename and not filename.startswith("<") else None
+            self.cache[filename] = lab
+        return lab
+
+    def _prof(self, frame, event, arg):
+        if event not in ("call", "return"):
+            return
+        try:
+            self._record(frame, event, arg)
+        except Exception as exc:  # noqa: BLE001 -- a profiler that raises would change the lane; the failure is recorded
+            self.calls.append({"seq": len(self.calls) + 1, "event": "trace_error", "error": f"{type(exc).__name__}: {exc}"[:200]})
+
+    def _record(self, frame, event, arg):
+        co = frame.f_code
+        lab = self._label(co.co_filename)
+        if lab is None or co.co_name not in WATCH[lab]:
+            return
+        if event == "return":
+            if (lab, co.co_name) in RETURNS:
+                self.calls.append({"seq": len(self.calls) + 1, "event": "return", "file": lab, "function": co.co_name, "returned": repr(arg)[:200]})
+            return
+        back = frame.f_back
+        rec = {"seq": len(self.calls) + 1, "event": "call", "file": lab, "function": co.co_name, "thread": threading.current_thread().name,
+               "caller": f"{self._label(back.f_code.co_filename) or pathlib.PurePath(back.f_code.co_filename).name}:{back.f_code.co_name}" if back else None}
+        loc = frame.f_locals
+        try:
+            if lab == "lane_r32" and co.co_name == "b_tripwire":
+                rows = json.loads(json.dumps(loc.get("rows_by_pid"), default=str, ensure_ascii=False))
+                rec |= {"when": loc.get("when"), "pool_ids": sorted(rows or {})}
+                self.tripwire_inputs.append({"seq": rec["seq"], "when": loc.get("when"), "rows": rows})
+            elif co.co_name in ("process", "apply_form_reading") and lab in ("lane_r32", "document_sync"):
+                row, project = loc.get("row"), loc.get("project")
+                rec |= {"relative_path": getattr(row, "relative_path", None), "ep": getattr(project, "ep_number", None)}
+            elif lab == "document_processing" and co.co_name == "run":
+                rec |= {"ep": getattr(loc.get("project"), "ep_number", None)}
+            elif co.co_name == "complete":
+                rec |= {"self": type(loc.get("self")).__name__, "task": getattr(loc.get("request"), "task", None)}
+        except Exception as exc:  # noqa: BLE001 -- tracing never changes the lane; the failure is recorded
+            rec["trace_error"] = f"{type(exc).__name__}: {exc}"[:200]
+        self.calls.append(rec)
+
+    def start(self):
+        self.started = time.time()
+        threading.setprofile(self._prof)
+        sys.setprofile(self._prof)
+
+    def stop(self):
+        sys.setprofile(None)
+        threading.setprofile(None)
+        self.stopped = time.time()
+
+    def summary(self) -> dict:
+        n = {}
+        for c in self.calls:
+            if c["event"] == "call":
+                k = f"{c['file']}.{c['function']}"
+                n[k] = n.get(k, 0) + 1
+        return {"calls_by_function": dict(sorted(n.items())), "tripwire_calls": [{"seq": t["seq"], "when": t["when"], "pool_ids": sorted(t["rows"])}
+                                                                                  for t in self.tripwire_inputs],
+                "provider_complete_calls": [c for c in self.calls if c["event"] == "call" and c["function"] == "complete"]}
+
+    def record(self) -> dict:
+        return {"method": "sys.setprofile and threading.setprofile in the lane process for the whole drill (call and return events of the "
+                          "watched functions; b_tripwire's arguments captured as the tripwire receives them)",
+                "watched": {k: sorted(v) for k, v in WATCH.items()}, "files": self.files, "started": self.started, "stopped": self.stopped,
+                "summary": self.summary(), "calls": self.calls, "tripwire_inputs": self.tripwire_inputs}
+
+
+def lane_manifest(*, recorder, ctl, trip, provider, prov, stub, blocked, isolation, app_env, env_check, task_kinds, stopped, seconds,
+                  install, tracer) -> dict:
+    """The drill lane's manifest (LANE-B.json): no allowance, store, gate or ledger figure exists to report."""
+    docs = recorder.documents()
+    return {"drill": NAME, "documents": docs, "tripwire": trip, "stop_state": ctl.state(), "lane_stop_state": ctl.state()["lanes"][LANE],
+            "stopped": stopped, "seconds": seconds, "limit_events": recorder.events, "application_env_check": app_env, "environment_check": env_check,
+            "task_kinds": sorted(task_kinds), "isolation_check": isolation, "live_provider_attempts_blocked": blocked,
+            "dry_stub_calls": stub.calls, "model_requests": 0,
+            "global_provider": {"lane_kind": "refusing (baseline-facts drill)", "installed": install,
+                                "at_end": type(prov.get_provider()).__name__, "still_installed_at_end": prov.get_provider() is provider,
+                                "requests_refused": provider.calls, "records": provider.records, "events": provider.events},
+            "violations": list(VIOLATIONS), "trace": tracer.summary(),
+            "not_consulted": "run state, allowance, capture store, gate, ledger (real or fake), ledger scope, authorization, nonce, token, RUN file"}
+
+
+def finish_lane(out, manifest, tracer) -> int:
+    """Writes LANE-B.json and DRILL-TRACE.json; a drill rule broken in the lane (a forbidden object used, the provider
+    replaced, a live provider reached, isolation lost) fails the lane (exit 3) AFTER its evidence is written."""
+    out = pathlib.Path(out)
+    (out / "DRILL-TRACE.json").write_text(json.dumps(tracer.record(), indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n",
+                                          encoding="utf-8", newline="\n")
+    (out / "LANE-B.json").write_text(json.dumps(manifest, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n",
+                                     encoding="utf-8", newline="\n")
+    problems = list(manifest["violations"])
+    if not manifest["global_provider"]["still_installed_at_end"]:
+        problems.append("the refusing global provider was replaced during the drill")
+    if manifest["live_provider_attempts_blocked"]:
+        problems.append(f"a live provider was reached: {manifest['live_provider_attempts_blocked']}")
+    if not (manifest["isolation_check"].get("end") or {}).get("ok"):
+        problems.append(f"isolation at the end: {(manifest['isolation_check'].get('end') or {}).get('refused')}")
+    print(json.dumps({"drill": NAME, "lane": LANE, "documents": {p: v["status"] for p, v in manifest["documents"].items()},
+                      "stop": manifest["stop_state"]["comparison"], "refusing_provider_calls": manifest["global_provider"]["requests_refused"],
+                      "dry_stub_calls": manifest["dry_stub_calls"], "problems": problems}, default=str))
+    if problems:
+        print(f"refused: baseline-facts drill rule broken in the lane: {problems}", file=sys.stderr)
+        return 3
+    return 0
+
+
+# ---- the runner side -----------------------------------------------------------------------------------------------------
+def run(args, RN) -> int:
+    """`runner_r32.py run --mode dry --dry-baseline-facts SPEC.json ...` (called by runner_r32.main before anything else)."""
+    import dispatch_guard_r32 as DG
+    import preflight_r32 as PF
+    import sandbox_ingest_r32 as SI
+
+    if args.mode != "dry":
+        refuse("refused: --dry-baseline-facts is a dry-mode drill only")
+    if args.command != "run":
+        refuse("refused: the baseline-facts drill is one fresh run of its own folder; it is never resumed")
+    if args.dry_fault or args.dry_inject or args.dry_synthetic:
+        refuse("refused: the baseline-facts drill takes no other drill (--dry-fault / --dry-inject / --dry-synthetic)")
+    if args.declaration or args.declaration_sha or args.out:
+        refuse("refused: the baseline-facts drill takes no declaration and no --out (its folder is r32-drill-<stamp>)")
+    if os.environ.get(DG.TOKEN_ENV) is not None:
+        refuse(f"refused: {DG.TOKEN_ENV} is set; the drill never reads an owner token (nothing was created)")
+    VIOLATIONS.clear()
+    started = time.time()
+    with forbid(RN) as forbidden:
+        spec = json.loads(pathlib.Path(args.dry_baseline_facts).read_text(encoding="utf-8"))
+        docs = spec_documents(spec)
+        binding = PF.verify_binding(args.binding, args.binding_sha)
+        rs_sha = sha256_file(args.run_set)
+        if rs_sha != RUN_SET_SHA256:
+            refuse(f"refused: the run set {rs_sha} is not the declared run set {RUN_SET_SHA256}")
+        base = PF.sandbox_base(args.sandbox_base)
+        folder = drill_folder(base, args.stamp)
+        disk = PF.verify_free_disk(PF.dry_disk_precondition(base.as_posix()))
+        heads = PF.heads()
+        truth = PF.build_truth()
+        if sha256_text(PF.truth_text(truth)) != TRUTH_SHA256:
+            refuse(f"refused: the built truth is not the declared truth {TRUTH_SHA256}")
+        gate = PF.population(truth)
+        run_set = select(PF.load_run_set(args.run_set, truth), truth, docs)
+        folder.mkdir(parents=True)
+        out = folder / "out"
+        out.mkdir()
+        truth_path = out / "TRUTH-R32.json"
+        truth_path.write_text(PF.truth_text(truth), encoding="utf-8", newline="\n")
+        SI.SANDBOX_BASE = pathlib.Path(base)
+        ing = SI.ingest(folder / LANE, [d["pool_id"] for d in run_set], truth)
+        if not ing["ok"]:
+            refuse("refused: the drill's B sandbox ingestion check failed")
+        cfg = {"drill": NAME, "mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(out), "truth": str(truth_path),
+               "run_set": run_set, "run_set_path": str(args.run_set), "run_folder": folder.as_posix(), "run_key": None, "stamp": args.stamp,
+               "invocation": 1, "sandbox_base": pathlib.Path(base).as_posix(), "trees": dict(RN.TREES), "sandbox": {LANE: str(folder / LANE)},
+               "binding": str(args.binding), "binding_sha256": binding["sha256"], "lane_switches": {LANE: dict(RN.DRY_LANE_SWITCHES[LANE])},
+               "model_identity": dict(RN.DRY_PINS), "cli_version": RN.DRY_CLI_VERSION, "switch_source": PF.DRY_LANE_SWITCHES_LABEL,
+               "policies": {LANE: "B:accepted-path:evidence-off"}, "application_env": dict(PF.APPLICATION_ENV),
+               "lane_task_kinds": {LANE: PF.task_kinds_for(RN.DRY_LANE_SWITCHES)[LANE]}, "ai_enabled": False}
+        check_config(cfg, LANE)
+        cfg_path = out / CONFIG_NAME
+        cfg_path.write_text(json.dumps(cfg, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
+        env = RN.lane_env("dry", folder / LANE, LANE, cfg)
+        env["AI_ENABLED"] = "false"                                   # AI off: the application reads deterministically
+        env.pop(DG.TOKEN_ENV, None)
+        lane = RN.run_lane(LANE, cfg_path, out, env, RN.TREES["baseline"])
+        facts = facts_of(out, truth_path, env)
+        report = build_report(lane, facts, json.loads((out / "rows-B.json").read_text(encoding="utf-8")), run_set)
+        report |= {"drill": NAME, "folder": folder.as_posix(), "stamp": args.stamp, "binding": binding, "run_set_sha256": rs_sha,
+                   "truth_sha256": sha256_file(truth_path), "heads": heads, "free_disk": disk, "population_gate": gate.get("action"),
+                   "ingest": {k: ing[k] for k in ("ok", "documents", "projects", "registration", "b_database_sha256")},
+                   "forbidden_in_runner": forbidden, "violations": list(VIOLATIONS), "seconds": round(time.time() - started, 1),
+                   "spec_sha256": sha256_file(args.dry_baseline_facts), "statement": "a dry drill: 0 model requests; it authorizes nothing"}
+        report["criterion"] = criterion(report)
+        (out / "DRILL-REPORT.json").write_text(json.dumps(report, indent=1, sort_keys=True, default=str, ensure_ascii=False) + "\n",
+                                               encoding="utf-8", newline="\n")
+    print(json.dumps({"drill": NAME, "folder": folder.as_posix(), "criterion": report["criterion"]["result"],
+                      "documents": {p: {k: v.get(k) for k in ("exercised", "facts_final", "resolved_criticals", "unresolved_criticals")}
+                                    for p, v in report["per_document"].items()},
+                      "stop_condition_fired": report["stop_condition_fired"], "requests": report["requests"]}, default=str))
+    return 0
+
+
+def facts_of(out, truth_path, env) -> dict:
+    """The facts of every tripwire input the lane gave (captured in DRILL-TRACE.json), by the SAME functions the tripwire
+    uses (tripwire_r32.facts_from_row, tripwire, lane_judge_r32.judge_document), in a subprocess like b_tripwire's."""
+    o = pathlib.Path(out) / "DRILL-FACTS.json"
+    r = subprocess.run([sys.executable, str(HERE / "drill_r45.py"), "facts", str(truth_path), str(pathlib.Path(out) / "DRILL-TRACE.json"), str(o)],
+                       cwd=str(HERE), env={**env, "PYTHONDONTWRITEBYTECODE": "1", "AI_ENABLED": "false"}, capture_output=True, text=True)
+    if r.returncode:
+        raise RuntimeError(f"drill facts failed: {r.stderr[-2000:]}")
+    return json.loads(o.read_text(encoding="utf-8"))
+
+
+def build_report(lane: dict, facts: dict, rows: dict, run_set: list) -> dict:
+    trip = lane.get("tripwire") or []
+    lane_pairs = [(t["pool_id"], t["when"], json.dumps(t["resolved"], sort_keys=True), json.dumps(t["unresolved"], sort_keys=True)) for t in trip]
+    re_pairs = [(pid, c["when"], json.dumps(v["resolved"], sort_keys=True), json.dumps(v["unresolved"], sort_keys=True))
+                for c in facts["calls"] for pid, v in c["documents"].items()]
+    per = {}
+    for d in run_set:
+        pid = d["pool_id"]
+        row = rows.get(d["doc_key"]) or {}
+        evals = [{"when": c["when"], "seq": c["seq"], "facts": len(c["documents"][pid]["facts"]),
+                  "resolved_criticals": c["documents"][pid]["resolved"], "unresolved_criticals": c["documents"][pid]["unresolved"],
+                  "fields": c["documents"][pid]["fields"]} for c in facts["calls"] if pid in c["documents"]]
+        final = next((c["documents"][pid] for c in reversed(facts["calls"]) if pid in c["documents"] and c["when"] == "final"), None)
+        status = (lane.get("documents") or {}).get(pid) or {}
+        n_facts = max([e["facts"] for e in evals] or [0])
+        read = row.get("extracted") is not None and row.get("state") in ("fresh", "processing")
+        res = [c for e in evals for c in e["resolved_criticals"]]
+        unres = [c for e in evals for c in e["unresolved_criticals"]]
+        reason = None
+        if not read:
+            reason = f"not read by the application (row state {row.get('state')!r}, error {row.get('error')!r}, lane status {status.get('status')!r}: {status.get('reason')!r})"
+        elif n_facts == 0:
+            reason = "read, but the tripwire evaluated no fact"
+        per[pid] = {"doc_key": d["doc_key"], "staged_sha256": ALLOW[pid], "lane_status": status.get("status"), "lane_reason": status.get("reason"),
+                    "row": {k: row.get(k) for k in ("role", "state", "error", "sha256", "mirror")}, "extracted_present": row.get("extracted") is not None,
+                    "evaluations": evals, "facts_final": len((final or {}).get("facts") or []), "facts": (final or {}).get("facts"),
+                    "judged_rows_final": (final or {}).get("rows"), "resolved_criticals": res, "unresolved_criticals": unres,
+                    "exercised": read and n_facts > 0, "unread_reason": reason,
+                    "staged_sha_equals_row_sha": row.get("sha256") == ALLOW[pid]}
+    comp = (lane.get("stop_state") or {}).get("comparison")
+    gp = lane.get("global_provider") or {}
+    return {"per_document": per, "stop_state": lane.get("stop_state"), "stop_condition": STOP_CONDITION,
+            "stop_condition_fired": comp == STOP_CONDITION, "lane_stopped": lane.get("stopped"),
+            "tripwire_consistency": {"lane_entries": len(lane_pairs), "recomputed_entries": len(re_pairs), "equal": lane_pairs == re_pairs},
+            "requests": {"refusing_provider_calls": gp.get("requests_refused"), "dry_stub_calls": lane.get("dry_stub_calls"),
+                         "live_provider_attempts_blocked": lane.get("live_provider_attempts_blocked"),
+                         "provider_complete_calls_traced": len((lane.get("trace") or {}).get("provider_complete_calls") or []),
+                         "model_requests": lane.get("model_requests")},
+            "global_provider": {k: gp.get(k) for k in ("installed", "at_end", "still_installed_at_end", "requests_refused")},
+            "trace": lane.get("trace"), "lane_violations": lane.get("violations"), "evaluator": facts.get("evaluator")}
+
+
+def criterion(report: dict) -> dict:
+    """DRILL-CRITERION.md section 3, as declared before the first run."""
+    per = report["per_document"]
+    req = report["requests"]
+    zero_requests = (req["refusing_provider_calls"] == 0 and req["dry_stub_calls"] == 0 and not req["live_provider_attempts_blocked"]
+                     and req["provider_complete_calls_traced"] == 0)
+    resolved = {p: v["resolved_criticals"] for p, v in per.items() if v["resolved_criticals"]}
+    not_exercised = {p: v["unread_reason"] for p, v in per.items() if not v["exercised"]}
+    fields_ok = all(c.get("field") in FIELDS for v in resolved.values() for c in v)
+    if resolved or report["stop_condition_fired"] or not zero_requests:
+        result = "FAIL"
+    elif not_exercised:
+        result = "NOT PASS (incomplete)"
+    else:
+        result = "PASS"
+    return {"result": result, "declared_in": "DRILL-CRITERION.md (sha256 recorded in the R43 session log before the first run)",
+            "zero_resolved_criticals": not resolved, "resolved_criticals": resolved, "criticals_in_the_three_fields": fields_ok,
+            "stop_condition_fired": report["stop_condition_fired"], "all_exercised": not not_exercised, "not_exercised": not_exercised,
+            "zero_requests": zero_requests, "rule": "a critical is reported, never fixed here"}
+
+
+# ---- the facts subcommand (a subprocess, like the lane's tripwire) ---------------------------------------------------------
+def facts_main(truth_path, trace_path, out_path) -> int:
+    import lane_judge_r32 as J
+    import tripwire_r32 as TW
+
+    truth = json.loads(pathlib.Path(truth_path).read_text(encoding="utf-8"))
+    trace = json.loads(pathlib.Path(trace_path).read_text(encoding="utf-8"))
+    EV = TW.load_evaluator()
+    calls = []
+    for t in trace["tripwire_inputs"]:
+        docs = {}
+        for pid, row in (t["rows"] or {}).items():
+            facts = TW.facts_from_row(EV, row, None, None)
+            res = TW.tripwire(truth, pid, facts, (row or {}).get("sha256"))
+            jd = J.judge_document(truth, pid, {"facts": facts, "source_sha256": (row or {}).get("sha256")})
+            docs[pid] = {"facts": facts, "resolved": res["resolved"], "unresolved": res["unresolved"], "fields": res["fields"],
+                         "rows": [{k: j.get(k) for k in ("page", "field", "truth_kind", "outcome", "accepted_correct", "accepted_wrong")} for j in jd["rows"]]}
+        calls.append({"seq": t["seq"], "when": t["when"], "documents": docs})
+    pathlib.Path(out_path).write_text(json.dumps({"evaluator": EV.EVALUATOR_VERSION, "calls": calls}, indent=1, sort_keys=True, ensure_ascii=False,
+                                                 default=str) + "\n", encoding="utf-8", newline="\n")
+    return 0
+
+
+if __name__ == "__main__":
+    if len(sys.argv) == 5 and sys.argv[1] == "facts":
+        sys.exit(facts_main(sys.argv[2], sys.argv[3], sys.argv[4]))
+    raise SystemExit("usage: drill_r45.py facts <truth json> <DRILL-TRACE.json> <out json>")
--- review43/scripts/harness-r32/lane_r32.py
+++ review45/scripts/harness-r32/lane_r32.py
@@ -46,7 +46,11 @@
           provider (unchanged). The manifest records what the global provider was at the start and at the end.
   2.1.5   isolation: before anything is built, and again at the end, preflight_r32.verify_isolation refuses any
           environment value, application setting, import path or loaded module under the merged installation (except
-          the bound venv and this harness folder); the application's env file must not be the merged .env."""
+          the bound venv and this harness folder); the application's env file must not be the merged .env.
+R43-42 (review45): the dry-only baseline-facts drill (CFG 'drill', drill_r45.py): lane B, reader 'application', exactly
+F009 / F020 / F030 by id and sha256 (the cohort assertion below allows them only under that allow-list), AI off, the
+refusing global provider installed right after the provider module is imported; the lane's own B path runs unchanged;
+no capture store, allowance or ledger is opened (Forbidden sentinels); its own manifest and call trace, then the lane ends."""
 import json
 import os
 import pathlib
@@ -63,6 +67,13 @@
 assert MODE in ("dry", "live") and LANE in ("B", "C", "R", "P") and READER in ("application", "none")
 if pathlib.Path(CFG.get("harness_dir") or "").resolve() != HERE:
     raise SystemExit(f"refused: the configuration names another harness folder ({CFG.get('harness_dir')}); the lane runs only its own")
+DRILL = CFG.get("drill")                                            # R43-42: the baseline-facts drill, else None (every other mode)
+if DRILL is not None:
+    import drill_r45 as DR  # noqa: E402
+    try:
+        DRILL_CHECK = DR.check_config(CFG, LANE)                    # before anything else: lane B, dry, the allow-list, no run values
+    except DR._refused() as exc:
+        raise SystemExit(f"{exc} [lane {LANE} drill]")
 
 import allowance_r32 as AL  # noqa: E402
 import dispatch_guard_r32 as DG  # noqa: E402
@@ -83,6 +94,11 @@
 RUNSET = CFG["run_set"]
 if MODE == "dry" and READER == "application":
     cohort = [d["pool_id"] for d in RUNSET if not d["pool_id"].startswith("SYN")]
+    if DRILL is not None:                                           # R43-42: only the drill's allow-list (ids AND staged sha256)
+        try:
+            cohort = [p for p in cohort if p not in DR.check_cohort(RUNSET, TRUTH, CFG["truth"])]
+        except DR._refused() as exc:
+            raise SystemExit(f"{exc} [lane {LANE} drill]")
     assert not cohort, f"dry mode never runs a reader on a cohort document: {cohort[:5]}"
 TREE = pathlib.Path(os.getcwd())
 EXPECT_TREE = CFG["trees"]["baseline" if LANE == "B" else "candidate"]
@@ -93,6 +109,17 @@
     assert os.environ["DATABASE_URL"] == f"sqlite:///{(ROOT / 'db' / 'default.db').as_posix()}", os.environ["DATABASE_URL"]
 if MODE == "dry":
     assert not os.environ.get("AI_LEDGER_PATH"), "dry mode: no ledger"
+DRILL_GLOBAL = DRILL_INSTALL = None
+if DRILL is not None:                                               # R43-42: the refusing global provider, before any other application module
+    if os.environ.get("AI_ENABLED", "").lower() != "false" or os.environ.get("R34_OWNER_DISPATCH_TOKEN") is not None:
+        raise SystemExit(f"refused: the baseline-facts drill runs with AI_ENABLED=false and no owner token [lane {LANE} drill]")
+    from app.ai import provider as prov  # noqa: E402   (the drill's first application import)
+    import run_control_r38 as RC  # noqa: E402
+    DRILL_GLOBAL = RC.RefusingGlobalProvider(prov.AiResponse, lane=LANE, run_folder=CFG["run_folder"], invocation=int(CFG["invocation"]))
+    prov.set_provider(DRILL_GLOBAL)
+    DRILL_INSTALL = DR.check_provider(prov, DRILL_GLOBAL) | {"application_modules_at_installation": sorted(m for m in sys.modules if m == "app" or m.startswith("app."))}
+    DR.TRACER = DR.Tracer(HERE, TREE)
+    DR.TRACER.start()
 
 from app.core.config import get_settings  # noqa: E402
 
@@ -268,17 +295,22 @@
 IDENT = MI.IdentityGuard(base_inner, AiResponse, declared=declared, run_folder=RUN_FOLDER, invocation=INVOCATION, lane=LANE,
                          log_path=RUN_FOLDER / f"inv-{INVOCATION}" / f"IDENTITY-LOG-{LANE}.jsonl", ctx_fn=CS.get_context, provider_name_fn=provider_name_fn)
 MID = RC.CrashAfterResponse(IDENT, LANE, INJECT) if MODE == "dry" else IDENT
-if AL.bound_key(CFG["store"]) != CFG["run_key"]:
+if DRILL is not None:                                               # R43-42: no capture store, allowance or ledger is opened or consulted
+    allowance = alw = store = DR.Forbidden("the run's allowance / capture store (the baseline-facts drill has none)")
+elif AL.bound_key(CFG["store"]) != CFG["run_key"]:
     raise SystemExit("refused: the capture store is not bound to this run (RC-4)")
-allowance = AL.LaneAllowance(CFG["allowance"], CFG["caps"], CFG["project_window"], parent=CFG["parent"], run_key=CFG["run_key"],
-                             require_project=MODE == "live", create=False, project_totals=CFG.get("project_totals"))
-alw = AL.AllowanceProvider(allowance, LANE, MID, AiResponse, ep_of=ep_of, context_of=CS.get_context, invocation=INVOCATION,
-                           ledger_entry_of=lambda: LEDGER_LAST.pop("entry", None))
-store = CS.CaptureStore(CFG["store"])
+if DRILL is None:
+    allowance = AL.LaneAllowance(CFG["allowance"], CFG["caps"], CFG["project_window"], parent=CFG["parent"], run_key=CFG["run_key"],
+                                 require_project=MODE == "live", create=False, project_totals=CFG.get("project_totals"))
+    alw = AL.AllowanceProvider(allowance, LANE, MID, AiResponse, ep_of=ep_of, context_of=CS.get_context, invocation=INVOCATION,
+                               ledger_entry_of=lambda: LEDGER_LAST.pop("entry", None))
+    store = CS.CaptureStore(CFG["store"])
 ctl = RC.ControllerR38()
 TRIP = []
 if GLOBAL is not None:
     GLOBAL.attach(recorder=recorder, allowance=allowance, ctl=ctl, ep_of=ep_of, page_of=page_of)
+if DRILL_GLOBAL is not None:                                        # R43-42: the drill's refusing provider records into the lane (no allowance)
+    DRILL_GLOBAL.attach(recorder=recorder, ctl=ctl, ep_of=ep_of, page_of=page_of)
 
 
 def gate(policy_fn, reference_from=None):
@@ -415,7 +447,7 @@
         con.close()
 
 
-SERVES_BEFORE = serves_by_mode()
+SERVES_BEFORE = serves_by_mode() if DRILL is None else None        # R43-42: the drill has no capture store
 t0 = time.perf_counter()
 manifest = {"lane": LANE, "mode": MODE, "reader": READER, "tree": str(TREE), "sandbox": str(ROOT) if ROOT else None, "invocation": INVOCATION,
             "run_key": CFG["run_key"], "switch_source": CFG.get("switch_source"), "environment_check": ENV_CHECK,
@@ -429,8 +461,8 @@
     from app.services import document_processing, document_sync  # noqa: E402
     from app.ai import submittal_reader  # noqa: E402
 
-    G = gate(lambda: CFG["policies"]["B"])
-    chain = stop_guard(G)
+    G = gate(lambda: CFG["policies"]["B"]) if DRILL is None else None
+    chain = stop_guard(G) if DRILL is None else DRILL_GLOBAL         # R43-42: the drill's provider is the refusing global provider
     prov.set_provider(chain)
     _orig_run_call = submittal_reader._Run.call
 
@@ -665,6 +697,17 @@
                      "env_switches": {k: v for k, v in os.environ.items() if k.startswith("AI_EVIDENCE_")},
                      "evidence_tasks": sorted(er.PROMPTS), "store_dispatched_to_inner": G.dispatched,
                      "application_reader_run": READER == "application"}
+if DRILL is not None:                                               # R43-42: the drill's manifest and end checks; nothing below runs
+    DR.TRACER.stop()
+    try:
+        ISOLATION_CHECK["end"] = PF.verify_isolation(LANE, os.environ, settings)
+    except PF.Refused as exc:
+        ISOLATION_CHECK["end"] = {"ok": False, "refused": str(exc)}
+    manifest |= DR.lane_manifest(recorder=recorder, ctl=ctl, trip=TRIP, provider=DRILL_GLOBAL, prov=prov, stub=STUB, blocked=blocked,
+                                 isolation=ISOLATION_CHECK, app_env=APP_ENV_CHECK, env_check=ENV_CHECK, task_kinds=TASK_KINDS, stopped=stopped,
+                                 seconds=round(time.perf_counter() - t0, 1), install=DRILL_INSTALL | {"ai_enabled_setting": settings.ai_enabled},
+                                 tracer=DR.TRACER) | {"drill_check": DRILL_CHECK}
+    sys.exit(DR.finish_lane(OUT, manifest, DR.TRACER))
 after = serves_by_mode()
 docs = recorder.documents()
 try:                                                                # ORCH-10 (2.1.5): isolation again, with every module the lane loaded
--- review43/scripts/harness-r32/runner_r32.py
+++ review45/scripts/harness-r32/runner_r32.py
@@ -4,6 +4,8 @@
   runner_r32.py run    --mode dry  --stamp S --run-set RS.json --binding BM.json --binding-sha SHA [--sandbox-base D]
                        [--out DIR] [--dry-fault L:N] [--dry-inject INJECT.json] [--dry-synthetic SPEC.json]
   runner_r32.py resume --mode dry  (the same arguments as the run)
+  runner_r32.py run    --mode dry  --dry-baseline-facts SPEC.json --stamp S --run-set RS.json --binding BM.json --binding-sha SHA
+                       [--sandbox-base D]   (R43-42, review45: lane B on frozen-r13, F009 / F020 / F030 only; drill_r45.py)
   runner_r32.py run    --mode live --declaration DECL.json --declaration-sha SHA --run-set RS.json --binding BM.json --binding-sha SHA
   runner_r32.py resume --mode live (the same arguments)
 There is no --auth-path (RC-3): the authorization is pinned beside the declaration (dispatch_guard_r32).
@@ -509,6 +511,8 @@
                                        "before it was saved (the row stays reserved and charged)")
     a.add_argument("--dry-inject", help="dry drill only: a JSON file {injections: [...], caps?, project_window?, parent?, dry_ledger?, application_limits?}")
     a.add_argument("--dry-synthetic", help="dry drill only: a JSON spec of SYNTHETIC EP-990001 documents (application readers on them only)")
+    a.add_argument("--dry-baseline-facts", help="dry drill only (R43-42): the baseline-facts drill SPEC -- lane B, frozen-r13, F009 / F020 / F030 "
+                                                "by id and sha256, AI off, the refusing global provider; no allowance, store or ledger (drill_r45.py)")
     return a.parse_args(argv)
 
 
@@ -609,10 +613,13 @@
 def main(argv=None) -> int:
     args = parse(argv)
     live = args.mode == "live"
-    if live and (args.dry_fault or args.dry_inject or args.dry_synthetic or args.sandbox_base):
-        raise Refused("refused: --dry-fault / --dry-inject / --dry-synthetic / --sandbox-base are dry-mode drills only")
+    if live and (args.dry_fault or args.dry_inject or args.dry_synthetic or args.sandbox_base or args.dry_baseline_facts):
+        raise Refused("refused: --dry-fault / --dry-inject / --dry-synthetic / --dry-baseline-facts / --sandbox-base are dry-mode drills only")
     if not live and (args.declaration or args.declaration_sha):
         raise Refused("refused: dry mode takes no declaration (a declaration is the live contract)")
+    if args.dry_baseline_facts:                                          # R43-42 (review45): an additional, explicitly named dry drill
+        import drill_r45 as DR
+        return DR.run(args, sys.modules[__name__])
     started = _now()
     # ---- 0. preflight: NOTHING is created, re-opened or consumed before every check has passed (ORCH-10, R41-09) ------
     binding = PF.verify_binding(args.binding, args.binding_sha)
--- /dev/null
+++ review45/scripts/harness-r32/test_dry_baseline_drill_r45.py
@@ -0,0 +1,352 @@
+"""R43-42 (review45): the dry-only baseline-facts drill (drill_r45.py; runner_r32 --dry-baseline-facts; lane_r32 drill branch).
+(a) refusals: a fourth or a substituted document, lanes C / R / P, the cand-r30n tree, the live flag, a resume, another
+drill flag, a stamp naming a live run, an owner token in the environment, a provider that is not the refusing stub, and a
+ledger / scope / RUN / allowance / authorization path being consulted (runner: forbid; lane: the configuration check and
+the Forbidden sentinels) -- each before anything is created; the other dry rules are unchanged (reader 'none' over the real
+cohort, the cohort assertion without the drill, --dry-synthetic SYN* only);
+(b) ONE real drill over F009, F020 and F030 (lane B, frozen-r13, AI off): the three documents pass through the lane's own
+functions, asserted on the lane's call trace (document_processing.run -> lane process -> document_sync.process ->
+b_tripwire 'after_document', and the 'final' tripwire over all three), the tripwire recomputation equals the lane's, 0
+requests (refusing provider 0 calls, dry stub 0 calls, no complete() traced), the AI ledger unchanged, and no run state,
+allowance, capture store or authorization file in the drill folder;
+(c) the criterion evaluation of DRILL-CRITERION.md (PASS, FAIL on a resolved critical or a request, NOT PASS when a
+document is not exercised). The drill's RESULT on the real documents is not asserted here: a critical is reported, never
+made to pass. Run: python -m pytest -q test_dry_baseline_drill_r45.py"""
+import hashlib
+import json
+import os
+import pathlib
+import subprocess
+import uuid
+
+import pytest
+
+import allowance_r32 as AL
+import dispatch_guard_r32 as DG
+import drill_r45 as DR
+import model_identity_r38 as MI
+import preflight_r32 as PF
+import request_paths_r42 as RP
+import run_control_r38 as RC
+import runner_r32 as RN
+
+RUN_SET = "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot/review34/RUN-SET-PROPOSAL.json"
+_T = {}
+
+
+def _truth():
+    if "t" not in _T:
+        _T["t"] = PF.build_truth()
+    return _T["t"]
+
+
+def _binding(tmp_path):
+    tmp_path.mkdir(parents=True, exist_ok=True)
+    f = tmp_path / "bound.txt"
+    f.write_text("bound", encoding="utf-8", newline="\n")
+    p = tmp_path / "BINDING.json"
+    p.write_text(json.dumps({"files": {"g": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()}}}), encoding="utf-8", newline="\n")
+    return p, hashlib.sha256(p.read_bytes()).hexdigest()
+
+
+def _spec(tmp_path, **over):
+    spec = {"drill": "baseline-facts", "lane": "B", "tree": "C:/t/iso/frozen-r13",
+            "documents": [{"pool_id": p, "staged_sha256": s} for p, s in DR.ALLOW.items()]}
+    spec |= over
+    p = tmp_path / f"SPEC-{uuid.uuid4().hex[:6]}.json"
+    p.write_text(json.dumps(spec), encoding="utf-8", newline="\n")
+    return p
+
+
+def _stamp():
+    return f"t45-{uuid.uuid4().hex[:10]}"
+
+
+def _args(tmp_path, spec, stamp=None, mode="dry", command="run", extra=()):
+    b, sha = _binding(tmp_path)
+    return [command, "--mode", mode, "--dry-baseline-facts", str(spec), "--stamp", stamp or _stamp(), "--run-set", RUN_SET,
+            "--binding", str(b), "--binding-sha", sha, *extra]
+
+
+def _created(stamp):
+    return (RN.SANDBOX_BASE / f"{DR.FOLDER_PREFIX}{stamp}").exists() or (RN.SANDBOX_BASE / stamp).exists()
+
+
+# ---- (a) refusals, runner side: nothing is created ---------------------------------------------------------------------------
+@pytest.mark.parametrize("docs,match", [
+    (list(DR.ALLOW.items()) + [("F037", "0" * 64)], "exactly"),
+    ([("F009", DR.ALLOW["F009"]), ("F020", DR.ALLOW["F020"])], "exactly"),
+    ([("F009", DR.ALLOW["F009"]), ("F020", DR.ALLOW["F020"]), ("F033", DR.ALLOW["F030"])], "exactly"),
+    ([("F009", DR.ALLOW["F009"]), ("F020", DR.ALLOW["F020"]), ("F030", DR.ALLOW["F020"])], "is not the allowed"),
+])
+def test_any_other_document_set_is_refused_before_anything_is_created(tmp_path, docs, match):
+    stamp = _stamp()
+    spec = _spec(tmp_path, documents=[{"pool_id": p, "staged_sha256": s} for p, s in docs])
+    with pytest.raises(RN.Refused, match=match):
+        RN.main(_args(tmp_path, spec, stamp))
+    assert not _created(stamp)
+
+
+@pytest.mark.parametrize("lane", ["C", "R", "P"])
+def test_lanes_c_r_and_p_are_refused(tmp_path, lane):
+    stamp = _stamp()
+    with pytest.raises(RN.Refused, match="lane B only"):
+        RN.main(_args(tmp_path, _spec(tmp_path, lane=lane), stamp))
+    assert not _created(stamp)
+
+
+@pytest.mark.parametrize("tree", ["C:/t/iso/cand-r30n", "C:/t/iso/cand-r30", "C:/t/iso/frozen-r12"])
+def test_any_tree_but_frozen_r13_is_refused(tmp_path, tree):
+    stamp = _stamp()
+    with pytest.raises(RN.Refused, match="frozen-r13 only"):
+        RN.main(_args(tmp_path, _spec(tmp_path, tree=tree), stamp))
+    assert not _created(stamp)
+
+
+def test_the_live_flag_is_refused(tmp_path):
+    stamp = _stamp()
+    with pytest.raises(RN.Refused, match="dry-mode drills only"):
+        RN.main(_args(tmp_path, _spec(tmp_path), stamp, mode="live"))
+    assert not _created(stamp)
+
+
+@pytest.mark.parametrize("extra,command,match", [
+    ([], "resume", "never resumed"),
+    (["--dry-synthetic", "x.json"], "run", "no other drill"),
+    (["--dry-inject", "x.json"], "run", "no other drill"),
+    (["--dry-fault", "B:1"], "run", "no other drill"),
+    (["--out", "C:/t/r2x/r42-sandbox/anywhere"], "run", "no --out"),
+])
+def test_a_resume_another_drill_or_an_output_folder_is_refused(tmp_path, extra, command, match):
+    stamp = _stamp()
+    with pytest.raises(RN.Refused, match=match):
+        RN.main(_args(tmp_path, _spec(tmp_path), stamp, command=command, extra=extra))
+    assert not _created(stamp)
+
+
+@pytest.mark.parametrize("stamp", ["r32-v4", "x-r32-v5", "R32-V9-b", "a/b", "ab"])
+def test_a_stamp_naming_a_live_run_or_a_bad_stamp_is_refused(tmp_path, stamp):
+    with pytest.raises(RN.Refused, match="drill stamp"):
+        RN.main(_args(tmp_path, _spec(tmp_path), stamp))
+    assert not (RN.SANDBOX_BASE / "r32-v4").exists()
+
+
+def test_an_owner_token_in_the_environment_is_refused(tmp_path, monkeypatch):
+    monkeypatch.setenv(DG.TOKEN_ENV, "test-token-not-real")
+    stamp = _stamp()
+    with pytest.raises(RN.Refused, match="never reads an owner token"):
+        RN.main(_args(tmp_path, _spec(tmp_path), stamp))
+    assert not _created(stamp)
+
+
+def test_forbid_refuses_every_ledger_scope_run_allowance_and_authorization_function_and_restores_them(tmp_path):
+    before = {n: getattr(m, n) for m, n in ((PF, "verify_ledger_scope"), (DG, "authorize"), (AL, "LaneAllowance"), (RN, "ledger_state"))}
+    with DR.forbid(RN) as names:
+        assert {"preflight_r32.verify_ledger_scope", "preflight_r32.ledger_counts", "dispatch_guard_r32.authorize", "dispatch_guard_r32.check",
+                "allowance_r32.LaneAllowance", "allowance_r32.bind_store", "runner_r32.ledger_state", "runner_r32.create_allowance_atomic",
+                "runner_r32._state_write", "model_identity_r38.record_invocation"} <= set(names)
+        calls = [lambda: PF.verify_ledger_scope({"path": "x", "scope": "y"}), lambda: PF.ledger_counts(), lambda: PF.ledger_snapshot("x"),
+                 lambda: DG.authorize("d", "s", run_folder=tmp_path, invocation=1, action="consume"), lambda: DG.check("d", "s"),
+                 lambda: AL.LaneAllowance(tmp_path / "a.sqlite", {}, {}), lambda: AL.bind_store(tmp_path / "c.sqlite", "k"),
+                 lambda: RN.ledger_state(), lambda: RN.create_allowance_atomic({}, tmp_path), lambda: RN._state_write(tmp_path / "RUN-STATE.json", {}),
+                 lambda: MI.record_invocation(tmp_path, 1, {}, "v")]
+        for c in calls:
+            with pytest.raises(PF.Refused, match="never consults"):
+                c()
+    assert list(tmp_path.iterdir()) == [], "nothing was written"
+    assert {n: getattr(m, n) for m, n in ((PF, "verify_ledger_scope"), (DG, "authorize"), (AL, "LaneAllowance"), (RN, "ledger_state"))} == before
+
+
+def test_the_forbidden_sentinel_refuses_and_records_every_use():
+    DR.VIOLATIONS.clear()
+    f = DR.Forbidden("the run's allowance / capture store")
+    with pytest.raises(PF.Refused, match="never consults"):
+        f.record_refusal("B", "x", "y")
+    with pytest.raises(PF.Refused, match="never consults"):
+        f.used("B")
+    assert len(DR.VIOLATIONS) == 2
+    DR.VIOLATIONS.clear()
+
+
+class _Prov:
+    def __init__(self, p):
+        self.p = p
+
+    def get_provider(self):
+        return self.p
+
+
+def test_a_provider_that_is_not_the_refusing_stub_is_refused():
+    from app.ai.provider import AiResponse, Usage
+    good = RC.RefusingGlobalProvider(AiResponse, lane="B", run_folder="C:/t/r2x/r42-sandbox/none", invocation=1)
+    other = RC.RefusingGlobalProvider(AiResponse, lane="B", run_folder="C:/t/r2x/r42-sandbox/none", invocation=1)
+    stub = RC.DryStub(AiResponse, Usage, "B")
+    assert DR.check_provider(_Prov(good), good)["global_provider"] == "RefusingGlobalProvider"
+    for installed, expected in ((stub, stub), (other, good), (None, good), (good, None)):
+        with pytest.raises(PF.Refused, match="not the refusing global provider"):
+            DR.check_provider(_Prov(installed), expected)
+
+
+# ---- (a) refusals, lane side: a direct lane invocation with a drill configuration ---------------------------------------------
+def _lane_cfg(tmp_path, **over):
+    T = _truth()
+    folder = tmp_path / "r32-drill-direct"
+    cfg = {"drill": "baseline-facts", "mode": "dry", "reader": "application", "harness_dir": str(RN.HERE), "out_dir": str(tmp_path / "out"),
+           "truth": str(tmp_path / "TRUTH.json"), "run_folder": folder.as_posix(), "run_key": None, "invocation": 1, "trees": dict(RN.TREES),
+           "sandbox": {"B": str(folder / "B")},
+           "run_set": [{"pool_id": p, "doc_key": T["documents"][p]["doc_key"], "ep": T["documents"][p]["ep"]} for p in DR.ALLOW]}
+    for k, v in over.items():
+        if v is None:
+            cfg.pop(k, None)
+        else:
+            cfg[k] = v
+    (tmp_path / "out").mkdir(exist_ok=True)
+    p = tmp_path / "out" / "DRILL-CONFIG.json"
+    p.write_text(json.dumps(cfg), encoding="utf-8", newline="\n")
+    return p
+
+
+@pytest.mark.parametrize("lane,over,match", [
+    ("C", {}, "lane B only"), ("R", {}, "lane B only"), ("P", {}, "lane B only"),
+    ("B", {"trees": {"baseline": "C:/t/iso/cand-r30n/backend", "candidate": "C:/t/iso/cand-r30n/backend"}}, "frozen-r13/backend only"),
+    ("B", {"mode": "live"}, "dry mode only"),
+    ("B", {"ledger": {"path": "C:/t/r2x/ledger/r2x-ledger.sqlite", "scope": "x"}}, "never consults or writes \\['ledger'\\]"),
+    ("B", {"store": "C:/t/r2x/r42-sandbox/x/capture.sqlite"}, "never consults or writes \\['store'\\]"),
+    ("B", {"allowance": "C:/t/r2x/r42-sandbox/x/allowance.sqlite"}, "never consults or writes \\['allowance'\\]"),
+    ("B", {"run_key": "k"}, "never consults or writes \\['run_key'\\]"),
+    ("B", {"declaration_path": "C:/x/DECLARATION.json"}, "declaration_path"),
+    ("B", {"dry_inject": [{"kind": "usage", "lane": "B", "calls": [1]}]}, "dry_inject"),
+    ("B", {"run_folder": "C:/t/r2x/r42-sandbox/r32-v4"}, "r32-drill-<stamp>"),
+    ("B", {"run_set": [{"pool_id": "F037", "doc_key": "x", "ep": "1"}]}, "takes exactly"),
+])
+def test_a_direct_lane_invocation_with_a_bad_drill_configuration_is_refused_before_the_application_is_imported(tmp_path, lane, over, match):
+    cp = _lane_cfg(tmp_path, **over)
+    tree = RN.TREES["candidate" if lane != "B" else "baseline"]
+    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_")} | {"AI_ENABLED": "false"}
+    r = subprocess.run([RN.PY, str(RN.HERE / "lane_r32.py"), lane, str(cp)], cwd=tree, env=env, capture_output=True, text=True)
+    assert r.returncode != 0 and f"[lane {lane} drill]" in r.stderr, r.stderr[-1500:]
+    import re
+    assert re.search(match, r.stderr), r.stderr[-1500:]
+    assert not (tmp_path / "out" / f"LANE-{lane}.json").exists() and not (tmp_path / "r32-drill-direct").exists()
+
+
+def test_without_the_drill_the_dry_cohort_rule_is_unchanged(tmp_path):
+    """No 'drill' key: a dry lane with reader 'application' on a cohort document still fails the cohort assertion."""
+    T = _truth()
+    tp = tmp_path / "TRUTH.json"
+    tp.write_text(PF.truth_text(T), encoding="utf-8", newline="\n")
+    cp = _lane_cfg(tmp_path, drill=None, truth=str(tp))
+    env = {k: v for k, v in os.environ.items() if not k.startswith("AI_")}
+    r = subprocess.run([RN.PY, str(RN.HERE / "lane_r32.py"), "B", str(cp)], cwd=RN.TREES["baseline"], env=env, capture_output=True, text=True)
+    assert r.returncode != 0 and "dry mode never runs a reader on a cohort document" in r.stderr, r.stderr[-1500:]
+
+
+def test_static_the_other_dry_rules_and_the_single_application_entry_are_unchanged():
+    src = (RN.HERE / "runner_r32.py").read_text(encoding="utf-8")
+    assert '"reader": "application" if (live or synthetic is not None) else "none"' in src, "reader 'none' over the real cohort in every other dry mode"
+    assert 'raise Refused("refused: a synthetic drill holds only SYN* documents of EP-990001")' in src
+    lane = (RN.HERE / "lane_r32.py").read_text(encoding="utf-8")
+    assert 'assert not cohort, f"dry mode never runs a reader on a cohort document: {cohort[:5]}"' in lane
+    ins = RP.lane_installs()
+    assert [e["call"] for e in ins["entries"]["B"]].count("document_processing.run") == 1, "the drill uses the lane's one application entry"
+    i_install = lane.index("prov.set_provider(DRILL_GLOBAL)")
+    assert i_install < lane.index("from app.core.config import get_settings"), "the refusing provider precedes every other application import"
+    assert lane.index("from app.ai import provider as prov  # noqa: E402   (the drill's first application import)") < i_install
+    assert RP.global_resolution(ins)["B"]["installed_before_every_application_entry"]
+
+
+# ---- (b) ONE real drill over F009, F020, F030 ---------------------------------------------------------------------------------
+@pytest.fixture(scope="module")
+def drill(tmp_path_factory):
+    tmp = tmp_path_factory.mktemp("drill45")
+    led_before = RN.ledger_state()
+    stamp = _stamp()
+    rc = RN.main(_args(tmp, _spec(tmp), stamp))
+    folder = RN.SANDBOX_BASE / f"{DR.FOLDER_PREFIX}{stamp}"
+    out = folder / "out"
+    j = lambda n: json.loads((out / n).read_text(encoding="utf-8"))  # noqa: E731
+    return {"rc": rc, "folder": folder, "lane": j("LANE-B.json"), "trace": j("DRILL-TRACE.json"), "report": j("DRILL-REPORT.json"),
+            "rows": j("rows-B.json"), "led_before": led_before, "led_after": RN.ledger_state()}
+
+
+def test_the_drill_ran_in_its_own_folder_with_no_run_state_allowance_store_or_authorization(drill):
+    f = drill["folder"]
+    assert drill["rc"] == 0 and f.name.startswith("r32-drill-") and not DR._LIVE_RUN.search(f.name)
+    names = {p.name for p in f.rglob("*")}
+    for n in ("RUN-STATE.json", "allowance.sqlite", "capture.sqlite", "WRITER.lock", "FAKE-LEDGER.sqlite", "CONTRACT-BREACH.json",
+              "IDENTITY-INVALID.json", "PROVIDER-IDENTITY.json", "CLI-VERSIONS.jsonl"):
+        assert n not in names, n
+    assert not (f / DG.CONSUMED_DIR).exists() and not any("authorization" in n.lower() for n in names)
+    assert set(p.name for p in f.iterdir()) == {"out", "B"}
+
+
+def test_zero_requests_and_the_ledger_unchanged(drill):
+    lane, rep = drill["lane"], drill["report"]
+    assert lane["model_requests"] == 0 and lane["dry_stub_calls"] == 0 and lane["live_provider_attempts_blocked"] == []
+    assert lane["global_provider"]["requests_refused"] == 0 and lane["global_provider"]["still_installed_at_end"]
+    assert lane["global_provider"]["at_end"] == "RefusingGlobalProvider" and lane["violations"] == []
+    assert lane["global_provider"]["installed"]["ai_enabled_setting"] is False
+    assert set(lane["global_provider"]["installed"]["application_modules_at_installation"]) <= {"app", "app.ai", "app.ai.guard", "app.ai.provider",
+                                                                                                "app.core", "app.core.config"}
+    assert drill["trace"]["summary"]["provider_complete_calls"] == [] and rep["requests"]["provider_complete_calls_traced"] == 0
+    assert drill["led_before"] == drill["led_after"]
+
+
+def test_the_three_documents_pass_through_the_lanes_own_functions_by_call_trace(drill):
+    calls = [c for c in drill["trace"]["calls"] if c["event"] == "call"]
+    by = lambda f, fn: [c for c in calls if c["file"] == f and c["function"] == fn]  # noqa: E731
+    runs = by("document_processing", "run")
+    assert len(runs) == 1 and str(runs[0]["ep"]) == DR.EP and runs[0]["caller"] == "lane_r32:<module>"
+    T = _truth()
+    rel = {T["documents"][p]["relative_path"].replace("\\", "/"): p for p in DR.ALLOW}
+    pid = lambda c: rel[str(c["relative_path"]).replace("\\", "/")]  # noqa: E731
+    lane_process = by("lane_r32", "process")
+    app_process = by("document_sync", "process")
+    assert all(c["caller"] == "document_processing:run" for c in lane_process), "the application calls the lane's hook"
+    assert all(c["caller"] == "lane_r32:process" for c in app_process), "the lane's hook calls the application's own process"
+    read = {pid(c) for c in lane_process}
+    assert read and read <= set(DR.ALLOW) and {pid(c) for c in app_process} == read
+    trips = drill["trace"]["tripwire_inputs"]
+    after = {p for t in trips if t["when"] == "after_document" for p in t["rows"]}
+    assert after == read, "every document the application read was judged by the lane's after_document tripwire"
+    finals = [t for t in trips if t["when"] == "final"]
+    assert len(finals) == 1 and set(finals[0]["rows"]) == set(DR.ALLOW), "the final tripwire judges all three"
+    assert by("lane_r32", "row_dict") and len(by("lane_r32", "b_tripwire")) == len(trips)
+    assert all(c["caller"] in ("lane_r32:_after", "lane_r32:<module>") for c in by("lane_r32", "b_tripwire"))
+    avail = [c for c in drill["trace"]["calls"] if c["event"] == "return" and c["function"] == "available"]
+    assert avail and all("AI_ENABLED=false" in c["returned"] for c in avail), "AI off: no form read can be requested"
+    docs = drill["lane"]["documents"]
+    for p in set(DR.ALLOW) - read:            # a document not read is visible, never silent (a stop by a critical)
+        assert docs[p]["status"] == "INCOMPLETE" and drill["report"]["stop_condition_fired"], docs[p]
+
+
+def test_the_tripwire_recomputation_equals_the_lanes_and_the_rows_are_the_staged_bytes(drill):
+    rep = drill["report"]
+    assert rep["tripwire_consistency"]["equal"] and rep["tripwire_consistency"]["lane_entries"] > 0
+    for p, v in rep["per_document"].items():
+        if v["extracted_present"]:
+            assert v["staged_sha_equals_row_sha"], p
+    assert rep["criterion"]["result"] in ("PASS", "FAIL", "NOT PASS (incomplete)")
+    assert rep["criterion"] == DR.criterion(rep)
+
+
+# ---- (c) the criterion evaluation -------------------------------------------------------------------------------------------
+def _rep(resolved=None, exercised=None, refusing=0, stub=0, blocked=(), traced=0, fired=False):
+    per = {p: {"resolved_criticals": (resolved or {}).get(p, []), "exercised": (exercised or {}).get(p, True),
+               "unread_reason": None if (exercised or {}).get(p, True) else "UNREAD: needs OCR"} for p in DR.ALLOW}
+    return {"per_document": per, "stop_condition_fired": fired,
+            "requests": {"refusing_provider_calls": refusing, "dry_stub_calls": stub, "live_provider_attempts_blocked": list(blocked),
+                         "provider_complete_calls_traced": traced}}
+
+
+def test_criterion_pass_fail_and_not_pass():
+    assert DR.criterion(_rep())["result"] == "PASS"
+    crit = {"F009": [{"pool_id": "F009", "page": "3", "field": "identity", "value": "X", "outcome": "wrong_only", "truth": "Y"}]}
+    c = DR.criterion(_rep(resolved=crit, fired=True))
+    assert c["result"] == "FAIL" and c["resolved_criticals"] == crit and c["criticals_in_the_three_fields"]
+    assert DR.criterion(_rep(resolved={"F030": [{"field": "decision"}]}))["result"] == "FAIL"
+    for kw in ({"refusing": 1}, {"stub": 1}, {"blocked": ["ClaudeCodeProvider"]}, {"traced": 1}):
+        assert DR.criterion(_rep(**kw))["result"] == "FAIL", kw
+    c = DR.criterion(_rep(exercised={"F020": False}))
+    assert c["result"] == "NOT PASS (incomplete)" and list(c["not_exercised"]) == ["F020"]
+    assert DR.criterion(_rep(exercised={"F020": False}, resolved=crit))["result"] == "FAIL", "a critical outranks an unread document"
```
