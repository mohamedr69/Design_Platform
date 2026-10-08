"""ORCH-10 (R42; Verification 41 R41-09, R41-10, R41-11): the invocation order of the corrected runner and the closure of the
invocation-1 dead-end class. Every case of Verification 41's deadends_r41 (T, A, B, C, D, E) is reproduced:
  * dry mode (in process, 2-document run set, reader 'none', the refusing stub): no failure leaves an unusable run --
    a failure before the folder creates nothing; a failure after the folder but before the allowance leaves a folder that
    'run' re-enters (REENTRY-<n>.json proves no allowance, no nonce, no charge); a failure after the allowance is resumed;
  * live-shaped (in process: a temporary contract-5 declaration, a FAKE ledger with the scope, the pinned "CLI" a text
    file that is hashed and never executed, `--version` replaced, the owner's authorization an IN-MEMORY object returned by
    a replaced loader -- no authorization file is ever written -- and the lanes replaced by a raising stub, so no lane and
    no provider ever starts): no failure before the allowance and the capture store exist consumes the authorization;
    a resume re-checks the CLI file, the version line and the free disk BEFORE it consumes its nonce.
The refusals that must stay, stay: a second 'run' with an allowance, a resume without an allowance, WRITER.lock, an
identity mismatch (INVALID, never resumed). This suite runs under the R42 audit guard (no claude process, no network).
Run: python -m pytest -q test_runner_order_r42.py"""
import hashlib
import json
import pathlib
import shutil
import uuid
from collections import namedtuple

import pytest

import allowance_r32 as AL
import dispatch_guard_r32 as DG
import model_identity_r38 as MI
import preflight_r32 as PF
import r32_test_helpers as H
import runner_r32 as RN

IDS = ("F045", "F051")
_T = {}
Disk = namedtuple("Disk", "total used free")
REAL_DISK_USAGE = shutil.disk_usage


def _truth():
    if "t" not in _T:
        _T["t"] = PF.build_truth()
    return _T["t"]


def _binding(tmp_path):
    f = tmp_path / "bound.txt"
    f.write_text("bound", encoding="utf-8", newline="\n")
    p = tmp_path / "BINDING.json"
    p.write_text(json.dumps({"files": {"g": {f.as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()}}}), encoding="utf-8", newline="\n")
    return p, hashlib.sha256(p.read_bytes()).hexdigest()


def _run_set(tmp_path):
    T = _truth()
    p = tmp_path / "RUN-SET.json"
    p.write_text(json.dumps({"documents": [{"pool_id": i, "doc_key": T["documents"][i]["doc_key"], "ep": T["documents"][i]["ep"]} for i in IDS]}),
                 encoding="utf-8", newline="\n")
    return p


def _state(folder):
    return json.loads((folder / RN.RUN_STATE).read_text(encoding="utf-8"))


def _consumed(folder):
    d = folder / DG.CONSUMED_DIR
    return sorted(p.name for p in d.glob("consumed-*.json")) if d.is_dir() else []


# ---- dry -----------------------------------------------------------------------------------------------------------------------
class Dry:
    def __init__(self, tmp_path):
        b, sha = _binding(tmp_path)
        rs = _run_set(tmp_path)
        self.stamp = f"r42d-ord-{uuid.uuid4().hex[:8]}"
        self.args = ["--mode", "dry", "--stamp", self.stamp, "--run-set", str(rs), "--binding", str(b), "--binding-sha", sha]
        self.folder = RN.SANDBOX_BASE / self.stamp

    def run(self, *extra):
        return RN.main(["run"] + self.args + list(extra))

    def resume(self, *extra):
        return RN.main(["resume"] + self.args + list(extra))

    def report(self, n):
        return json.loads((self.folder / f"inv-{n}" / "out" / "RUN-REPORT.json").read_text(encoding="utf-8"))


