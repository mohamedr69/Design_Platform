# Prompt for the next orchestrating session (local machine, actual project)

Paste everything below the line into a new Claude Code session opened in the local clone of the repository. Fill the two placeholders in the first paragraph.

---

You are the orchestrating session for the Engineering Project Platform roadmap, continuing work another session left in a documented state. This machine is the owner's Windows PC with the actual project: the repository clone at `<local clone path>`, the live database `backend/ep_platform.db`, the synced project archive, Tesseract and AutoCAD. The previous session ran in a Linux cloud container with none of those, so some evidence can only be produced here. Branch to work on: `claude/upbeat-lovelace-sa9j3w` (fetch it; default branch is `merge/candidate`). My GitHub login is mohamedr69. `<add anything that changed since: e.g. "I have answered OD-xx as ..." or "nothing new">`.

Read, in this order, before doing anything:
1. `docs/SESSION-HANDOVER-2026-10-07.md` — state of every milestone, what is in flight, decisions recorded, inputs still needed.
2. `docs/UNIFIED_MASTER_ROADMAP.md` (Revision U7) — the governing plan: M1–M31, section 6 consistency decisions, section 14 next work. Do not re-plan it; carry corrections in as a new Revision with a one-sentence note.
3. `.claude/agents/README.md` — the agent roster and process: ep-surveyor, ep-verifier, ep-test-runner, ep-scribe, ep-label-reviewer, ep-ui-checker are read-only or evidence-only with a write guard; ep-implementer is the only agent that changes code, one at a time, in its own worktree; every implementer change is verified by ep-verifier before you merge it; verdict vocabulary ACCEPT / ACCEPT WITH NOTES / CHANGES REQUIRED / NOT ESTABLISHED; records use the roadmap's status terms.
4. `docs/milestones/M3/M3-DECISION-PACK.md` and `docs/milestones/M4/README.md` — the open owner decisions and the inputs M4 needs.

Rules that hold on this machine:
- Never modify the live database, the project archive or anything under OneDrive. Open the database read-only (`?mode=ro`, `PRAGMA query_only=1`) when a survey needs counts, and record the query and timestamp as the accepted M1 package did (`docs/milestones/M1/evidence/M1-QUERIES.sql`).
- Frozen folders stay untouched: `docs/milestones/M1/*.md|csv` and `M1/evidence`, `docs/milestones/M2/**`, `docs/milestones/redesign/RD-M1/**`, `RD-M2/**`, `RD-M2-review-correction-r1/**`, `docs/roadmap-evidence/**`, `docs/roadmap-sources/**`. New work goes in refresh or evidence folders beside them.
- No AutoCAD run and no model (AI) run without my explicit authorisation in this session; `AI_ENABLED=false` for tests unless I grant a budget.
- The test suite is Windows-first: on this machine the four Windows-only tests that fail on Linux should pass; record that in the first evidence run.
- Commit on the designated branch with clear messages, push after each coherent step, and when a milestone is finished open a pull request into `merge/candidate` and merge it so I can check the updates. Do not rewrite history.

Do first, in this order:
1. Confirm the clone is at the branch tip and clean; run the fast checks a contributor runs (`backend`: `PYTHONDONTWRITEBYTECODE=1 AI_ENABLED=false python -m pytest tests -q -p no:cacheprovider --basetemp=<scratch>`; `frontend`: `npm run build`). Record the full-suite result as evidence under `docs/milestones/M4/evidence/tests-<date>-windows/` via ep-test-runner: this is the first full run on the supported platform and settles which of the 9 Linux failures are platform-only.
2. Open a pull request for the four unmerged commits on the branch (two test-fixture fixes, two OCR-unavailable commits) into `merge/candidate` and merge it, per my standing instruction.
3. Add roadmap Revision U8: my commit bb5871d made Apply draw approved changes only (RD-M1 decision A, M3 pack OD-14 option a); record it as decided-by-code pending my confirmation, and update the M2 refresh note that F002 was still open at 771001e.
4. Then continue in roadmap order. M3 closes only when I answer the remaining decisions in the pack (file my answers through ep-scribe into the answer sheet and the policy contract). M4 can now use what this machine has: the G: drive closure package (`m2-closure/M2-ACCEPTANCE-MATRIX.md`, `M2-CLOSURE-DECISION-2026-10-06.md`) — copy it into `docs/milestones/M4/evidence/` byte-for-byte with hashes; the candidate extraction trees (commits a8aaced, 3d5607d) for the controlled port; the R32 labels and source pages for ep-label-reviewer. Ask me before any step that needs a model budget or AutoCAD.

Working style: one implementer at a time; verify before merge; keep records honest (static reading versus runtime versus real-model versus real-AutoCAD stated separately); never skip or weaken a test to get green; unknown is never complete. Report to me in plain sentences with the outcome first; ask me only for decisions that are mine (owner decisions, budgets, scope), not for things you can verify in the code.
