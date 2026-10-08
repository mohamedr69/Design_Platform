"""R43-40: the same demonstrations on the review43 harness for declaration-r32-v4 (byte copy checked against its binding;
run folders under the dry base C:/t/r2x/r42-sandbox/r43p/sb, substitution S-BASE; stamps r43d-*; one more refusal case:
an authorization naming the executed v3 RUN hash).
ORCH-10 section 2.6 (R42PORT-IMPL): the scripted-provider demonstrations of the corrected harness. DRY / synthetic
providers only: the refusing DryStub (dry mode) or, for the authorization drills, an in-process live-SHAPED runner with
a temporary contract-5 declaration, a FAKE ledger, a text file standing for the pinned CLI (hashed, never executed),
`--version` replaced, the owner's authorization an IN-MEMORY object (no authorization file is ever written) and the lanes
replaced by a raising stub. 0 CLI invocations (the R42 audit guard refuses any `claude` process in this process and every
child), 0 model requests, the AI ledger read mode=ro before and after.

Usage: <bound python> -B demos_r42.py <harness dir> <out dir (new)>     (run with PYTHONPATH=<work>/guard)
Writes <out dir>/DEMOS-R42.json and per-demo records; run folders under C:/t/r2x/r42-sandbox (stamps r42d-demo-*, vis-*).
Demonstrations (each also names the tests that prove the same point):
  completion            ordinary completion of a dry run, every lane COMPLETE
  refusal_before_dispatch  no authorization / another hash / the frozen hash / the placeholder declaration / no token
  interruption          an interruption at every phase and its recovery (re-entry or resume), never re-sending a charged request
  deadends              Verification 41's dead-end cases T, A, B, C, D, E under the corrected runner (dry and live-shaped)
  durable_charging      failed (timeout), interrupted and dispatched-but-unsaved requests stay charged across the resume
  terminal_stop         a durable stop (three timeouts; a lane allowance) is never reopened by a resume
  window_deferral       the project-window deferral and its resume at retry_at_full (an early resume refused, nothing created)
  page_accounting       every page read, unread under the application's limits, or refused: summing to the document's pages
  global_provider       R40-04 option 2: get_provider().complete(...) refused in C, R and P (INVALID); B unchanged"""
from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sqlite3
import sys
import time
import traceback
import uuid
from collections import namedtuple

sys.dont_write_bytecode = True
H_DIR = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2])
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))   # R43-40: the package scripts
import r42common as C  # noqa: E402
import r43p_base as B  # noqa: E402

if H_DIR != C.HARNESS42.resolve():
    raise SystemExit(f"refused: the demonstrations run the checked harness folder {C.HARNESS42} only")
COPY = C.check_run_copy()
sys.path.insert(0, str(H_DIR))
import allowance_r32 as AL  # noqa: E402
import dispatch_guard_r32 as DG  # noqa: E402
import model_identity_r38 as MI  # noqa: E402
import preflight_r32 as PF  # noqa: E402
import r32_test_helpers as H  # noqa: E402
import run_state_r38 as RS  # noqa: E402
import runner_r32 as RN  # noqa: E402
import visibility_r38 as V  # noqa: E402
import sandbox_ingest_r32 as SI  # noqa: E402

BASE = B.redirect(PF, RN, SI)                                         # R43-40: S-BASE

LEDGER = "C:/t/r2x/ledger/r2x-ledger.sqlite"
Disk = namedtuple("Disk", "total used free")
REAL_DISK = shutil.disk_usage
_T = {}


def truth():
    if "t" not in _T:
        _T["t"] = PF.build_truth()
    return _T["t"]


class Patch:
    """A minimal monkeypatch (restores on exit)."""

    def __init__(self):
        self.saved = []

    def set(self, obj, name, value):
        self.saved.append((obj, name, getattr(obj, name)))
        setattr(obj, name, value)

    def undo(self):
        for obj, name, value in reversed(self.saved):
            setattr(obj, name, value)
        self.saved = []


