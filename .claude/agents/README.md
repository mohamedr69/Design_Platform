# Agent roster

Project agent definitions for the Engineering Project Platform. The orchestrating Claude Code session (Fable 5.1, high effort) uses these through the Agent tool by `subagent_type`. The roadmap they serve is `docs/UNIFIED_MASTER_ROADMAP.md` (M1–M29).

| Role | Agent | Model / effort | Writes | Parallel |
|---|---|---|---|---|
| Orchestrator | this session | Fable 5.1 / high | designated branch only | n/a |
| Implementer (code, tests, migrations, frontend) | `ep-implementer` | Opus 5.5 / high, own worktree | its worktree | **No**: one at a time |
| Independent verifier (acceptance verdicts) | `ep-verifier` | Opus 5.5 / high, read-only | nothing | Yes |
| Test runner (runs suites, records evidence) | `ep-test-runner` | Sonnet 5.5 / medium | `docs/roadmap-evidence/`, `docs/milestones/**` evidence only | Yes |
| Surveyor (read-only inventories) | `ep-surveyor` | Sonnet 5.5 / medium | nothing | Yes |
| Scribe (milestone records, matrices) | `ep-scribe` | Sonnet 5.5 / medium | `docs/`, `README.md` | Yes |
| Label reviewer (Golden truth, M4, M13, M27) | `ep-label-reviewer` | Opus 5.5 / high, read-only | nothing | Yes, one project each |
| UI checker (drives local app, screenshots) | `ep-ui-checker` | Sonnet 5.5 / medium | evidence folders only | Yes for API-level checks; browser checks sequential per container (fixed Vite proxy port) |

## How writes are kept in their lane

Claude Code cannot restrict Bash by command in an agent's `tools` list, so every non-implementer agent runs `.claude/scripts/guard-agent-writes.py` as a `PreToolUse` hook on Bash, Write, Edit and NotebookEdit. It blocks mutating git subcommands, file-writing shell commands, in-place edits, redirections and inline file-writing scripts unless the target is under `/tmp`, the session scratchpad, or a folder the agent is explicitly allowed (`--allow`). It is a safety net, not a sandbox: the orchestrator runs `git status` after every agent and reverts anything unexpected.

The implementer has no guard because it works in its own git worktree (`isolation: worktree`); the orchestrator reviews and merges its commits into the designated branch and is the only one who pushes.

## Orchestration rules

1. **One implementer at a time.** Parallel implementers produce conflicting worktrees. Surveyors, verifiers, test runners, scribes, label reviewers and UI checkers may run in parallel on disjoint inputs.
2. **Every implementer task names** the unified milestone, bounded scope, snapshot it changes, exact completion gate and evidence destination (roadmap section 14). Without all five, the implementer stops.
3. **Every implementer run is followed by** `ep-verifier` (verdict) and, where tests or UI changed, `ep-test-runner` and/or `ep-ui-checker` (evidence). A milestone status line changes only when the scribe is handed a verifier verdict.
4. **Verdict vocabulary** is the verifier's: ACCEPT, ACCEPT WITH NOTES, CHANGES REQUIRED, NOT ESTABLISHED. Passing tests, historical reports and source comments never produce ACCEPT.
5. **Evidence lives in** `docs/roadmap-evidence/<YYYY-MM-DD>/` for roadmap-level runs and `docs/milestones/<M>/evidence/` for milestone records. Past evidence folders, `docs/milestones/M2/**` and `docs/roadmap-sources/**` are frozen for everyone.
6. **Environment facts** every agent is told: Linux cloud container, Python 3.13, no Tesseract, no AutoCAD, no live archive or `.env`; `AI_ENABLED=false` unless a budget is granted explicitly; always an explicit pytest `--basetemp` under the scratchpad.
7. **Owner decisions** (roadmap section 6 items left to M3, label sign-off, budgets, live validation) are never taken by an agent; they are reported for the user.

## Files

- `ep-implementer.md`, `ep-verifier.md`, `ep-test-runner.md`, `ep-surveyor.md`, `ep-scribe.md`, `ep-label-reviewer.md`, `ep-ui-checker.md` — the definitions (frontmatter + instructions).
- `../scripts/guard-agent-writes.py` — the write guard; `python -I .claude/scripts/guard-agent-writes.py --help` is the docstring.
