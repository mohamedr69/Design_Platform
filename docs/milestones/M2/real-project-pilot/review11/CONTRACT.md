# M2 Review 11: durable association context and attempt order

This is implemented by `evidence-reader-2026-09-29.6` (`backend/app/ai/evidence_reader.py`), candidate `a977364`. The Review 10 association rules ([`../review10/COMPATIBILITY.md`](../review10/COMPATIBILITY.md)) are unchanged. What changed is **where their context comes from**.

## The invariant

**Dropping audit history, retrying unrelated fields, failed or budget-stopped attempts, and reopening or restarting a stored row never improve the acceptance of a retained fact. Acceptance improves only when compatible source evidence is newly read.**

At `a34d3f8`, selection reconstructed a retained fact's context from two things:
- the field history, which is bounded to 4 entries;
- attempt numbers derived from the attempt-summary list, which is bounded to 12.

Both can lose or repeat the information the reconstruction relied on. In `.6`, selection reads the context from the fact itself.

## 1. Attempt order: a persistent per-row sequence

| Item | Rule |
|---|---|
| **Where it is stored** | `ai_evidence.attempt_seq`: an integer in the row's own stored evidence. It never shrinks. |
| **Each merge** | Takes `seq = attempt_seq + 1`, stores it as the new `attempt_seq`, and writes it into the attempt summary (`seq`) and into the provenance of every field it writes (`provenance.seq`). |
| **Evidence stored before .6** | Its first `seq` is one more than **any** attempt number the row records anywhere: summaries, field provenance, history and superseded envelopes (`next_attempt_number`). It is therefore always later than every earlier attempt, including the repeated 13s the old counter produced. |
| **Numbering** | `evidence_stage` numbers attempts with `next_attempt_number(previous)`; the length of the bounded summary list is no longer used. A caller-supplied `attempt` is kept as given, for display. Order is always taken from `seq`. |
| **Restart and reload** | The counter lives in the row, not in the process, so it survives both. |
| **Bounds** | Unchanged: 12 attempt summaries, and 4 history entries per field. |

## 2. Durable association context: `anchor` on the fact's own entry

Every retained **dependent** fact carries an `anchor` in its own field entry. A dependent fact is `own:revision` or `own:decision`. The anchor is a few keys, bounded, and never pruned, because it belongs to the retained entry, not to history.

| `anchor.source` | When | Keys |
|---|---|---|
| `read` | Stamped by the merge that wrote the fact | `seq`; `identity`, the component's identity as it stood after that attempt; for a decision, `revision`: the revision then compatible with its target, or else with that identity |
| `reconstructed` | Evidence stored before .6, stamped **once** by the next merge. This happens before that merge can prune anything, and only from reliably ordered history (§3). | `attempt`, `identity`, and for a decision `revision` and `revision_known` |
| `unavailable` | The history cannot establish the context reliably | `reason` |

**How selection uses it.** `evidence_for` / `association_of` take a fact's context only from its anchor.
- A row never merged since .6 has no stamped anchor. Its anchor is reconstructed at selection, under the same rules, from its current (unpruned) history.
- A revision's own context, used to decide whether it is compatible with a target, is its recorded `target`, else its anchor.

**The anchor records what was read.** It never writes an explicit target, and a legacy fact's `target` / `target_revision` stay absent.

## 3. Evidence stored before .6: no invented chronology

**When legacy history counts as reliable.** An anchor is reconstructed from legacy history only when that history is reliably ordered.
- **The fact's attempt number must be present** and recorded for **one** attempt. Review 06 `legacy` is the single flat reading of its envelope.
- **Unreliable, and so `unavailable`:**
  - a number recorded by more than one attempt summary;
  - a number recorded at different times on field entries;
  - a missing attempt number.

**What reconstruction looks up.** It uses the identity, and for a decision the revision, in effect at that attempt: the latest entry numbered no later.
- **Entries written since .6 are always later** than any legacy attempt.
- **If nothing old enough remains, and the field's history is full,** the entry that was in effect may already have been pruned. The identity context is then `unavailable`, and a decision's revision is `revision_known: false`.

**What a hold means here:**

| Situation | Status |
|---|---|
| A targetless fact with an `unavailable` context | `held:context_unavailable`, with the reason |
| A decision whose revision anchor is unknown, while a compatible revision has been read since (or its order cannot be established) | `held:revision_unverifiable` |

Missing history never makes a known incompatibility disappear, and never lets a fact be accepted.

**Resolving a hold.** Once a merge has stamped an anchor, it never changes. A hold is resolved only by a **new read of the fact**, which writes a new entry with a `read` anchor and, from the current reader, an explicit target and target revision.

## 4. Concurrency: what the implementation guarantees, and no more

- **One job at a time.** A `process_documents` job runs one at a time across every document worker: `app.services.jobs` lane `documents` has limit 1, and a claim is a single compare-and-set statement.
- **One row at a time.** Within the job, `evidence_stage` reads, merges and commits one row at a time, in the job's process.
- **One consistent chain per stored state.** A row's `ai_evidence` is one JSON value rewritten whole (read, modify, write). The sequence, the anchors and the attempts in any stored state therefore form one consistent chain.
- **Not guaranteed.** Two writers that nevertheless overlap on the same row are not serialized against each other. This could happen with a job requeued by stale recovery while its worker is still alive, or a direct call outside the job system.
  - Both writers read the same `attempt_seq`, so they **can allocate the same attempt number**.
  - The later commit replaces the whole value: the earlier attempt is lost, and the stored state holds only one of the two.
  - No lock, version check or compare-and-set on the row prevents this. Nothing in `.6` adds one.
- **The scope of the uniqueness guarantee.** Attempt numbers are unique and increasing **for writes serialized by the existing job contract** (one `process_documents` job at a time, one row at a time), including across restarts and reloads. That is what `test_attempt_identity_is_persistent_and_unique_across_reloads_past_both_limits` exercises: sequential processing with a reload after every attempt. Overlapping writers are **not** tested, and uniqueness is **not** claimed for them. No stronger ordering guarantee is claimed.

## 5. Scope

- **Changed:** evidence provenance, ordering and association only (`merge_evidence`, `evidence_for` / `association_of` and their helpers, and the numbering in `evidence_stage`).
- **Unchanged:** usable reads (R9-01), source identity (R9-03), BOQ item presence (R9-04), the ledger, evaluator `.9`, and routing, status and business logic.
- **Storage stays bounded.** The additions are one integer per row and a small anchor per retained dependent field.