def call(fn, *a):
    try:
        fn(*a)
        return {"result": "finished"}
    except RN.Refused as exc:
        return {"result": "refused", "why": str(exc)[:400]}
    except KeyboardInterrupt:
        return {"result": "interrupted", "why": "KeyboardInterrupt (injected)"}
    except BaseException as exc:  # noqa: BLE001
        return {"result": "error", "why": f"{type(exc).__name__}: {str(exc)[:300]}"}


def binding(work):
    work.mkdir(parents=True, exist_ok=True)
    f = work / "bound.txt"
    f.write_text("r42 demo binding (dry)", encoding="utf-8", newline="\n")
    b = work / "BINDING.json"
    b.write_text(json.dumps({"files": {"demo": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()}}}), encoding="utf-8", newline="\n")
    return b, hashlib.sha256(b.read_bytes()).hexdigest()


def run_set(work, ids=("F045", "F051")):
    T = truth()
    p = work / "RUN-SET.json"
    p.write_text(json.dumps({"documents": [{"pool_id": i, "doc_key": T["documents"][i]["doc_key"], "ep": T["documents"][i]["ep"]} for i in ids]}),
                 encoding="utf-8", newline="\n")
    return p


def state(folder):
    p = folder / RN.RUN_STATE
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def report(folder, n):
    p = folder / f"inv-{n}" / "out" / "RUN-REPORT.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def consumed(folder):
    d = folder / DG.CONSUMED_DIR
    return sorted(p.name for p in d.glob("consumed-*.json")) if d.is_dir() else []


def store_facts(folder):
    cap = folder / "capture.sqlite"
    if not cap.is_file():
        return None
    s = RN.store_counts(cap)
    return {"rows": s["rows"], "duplicate_bound_keys": len(s["duplicate_bound_keys"]), "reserved_without_answer": s["reserved_without_answer"],
            "serves": s["serves_by_lane_mode"]}


def charges(folder):
    p = folder / "allowance.sqlite"
    if not p.is_file():
        return None
    con = sqlite3.connect(f"file:{p.as_posix()}?mode=ro", uri=True)
    try:
        return {"total": con.execute("select count(*) from charges").fetchone()[0],
                "by_lane_outcome": [list(r) for r in con.execute("select lane, coalesce(outcome, 'unsettled'), count(*) from charges group by lane, outcome order by lane")],
                "stops": [list(r) for r in con.execute("select lane, kind, invocation from stops order by lane")]}
    finally:
        con.close()


class Dry:
    def __init__(self, work, ids=("F045", "F051"), inject=None):
        b, sha = binding(work)
        rs = run_set(work, ids)
        self.stamp = f"r43d-demo-{uuid.uuid4().hex[:8]}"
        self.args = ["--mode", "dry", "--stamp", self.stamp, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha]
        if inject:
            (work / "INJECT.json").write_text(json.dumps(inject), encoding="utf-8", newline="\n")
            self.args += ["--dry-inject", str(work / "INJECT.json")]
        self.folder = RN.SANDBOX_BASE / self.stamp

    def run(self, *extra):
        return call(RN.main, ["run"] + self.args + list(extra))

    def resume(self, *extra):
        return call(RN.main, ["resume"] + self.args + list(extra))

    def facts(self):
        st = state(self.folder)
        return {"folder_exists": self.folder.exists(), "allowance_exists": (self.folder / "allowance.sqlite").exists(),
                "invocations": [{k: i.get(k) for k in ("n", "kind", "status", "run_state", "comparison_state")} for i in (st or {}).get("invocations", [])],
                "store": store_facts(self.folder), "charges": charges(self.folder)}


