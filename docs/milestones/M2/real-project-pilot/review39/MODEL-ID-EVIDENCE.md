# Model-identity evidence from the installed CLI (ORCH-08C task item 6; Verification 39 R39-09 / Q1; owner decision A-10 item 2)

- **Author:** R39HARNESS-IMPL (Claude Opus 5.5, `claude-opus-5-5`, self-reported), 2026-10-04.
- **Method:**
  - A read-only byte search of the installed CLI file, `scripts/model_id_evidence_r39.py`. Its output is `MODEL-ID-EVIDENCE.json`: every finding with its byte offset, a short fragment and the sha256 of a 2 KiB window around it, so anyone can find it again.
  - **The CLI was not executed in any form.** No `claude`, no `--version`, no probe. The version 2.1.263 had already been recorded by ORCH-08.
  - No provider or model request was made.
- **Owner probe:** the probe below is for the owner to run **before dispatch**, outside the experiment (A-10). It was **not run** here.

## 1. The installed CLI

| Item | Value |
|---|---|
| File | `C:/Users/moham/AppData/Local/Microsoft/WinGet/Packages/Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe/claude.exe`. This is the only `claude` on PATH; `where claude` was run, which does not execute it. |
| Size / sha256 | 218,746,016 bytes / `0b35df94c1307004f07b738390bfef8dfca5e9af29aaf6517f305bf086b95b03` |
| Embedded package | `@anthropic-ai/claude-code`, version **2.1.263**, build time 2026-09-06T01:08:56Z, source commit `37ae3f38d765199d54a6913cd61c6c9ad8576cc6` (offset 95,598,220). This equals the `2.1.263 (Claude Code)` line ORCH-08 recorded. |
| Form | A Bun single-file executable. Its JavaScript bundle is present as minified text (bundle headers `// Version: 2.1.263`). |
| User settings that could remap models | `~/.claude/settings.json` holds `model: "opus[1m]"`, the default model, which `--model` overrides. It has no `modelOverrides`, no `availableModels` and no model environment keys. No managed (policy) settings file exists. The process environment has no `ANTHROPIC_*MODEL` variable. |

## 2. What the CLI does with `--model` (code reading)

Fragments are short and quoted only to locate the code. The offsets are in `MODEL-ID-EVIDENCE.json`.

1. **Both pinned ids are known to this CLI.**
   - The baked model catalog has an entry `{id:"claude-sonnet-5",family:"sonnet"`, display "Sonnet 5", with first-party wire id `claude-sonnet-5`.
   - It has an entry `{id:"claude-opus-5",family:"opus"`, with first-party wire id `claude-opus-5`.
   - Both are in the list of recognised model ids.
2. **Aliases resolve through the catalog, and can be changed.**
   - First-party defaults: `sonnet` → `claude-sonnet-5`, `opus` → `claude-opus-5`, `haiku` → `claude-haiku-4-5`, `fable` → `claude-fable-5-1`. Other providers (Bedrock, Vertex, …) have their own per-provider defaults.
   - The `sonnet` alias first honours `ANTHROPIC_DEFAULT_SONNET_MODEL`; likewise for `opus` and `haiku`.
   - The CLI can also load a signed remote catalog (`https://downloads.claude.ai/model-catalog/v1/catalog.json`), so an alias's target can change without a new CLI. **This is why aliases are not an identity**; the declaration refuses them.
3. **A full id passes through unchanged.**
   - `parseUserSpecifiedModel` (minified `wt`) sends only alias names (`sonnet`, `opus`, `haiku`, `fable`, `best`, `opusplan`, with an optional `[1m]`) to the default-model getters.
   - Any other value is returned through `uS`, which is the identity function (`function uS(e){return e}`).
   - A small legacy remap applies only to the Opus-4 family ids.
   - `vetUserSpecifiedModel` (`DAt`) steps a model down or drops it only when an organisation `availableModels` policy excludes it; there is none here.
