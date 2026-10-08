"""ORCH-10 (R42; A-11) portability and contract 5: the merged-installation bindings, the bound interpreter, extended-length
opens, the CLI pinned by absolute path + sha256 + version line, the free-disk floor (configurable only upward), the
isolation from the merged installation, and every new contract-5 key refused when missing or different. Temporary
declarations and fake files under pytest's tmp_path only; nothing is executed; no model request.
Run: python -m pytest -q test_portability_r42.py"""
import copy
import hashlib
import json
import os
import pathlib
import sys
import types

import pytest

import inputs_r32 as I
import model_identity_r38 as MI
import preflight_r32 as PF
import r32_test_helpers as H
import runner_r32 as RN
import sandbox_ingest_r32 as SI

MERGED_PILOT = "G:/dev (2)/dev/ep-platform-merged/ep-platform/docs/milestones/M2/real-project-pilot"
MERGED_PY = "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe"
HERE = pathlib.Path(__file__).resolve().parent


def _decl(tmp_path, **over):
    p, sha, rec = H.live_declaration(tmp_path / "pkg", binding_sha="b" * 64, run_set_sha="c" * 64, stamp="r42-contract-test",
                                     ledger_path=tmp_path / "fake-ledger.sqlite", **over)
    return p, sha, rec


# ---- 2.1.1 the bindings and the interpreter ---------------------------------------------------------------------------------
def test_the_inputs_and_the_interpreter_name_the_merged_installation():
    assert I.PILOT.as_posix() == MERGED_PILOT and SI.PY == MERGED_PY and PF.INTERPRETER_PATH == MERGED_PY and RN.PY == MERGED_PY
    assert os.path.normcase(sys.executable) == os.path.normcase(os.path.abspath(MERGED_PY)), "the tests run under the bound interpreter"
    for name, (path, want) in I.INPUTS.items():
        assert pathlib.Path(path).exists(), name
        if want:
            assert I.sha256_file(path) == want, f"{name}: the merged copy is byte-identical"


def test_no_module_of_the_harness_names_the_absent_desktop_installation_in_code():
    """Only docstrings / comments may mention it (as history); no string constant or path in code does."""
    import ast

    hits = []
    for f in sorted(p for p in HERE.glob("*.py") if not p.name.startswith("test_")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        docs = {id(n.body[0].value) for n in ast.walk(tree) if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))
                and n.body and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
        for n in ast.walk(tree):
            if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs and "Desktop/dev/dev" in n.value:
                hits.append(f"{f.name}:{n.lineno}")
    assert hits == []


def test_verify_interpreter_accepts_the_bound_one_and_refuses_any_other(tmp_path):
    b = H.interpreter_binding()
    assert PF.verify_interpreter(b)["verified"]
    with pytest.raises(PF.Refused, match="this process runs"):
        PF.verify_interpreter(b, executable="C:/Python312/python.exe")
    with pytest.raises(PF.Refused, match="hashes to"):
        PF.verify_interpreter(dict(b, sha256="0" * 64))
    with pytest.raises(PF.Refused, match="version is"):
        PF.verify_interpreter(dict(b, version="3.12.9"))
    with pytest.raises(PF.Refused, match="must be the bound"):
        PF.validate_interpreter(dict(b, path="C:/Users/moham/Desktop/dev/dev/ep-platform/backend/venv/Scripts/python.exe"))


# ---- 2.1.3 path lengths -----------------------------------------------------------------------------------------------------
def test_hashing_and_the_binding_check_open_long_paths_through_the_extended_prefix(tmp_path):
    deep = tmp_path
    while len(deep.as_posix()) < 270:
        deep = deep / ("d" * 40)
    os.makedirs(I.long_path(deep), exist_ok=True)
    f = deep / "bound-file-beyond-260.txt"
    assert len(f.as_posix()) >= 260
    with open(I.long_path(f), "wb") as fh:
        fh.write(b"bound")
    assert I.sha256_file(f) == hashlib.sha256(b"bound").hexdigest()
    man = tmp_path / "BINDING.json"
    man.write_text(json.dumps({"files": {"g": {f.as_posix(): hashlib.sha256(b"bound").hexdigest()}}}), encoding="utf-8", newline="\n")
    assert PF.verify_binding(man, hashlib.sha256(man.read_bytes()).hexdigest())["files_verified"] == 1


