"""ORCH-10 (R42PORT-IMPL): LIVE-RUN-CONTRACT.md version 5 for the review42 harness = the frozen version 4
(PILOT/review39/LIVE-RUN-CONTRACT.md) with exact, listed substitutions in its header and sections 2, 3, 7 and 10, and three
new sections (14 invocation order and re-entry; 15 the global-provider boundary; 16 portability and isolation). Sections
4, 5, 6, 8, 9, 11, 12 and 13 are carried byte for byte (checked). Writes argv[1]."""
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import r42common as C  # noqa: E402

V4 = C.REVIEW39 / "LIVE-RUN-CONTRACT.md"
V4_SHA = None   # recorded, not asserted (bound by BINDING-MANIFEST-R42 group outputs_r39 / review39 manifest)

SUBS = [
    ("# Live-run contract of the r39 runner, version 4 (ORCH-08C; Verification 39; owner decisions A-09 and A-10)",
     "# Live-run contract of the r42 runner, version 5 (ORCH-10; Verifications 40 and 41; owner decisions A-09, A-10 and A-11)"),
    ("`sandbox_ingest_r32.py` and the unchanged `dispatch_guard_r32.py` require and do before and during a live run. These are the files bound in `BINDING-MANIFEST-R39.json` (review39).",
     "`sandbox_ingest_r32.py` and `dispatch_guard_r32.py` require and do before and during a live run. These are the files bound in `BINDING-MANIFEST-R42.json` (review42), run only from `PILOT/review42/scripts/harness-r32/` in the merged installation."),
    ("- Version 3 (`review38/LIVE-RUN-CONTRACT.md`) stays frozen. This version replaces it for the r39 harness.",
     "- Versions 3 (`review38/LIVE-RUN-CONTRACT.md`) and 4 (`review39/LIVE-RUN-CONTRACT.md`) stay frozen. This version replaces version 4 for the r42 harness."),
    ("**What changed since version 3 (each section names its finding):**",
     "**What changed since version 4 (ORCH-10; each section names its finding):**\n"
     "- §2: contract 5 (`interpreter`, `disk_precondition`, `isolation`, `resume_authorization`, `global_provider`; the CLI pinned by absolute path, file sha256 and version line).\n"
     "- §3: the separable multi-invocation authorization form (A-11 §4), default off; the nonce is consumed only after the allowance and the capture store exist.\n"
     "- §7: the CLI pin.\n"
     "- §10: the dry and test sandbox base `C:/t/r2x/r42-sandbox`.\n"
     "- §14 (new): the invocation order, re-entry of a folder without an allowance, the free-disk floor (R41-09, R41-10, R41-11).\n"
     "- §15 (new): the fail-closed global provider of lanes C, R and P (R40-04, owner option 2).\n"
     "- §16 (new): portability to the merged installation and isolation from it.\n\n"
     "**What changed from version 3 to version 4 (carried for the record; each section names its finding):**"),
    ("## 2. The declaration contract 4 (`preflight_r32.validate_declaration`, then `verify_bounds` in the live preflight)\n\nEvery key is required. A missing or different value refuses the run before any folder exists.",
     "## 2. The declaration contract 5 (`preflight_r32.validate_declaration`, then `verify_bounds` in the live preflight)\n\n"
     "Every key is required. A missing or different value refuses the run before any folder exists. Contract 5 is contract 4 (the rows below) "
     "with `contract` = `\"r42-live-contract-5\"`, the CLI pin of `model_identity` and the five new keys at the end of the table."),
    ("| `contract` | `\"r39-live-contract-4\"` | — |", "| `contract` | `\"r42-live-contract-5\"` | ORCH-10 |"),
    ("| `model_identity` | Full ids (no alias), equal to `AI_MODEL_SMALL` / `AI_MODEL_STANDARD`; provider; CLI path and version. | R38-10 |",
     "| `model_identity` | Full ids (no alias), equal to `AI_MODEL_SMALL` / `AI_MODEL_STANDARD`; provider; **the CLI by absolute path (= `AI_CLAUDE_CLI`), the file's sha256 and the exact version line** (a name on PATH or a null version is refused). | R38-10; **ORCH-10** |"),
    ("| **`decision_coverage_gate`** | `\"C_GE_B_ONLY\"` (§12). A declaration that binds R into eligibility, such as plan v2's `C_GE_B_AND_C_GE_R` or any other id, is refused. | **R39-15; A-10 (new)** |",
     "| **`decision_coverage_gate`** | `\"C_GE_B_ONLY\"` (§12). A declaration that binds R into eligibility, such as plan v2's `C_GE_B_AND_C_GE_R` or any other id, is refused. | **R39-15; A-10 (new)** |\n"
     "| **`interpreter`** | `{path, sha256, version}` of the bound interpreter `G:/dev (2)/dev/ep-platform-merged/ep-platform/backend/venv/Scripts/python.exe`. The runner and every live lane refuse another `sys.executable`, file hash or `sys.version`. | **ORCH-10 2.1.1** |\n"
     "| **`disk_precondition`** | `{path: the sandbox base's drive, min_free_bytes ≥ 2147483648}` (2 GiB; configurable only upward). Checked before invocation 1 and every resume, before any folder is created or re-opened and before any nonce is consumed (§14). | **R41-10 (C1)** |\n"
     "| **`isolation`** | Exactly `{forbidden_root: \"G:/dev (2)/dev/ep-platform-merged\", allowed_under_forbidden: {interpreter: <the venv>, harness: <this harness folder>}, env_file_never_read: <the merged .env>}` (§16). | **ORCH-10 2.1.5** |\n"
     "| **`resume_authorization`** | `{max_invocations_per_file: 1..3, …}`: the bound of the multi-invocation authorization form (§3). | **A-11 §4** |\n"
     "| **`global_provider`** | Exactly `{\"B\": \"harness_chain\", \"C\": \"refusing\", \"R\": \"refusing\", \"P\": \"refusing\"}` (§15). | **R40-04; A-11** |"),
    ("## 3. The authorization (`dispatch_guard_r32`, unchanged)\n\nAs in contract 2, section 3:",
     "## 3. The authorization (`dispatch_guard_r32`; ORCH-10 adds the multi-invocation form)\n\nAs in contract 2, section 3:"),
    ("A resume is a new invocation with a new authorization.\n",
     "A resume is a new invocation with a new authorization.\n\n"
     "ORCH-10 (A-11 §4), a separable feature, off unless the owner writes it:\n"
     "- The file has exactly the keys `authorized_by`, `declaration_sha256`, `owner_token_sha256` and either `nonce` (the per-invocation form, unchanged) "
     "or `invocations_authorized` N with `nonces` (N distinct one-run nonces), 1 ≤ N ≤ the declared `resume_authorization.max_invocations_per_file` (3). "
     "Any other key is refused: an authorization can never name, raise, reset or re-create an allowance, the parent budget, the window, the scope or any limit.\n"
     "- Each invocation consumes exactly one nonce, the first unconsumed one in list order. A nonce consumed out of order, a nonce consumed under another "
     "authorization file, a repeated nonce or N above the bound is refused. After N invocations, invocation N+1 needs a new file.\n"
     "- A file naming any hash other than the RUN hash the runner verified (for example the frozen hash) is refused, as before.\n"
     "- The nonce of an invocation is consumed only after the run's capture store is bound and its allowance exists (§14), so a failure before that "
     "consumes nothing and the same authorization serves the next attempt.\n"),
    ("## 7. Model identity (unchanged; see `MODEL-ID-EVIDENCE.md`)",
     "## 7. Model identity (ORCH-10: the CLI pinned by absolute path, file sha256 and version line; see `MODEL-ID-EVIDENCE.md`)"),
    ("- **What is checked.** The CLI version is recorded before any lane. Every response's reported model and provider are checked.",
     "- **What is checked.** The pinned CLI file's sha256 (read as bytes) and its `--version` line, before anything is created or re-opened (§14), and recorded before any lane. Every response's reported model and provider are checked."),
    ("The sandbox base defaults to `C:/t/r2x/r39-sandbox` for dry runs and tests. Live runs use the declaration's.",
     "The sandbox base defaults to `C:/t/r2x/r42-sandbox` for dry runs and tests (ORCH-10). Live runs use the declaration's."),
]