4. **What `--output-format json` reports.**
   - The result object has no top-level model field.
   - Its `modelUsage` is the cost ledger's map: `total_cost_usd:ru(),usage:Ai(),modelUsage:jw()`. The ledger records usage under its third argument (`recordCost(e,t,o){this.#l[o]=t`).
   - On the main streaming path that argument is **the request's model** (`…VG($N(F,Oc),Oc,f.model,…`), **not the API response's `message.model`**.
   - After a server-side refusal fallback, the key is the fallback model (`f.serverRefusalFallback?.model??f.model`).
   - Each entry carries the usage counts, `costUSD`, `canonicalModel` and `provider`. The CLI's own schema describes these as the canonical id "used for the pricing lookup" and the API provider route (for example `firstParty`).
   - Helper calls outside the main loop may add other keys, typically `claude-haiku-4-5`.
5. **What `--output-format stream-json --verbose` adds.**
   - The `system`/`init` line carries `claude_code_version` and `model`, the CLI's configured main model.
   - Every `assistant` line carries `message`, which the CLI's schema describes as a Messages API Message object: "id, model, content blocks … stop_reason and usage".
   - `message.model` is **the server's response field** naming the model that produced the response. It is the only server-reported identity the CLI exposes.
6. **What the application's adapter reads.** Candidate and baseline `app/ai/provider.py` are identical (`d465961e…`). The adapter runs `claude -p --output-format json --model <id> …` and records the response's model as:
   - the first `modelUsage` key that does not contain `haiku`;
   - else the configured id (also echoed on a timeout or a transport error).

## 3. Outcome of the offline investigation

- **Accepted identifiers.** `claude-sonnet-5` and `claude-opus-5` are known to CLI 2.1.263, and a full id passes `--model` unchanged.
- **The returned key.** With `--model claude-sonnet-5` and no remapping environment or policy, the `modelUsage` key will be `claude-sonnet-5`, unless a refusal fallback substitutes another model.
- **No more specific id is exposed.** No dated or suffixed id is exposed by the `json` output, because the key is the requested id.
- **UNRESOLVED.** Verifiable identity of the underlying served model cannot be established offline. `--output-format json`, the format the adapter uses, cannot prove it even when run: it reports the requested id. The only server-side identity is `message.model` in `stream-json` output, and that is the server's own statement, not an independent proof.

## 4. The owner's probe: exact command, expected evidence, interpretation (A-10 item 2; not run here)

**When and how.** Run it once, yourself, before dispatch:
- outside the experiment, in an empty folder;
- not through the harness;
- with `ANTHROPIC_API_KEY` and `ANTHROPIC_AUTH_TOKEN` unset, as the adapter does, so the subscription login is used.

**What it costs.** One request.

**Which model.** Only the small tier `claude-sonnet-5` is exercised by this run: every B, C and R read. `claude-opus-5` (the standard tier) is used only by EV2 escalations, which are off under the declared EV1 switches. A second, optional probe with `--model claude-opus-5` would cost one more request.

### 4.1 The minimal probe (as asked: the declared full id, `--output-format json`; cmd.exe)

```cmd
cd /d %TEMP% && mkdir ep-model-probe && cd ep-model-probe
set ANTHROPIC_API_KEY=
set ANTHROPIC_AUTH_TOKEN=
echo Reply with the single word OK.| "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe" -p --output-format json --model claude-sonnet-5 --no-session-persistence --disable-slash-commands --strict-mcp-config --tools "" > probe-claude-sonnet-5.json
```

These are the adapter's own flags (`app/ai/provider.py`), without its system prompt and schema. Use cmd.exe rather than Windows PowerShell 5.1: the latter drops the empty `""` argument when it calls a native program.

**Expected evidence in `probe-claude-sonnet-5.json`:**
- `"type": "result"`, `"subtype": "success"`, `"is_error": false`, `"num_turns": 1`.
- `"modelUsage"`:
  - Exactly one key without `haiku`, and it must be exactly `"claude-sonnet-5"`. A `claude-haiku-4-5` key from internal helper calls may also appear.
  - In that entry: `inputTokens` > 0, `outputTokens` > 0, `"canonicalModel": "claude-sonnet-5"`, `"provider": "firstParty"`.