def test_dry_A_and_T_a_version_refusal_or_a_version_timeout_creates_nothing(tmp_path, monkeypatch):
    d = Dry(tmp_path)
    for why in ("refused: CLI version '2.1.264 (Claude Code)' differs from the declared '2.1.263 (Claude Code)'",
                "refused: `claude --version` failed: Command timed out after 60 seconds"):
        def boom(*a, why=why, **k):
            raise MI.IdentityRefused(why)
        monkeypatch.setattr(MI, "check_version", boom)
        with pytest.raises(RN.Refused, match="nothing was created and no authorization was consumed"):
            d.run()
        assert not d.folder.exists()
    monkeypatch.undo()
    assert d.run() == 0 and _state(d.folder)["invocations"][-1]["run_state"] == "FINISHED"


def test_dry_the_disk_floor_refuses_before_any_folder_and_a_resume_before_it_reopens(tmp_path, monkeypatch):
    d = Dry(tmp_path)
    monkeypatch.setattr(PF.shutil, "disk_usage", lambda p: Disk(10 ** 12, 10 ** 12 - 100, 2 * 1024 ** 3 - 1))
    with pytest.raises(RN.Refused, match="below the declared floor"):
        d.run()
    assert not d.folder.exists()
    monkeypatch.undo()
    with pytest.raises(RuntimeError, match="lane C failed"):
        d.run("--dry-fault", "C:1")
    st = _state(d.folder)
    before = (len(st["invocations"]), sorted(p.name for p in d.folder.iterdir()))
    monkeypatch.setattr(PF.shutil, "disk_usage", lambda p: Disk(10 ** 12, 10 ** 12 - 100, 100))
    with pytest.raises(RN.Refused, match="below the declared floor"):
        d.resume()
    assert (len(_state(d.folder)["invocations"]), sorted(p.name for p in d.folder.iterdir())) == before, "nothing re-opened or created"


def test_dry_B_a_full_disk_while_recording_the_identity_leaves_a_folder_that_run_re_enters(tmp_path, monkeypatch):
    d = Dry(tmp_path)

    def full(*a, **k):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(MI, "record_invocation", full)
    with pytest.raises(OSError):
        d.run()
    assert d.folder.exists() and not (d.folder / "allowance.sqlite").exists() and _consumed(d.folder) == []
    with pytest.raises(RN.Refused, match="no allowance was ever created, so 'run' re-enters"):
        d.resume()
    monkeypatch.undo()
    assert d.run() == 0
    st = _state(d.folder)
    assert [i["kind"] for i in st["invocations"]] == ["fresh", "reentry"] and st["invocations"][0]["status"] == "interrupted"
    proof = json.loads((d.folder / "REENTRY-2.json").read_text(encoding="utf-8"))
    assert proof["allowance_created"] is False and proof["nonces_consumed"] == 0 and proof["requests_charged"] == 0
    assert d.report(2)["run_state"] == "FINISHED" and d.report(2)["kind"] == "reentry"


def test_dry_C_an_interruption_at_the_allowance_creation_leaves_no_allowance_and_run_re_enters(tmp_path, monkeypatch):
    d = Dry(tmp_path)
    real = RN.create_allowance_atomic

    def ctrl_c(cfg, folder):
        (folder / "allowance.sqlite.new").write_bytes(b"partial sqlite file of an interrupted creation")
        raise KeyboardInterrupt
    monkeypatch.setattr(RN, "create_allowance_atomic", ctrl_c)
    with pytest.raises(KeyboardInterrupt):
        d.run()
    assert not (d.folder / "allowance.sqlite").exists() and (d.folder / "allowance.sqlite.new").exists()
    assert AL.bound_key(d.folder / "capture.sqlite") is not None, "the capture store was bound first (before the allowance)"
    monkeypatch.setattr(RN, "create_allowance_atomic", real)
    assert d.run() == 0
    rep = d.report(2)
    assert rep["allowance_creation"]["partial_kept_as"].startswith("allowance.partial-") and rep["run_state"] == "FINISHED"
    assert (d.folder / rep["allowance_creation"]["partial_kept_as"]).read_bytes().startswith(b"partial"), "kept aside, never used"