# ---- 2.1.4 the CLI pinned by absolute path, sha256 and version line -------------------------------------------------------------
def test_the_declaration_pins_the_cli_file_and_the_preflight_hashes_it(tmp_path):
    p, sha, rec = _decl(tmp_path)
    v = PF.validate_declaration(dict(rec, authorization=dict(rec["authorization"])), p)
    pins = v["model_identity"]
    assert pins["cli_sha256"] == hashlib.sha256(H.FAKE_CLI_BYTES).hexdigest() and pins["cli_version"] == H.TEST_CLI_VERSION
    assert PF.verify_cli(pins)["executed"] is False
    (pathlib.Path(pins["cli_path"])).write_bytes(H.FAKE_CLI_BYTES + b"changed")
    with pytest.raises(PF.Refused, match="hashes to"):
        PF.verify_cli(pins)


@pytest.mark.parametrize("cli,match", [({"path": "claude"}, "must equal AI_CLAUDE_CLI"), ({"sha256": None}, "cli.sha256 must pin"),
                                       ({"version": None}, "never null")])
def test_a_cli_pinned_by_name_or_without_hash_or_version_is_refused(tmp_path, cli, match):
    p, sha, rec = _decl(tmp_path)
    rec = copy.deepcopy(rec)
    rec["model_identity"]["cli"] |= cli
    with pytest.raises(PF.Refused, match=match):
        PF.validate_declaration(rec, p)


# ---- 2.3 / C1 the free-disk floor ---------------------------------------------------------------------------------------------
def test_the_disk_floor_is_2_gib_on_the_sandbox_drive_and_only_upward(tmp_path):
    p, sha, rec = _decl(tmp_path)
    assert PF.validate_declaration(rec, p)["disk_precondition"] == {"path": "C:/", "min_free_bytes": 2 * 1024 ** 3}
    for bad, match in (({"path": "C:/", "min_free_bytes": 2 * 1024 ** 3 - 1}, "configurable only upward"),
                       ({"path": "G:/", "min_free_bytes": 2 * 1024 ** 3}, "drive of the sandbox base"),
                       ({"path": "C:/", "min_free_bytes": "2147483648"}, "integer"),
                       ({"path": "C:/", "min_free_bytes": 2 * 1024 ** 3, "skip": True}, "must bind")):
        r = dict(rec, disk_precondition=bad)
        with pytest.raises(PF.Refused, match=match):
            PF.validate_declaration(r, p)
    higher = dict(rec, disk_precondition={"path": "C:/", "min_free_bytes": 5 * 1024 ** 3})
    assert PF.validate_declaration(higher, p)["disk_precondition"]["min_free_bytes"] == 5 * 1024 ** 3


def test_verify_free_disk_fails_closed_below_the_floor():
    d = {"path": "C:/", "min_free_bytes": 2 * 1024 ** 3}
    assert PF.verify_free_disk(d, free_fn=lambda p: 2 * 1024 ** 3)["ok"]
    with pytest.raises(PF.Refused, match="below the declared floor"):
        PF.verify_free_disk(d, free_fn=lambda p: 2 * 1024 ** 3 - 1)
    assert PF.dry_disk_precondition("C:/t/r2x/r42-sandbox") == d


# ---- 2.1.5 isolation from the merged installation -----------------------------------------------------------------------------
def test_isolation_refuses_every_value_under_the_merged_installation_except_the_venv_and_the_harness():
    ok = {"PATH": f"C:/Windows;{PF.ISOLATION_VENV}/Scripts", "X": "C:/t/r2x/r42-sandbox/x", "H": PF.HERE.as_posix()}
    assert PF.verify_isolation("C", ok, None, path_entries=[PF.ISOLATION_VENV + "/Lib/site-packages", "C:/t/iso/cand-r30n/backend"], modules={})["ok"]
    for env in ({"DATA_ROOT": "G:/dev (2)/dev/ep-platform-merged/data"}, {"PATH": "C:/Windows;G:\\dev (2)\\dev\\ep-platform-merged\\tools\\claude-2.1.289"},
                {"PWD": "G:/dev (2)/dev/ep-platform-merged/ep-platform"}, {"AI_CLAUDE_CLI": "G:/dev (2)/dev/ep-platform-merged/tools/claude-2.1.289/claude.exe"}):
        with pytest.raises(PF.Refused, match="isolation from the merged installation failed"):
            PF.verify_isolation("C", env, None, path_entries=[], modules={})
    with pytest.raises(PF.Refused, match="sys.path"):
        PF.verify_isolation("B", {}, None, path_entries=["G:/dev (2)/dev/ep-platform-merged/ep-platform/backend"], modules={})
    mod = types.SimpleNamespace(__file__="G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/app/core/config.py")
    with pytest.raises(PF.Refused, match="module app.core.config"):
        PF.verify_isolation("R", {}, None, path_entries=[], modules={"app.core.config": mod})


