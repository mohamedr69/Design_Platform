# Live-run contract of the r34 runner (RC-3, RC-4, RC-5)

This is what `runner_r32.py`, `lane_r32.py`, `dispatch_guard_r32.py`, `allowance_r32.py` and `preflight_r32.py` (review34, bound in `BINDING-MANIFEST-R34.json`) require before a live run can send anything. **It authorizes nothing.** The ORCH-07 declaration and the owner's authorization do not exist; this task created neither, and no live run, budget or ledger scope exists.

## 1. Entry points

```text
runner_r32.py run    --mode live --declaration <DECL> --declaration-sha <SHA> --run-set <RUN-SET> --binding <BINDING> --binding-sha <SHA>
runner_r32.py resume --mode live --declaration <DECL> --declaration-sha <SHA> --run-set <RUN-SET> --binding <BINDING> --binding-sha <SHA>
```

- There is **no `--auth-path`** (argparse rejects it) and no `--stamp` other than the declaration's (a different one is refused).
- `run` is the **first** invocation of a declaration; `resume` is every later one (§4).
- Dry mode (`--mode dry --stamp <S>`) takes **no** declaration; a dry run has its own run key (sha256 of `r34-dry-run|<stamp>|<binding sha>|<run-set sha>`).

## 2. The declaration contract (`preflight_r32.validate_declaration`)

Every key is **required** in live mode. A missing or different value refuses the run before any folder exists.

| Key | Required value | Finding |
|---|---|---|
| `binding_manifest_sha256`, `run_set_sha256` | the binding manifest and run-set file of this run (both re-hashed) | R33-06 |
| `run.stamp`, `run.folder` | stamp of 3–64 characters `[A-Za-z0-9._-]`; `run.folder` **equals** `C:/t/r2x/r34-sandbox/<stamp>`: **one run folder per declaration** | R34-04 |
| `authorization.path` | **exactly** `<the declaration's folder>/OWNER-DISPATCH-AUTHORIZATION.json` (the pinned path) | R34-03 |
| `authorization.owner_token_sha256` | the sha256 (64 hex) of the owner's token; the token is never stored in any file | R34-03 |
| `caps` | exactly `{"B": 240, "C": 240, "R": 40, "P": 36}` (at most 556) | plan v2 §7 |
| `project_day_limit` | an integer 1–60 (plan: 60 charges per project per UTC day, across all lanes) | R34-04, R34-09 |
| `lane_switches` | exactly the lanes `B`, `C`, `R`, `P`; each maps `AI_EVIDENCE_*` names to strings; B, C and R state `AI_EVIDENCE_VARIANT`; `P` is `{}` (it re-sends captured payloads) | R34-05 |
| `provider_env` | `AI_PROVIDER` (one of claude-code, claude_code, subscription, claude, anthropic, openai, gpt), `AI_MODEL_STANDARD`, `AI_MODEL_SMALL`, `AI_EFFORT`, `AI_TIMEOUT_S`, `AI_CLI_TIMEOUT_S`, `AI_CLAUDE_CLI`, `AI_LEDGER_PATH`, `AI_LEDGER_SCOPE`, `AI_LEDGER_LIMITS`; any further `AI_*` key is also verified; never `AI_ENABLED`, an `AI_EVIDENCE_*` key or a non-`AI_` key | R34-05 |
| `ledger` | `path`, `scope`, `limits` (equal to `AI_LEDGER_PATH` / `AI_LEDGER_SCOPE` / `AI_LEDGER_LIMITS`), `wrap_provider: true`; `limits.requests` between 1 and 556 | R34-04 |

A declaration with `dry_exercise` set is never a live declaration.

## 3. The authorization (`dispatch_guard_r32`)

**Where.** Only at the pinned path: the folder that holds the declaration (its package root), file `OWNER-DISPATCH-AUTHORIZATION.json`. No argument, configuration key (`auth_path` is refused by the runner and by every lane) or function parameter can name another path.

**What it must carry** (a JSON object written by the owner; this harness never writes one):

| Field | Check |
|---|---|
| `declaration_sha256` | present, 64 hex, equal to the verified declaration hash (missing → refused) |
| `owner_token_sha256` | equal to the digest the declaration binds (different → refused) |
| `authorized_by` | `"owner"` |
| `nonce` | a one-run nonce, 16–128 characters `[A-Za-z0-9_-]` |

**The token.** At live start the owner presents the token in the environment variable `R34_OWNER_DISPATCH_TOKEN`; its sha256 must equal the bound digest (missing or different → refused). Each lane reads it once, removes it from its environment (no child process inherits it) and keeps it in memory for the per-request checks. The harness writes only digests.