def test_dry_D_a_failure_after_the_allowance_is_resumed_never_re_run(tmp_path, monkeypatch):
    d = Dry(tmp_path)

    def boom(*a, **k):
        raise RuntimeError("injected failure after the allowance and the capture store exist")
    monkeypatch.setattr(RN, "execute", boom)
    with pytest.raises(RuntimeError):
        d.run()
    assert (d.folder / "allowance.sqlite").exists() and (d.folder / "capture.sqlite").exists()
    monkeypatch.undo()
    with pytest.raises(RN.Refused, match="holds the run's allowance\\); use 'resume'"):
        d.run()
    bound_at = AL.LaneAllowance(d.folder / "allowance.sqlite", run_key=_state(d.folder)["run_key"], create=False).bound_at
    assert d.resume() == 0 and d.report(2)["run_state"] == "FINISHED"
    assert AL.LaneAllowance(d.folder / "allowance.sqlite", run_key=_state(d.folder)["run_key"], create=False).bound_at == bound_at, \
        "the allowance was never reset or re-created"


def test_dry_E_a_lane_crash_after_a_response_is_resumed_and_nothing_charged_is_re_sent(tmp_path):
    d = Dry(tmp_path)
    with pytest.raises(RuntimeError, match="lane C failed"):
        d.run("--dry-fault", "C:1")
    assert d.resume() == 0
    rep = d.report(2)
    assert rep["run_state"] == "FINISHED" and rep["store"]["reserved_without_answer"] == 1
    assert any(s["mode"] == "same_bound_fingerprint" for s in rep["store"]["serves_by_lane_mode"] if s["lane"] == "C")


def test_dry_the_refusals_that_must_stay_still_refuse(tmp_path, monkeypatch):
    d = Dry(tmp_path)
    with pytest.raises(RN.Refused, match="nothing to resume"):
        d.resume()
    assert d.run() == 0
    with pytest.raises(RN.Refused, match="use 'resume'"):
        d.run()
    with pytest.raises(RN.Refused, match="the run is complete"):
        d.resume()
    (d.folder / "WRITER.lock").write_text("123", encoding="utf-8")
    (tmp_path / "w").mkdir()
    d2 = Dry(tmp_path / "w")
    d2.folder.mkdir(parents=True)
    (d2.folder / "WRITER.lock").write_text("123", encoding="utf-8")
    with pytest.raises(RN.Refused, match="WRITER.lock"):
        d2.run()
    (d2.folder / "WRITER.lock").unlink()
    (d.folder / "WRITER.lock").unlink()
    (d.folder / MI.MARKER).write_text(json.dumps({"lane": "C"}), encoding="utf-8")
    with pytest.raises(RN.Refused, match="never resumed"):
        d.resume()


def test_dry_run_never_re_enters_a_folder_with_a_consumed_nonce_or_charged_requests(tmp_path):
    d = Dry(tmp_path)
    d.folder.mkdir(parents=True)
    (d.folder / DG.CONSUMED_DIR).mkdir()
    (d.folder / DG.CONSUMED_DIR / "consumed-0123.json").write_text("{}", encoding="utf-8")
    with pytest.raises(RN.Refused, match="nonce was consumed in this run folder"):
        d.run()
    shutil.rmtree(d.folder / DG.CONSUMED_DIR)
    AL.bind_store(d.folder / "capture.sqlite", "another-run-key")
    with pytest.raises(RN.Refused, match="bound to another run"):
        d.run()