APPEND = """
## 14. The invocation order, re-entry and the free-disk floor (ORCH-10; R41-09, R41-10, R41-11)

`runner_r32.main` now orders every invocation so that a failure before the run's allowance exists can never strand the run or consume an authorization:

1. **Every check, nothing created, re-opened or consumed:** the binding; (live) contract 5, the bound interpreter, the pinned CLI file's sha256; the free space of the sandbox base's drive (≥ the declared floor, 2 GiB; dry mode uses the same floor); the HEADs; the truth and the population gate; the run set; (live) the bounds and the ledger scope; the resume rules (a resume) or the re-entry proof (a `run` on an existing folder); the guard preview; then `claude --version`, the only process this step starts, compared with the pin and with the run's first recorded line.
2. The run folder (invocation 1), or the re-entered or re-opened folder; `RUN-STATE.json`; the `WRITER.lock`; the output folder; the version and provider-identity record.
3. The capture store bound to the run key; then the ONE allowance, created atomically (built as `allowance.sqlite.new` and renamed into place only once its binding is committed; a resume opens the existing one and never re-creates it).
4. (live) **Only now** the authorization nonce is consumed (the O_EXCL consumption record).
5. The lanes, the allowance audit, the scoring.

**Re-entry.** A failure in steps 2–3 leaves a folder that `run` may re-enter. `reentry_proof` requires, from the folder's own records, that no allowance was ever created (`allowance.sqlite` absent), no nonce was consumed (no consumption record) and no request was charged (the capture store, if bound, is bound to this run key and holds no request). It writes `REENTRY-<n>.json`; the re-entry is a new invocation number; nothing existing is reset or re-created (an unreadable `RUN-STATE.json` and a partial allowance file are kept aside under new names, never used). With an allowance present, `run` is refused (`use 'resume'`).

**Resume.** A resume re-checks the CLI file, the version line and the free disk before it consumes its nonce (R41-11). A failure after the allowance exists but before the consumption is resumed with the same, still unconsumed authorization.

**Refusals that stay.** A second `run` with an allowance present; a resume without an allowance (now with the hint that `run` re-enters); `WRITER.lock`; an identity mismatch or a contract breach (INVALID, never resumed); a terminal comparison; a resume before the resume policy's time; after the elapsed bound (CLOSED).

## 15. The global-provider boundary of lanes C, R and P (ORCH-10; R40-04, owner decision A-11: option 2)

- Lane B keeps the harness chain as the application's global provider (unchanged).
- Lanes C, R and P install `run_control_r38.RefusingGlobalProvider` as the application's global provider (`app.ai.provider.set_provider`) right after the provider module is imported, before any application code runs; the lane checks at the end that it is still installed.
- An application path that calls `get_provider().complete(...)` in C, R or P is refused (`dispatch_refused`): never dispatched, never charged, never reaching the CLI or a ledger. It is recorded as the contract breach `global_provider_request` (`CONTRACT-BREACH.json`, the lane's events per document and page, the allowance's refusals) and makes the run INVALID under the undeclared-request rule; the lane's stop controller makes every lane terminal.
- `REQUEST-PATHS-STATIC.json` (request_paths_r42) resolves every `get_provider()` site of both trees to the refusing provider (C, R, P) or the chain (B), installed before every application entry; `test_global_provider_r42.py` shows the dynamic refusal in C, R and P and lane B unchanged.

## 16. Portability to the merged installation and isolation from it (ORCH-10 2.1)

- Every binding names the merged installation (`G:/dev (2)/dev/ep-platform-merged/ep-platform/…`); every bound file hashes as before (`BINDING-MANIFEST-R42.json`).
- The interpreter is bound (§2): the merged venv's `python.exe`, its sha256 and `sys.version`; lanes, ingestion and scoring run under it.
- `sha256` of bound files and the binding check open files through the extended-length prefix (`\\\\?\\`): `LongPathsEnabled` is 0 on this machine.
- Isolation: every lane, live and dry, at its start and again at its end, refuses any environment value, application setting, `sys.path` entry or loaded module under `G:/dev (2)/dev/ep-platform-merged/` except the bound venv and this harness folder, and refuses an application env file that is the merged `.env` (the frozen trees read only their own, absent, `.env`). `sandbox_env` drops the shell's `PWD` / `OLDPWD`. The lanes' application settings come only from the declaration and the sandbox; the merged installation's `.env`, data and code are never read, and its bundled CLI 2.1.289 is never used.
"""


def main(out) -> int:
    text = V4.read_text(encoding="utf-8")
    keep = {}
    for h in ("## 4.", "## 5.", "## 6.", "## 8.", "## 9.", "## 11.", "## 12.", "## 13."):
        i = text.index("\n" + h) + 1
        j = text.find("\n## ", i + 1)
        keep[h] = text[i:(j + 1 if j > 0 else len(text))]
    for old, new in SUBS:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"anchor found {n} times: {old[:80]!r}")
        text = text.replace(old, new)
    text = text.rstrip("\n") + "\n" + APPEND
    for h, body in keep.items():
        if body not in text:
            raise SystemExit(f"section {h} is not carried byte for byte")
    C.write_text(out, text)
    print({"written": str(out), "v4_sha256": C.sha256_file(V4), "v5_sha256": C.sha256_file(out), "carried_verbatim": sorted(keep)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