class Live:
    """Live-SHAPED (module docstring): no authorization file, no lane, no CLI process."""

    def __init__(self, work, patch: Patch, nonces=("nonce-demo-0123456789-a",), multi=False):
        self.p = patch
        b, sha = binding(work)
        rs = run_set(work)
        led = H.fake_ledger(work / "fake-ledger.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, None, 0)})
        self.stamp = f"r43d-demo-live-{uuid.uuid4().hex[:8]}"
        self.decl, self.dsha, self.rec = H.live_declaration(work / "pkg", binding_sha=sha, run_set_sha=hashlib.sha256(rs.read_bytes()).hexdigest(),
                                                           stamp=self.stamp, ledger_path=led, run_set_path=rs,
                                                           sandbox_base=RN.SANDBOX_BASE.as_posix())   # R43-40: S-BASE
        self.args = ["--mode", "live", "--declaration", str(self.decl), "--declaration-sha", self.dsha, "--run-set", str(rs), "--binding", str(b),
                     "--binding-sha", sha]
        self.folder = RN.SANDBOX_BASE / self.stamp
        self.version, self.version_calls = H.TEST_CLI_VERSION, 0
        import os
        os.environ[DG.TOKEN_ENV] = H.TEST_TOKEN
        patch.set(MI, "cli_version", self._version)
        patch.set(RN, "execute", self._no_lanes)
        self.authorize(list(nonces), multi)

    def _version(self, cli, **k):
        self.version_calls += 1
        if isinstance(self.version, Exception):
            raise self.version
        return self.version

    @staticmethod
    def _no_lanes(*a, **k):
        raise RuntimeError("live-shaped demo: stopped before any lane (no lane, no provider, no request)")

    def authorize(self, nonces, multi=False, named=None, real_loader=False):
        if real_loader:
            return None
        obj = {"authorized_by": "owner", "declaration_sha256": named or self.dsha, "owner_token_sha256": hashlib.sha256(H.TEST_TOKEN.encode()).hexdigest()}
        obj |= {"invocations_authorized": len(nonces), "nonces": list(nonces)} if multi else {"nonce": nonces[0]}
        sha = hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
        self.p.set(DG, "_load_authorization", lambda path: (obj, sha))
        return sha

    def run(self):
        return call(RN.main, ["run"] + self.args)

    def resume(self):
        return call(RN.main, ["resume"] + self.args)

    def facts(self):
        st = state(self.folder)
        return {"folder_exists": self.folder.exists(), "allowance_exists": (self.folder / "allowance.sqlite").exists(),
                "nonces_consumed": len(consumed(self.folder)), "version_calls": self.version_calls,
                "invocations": [{k: i.get(k) for k in ("n", "kind", "status", "authorization_consumed")} for i in (st or {}).get("invocations", [])]}


# ---- the demonstrations -------------------------------------------------------------------------------------------------------
def demo_completion(work):
    d = Dry(work)
    r = d.run()
    rep = report(d.folder, 1)
    statuses = {lane: sorted({v["status"] for v in docs.values()}) for lane, docs in rep["documents"].items() if docs}
    return {"steps": [r], "facts": d.facts(), "run_state": rep["run_state"], "statuses": statuses, "model_requests": rep["model_requests"],
            "ledger_unchanged": rep["ledger_unchanged"],
            "ok": r["result"] == "finished" and rep["run_state"] == "FINISHED" and all(s == ["COMPLETE"] for s in statuses.values()) and rep["model_requests"] == 0,
            "tests": ["test_runner_r32.py (the dry pipeline on the real reference set)", "test_runner_order_r42.py::test_dry_A_and_T_..."]}


def demo_refusal_before_dispatch(work):
    out, p = {}, Patch()
    try:
        lv = Live(work / "a", p)
        p.set(DG, "_load_authorization", ORIG_LOAD)          # the REAL loader: the pinned file does not exist
        out["no_authorization_file"] = lv.run() | {"facts": lv.facts()}
        lv.authorize(["nonce-demo-0123456789-b"], named="e" * 64)
        out["authorization_names_another_hash"] = lv.run() | {"facts": lv.facts()}
        lv.authorize(["nonce-demo-0123456789-c"], named="f38fb281f30b4ca45fea1c801d58f37d83ffdaa2b61cd406d9a087e8e51725af")
        out["authorization_names_the_frozen_v2_hash"] = lv.run() | {"facts": lv.facts()}
        lv.authorize(["nonce-demo-0123456789-e"], named=C.V3_RUN_SHA)      # R43-40: the executed v3 RUN hash
        out["authorization_names_the_executed_v3_run_hash"] = lv.run() | {"facts": lv.facts()}
        lv.authorize(["nonce-demo-0123456789-d"])
        import os
        tok = os.environ.pop(DG.TOKEN_ENV)
        out["token_not_presented"] = lv.run() | {"facts": lv.facts()}
        os.environ[DG.TOKEN_ENV] = tok
        rec = dict(lv.rec)
        rec["authorization"] = dict(rec["authorization"], owner_token_sha256="TO-BE-NAMED-BY-OWNER-BUDGET-AUTHORIZATION")
        frozen = work / "a" / "pkg" / "FROZEN-AS-WRITTEN.json"
        frozen.write_text(json.dumps(rec, indent=1, sort_keys=True), encoding="utf-8", newline="\n")
        args = list(lv.args)
        args[args.index("--declaration") + 1] = str(frozen)
        args[args.index("--declaration-sha") + 1] = hashlib.sha256(frozen.read_bytes()).hexdigest()
        out["the_declaration_as_written_with_the_placeholder"] = call(RN.main, ["run"] + args) | {"facts": lv.facts()}
    finally:
        p.undo()
        import os
        os.environ.pop(DG.TOKEN_ENV, None)
    ok = all(v["result"] == "refused" and not v["facts"]["folder_exists"] and v["facts"]["nonces_consumed"] == 0 and v["facts"]["version_calls"] == 0
             for v in out.values())
    return {"cases": out, "ok": ok, "tests": ["test_dispatch_guard_r32.py", "test_resume_authorization_r42.py::test_a_file_naming_the_frozen_hash_is_refused_in_both_forms",
                                               "test_runner_r32.py::test_live_mode_* (refusals before any folder)"]}


def demo_interruption_and_deadends(work):
    """Every phase: interrupted, then recovered without re-sending a charged request; the dead-end cases T, A, B, C, D, E."""
    rows, p = {}, Patch()

    def finish(name, d, first, recover, cmd):
        rec = {"first": first, "facts_after_failure": d.facts(), "recovery_command": cmd, "recovery": recover, "facts_final": d.facts()}
        st = state(d.folder) or {}
        last = (st.get("invocations") or [{}])[-1]
        s = rec["facts_final"]["store"] or {}
        rec["ok"] = recover["result"] == "finished" and last.get("run_state") == "FINISHED" and s.get("duplicate_bound_keys", 1) == 0
        rows[name] = rec

    # A / T: the version refused or timed out -> nothing created
    for name, why in (("A_version_mismatch", "refused: CLI version '2.1.264 (Claude Code)' differs from the declared '2.1.263 (Claude Code)'"),
                      ("T_version_timeout", "refused: `claude --version` failed: timed out after 60 s")):
        d = Dry(work / name)

        def boom(*a, why=why, **k):
            raise MI.IdentityRefused(why)
        p.set(MI, "check_version", boom)
        first = d.run()
        p.undo()
        nothing = not d.folder.exists()
        finish(name, d, first | {"nothing_created": nothing}, d.run(), "run")
        rows[name]["ok"] = rows[name]["ok"] and nothing
    # B: disk full while recording the identity -> re-entry
    d = Dry(work / "B")
    p.set(MI, "record_invocation", lambda *a, **k: (_ for _ in ()).throw(OSError(28, "No space left on device")))
    first = d.run()
    p.undo()
    finish("B_disk_full_at_identity_record", d, first, d.run(), "run (re-entry)")
    # C: interruption at the allowance creation -> re-entry
    d = Dry(work / "C")
    real = RN.create_allowance_atomic

    def ctrl_c(cfg, folder):
        (folder / "allowance.sqlite.new").write_bytes(b"partial")
        raise KeyboardInterrupt
    p.set(RN, "create_allowance_atomic", ctrl_c)
    first = d.run()
    p.undo()
    assert RN.create_allowance_atomic is real
    finish("C_interrupted_at_allowance_creation", d, first, d.run(), "run (re-entry)")
    # D: after the allowance and the capture store, before any lane -> resume
    d = Dry(work / "D")
    p.set(RN, "execute", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("injected failure after the allowance")))
    first = d.run()
    p.undo()
    second_run = d.run()
    finish("D_failure_after_the_allowance", d, first | {"second_run": second_run}, d.resume(), "resume")
    rows["D_failure_after_the_allowance"]["ok"] = rows["D_failure_after_the_allowance"]["ok"] and second_run["result"] == "refused"
    # E: a lane dies after a response came back (B, C, R) -> resume serves it interrupted_charged, never re-sends it
    for lane in ("B", "C", "R"):
        d = Dry(work / f"E{lane}")
        first = d.run("--dry-fault", f"{lane}:1")
        finish(f"E_lane_{lane}_crash_after_a_response", d, first, d.resume(), "resume")
        s = rows[f"E_lane_{lane}_crash_after_a_response"]["facts_final"]["store"]
        rows[f"E_lane_{lane}_crash_after_a_response"]["served_interrupted_charged"] = [x for x in s["serves"] if x["mode"] == "same_bound_fingerprint"]
    # live-shaped: the authorization is consumed only after the allowance exists
    live = {}
    pl = Patch()
    try:
        lv = Live(work / "LB", pl)
        pr = Patch()
        pr.set(MI, "record_invocation", lambda *a, **k: (_ for _ in ()).throw(OSError(28, "No space left on device")))
        live["B_identity_record_disk_full"] = lv.run() | {"facts": lv.facts()}
        pr.undo()
        pc = Patch()
        pc.set(RN, "create_allowance_atomic", lambda cfg, folder: (_ for _ in ()).throw(KeyboardInterrupt()))
        live["C_interrupted_at_allowance"] = lv.run() | {"facts": lv.facts()}
        pc.undo()
        live["re_entry_with_the_same_authorization"] = lv.run() | {"facts": lv.facts()}
    finally:
        pl.undo()
    pl2 = Patch()
    try:
        lv2 = Live(work / "LD", pl2)
        orig_auth = DG.authorize

        def consume_fails(*a, **k):
            if k.get("action") == "consume":
                raise OSError(28, "No space left on device (consumption record)")
            return orig_auth(*a, **k)
        pa = Patch()
        pa.set(DG, "authorize", consume_fails)
        live["D_consumption_fails_after_the_allowance"] = lv2.run() | {"facts": lv2.facts()}
        pa.undo()
        live["D_run_again_refused"] = lv2.run() | {"facts": lv2.facts()}
        live["D_resume_with_the_same_unconsumed_authorization"] = lv2.resume() | {"facts": lv2.facts()}
        live["E_resume_with_the_consumed_nonce"] = lv2.resume() | {"facts": lv2.facts()}
        lv2.authorize(["nonce-demo-fresh-second-01"])
        lv2.version = "2.1.300 (Claude Code)"
        live["E_resume_cli_updated"] = lv2.resume() | {"facts": lv2.facts()}
        lv2.version = H.TEST_CLI_VERSION
        pd = Patch()
        pd.set(PF.shutil, "disk_usage", lambda q: Disk(10 ** 12, 10 ** 12 - 1, 4096))
        live["E_resume_disk_below_floor"] = lv2.resume() | {"facts": lv2.facts()}
        pd.undo()
        live["E_resume_fresh_nonce"] = lv2.resume() | {"facts": lv2.facts()}
    finally:
        pl2.undo()
        import os
        os.environ.pop(DG.TOKEN_ENV, None)
    lok = (live["B_identity_record_disk_full"]["facts"]["nonces_consumed"] == 0 and live["C_interrupted_at_allowance"]["facts"]["nonces_consumed"] == 0
           and live["re_entry_with_the_same_authorization"]["facts"]["nonces_consumed"] == 1
           and live["D_consumption_fails_after_the_allowance"]["facts"]["nonces_consumed"] == 0 and live["D_run_again_refused"]["result"] == "refused"
           and live["D_resume_with_the_same_unconsumed_authorization"]["facts"]["nonces_consumed"] == 1
           and live["E_resume_with_the_consumed_nonce"]["result"] == "refused" and live["E_resume_cli_updated"]["result"] == "refused"
           and live["E_resume_disk_below_floor"]["result"] == "refused" and live["E_resume_fresh_nonce"]["facts"]["nonces_consumed"] == 2)
    summary = {k: {"first": v["first"]["result"], "recovered_by": v["recovery_command"], "final": (v["facts_final"]["invocations"] or [{}])[-1].get("run_state"),
                   "ok": v["ok"]} for k, v in rows.items()}
    summary["live_shaped"] = {k: {"result": v["result"], "nonces_consumed": v["facts"]["nonces_consumed"], "allowance": v["facts"]["allowance_exists"]}
                              for k, v in live.items()}
    summary["ok"] = all(v["ok"] for v in rows.values()) and lok
    return {"dry": rows, "live_shaped": live, "summary": summary, "ok": summary["ok"],
            "tests": ["test_runner_order_r42.py (15 tests)", "test_runner_r32.py::test_* two-invocation drills"]}