def test_isolation_checks_the_settings_and_the_env_file():
    class S:
        model_fields = {"cache_root": None, "uploads_root": None, "n": None}
        model_config = {"env_file": "C:/t/iso/cand-r30n/backend/.env"}

        def __init__(self, cache):
            self.cache_root, self.uploads_root, self.n = cache, "C:/t/r2x/r42-sandbox/up", 3
    assert PF.verify_isolation("C", {}, S("C:/t/r2x/r42-sandbox/c"), path_entries=[], modules={})["settings_checked"] == 2
    with pytest.raises(PF.Refused, match="setting cache_root"):
        PF.verify_isolation("C", {}, S("G:/dev (2)/dev/ep-platform-merged/data/cache"), path_entries=[], modules={})

    class E(S):
        model_config = {"env_file": PF.ISOLATION_ENV_FILE}
    with pytest.raises(PF.Refused, match="settings env_file"):
        PF.verify_isolation("C", {}, E("C:/t/r2x/r42-sandbox/c"), path_entries=[], modules={})


def test_the_frozen_trees_settings_never_read_the_merged_env_file():
    for tree in ("C:/t/iso/frozen-r13/backend", "C:/t/iso/cand-r30n/backend"):
        src = (pathlib.Path(tree) / "app/core/config.py").read_text(encoding="utf-8")
        assert 'env_file=str(BACKEND_DIR / ".env")' in src, "the application reads ITS OWN tree's .env only"
        assert not (pathlib.Path(tree) / ".env").exists(), "and neither frozen tree has one"


def test_sandbox_env_drops_the_shells_bookkeeping_folder(tmp_path, monkeypatch):
    monkeypatch.setenv("PWD", "G:/dev (2)/dev/ep-platform-merged/ep-platform")
    monkeypatch.setenv("OLDPWD", "G:/dev (2)/dev/ep-platform-merged")
    env = SI.sandbox_env(tmp_path / "root")
    assert "PWD" not in env and "OLDPWD" not in env


# ---- contract 5: every new key required and closed -----------------------------------------------------------------------------
@pytest.mark.parametrize("key", ["interpreter", "disk_precondition", "isolation", "resume_authorization", "global_provider"])
def test_every_contract_5_key_is_required(tmp_path, key):
    p, sha, rec = _decl(tmp_path, **{key: None})
    with pytest.raises(PF.Refused, match=f"does not bind '{key}'"):
        PF.validate_declaration(rec, p)


@pytest.mark.parametrize("key,value,match", [
    ("global_provider", {"B": "harness_chain", "C": "harness_chain", "R": "refusing", "P": "refusing"}, "global_provider must be exactly"),
    ("global_provider", {"B": "refusing", "C": "refusing", "R": "refusing", "P": "refusing"}, "global_provider must be exactly"),
    ("isolation", {"forbidden_root": "G:/other"}, "isolation must be exactly"),
    ("resume_authorization", {"max_invocations_per_file": 4}, "max_invocations_per_file must be an integer 1..3"),
    ("resume_authorization", {"max_invocations_per_file": 0}, "max_invocations_per_file must be an integer 1..3"),
    ("interpreter", {"path": MERGED_PY, "sha256": "x", "version": "3.12.10"}, "interpreter must bind"),
    ("contract", "r39-live-contract-4", "is not contract r42-live-contract-5"),
])
def test_contract_5_values_are_closed(tmp_path, key, value, match):
    p, sha, rec = _decl(tmp_path, **{key: value})
    with pytest.raises(PF.Refused, match=match):
        PF.validate_declaration(rec, p)


def test_a_valid_contract_5_declaration_reports_every_new_value(tmp_path):
    p, sha, rec = _decl(tmp_path)
    v = PF.validate_declaration(rec, p)
    assert v["contract"] == "r42-live-contract-5" and v["global_provider"] == {"B": "harness_chain", "C": "refusing", "R": "refusing", "P": "refusing"}
    assert v["resume_authorization_max"] == 3 and v["isolation"]["forbidden_root"] == "G:/dev (2)/dev/ep-platform-merged"
    assert v["interpreter"]["path"] == MERGED_PY and v["model_identity"]["cli_version"] == "2.1.263 (Claude Code)"


def test_a_harness_isolation_binding_names_the_running_harness_folder():
    b = PF.isolation_binding()
    assert b["allowed_under_forbidden"] == {"interpreter": "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv", "harness": PF.HERE.as_posix()}
    assert b["env_file_never_read"] == "G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/.env"
    assert MI.SHA256.fullmatch("a" * 64)
