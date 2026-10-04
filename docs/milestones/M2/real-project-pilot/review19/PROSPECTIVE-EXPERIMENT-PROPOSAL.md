# Proposal: a prospective experiment that isolates the three changes

**This is a proposal only.** It becomes relevant after the Review 19 corrections are independently accepted. Nothing here is executed, no residual request is spent, and no sealed project is opened.

## Question

What does each change contribute on its own, at equal budget, on documents never predicted before?

| Change | Kind |
|---|---|
| **R:** rotation-correct region support (`region_texts_v2` text layer + local OCR) | deterministic |
| **E:** located / ROI discovery for drawing sheets, with deadline-bound timeouts | changes the first model request |
| **X:** extra targeted context reads (T's optional `read_field_context`) | extra model requests |

## Design

1. **Arms, factorial where it matters, one change per step:**

   | Arm | Composition |
   |---|---|
   | S | accepted |
   | S+R | support fix only |
   | S+R+E | plus located discovery |
   | S+R+E+X | plus targeted reads |

   The guard G stays on in every non-S arm; it is a validator fix and is replayed offline.

   R needs no model request of its own. It can also be measured **offline on S's captured readings** (as `SUPPORT-REPLAY.json` does), which separates it from model variance. Its live arm is still run so the persisted behaviour is observed.

2. **Equal budgets:**
   - the same per-document cap (12), the same 120 s job budget, the same ledger breaker;
   - arms compared at **equal request counts** (prefix) as well as at their caps;
   - X's extra calls reported as incremental cost per recovered fact.

3. **Sample:**
   - chosen by a seeded rule from the non-sealed exploration manifest;
   - never predicted before;
   - stratified by rotation (0 / 90 / 180 / 270), scan vs vector, drawing sheet vs A4 / A3, and whether the decision block lies inside or outside the title block;
   - frozen with hashes before any label or prediction.

4. **Labels:**
   - drafted and frozen before any prediction, with page / region bindings;
   - uncertain items listed;
   - an independent (AI or human) source review of a declared subset before scoring;
   - no prediction ever becomes truth.

5. **Measures:** all planned documents are the headline denominator. Report by field:
   - accepted precision (numerator and denominator);
   - correctly associated recovery;
   - held evidence and false accepts;
   - field coverage classes: completed read / discovery absent / located incomplete / no region / unusable / failed / budget / not attempted;
   - transport state reported separately;
   - latency and tokens, including timeouts at their estimates.

   Matched subsets are field-specific and carry document IDs.

6. **Stop rules:** a critical acceptance on a resolved label; three provider failures; a breaker; any budget or scope refusal.

7. **Decision rule, declared in advance:**
   - X is adopted only if it shows a positive incremental recovery at equal cost, with no new false accepts.
   - E is adopted only if coverage (including decisions outside the title block) is not worse than S's.

## Budget

The size is not settled here. It needs a new declaration and the owner's decision. The residual of the original 150 is not assumed to fund it.