def scenario(work, name):
    res = V.run_scenario(name, work / name)
    folder = pathlib.Path(res["run_folder"])
    st = state(folder)
    audits = {}
    for inv in st["invocations"]:
        a = folder / f"inv-{inv['n']}" / "out" / "ALLOWANCE-AUDIT.json"
        if a.is_file():
            x = json.loads(a.read_text(encoding="utf-8"))
            audits[inv["n"]] = {"total_charged": x["total_charged"], "charges_by_lane_outcome": sorted({(c["lane"], c["outcome"]) for c in x["charges"]}),
                                "stops": x["stops"], "lanes": {k: v.get("charged") for k, v in (x.get("lanes") or {}).items()}}
    return res, folder, st, audits


def demo_durable_charging(work):
    out = {}
    for name in ("provider_timeout", "interrupted", "unsaved"):
        res, folder, st, audits = scenario(work, name)
        ns = sorted(audits)
        never_decreases = all(audits[ns[i]]["total_charged"] <= audits[ns[i + 1]]["total_charged"] for i in range(len(ns) - 1))
        out[name] = {"steps": res["steps"], "invocations": [(i["n"], i["status"]) for i in st["invocations"]], "audits": audits,
                     "charges_never_decrease": never_decreases, "duplicates_in_capture": V.capture_duplicates(folder)}
    to = out["provider_timeout"]["audits"]
    ok = all(v["charges_never_decrease"] and v["duplicates_in_capture"] == 0 for v in out.values()) and \
        any(o == "timeout" for _lane, o in to[min(to)]["charges_by_lane_outcome"])
    return {"scenarios": out, "ok": ok, "tests": ["test_visibility_r38.py::test_provider_timeouts_are_visible_per_page_and_the_terminal_stop_survives_the_resume",
                                                  "test_visibility_r38.py::test_an_interrupted_or_unsaved_dispatch_stays_charged_and_is_visible_on_the_resume",
                                                  "test_allowance_r32.py::test_charges_are_never_refunded_whatever_the_outcome"]}