- There is **no** top-level model field. Do not look for one.

### 4.2 The same single request with the server-reported identity (recommended alternative: `stream-json`)

```cmd
echo Reply with the single word OK.| "%LOCALAPPDATA%\Microsoft\WinGet\Packages\Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe\claude.exe" -p --output-format stream-json --verbose --model claude-sonnet-5 --no-session-persistence --disable-slash-commands --strict-mcp-config --tools "" > probe-claude-sonnet-5.jsonl
```

**Expected evidence, one JSON object per line:**
- The `{"type":"system","subtype":"init",…}` line, with `"claude_code_version": "2.1.263"` and `"model": "claude-sonnet-5"`.
- Every `{"type":"assistant",…}` line, with `"message": {"model": "claude-sonnet-5", …}`.
- The final `{"type":"result","subtype":"success","is_error":false,…}` line, whose `modelUsage` reads as in 4.1.

### 4.3 Interpretation

| Field | What it shows | What it does not show |
|---|---|---|
| `modelUsage` key `claude-sonnet-5` (json or stream-json) | The CLI accepted the full id. Nothing remapped it: no alias, environment or policy. No refusal fallback substituted another model. | **Which model the server ran.** The key is the CLI's record of the requested id. |
| `canonicalModel`, `provider: firstParty` | The CLI's own pricing canonicalisation of the requested id, and its route. | The served model (both are client-side). |
| `init` `model`, `claude_code_version` | The CLI's configured main model and its version. | The served model. |
| `assistant` `message.model` (stream-json only) | **The server's statement** of the model that produced the response: the strongest identity the CLI exposes. `claude-sonnet-5` agrees with the declaration. Any other value, for example a dated id, means the declaration's pin does not describe what the server reports. | An independent or cryptographic proof. It is the server's self-report. |
| An alias (`sonnet`), or the echoed configured id | Nothing about identity. The adapter echoes the configured id on timeouts and transport errors, and when `modelUsage` has no non-haiku key. | It is **never** proof. |

**Verdicts:**
- **The 4.1 probe "passes"** when the non-haiku key is exactly `claude-sonnet-5`. That still leaves the served-model identity **UNRESOLVED**.
- **With 4.2**, the server-reported `message.model` becomes available. If it equals `claude-sonnet-5`, the run's pin agrees with the server's report. That is consistent evidence, not proof of the underlying model.
- **Either probe fails** if `is_error` is true, the subtype is not `success`, a different non-haiku key appears, or `message.model` differs. Then the declaration must not be dispatched as written.

## 5. Runtime identity check: still fail-closed under the declared INVALID rule

- **The check.** `model_identity_r38.IdentityGuard` compares every response's reported model and provider with the declared pins: `claude-sonnet-5` and `claude-opus-5`, provider `claude-code`. The reported model is the adapter's first non-haiku `modelUsage` key.
- **On a mismatch:**
  - it writes `IDENTITY-INVALID.json` once, naming the offending request;
  - it turns the response into the failure `identity_mismatch`, so its answer is never used; the request stays charged;
  - every lane becomes terminal and the run is INVALID;
  - the next request is refused at the gate, and any resume is refused.
- **Tests and drills:** `test_model_identity_r38.py`, `test_run_control_r38.py` and the `identity_mismatch` visibility drill. ORCH-08C changes none of this.
- **Limit 1: it can only compare what the CLI reports.**
  - In json mode that is the **requested** id. The check therefore verifies the CLI's resolution of `--model` and the absence of a fallback or remap.
  - It does **not** verify the served model. That needs `message.model`, which the application's adapter does not read. Making it read that field would be an application-code change, outside this program.
- **Limit 2: an echoed id passes.** A response with no non-haiku `modelUsage` key echoes the configured id, so the check cannot tell it from a real report.
- **Fail-closed:** any **verifiable** mismatch is fail-closed under the INVALID rule; these two limits are stated, not hidden.
