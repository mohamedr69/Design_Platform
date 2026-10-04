# Run-set rule R32 (plan v2 section 2.3, executable) and the proposal

| | |
|---|---|
| **Code** | `scripts/harness-r32/run_set_selector_r32.py`, 8 tests in `tests/test_run_set_selector_r32.xml` |
| **Output** | `RUN-SET-PROPOSAL.json` |
| **Status** | A **proposal**. The run set is frozen only by the ORCH-07 declaration. Nothing was dispatched and nothing was predicted |
| **Inputs** | Truth presence only, from the frozen `r32-labels-reviewed-2` through the adapter: `resolved_for_scoring`, `carries_fact`, the decision rows' states, and `pages_in_scope`. It never uses a prediction, a candidate output or a file name as evidence |

## Rule

**Seeded order.** Documents are taken in ascending `sha256("m2-r30-runset-2026-10-02|EP-<ep>|<relative path>")`.

- This is the same construction as `FROZEN-SELECTION.json`'s pool order.
- The path is a sort key only, never evidence.
- The seed is the one declared in DRAFT-DECLARATION.v2 (`run_set.seed`).

**Canonical ids only.** The count-once aliases F031, F052, F059 and F070 are never drawn (R33-07).

The selection then runs in five steps:

1. **Decision-bearing documents.** Take every canonical document whose decision has `resolved_for_scoring = yes` and `carries_fact = yes`. If there are more than 16, take the first 16 in the seeded order.
2. **Top-up, at most 8.** Take canonical documents **without** a decision fact that carry identity or revision (resolved yes, carries yes), in the seeded order.
   - A document is added only while it carries a field whose run-set count is below 16.
   - Stop when identity and revision both reach 16, or when 8 have been added.
3. **Negative controls, 4.** These are executable as follows. A document qualifies if it is canonical, not yet drawn, its decision `resolved_for_scoring = yes`, and **every** in-scope decision row is a scorable ABSENT (`blank_decision_area` or `no_decision_area`). This is the adapter's `decision_control == "negative"`. Take them in the seeded order.
4. **Unsupported controls, 2.** These are executable as follows. A document qualifies if it is canonical, not yet drawn, and has **at least one in-scope page with a field labelled `unsupported` or `illegible`**. Take them in the seeded order.
5. **Cap.** At most 30 documents in all. If the pool cannot supply a step's number, the shortfall is recorded. Nothing is invented, and no file outside the pool is drawn.

## The proposal (`RUN-SET-PROPOSAL.json`)

| Step | Candidates in the pool | Drawn |
|---|---|---|
| decision-bearing | 38 | 16 |
| top-up (revision) | 20 | 4: F060, F043, F057, F046 (all add revision; identity was already 16) |
| negative controls | 25 | 4: F051, F042, F047, F066 |
| unsupported controls | **0** | **0. SHORTFALL 2.** No canonical pool document has an in-scope page labelled `unsupported` or `illegible` in reviewed-2 (D4-08). Nothing is invented |
| **total** | | **24** (at most 30) |

**Per-field matched-population projection.** These are the run-set documents that carry the field. The realised matched population also needs B and C to attempt each document.

| Field | Documents | Margin over 12 | By project |
|---|---|---|---|
| identity | 23 | 11 | EP-15744 1, EP-22349 5, EP-26687 6, EP-27331 6, EP-29255 2, EP-3563 3 |
| revision | 16 | **4** | EP-15744 1, EP-22349 1, EP-26687 5, EP-27331 6, EP-3563 3 |
| decision | 16 | **4** | EP-22349 2, EP-26687 3, EP-27331 6, EP-29255 2, EP-3563 3 |

**Decision controls in the run set:**

- 16 positive. These are the decision-bearing documents: 15 review_signal and 1 other.
- 8 negative: the 4 controls plus the 4 revision top-ups, whose decision truth is a resolved absence.

**Disclosure (R33-10, D4-09).** The realistic matched margin is 4 documents for revision and for decision. A document that C does not attempt or cannot read, an allowance refusal, or a project's rolling day limit can take a field below 12. The comparison would then be INCONCLUSIVE or INCOMPLETE for that field, and the scorer reports it. A larger decision allowance within 30 documents is an owner and plan decision, not part of this task.
