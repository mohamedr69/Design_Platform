# M2 Review 07: validation policy .2 (R7-02) and evidence lifecycle (R7-03)

Source files:
- `app/ai/evidence_reader.py`: `evidence-reader-2026-09-29.2`, `evidence-policy-2026-09-29.2`;
- the frozen candidate commit `c9a1a14`;
- the review 06 reader, pinned unchanged as `tests/fixtures/evidence_reader_r6.py`.

The reviewer's probes run against **both** readers, in `tests/test_evidence_reader_r7.py`. Each case below is validated by policy `.1` and refused by `.2`.

## Validation policy .2

| Reviewer probe | Policy .1 | Policy .2 | Rule |
|---|---|---|---|
| `ABC-123` "supported" by page text `ABC-1234` | validated | **candidate** | Support is a whole-token match with identity boundaries (`A-Z0-9&/._-`), not a substring. |
| `AB-SD-1235` against OCR `AB-SD-1234` | validated (`ocr_near`) | **candidate** ("only a near match") | A one-character near match is evidence for a candidate, never support. |
| Revision `12` supported only by `Date 12/09/2026` | validated | **candidate** | A match inside a date span is not support. A revision inside an identity (`AB-12-R3` for `3`) isn't either. |
| A lone blind approval with empty printed options | validated | **candidate** | A decision needs discovery and a blind reading that agree; a marked option on the form's printed legend; one evidenced consultant or client actor; and a target component. |
| Discovery says consultant, blind says contractor | validated | **candidate** ("the readings disagree on who marked it") | Actors must agree and be consultant or client. |
| Escalation: discovery `X-SD-1`, two blind reads `X-SD-2` | validated (the last two readings only) | **conflict**, with every reading and candidate kept | The verdict is over all readings; no subset. |
| BOQ quantity `1.5` against `15` | validated | **conflict** | Numbers keep their decimal, sign and unit. `1,5` and marks such as `\| 15` are *unresolved*, not guessed. |

Further contracts:
- **Region-bound support.** The source text is only the page's text layer inside the area the blind reader saw (`crop_clip`), plus the title-block OCR words whose boxes lie inside it. Nothing from elsewhere on the page counts. On a scanned page with no boxed OCR there is no support, so the result is at most a candidate.
- **Literal and normalised values** are stored apart (`value_literal`, `value_normalized`). Identities, parts and revisions compare as printed, ignoring only whitespace: `PT-1S` is not `PT-1S+`, and `0012` is not `12`.
- **Decisions map only through the printed legend.** A marked code `B` becomes ANN only because the form prints "B = NO OBJECTION AS NOTED". A code not on the legend maps to nothing. Receipt stamps and compliance words ("Comply", "RECEIVED") are `not_a_decision`, not a conflict.
- **Own and referenced identities.** Discovery's `other_numbers` become separate observations (`role` listed_item, referenced_drawing and so on; `state: observed_reference`, component `refN`). They are never the page's own identity. A role mismatch against the deterministic value is kept as a conflict, with the role noted; it is not resolved by majority.
- **BOQ rows** keep `part` and `quantity` verdicts apart:
  - `validated` only when both are verified;
  - `part_verified_quantity_unverified` otherwise;
  - `conflict` when either disagrees.

  A count printed in the blind description as "( n )" is a located quantity fact (`quantity_source: description_count`).

### Replay of the stored real-model readings under .2

`scripts/replay_policy2.py` makes no model call. It re-validates every stored reading (discovery, blind, escalated) of the review 06 AI-EV1 and AI-EV2 runs. Support is rebuilt from the staged PDF inside the stored read region, plus the EV0 run's cached title-block OCR boxes.

A replay can re-evaluate a policy. It cannot stand in for a changed prompt or model: discovery's referenced identities were not stored by `.1`, so the own/referenced split cannot be replayed.

State transitions (`evidence/replay-ai-ev*-transitions.json`):

| Variant | Loosened by .1, now stricter | Now validated under .2 |
|---|---|---|
| EV1 | identity validated→candidate 3, validated→conflict 1; revision validated→candidate 16; decision validated→candidate 2; decision conflict→not_a_decision 2 ("Comply") | revision candidate→validated 4 (support now found in region-bound OCR boxes) |
| EV2 | identity validated→candidate 3, validated→conflict 2; revision validated→candidate 14; decision validated→candidate 1 | revision candidate→validated 11 |

Scores are in EVALUATOR.md (`r7-replay-*` rows):
- introduced AI errors 1 (eligible set) and 0 (EP-29076);
- EV1 on EP-29076 evidence-layer decision recovery stays at 0.750, with precision 1.000 (0.857 under `.1`).

## Evidence lifecycle

`merge_evidence`, `current_evidence` and `evidence_stage`.

- **Shape.** `extracted.ai_evidence` is `{envelopes, current_key, attempts, superseded}`.
- **Envelopes.** One per `profile|variant`: default/promoted and EV1/EV2 are separate axes. Each carries `read_sha256` and `pages`. Every page has its own **provenance**: attempt number, reader version, policy, prompts, models returned, profile, variant, source hash and time.
- **An attempt changes only the pages it read completely** (`evidence` or `no_components`). Every other page keeps its last-good evidence, with its own provenance and without being restamped. A **failed, timed-out, partial or budget-stopped** attempt changes no evidence. The attempt is kept in `attempts` (the last 12).
- **Changed bytes.** An envelope read from other bytes is marked `stale`. It is never current, and it is kept whole in `superseded` (the last 4).
- **Legacy.** A review 06 flat envelope becomes one envelope with its recorded provenance; a missing profile stays **unknown** (`None`), never assumed.
- **Profile binding.** `evidence_stage(profile=...)` defaults to `document_control.extraction_profile()`, and `document_processing` passes it explicitly. It reaches `EvidenceRun.profile`, the request cache key context, the observations and the envelope.
- **Coverage outcome.** It is `partial` when any page failed or stopped on budget. It is never `complete` in that case.

Tests (`tests/test_evidence_reader_r7.py`, 36 tests; `tests/test_evidence_reader.py`, 21 tests):
- failed and budget-stopped attempts keep last-good evidence, and the provenance is per page;
- changed bytes give stale, then a fresh envelope, with `superseded` kept;
- profile and variant axes stay separate, and a policy change does not restamp retained pages;
- a legacy envelope keeps profile unknown;
- the stage binds the actual profile into the cache key: the other profile has no cache hits, while **duplicate content** under the same profile does;
- **resumed work** replays page 1 from the cache and reads page 2;
- records, mirrors and row status are untouched throughout.