def demo_terminal_stop(work):
    out = {}
    for name in ("provider_timeout", "lane_allowance"):
        res, folder, st, audits = scenario(work, name)
        ns = sorted(audits)
        stops = [audits[n]["stops"] for n in ns]
        out[name] = {"steps": res["steps"], "stops_per_invocation": stops, "stop_preserved": len(stops) >= 2 and all(s == stops[0] for s in stops) and bool(stops[0])}
    return {"scenarios": out, "ok": all(v["stop_preserved"] for v in out.values()),
            "tests": ["test_visibility_r38.py::test_lane_allowance_refusal_is_visible_everywhere_and_the_resume_keeps_the_stop",
                      "test_allowance_r32.py::test_refusals_and_terminal_stops_are_durable_and_a_resume_never_resets_them"]}


def demo_window_deferral(work):
    res, folder, st, audits = scenario(work, "retry_policy_full")
    invs = st["invocations"]
    early = [s for s in res["steps"] if s.get("early") or s.get("between_earliest_and_full")]
    deferred = [i for i in invs if i.get("run_state") == "DEFERRED"]
    ok = bool(deferred) and invs[-1].get("run_state") == "FINISHED" and all(s["result"] == "refused" for s in early) and \
        all(i.get("resume_policy") == "full" for i in deferred)
    return {"steps": res["steps"], "invocations": [{k: i.get(k) for k in ("n", "kind", "status", "run_state", "resume_policy", "earliest_retry_utc",
                                                                          "retry_at_full_utc", "resume_not_before_utc")} for i in invs],
            "ok": ok, "tests": ["test_visibility_r38.py::test_the_full_resume_policy_records_both_times_and_refuses_an_early_resume",
                                "test_visibility_r38.py::test_project_window_deferral_resumes_after_the_window_frees_and_never_resends",
                                "declaration-r32-v3 dry-run deferral loops (EP-27331, 2 and 3 invocations)"]}