# ---- live-shaped (in process; NO authorization file; NO lane; NO CLI process) ------------------------------------------------
class Live:
    """A temporary contract-5 declaration, a fake ledger with the scope, the owner's authorization as an in-memory object."""

    def __init__(self, tmp_path, monkeypatch, nonces=("nonce-0123456789abcdef-1",), multi=False):
        self.mp = monkeypatch
        b, sha = _binding(tmp_path)
        rs = _run_set(tmp_path)
        led = H.fake_ledger(tmp_path / "fake-ledger.sqlite", {H.TEST_SCOPE: (H.TEST_LIMITS, None, 0)})
        self.stamp = f"r42d-live-{uuid.uuid4().hex[:8]}"
        self.decl, self.dsha, self.rec = H.live_declaration(tmp_path / "pkg", binding_sha=sha, run_set_sha=hashlib.sha256(rs.read_bytes()).hexdigest(),
                                                           stamp=self.stamp, ledger_path=led, run_set_path=rs)
        self.args = ["--mode", "live", "--declaration", str(self.decl), "--declaration-sha", self.dsha, "--run-set", str(rs), "--binding", str(b),
                     "--binding-sha", sha]
        self.folder = RN.SANDBOX_BASE / self.stamp
        self.version = H.TEST_CLI_VERSION
        self.version_calls = 0
        monkeypatch.setenv(DG.TOKEN_ENV, H.TEST_TOKEN)
        monkeypatch.setattr(MI, "cli_version", self._version)                  # no process is ever started
        monkeypatch.setattr(RN, "execute", self._no_lanes)                        # no lane, no provider: stop right after step 4
        self.authorize(nonces, multi)

    def _version(self, cli, **k):
        self.version_calls += 1
        if isinstance(self.version, Exception):
            raise self.version
        return self.version

    @staticmethod
    def _no_lanes(*a, **k):
        raise RuntimeError("live-shaped drill: stopped before any lane (no lane, no provider, no request)")

    def authorize(self, nonces, multi=False):
        obj = {"authorized_by": "owner", "declaration_sha256": self.dsha, "owner_token_sha256": hashlib.sha256(H.TEST_TOKEN.encode()).hexdigest()}
        obj |= {"invocations_authorized": len(nonces), "nonces": list(nonces)} if multi else {"nonce": nonces[0]}
        sha = hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()
        self.mp.setattr(DG, "_load_authorization", lambda path: (obj, sha))
        return sha

    def run(self):
        return RN.main(["run"] + self.args)

    def resume(self):
        return RN.main(["resume"] + self.args)


def test_live_no_authorization_file_exists_anywhere_in_this_suite(tmp_path):
    assert not list(pathlib.Path(tmp_path).rglob(DG.AUTH_NAME))


def test_live_T_A_and_the_disk_floor_refuse_before_any_folder_and_consume_nothing(tmp_path, monkeypatch):
    lv = Live(tmp_path, monkeypatch)
    for v, match in ((MI.IdentityRefused("refused: `C:/x --version` failed: timed out after 60 s"), "failed: timed out"),
                     ("2.1.264 (Claude Code)", "differs from the declared")):
        lv.version = v
        with pytest.raises(RN.Refused, match=match):
            lv.run()
        assert not lv.folder.exists()
    lv.version = H.TEST_CLI_VERSION
    monkeypatch.setattr(PF.shutil, "disk_usage", lambda p: Disk(10 ** 12, 10 ** 12 - 1, 1024))
    calls = lv.version_calls
    with pytest.raises(RN.Refused, match="below the declared floor"):
        lv.run()
    assert not lv.folder.exists() and lv.version_calls == calls, "the disk refusal comes before `--version`"


def test_live_the_cli_file_hash_is_checked_before_anything(tmp_path, monkeypatch):
    lv = Live(tmp_path, monkeypatch)
    pathlib.Path(lv.rec["model_identity"]["cli"]["path"]).write_bytes(b"another binary")
    with pytest.raises(RN.Refused, match="hashes to"):
        lv.run()
    assert not lv.folder.exists() and lv.version_calls == 0


def test_live_B_and_C_failures_before_the_allowance_consume_nothing_and_run_re_enters(tmp_path, monkeypatch):
    lv = Live(tmp_path, monkeypatch)
    real_record = MI.record_invocation

    def full(*a, **k):
        raise OSError(28, "No space left on device")
    monkeypatch.setattr(MI, "record_invocation", full)
    with pytest.raises(OSError):
        lv.run()
    assert lv.folder.exists() and _consumed(lv.folder) == [], "case B: no authorization consumed"
    monkeypatch.setattr(MI, "record_invocation", real_record)
    real = RN.create_allowance_atomic

    def ctrl_c(cfg, folder):
        raise KeyboardInterrupt
    monkeypatch.setattr(RN, "create_allowance_atomic", ctrl_c)
    with pytest.raises(KeyboardInterrupt):
        lv.run()
    assert _consumed(lv.folder) == [] and not (lv.folder / "allowance.sqlite").exists(), "case C: no authorization consumed, no allowance"
    monkeypatch.setattr(RN, "create_allowance_atomic", real)
    with pytest.raises(RuntimeError, match="stopped before any lane"):
        lv.run()                                                               # the same authorization serves the re-entry
    st = _state(lv.folder)
    assert [i["kind"] for i in st["invocations"]] == ["fresh", "reentry", "reentry"]
    assert len(_consumed(lv.folder)) == 1 and st["invocations"][-1]["authorization_consumed"] is True
    rec = json.loads(next((lv.folder / DG.CONSUMED_DIR).glob("consumed-*.json")).read_text(encoding="utf-8"))
    assert rec["invocation"] == 3 and rec["kind"] == "reentry"