**One run, one nonce.**
- The runner checks everything without writing (`action="preview"`), creates or re-opens the run folder, then **consumes** the nonce (`action="consume"`): an `O_EXCL` record `<run folder>/authorization/consumed-<first 32 hex of sha256(nonce)>.json` with the nonce digest, the authorization file's own sha256, the declaration hash, the stamp and the invocation number. The authorization's hash is also written into `RUN-STATE.json`.
- A nonce that already has a record is refused (reuse).
- Every lane process, and every request through `GuardedProvider`, requires (`action="verify"`) the record of **its own invocation** with the **same** authorization hash: an edited, replaced, reused or withdrawn authorization stops the next request.
- A **resume is a new invocation** and needs the owner's new authorization (a fresh nonce) for the same declaration. A refused live invocation leaves no run folder, so a later authorized `run` is not blocked.

## 4. One run folder, allowance and capture store per declaration (RC-4)

```text
C:/t/r2x/r34-sandbox/<stamp>/        the run folder the declaration binds
  RUN-STATE.json                    run key (declaration sha256), stamp, binding and run-set hashes, caps, day limit, invocations
  allowance.sqlite                  the ONE durable allowance: lane caps and charges; r34_binding = run key, caps, day limit
  capture.sqlite                    the ONE capture store (capture_store unchanged); r34_binding = run key
  authorization/consumed-*.json     live only: one record per consumed nonce
  WRITER.lock                       one writer at a time
  inv-<n>/                          fresh sandboxes B, C, R, P and the scoring sandbox of invocation n; inv-<n>/out by default
```

- **run** refuses when the run folder exists ("a second fresh invocation is refused; use resume").
- **resume** requires the same run key, stamp, binding, run set, caps and day limit, the existing allowance and capture store (never re-created), and a capture store bound to the run key. It runs every lane again on new sandboxes: every bound fingerprint is **served** from the capture store (never re-sent); a reserved request without an answer is served `interrupted_charged` (charged, never re-sent); only requests never made before are dispatched and charged.
- **No fresh caps.** The caps and the day limit are stored in the allowance file; opening it with another run key, other caps or another day limit is refused; charges are never refunded or reset.
- **Resume is refused** after a terminal comparison (RESULT: the candidate failed the safety gate; INVALID) and after a complete run. It is allowed after an interrupted, refused or never-finished invocation and after INCOMPLETE.
- **Budget stops are not undone by a resume.** A request refused by the allowance (lane cap or day limit) is settled in the capture store as a failure `allowance_refused` and, like every failed row (review31 contract, `capture_store` unchanged), is served as its failure on resume; the stop rule makes it a budget stop again. A project that needs more than the day limit in one UTC day therefore stops the run INCOMPLETE; the declaration plans requests per project (R34-09).
- **Project-day counter.** 60 (or the declared limit) charges per project per UTC day, counted across **all** lanes. The probe lane is attributed to the project of the payload it re-sends. In live mode a request that cannot be attributed to a project is refused.
- **Writer lock.** A second runner on the same run is refused. After a crashed runner, the operator removes `WRITER.lock` once no runner is alive.

## 5. The AI ledger (RC-4)

- **Dry mode:** no ledger path, and the real AI ledger (`C:/t/r2x/ledger/r2x-ledger.sqlite`, opened `mode=ro`, `uri=True`) must read the same before and after (483 entries, 17 scopes, 0 amendments in this package). This assertion is **dry-only**.
- **Live mode:** the application's `LedgerProvider` wraps the real provider and writes to the **declared** scope with the declared limits. Before dispatch, the runner and every lane verify (read-only) that the declared scope **already exists** with **exactly** the declared limits and a closed breaker; otherwise the run is refused. This harness never creates a ledger file or a scope (the application's `Ledger` would create a missing scope, so the check runs again in the lane right before the provider is built). After the run the runner checks that the ledger grew only inside the declared scope: no new scope, no limit amendment, every other scope unchanged, and at most 556 new dispatch entries in the declared scope; otherwise the run ends with an error after its report is written.
- **No scope was created by this task.** Creating the scope is part of the owner's budget authorization at ORCH-07.

## 6. Lane verification (RC-5)

Every live lane process (started by the runner or directly):
1. refuses a configuration with `auth_path` or a dry fault, and runs only the harness folder it is in;
2. runs the runner's preflight again (`preflight_r32.live_preflight`): binding manifest and every bound file, the declaration contract, run set, candidate and baseline HEADs, truth and population gate, the declared ledger scope, and its run configuration against the declaration (mode, run key, run folder, stamp, store, allowance, caps, day limit, lane switches, provider environment, run set, truth file hash, invocation);
3. verifies its `AI_EVIDENCE_*` environment **equals** its declared switches (nothing missing, nothing extra), and every declared provider value is in its environment **and** in the application's settings (`ai_provider`, `ai_model_standard`, `ai_model_small`, `ai_effort`, `ai_timeout_s`, `ai_cli_timeout_s`, `ai_claude_cli`, `ai_ledger_path`, `ai_ledger_scope`, `ai_ledger_limits`, and `ai_enabled` true);
4. passes the same guard (`action="verify"`) before anything is built.

Dry mode uses `DRY_LANE_SWITCHES` (the DRAFT-DECLARATION.v2 arms), labelled "dry defaults … never in live mode" in every lane manifest; the lanes verify their environment against them too.