def page_rows(folder, n, lane):
    out = folder / f"inv-{n}" / "out"
    rep = json.loads((out / "RUN-REPORT.json").read_text(encoding="utf-8"))
    rows = json.loads((out / f"rows-{lane}.json").read_text(encoding="utf-8")) if (out / f"rows-{lane}.json").is_file() else {}
    T = json.loads((folder / "SYNTHETIC-TRUTH.json").read_text(encoding="utf-8")) if (folder / "SYNTHETIC-TRUTH.json").is_file() else truth()
    acc = {}
    for pid, doc in rep["documents"][lane].items():
        n_pages = int(T["documents"][pid].get("in_scope_pages") or 0)
        key = T["documents"][pid]["doc_key"]
        att = (((rows.get(key) or {}).get("extracted") or {}).get("ai_evidence") or {}).get("attempts") or []
        pages_att = (att[-1].get("pages") if att else {}) or {}
        items = pages_att.items() if isinstance(pages_att, dict) else [(str(e.get("page")), e) for e in pages_att]
        outcome = {str(k): str((v or {}).get("outcome") or "") for k, v in items}
        unread = {p for p, v in (doc.get("unread_pages") or {}).items() if not all(x.get("partial") for x in v)}
        refused = {p for p, kinds in (doc.get("pages") or {}).items() if p != "*" and any(RS.kind_class(k) in ("limit", "failure") for k in kinds)}
        if "*" in (doc.get("pages") or {}) and any(RS.kind_class(k) in ("limit", "failure") for k in doc["pages"]["*"]):
            refused |= {str(i) for i in range(1, n_pages + 1)} - unread
        per = {}
        for i in range(1, n_pages + 1):
            p = str(i)
            per[p] = ("unread_under_limit" if p in unread else "refused" if p in refused else
                      "not_triggered" if outcome.get(p) == "no_trigger" else "read" if outcome.get(p) else "no_attempt_page")
        counts = {k: sum(1 for v in per.values() if v == k) for k in ("read", "unread_under_limit", "refused", "not_triggered", "no_attempt_page")}
        acc[pid] = {"in_scope_pages": n_pages, "status": doc["status"], "pages": per, "counts": counts,
                    "sums_to_pages": sum(counts.values()) == n_pages and counts["no_attempt_page"] == 0}
    return acc


