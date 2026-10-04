# Cohort preparation after independent label review: r32-labels-reviewed-1 and counted populations

**Task:** ORCH-02.1, agent label R32APPLY-IMPL, under EP Platform Master Plan authority A-03 (owner decision 2026-10-03, Claude-only workflow).
**Model:** Claude Opus 5.5 (`claude-opus-5-5`), effort High, by my own system context.
**Date:** 2026-10-03 (UTC).
**Context:** Review 32 verdict was "REVIEW 31 ACCEPTED FOR COHORT PREPARATION ONLY". This task does not change it. M2 is CHANGES STILL REQUIRED. M3 has not started.

This task applied the frozen independent review mechanically. There was no image reading, no re-ruling, no model or provider request, no prediction, no ledger scope, no OneDrive access and no sealed project. Nothing was approved by this task.

## End state

| Item | Value |
|---|---|
| Reviewed labels | `labels/R32-LABELS-REVIEWED-1.json`, version `r32-labels-reviewed-1`, sha256 `00e53e8253adf86fc5cabbd1659576a2e728f4d0ef20b084f7aaba3157379779` |
| Derived from | `r32-labels-draft-1`, sha256 `ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334` (verbatim copy in `labels/`) |
| Ruling source | `REVIEWER-RESPONSE.final.json`, sha256 `920a21d63871d1618b36deb623e4121d31f3d52949d9c5617536aab7af9d4c5b` (verbatim copy in `review-r32-draft-1/`) |
| Field populations | `FIELD-POPULATION.json`: identity **57**, revision **38**, decision **38** |
| Gate action | **READY FOR INDEPENDENT PREPARATION REVIEW** |
| Package check | `evidence/PACKAGE-CHECK.json`, written by `scripts/verify_r32b_package.py` |
| Manifest | `evidence/EVIDENCE-MANIFEST.json`, written last. Its sha256 is recorded in the M2-REVIEW-RESPONSE.md entry. |

## How the rulings were applied

The rules are in `scripts/apply_rulings_r32.py`, function `build_reviewed`. The function is pure. It raises if any ruling is left over or any draft field has no ruling.

| Ruling | Effect on the draft field |
|---|---|
| accept | Draft values kept. |
| correct / reject | The ruling's state, literal, printed_label, semantic_role, class, actor, actor_state, location, association, association_note, absent_kind, region and evidence (its `evidence_checked`) replace the draft's. An empty value clears the key. `candidates` and `referenced_revision` are taken from the ruling when it records them. The full draft field is kept under `draft_value`. |
| unresolved | Draft values kept. `review_status` is "unresolved", `excluded_from_scoring` is true, and `open_question` comes from the matching DISPOSITIONS entry, which equals the ruling's own `open_question`. |

Every applied field carries `review_provenance`: ruling, provenance, disposition_id, superseded_batch_ruling (if any), note and evidence_checked.

**Ruling counts.** All were consumed exactly once.
- Page-field rulings: 432.
- Document-field rulings: 210.
- Question rulings: 56. These are the draft's 53 unresolved items plus 3 review-worklist questions (F031, F052, F070).

**Page-field outcome:**

| Field | accepted | corrected | rejected | unresolved |
|---|---|---|---|---|
| identity | 128 | 14 | 0 | 2 |
| revision | 123 | 20 | 0 | 1 |
| decision | 131 | 13 | 0 | 0 |

These equal the final response's own counts.

**Other changes:**
- **`resubmission_required: "yes"`** is set on the 9 decision rows named by final convention (d1): F001 p2, F031 p2, F017 p1, F022 p1, F026 p1, F033 p1, F030 p1, F030 p3 and F030 p4. Every one of them has class "approved as noted".
- **`other_identities` additions.** Values were added only where the final response or dispositions record them concretely. Each addition is checked against a verbatim quote of its source:
  - F047 p1: "2020 - 4 - 1072822", label "OLD APPLICATION NUMBER". Source: D-004 evidence, with D-009.
  - F028 p4: "00", label "REV", role "revision of the commented submission". Source: the F028 p4 revision ruling note.
  - Not added: F048 and F049. Topic (h2) names them, but no page or printed form is recorded, so nothing was invented.
- **Convention (a) check:** 0 uncertain rows without an association_note.

## Count-once aliases

| Alias | Counted under | Basis |
|---|---|---|
| F052 | F038 | Byte-identical file (conventions section 1; consolidator question ruling) |
| F070 | F067 | Byte-identical file (conventions section 1; consolidator question ruling) |
| F031 | F001 | Content duplicate, final convention (c)(ii) (`gate_count_once_with`) |
| F059 | F046 | Content duplicate, final convention (c)(ii) (`gate_count_once_with`) |

F052 and F070 have no rulings of their own. Each alias carries `counted_under`. Each canonical document lists its `count_once_members`. Every alias agrees with its canonical document in every field.

## Statuses, stated separately