def test_live_D_a_failed_consumption_after_the_allowance_is_resumed_with_the_same_authorization(tmp_path, monkeypatch):
    lv = Live(tmp_path, monkeypatch)
    real = DG.authorize

    def consume_fails(*a, **k):
        if k.get("action") == "consume":
            raise OSError(28, "No space left on device (writing the consumption record)")
        return real(*a, **k)
    monkeypatch.setattr(DG, "authorize", consume_fails)
    with pytest.raises(OSError):
        lv.run()
    assert (lv.folder / "allowance.sqlite").exists() and _consumed(lv.folder) == []
    monkeypatch.setattr(DG, "authorize", real)
    with pytest.raises(RN.Refused, match="use 'resume'"):
        lv.run()
    with pytest.raises(RuntimeError, match="stopped before any lane"):
        lv.resume()
    assert len(_consumed(lv.folder)) == 1, "the unconsumed authorization served the resume"


def test_live_E_after_consumption_a_resume_needs_a_fresh_nonce_and_rechecks_cli_and_disk_first(tmp_path, monkeypatch):
    lv = Live(tmp_path, monkeypatch)
    with pytest.raises(RuntimeError, match="stopped before any lane"):
        lv.run()
    assert len(_consumed(lv.folder)) == 1
    with pytest.raises(RN.Refused, match="already consumed"):
        lv.resume()
    lv.authorize(["nonce-fresh-for-invocation-2-xyz"])
    n_inv = len(_state(lv.folder)["invocations"])
    lv.version = "2.1.300 (Claude Code)"                                       # R41-11: the CLI was updated between invocations
    with pytest.raises(RN.Refused, match="differs from the declared"):
        lv.resume()
    lv.version = H.TEST_CLI_VERSION
    monkeypatch.setattr(PF.shutil, "disk_usage", lambda p: Disk(10 ** 12, 10 ** 12 - 1, 4096))
    with pytest.raises(RN.Refused, match="below the declared floor"):
        lv.resume()
    monkeypatch.setattr(PF.shutil, "disk_usage", REAL_DISK_USAGE)
    cli = pathlib.Path(lv.rec["model_identity"]["cli"]["path"])
    cli.write_bytes(b"updated binary")
    with pytest.raises(RN.Refused, match="hashes to"):
        lv.resume()
    assert len(_consumed(lv.folder)) == 1 and len(_state(lv.folder)["invocations"]) == n_inv, "no refused resume consumed or created anything"
    cli.write_bytes(H.FAKE_CLI_BYTES)
    with pytest.raises(RuntimeError, match="stopped before any lane"):
        lv.resume()
    assert len(_consumed(lv.folder)) == 2


def test_live_one_approval_for_all_planned_resumptions(tmp_path, monkeypatch):
    lv = Live(tmp_path, monkeypatch, nonces=("nonce-planned-0001-aaaa", "nonce-planned-0002-bbbb", "nonce-planned-0003-cccc"), multi=True)
    with pytest.raises(RuntimeError, match="stopped before any lane"):
        lv.run()
    for _ in range(2):
        with pytest.raises(RuntimeError, match="stopped before any lane"):
            lv.resume()
    recs = [json.loads(p.read_text(encoding="utf-8")) for p in sorted((lv.folder / DG.CONSUMED_DIR).glob("consumed-*.json"))]
    assert sorted((r["invocation"], r["nonce_index"]) for r in recs) == [(1, 1), (2, 2), (3, 3)]
    with pytest.raises(RN.Refused, match="needs a NEW authorization file"):
        lv.resume()
    assert AL.LaneAllowance(lv.folder / "allowance.sqlite", run_key=lv.dsha, create=False).caps_fixed() == {"B": 240, "C": 240, "R": 40, "P": 36}