def demo_page_accounting(work):
    out = {}
    for name in ("unread_pages", "application_path"):
        res, folder, st, audits = scenario(work, name)
        out[name] = {"steps": res["steps"], "lane_C": page_rows(folder, 1, "C")}
    ok = all(d["sums_to_pages"] for v in out.values() for d in v["lane_C"].values())
    return {"scenarios": out, "ok": ok, "rule": ("every in-scope page of every document is read, unread under the application's own per-document limits "
                                                 "(listed, the document COMPLETE), refused by a harness limit or failure (the document INCOMPLETE), or "
                                                 "not triggered by the reader's rule; the counts sum to the document's pages"),
            "tests": ["test_visibility_r38.py::test_pages_left_unread_by_the_application_are_listed_and_the_document_stays_complete",
                      "test_visibility_r38.py::test_the_application_path_on_synthetic_documents_records_pages", "test_unread_pages_r39.py (17 tests)"]}


def demo_global_provider(work):
    out = {}
    for lane, calls in (("C", [1]), ("R", [1]), ("P", [0]), ("B", [1])):
        d = Dry(work / f"gp-{lane}", inject={"injections": [{"kind": "global_provider_request", "lane": lane, "calls": calls}]})
        r = d.run()
        rep = report(d.folder, 1)
        lm = json.loads((d.folder / "inv-1" / "out" / f"LANE-{lane}.json").read_text(encoding="utf-8"))
        m = RS.breach_marker(d.folder)
        out[lane] = {"step": r, "run_state": rep["run_state"], "breach": m and {k: m[k] for k in ("kind", "lane", "task")},
                     "global_provider": {k: lm["global_provider"][k] for k in ("lane_kind", "at_start", "at_end", "requests_refused", "drill")},
                     "model_requests": rep["model_requests"], "ledger_unchanged": rep["ledger_unchanged"], "resume": d.resume() if m else None}
    ok = all(out[l]["run_state"] == "INVALID" and out[l]["breach"]["kind"] == "global_provider_request" and out[l]["resume"]["result"] == "refused"
             for l in ("C", "R", "P")) and out["B"]["run_state"] == "FINISHED" and out["B"]["breach"] is None and \
        all(v["model_requests"] == 0 and v["ledger_unchanged"] for v in out.values())
    summary = {l: {"run_state": v["run_state"], "breach": (v["breach"] or {}).get("kind"), "global_provider": v["global_provider"]["at_start"],
                   "drill_answer": (v["global_provider"]["drill"] or [{}])[0].get("error")} for l, v in out.items()}
    return {"lanes": out, "summary": summary, "ok": ok, "tests": ["test_global_provider_r42.py (7 tests)"]}