1. **Source and project permission and verification:** unchanged. They were authorized and verified in the r32 packet (`packet-inputs/AUTHORIZATION-2026-10-02.md`). This task did not touch OneDrive, sources or projects.
2. **Label drafting:** frozen. `r32-labels-draft-1` (`ebd1e24d…a334`) is copied verbatim and was not edited.
3. **Independent label review:** done, as an **owner-delegated independent Claude AI review. This is not human sign-off.**
   - **Agents:** R32REV-B1 to R32REV-B7 (batch reviewers), R32REV-CONSOLIDATE, R32REV-CRITIC (ORCH-01A.4) and R32REV-DISPOSE. All ran Claude Opus 5.5 (`claude-opus-5-5`) at effort High. The orchestrator was Claude Fable 5.1.
   - **Critique:** 8 disagreements, of which 6 were material. The 6 material ones were disposed: 1 upheld (D-006), 3 adopted (D-001, D-002, D-003) and **2 escalated** (D-004, D-005). Two non-material disagreements and two missed items were noted (D-007 to D-010).
   - **Escalated rows (open questions for the preparation review or the owner):**
     - **D-004:** F069 p1 and p3 identity, and the F069 identity `resolved_for_scoring`. Is the page identity ambiguous or absent? `carries_fact` is no either way.
     - **D-005:** F019 p1 revision, and F019 revision `resolved_for_scoring` / `carries_fact`. Does frozen section 4's cell-first order govern, or the topic (i) conflict rule?
4. **Field population counts:** counted (`FIELD-POPULATION.json`, status COUNTED, stage "initial pool after independent review", 0 extensions used).
   - **Rule:** per field, count the distinct documents, after count-once, whose document review has `resolved_for_scoring` = yes and `carries_fact` = yes.
   - **Counts:** identity 57, revision 38, decision 38.
   - **Excluded as unresolved:** identity [F069], revision [F019], decision [].
   - **Upper bound if every unresolved value resolved to yes:** identity 57, revision 39, decision 38. F069 identity carries no fact either way.
   - **Documents:** 72 staged files, 70 with their own rulings, 68 distinct after count-once.
   - **Decision-carrying documents by project (information only):**
     - EP-3563: 11
     - EP-22349: 2
     - EP-27331: 12
     - EP-26687: 3
     - EP-29255: 10
     - EP-15744: 0
   - **Consistency check:** OK. All 138 "carries_fact yes" document fields have at least one labelled page with the field present, association resolved and not excluded from scoring. No rulings were changed.
5. **Preparation gate:** all three fields are at least 12, so the result is **READY FOR INDEPENDENT PREPARATION REVIEW**. This is a mechanical count, not an approval. The two escalated questions are open for that review. No extension was drawn.
6. **Live-run authorization and budget:** none. Nothing was requested. The AI ledger `C:/t/r2x/ledger/r2x-ledger.sqlite` was opened read-only only (mode=ro) and still shows 483 entries and 17 scopes. No scope was created.
7. **M2:** CHANGES STILL REQUIRED. M3 has not started.

## Package contents

| Path | What it is |
|---|---|
| `labels/R32-LABELS-DRAFT-1.json` | Verbatim copy of the frozen draft |
| `labels/R32-LABELS-REVIEWED-1.json` | Reviewed labels |
| `review-r32-draft-1/` | Verbatim copy of the frozen review folder (23 files, including batches and notes), with `COPY-MANIFEST.json` |
| `packet-inputs/` | Verbatim copies, with `COPY-MANIFEST.json`: LABEL-CONVENTIONS-R32.md, FROZEN-SELECTION.json, SOURCE-MANIFEST.json, AUTHORIZATION-2026-10-02.md, EVIDENCE-INDEX.json |
| `FIELD-POPULATION.json` | Counted field populations |
| `scripts/` | check_inputs_r32b.py, copy_inputs_r32b.py, apply_rulings_r32.py, count_population_r32.py, verify_r32b_package.py, and the two test files |
| `tests/` | junit XML: 15 + 6 tests, all passed |
| `evidence/INPUT-HASH-CHECK.json` | Step-0 hash check: 8 of 8 frozen files and 110 of 110 packet files match |
| `evidence/PACKAGE-CHECK.json`, `evidence/EVIDENCE-MANIFEST.json` | Package check, then the manifest, written last |
| `COMMANDS-AND-AUDIT-LOG.md` | Every command, in UTC |

## Observations (facts, no action taken)

- **Ledger `-shm` file.** The read-only opens of the ledger (mode=ro) updated the mtime of the SQLite shared-memory file `r2x-ledger.sqlite-shm`. That file had already been modified at 06:18Z, before this task started. The database file itself (mtime 2026-10-01) and `-wal` (0 bytes) are unchanged, and the counts are unchanged.
- **Accepted printed labels.** On three accepted rows (F061 p1 to p3 identity), the final response's printed_label omits the draft's parenthetical gloss "(licence no.)". Accept keeps the draft value, as the rules require.