ORIG_LOAD = DG._load_authorization
_ORIG_AUTHORIZE = DG.authorize
_ORIG_RECORD = MI.record_invocation
_ORIG_CREATE = RN.create_allowance_atomic


def main() -> int:
    if OUT.exists():
        raise SystemExit("refused: the output folder is new for every demonstration run")
    OUT.mkdir(parents=True)
    work = RN.SANDBOX_BASE / f"r43d-demos-{uuid.uuid4().hex[:6]}"
    led0 = PF.ledger_counts(LEDGER)
    res = {"name": "DEMOS (R43-40) of the review43 harness for declaration-r32-v4 (the ORCH-10 section 2.6 demonstrations)", "harness": C.HARNESS43.as_posix(),
           "imported_from": H_DIR.as_posix(), "run_copy": COPY, "dry_base": BASE, "work": work.as_posix(), "ledger_before": led0,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "demos": {}}
    for name, fn in (("completion", demo_completion), ("refusal_before_dispatch", demo_refusal_before_dispatch),
                     ("interruption_and_deadends", demo_interruption_and_deadends), ("durable_charging", demo_durable_charging),
                     ("terminal_stop", demo_terminal_stop), ("window_deferral", demo_window_deferral), ("page_accounting", demo_page_accounting),
                     ("global_provider", demo_global_provider)):
        t0 = time.time()
        try:
            r = fn(work / name)
        except BaseException as exc:  # noqa: BLE001
            r = {"ok": False, "error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc()[-3000:]}
        r["seconds"] = round(time.time() - t0, 1)
        (OUT / f"DEMO-{name}.json").write_text(json.dumps(r, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
        res["demos"][name] = {"ok": r.get("ok"), "seconds": r["seconds"], "tests": r.get("tests"), "error": r.get("error")}
        if name == "interruption_and_deadends":
            res["deadends"] = {"summary": r.get("summary")}
        if name == "global_provider":
            res["global_provider"] = {"summary": r.get("summary")}
        print(name, r.get("ok"), r["seconds"], flush=True)
    res["ledger_after"] = PF.ledger_counts(LEDGER)
    res["ledger_unchanged"] = res["ledger_before"] == res["ledger_after"]
    res["authorization_files_written"] = sorted(p.as_posix() for p in work.rglob(DG.AUTH_NAME))
    res["model_requests"] = 0
    res["ok"] = all(v["ok"] for v in res["demos"].values()) and res["ledger_unchanged"] and not res["authorization_files_written"]
    res["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (OUT / "DEMOS-R42.json").write_text(json.dumps(res, indent=1, sort_keys=True, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: res[k] for k in ("ok", "ledger_unchanged", "authorization_files_written")} | {"demos": {k: v["ok"] for k, v in res["demos"].items()}}))
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
