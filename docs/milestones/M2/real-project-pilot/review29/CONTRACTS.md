# Review 29 contracts

These contracts were written and hash-frozen before any candidate code changed. The freeze log is `logs/CONTRACT-FREEZE.json`.

They govern four independent switches in the isolated candidate `C:/t/iso/cand-r29`, branched from `719e8de`. Each switch has its own environment variable, and each one appends its own suffix to the reader and/or policy identity. Those identities are bound into every cache key and every attempt. Switches never imply one another. Three switches require the required-first scheduling to be set explicitly, and they refuse to start without it, so no scheduling behaviour is attached silently.

| Switch | Variable | Identity suffix | Requires |
|---|---|---|---|
| Identity role guard (IG) | `AI_EVIDENCE_IDGUARD=1` | policy `+identity-role-guard-2026-10-02.1` | none |
| Conflict adjudication (CA) | `AI_EVIDENCE_ADJUDICATE=1` | policy `+conflict-adjudication-2026-10-02.2` (revision 1) | `AI_EVIDENCE_SCHEDULING=required_first` |
| Decision-region path (DR) | `AI_EVIDENCE_DECISION_REGION=1` | reader and policy `+decision-region-2026-10-02.1`; prompt `locate_decision` | `AI_EVIDENCE_SCHEDULING=required_first` |
| Page association invariant (PA) | `AI_EVIDENCE_ASSOC=1` | policy `+page-association-2026-10-02.1` | `AI_EVIDENCE_SCHEDULING=required_first` |

With all four off, `READER_VERSION`, `EVIDENCE_POLICY_VERSION` and `PROMPTS` equal those of `719e8de` byte for byte, and so does the reader's behaviour.

Shared vocabulary:
- **Own-identity label cue:** a printed label naming the document's own number. Examples are DRAWING / DWG / DRG NO, DOCUMENT / DOC NO, SHEET NO, SUBMITTAL NO, TRANSMITTAL NO, REVIEW NO / REFERENCE, and CLIENT / MUNICIPALITY / CONSULTANT DRAWING NO.
- **Reference label cue:** a printed label naming some other number. Examples are DWG REF, REF DWG, REFERENCE DRAWING, DRAWING REFERENCE, PROJECT NO / CODE, CONTRACT NO, JOB NO, PLOT, BILL NO, FORM NO, TEMPLATE, SPEC / SPECIFICATION REF, PO NO.
- **Non-own discovery role:** an `other_numbers` role other than own: referenced_drawing, listed_item, form_template, revision_history, quoted_reference or project_or_contract. A targeted read may also report its role as referenced_identity, template_or_form_code, date or other.
- **Source-bound:** the literal occurs as a whole token, under the existing `region_support` boundaries, in the text layer or OCR of the region the reading was made from.

## C1. Identity role guard (IG)

**Scope:** the own identity verdict of every page, in every reader path, through `validate_value(field="identity")`.

**Structural classes.** These are deterministic. They come from the literal, the readings' printed labels, the field region's geometry and discovery's `other_numbers`. They never come from a format whitelist.

| Class | Condition |
|---|---|
| S1 revision_token | the literal is a bare revision token, using the existing pattern |
| S2 structural_heading | after removing one leading word equal to a reading's printed label, the literal begins with a clause number followed by a word of three or more letters. A clause number means dotted digits, optionally in parentheses, or PART / SECTION / CLAUSE / ARTICLE / APPENDIX / ANNEX / CHAPTER plus a number. The class also applies when the remainder holds two or more plain words, meaning letters only and three or more letters each. |
| S3 generic_label | the literal consists only of plain words from the closed list of generic discipline and document-type labels in `GENERIC_LABELS` |
| S4 running_header_footer | the page is not a drawing sheet (`title_block.is_drawing_sheet` is false), and the field region lies wholly inside the top or bottom 10% of the displayed page height |
| S5 reference_role | a reading of the literal carries a reference label cue, discovery lists the literal under a non-own role, or a targeted reading reports a non-own role for it |

**Lift (S2 to S5 only, never S1).** A class is lifted only by independent evidence of the exact own-identity role. Two or more readings from distinct sources must carry this literal with an own-identity label cue, the literal must be source-bound, and no reading of it may carry a reference label cue. A model's role claim is not a printed label and never lifts a class by itself. This applies to the targeted read's `role` field too.

**Effect.**
- The observation is kept, with its field identity, component own, value, region and readings.
- Its state is `candidate`, which the evaluator counts as held.
- It carries `guard` (the class), `guard_reason` and `guard_evidence`.
- The page's own identity is then **not** established: no dependent fact gets a target from it, and no targeted read is made for it.
- Nothing is discarded or reinterpreted as another role.

**Positive controls.** These must stay unguarded when their evidence is otherwise good. Short or unusual real identifiers: `17`, `3561`, `0284`, `101`, `A1`, `X`, `FLS-107`, `SK-01`, `E-101`, `28 20 00` (label SECTION), `EP-23091/AS/MS-EM /101`, `TES/1343/NTH-MID-3B/SD/TEL-04`, `BH2031_DIB_AMB_ID_MAIN`, `DCH-M-BSB-DWG-ZZ-ARC-41034`, `MEC/SD/PR56/0284`, `ID-01 / ED-01`, `DJ-295-P-EN-SFD-01-ASY-0001-00`. A form number in the top band of a form is also a positive control when its own label, for example DOCUMENT NO., is read twice.

**Negative controls.** `2.4 Accessories`, `1.1 Summary`, `PART 1 GENERAL`, `Section 28 20 00 Video Surveillance System` (outside its label), `ELECTRICAL`, `GENERAL NOTES`, `Rev. 0`, `REV 01`, `R1`, a footer code in the bottom band of an A4 page, and a value read under the label `Dwg. Ref.`.

## C2. Conflict adjudication (CA)

**Scope:** an identity or revision verdict in state `conflict`, after every reading of that page's field exists, including a targeted read when one is made (`_finish_page`).

**Readings.** These are discovery, blind_small, blind_standard and blind_context, plus the deterministic value. Each reading keeps its own printed label, role, legibility and the source texts of the region it was made from. A discovery reading is bound to the region the primary read used.

**Evidence for a distinct literal V.** The literal key of V is matched, upper case with whitespace ignored, as before.

| | Condition |
|---|---|
| E1 legible | at least one legible reading of V |
| E2 own role | at least one reading of V has an own-identity (or own-revision) label cue, or is a targeted reading reporting `own_<field>`. In addition, no reading of V has a reference label cue, and discovery does not list V under a non-own role. |
| E3 source-bound | V is source-bound in the region of at least one of its readings |
| E4 independent support | **revision 1:** at least two distinct model readings of V, from distinct sources, at least one of them blind (blind_small, blind_standard or blind_context). The source text is required separately by E3 and never counts as a support. |
| E5 target (revision only) | the page's own identity is established, validated and unguarded, on the same page |

**Disqualification of a competing literal W.** W is disqualified when either:
- (a) W has a role contradiction: a reference label cue on a reading of W, discovery listing W under a non-own role, or a targeted reading reporting a non-own role for W; or
- (b) W is not source-bound in any read region on the page while V is.

**Resolution.** V resolves the conflict only when all of these hold:
- V meets E1 to E4, plus E5 for a revision;
- every other literal, including the deterministic one, is disqualified;
- no other literal also meets E1 to E4.

The verdict is then **recomputed by the unchanged `validate_value` over V's readings only**, with the source text of V's supporting region. Acceptance therefore still needs a legible blind reading, region support and no undisqualified deterministic contradiction. The losing readings stay on the observation under `superseded`, each with its disqualification, and the resolution is recorded under `adjudication`.

**Otherwise** the state stays `conflict`, with every candidate and the conditions that were not met recorded.

**Never used:** the order or recency of readings, agreement with any label, model confidence, the length of a literal, or "the longer value contains the shorter".

**Expected shapes.** These come from synthetic fixtures built from structure, not from copied expected strings.
- **D04 shape:** a form number is read by discovery and a targeted read under its own label, and is source-bound. The first blind read gave a referenced drawing number under a reference label, which discovery lists as referenced_drawing. The form number resolves.
- **D12 shape:** the first blind read is a truncation that is not source-bound, while the full number is source-bound and read twice. The full number resolves.
- **D06 shape:** two different own-labelled numbers, client and municipality, are both source-bound. The conflict stays held.

## C3. Decision-region coverage (DR)

1. **Title-block discovery is limited to identity and revision.** With ROI on, the located discovery's decision outputs are ignored for decisions, and decisions come only from the DR path.
2. **Decision signal.** Whole-page discovery may report printed options, a marked option, a decision region, or a mark type other than `none`. Any of these means a decision block may exist, and it must be read. It is never absent. When there is no readable region, the outcome is unknown.
3. **Candidate regions, bounded.** There are three sources:
   - (a) whole-page discovery's decision region;
   - (b) a deterministic search of the page's text layer and cached OCR lines for decision vocabulary outside the title-block zone, clustered into regions: APPROVED, NO OBJECTION, REVISE, RESUBMIT, REJECTED, AS NOTED, STATUS, CODE A/B/C/1/2/3, REVIEWED;
   - (c) when (a) and (b) give nothing and the page has no full text coverage, or discovery was a located crop, one `locate_decision` request on the whole page, which returns at most two regions with its own reading.

   At most two candidate regions are read per page. Everything stays inside the existing per-document request cap.
4. **Reads.** Each candidate region gets a blind `read_decision` at pad 0.15. When that read reports a marked option, the same region gets a second independent read with a wider crop at pad 0.35, as source `blind_wide`.
5. **Acceptance is not weakened.** `validated` requires all of the following:
   - two or more readings from distinct sources agree on the marked option;
   - it maps through a printed legend in those readings to a decision;
   - receipt or compliance words are no decision;
   - the actor is consultant or client in every reading;
   - the target is the page's own identity, established on the page.

   Disagreeing marks give `conflict`, which is held. Anything short of this is `candidate`.
6. **Absence.** `absent_by_discovery` is allowed only when three things hold: whole-page discovery completed with no decision signal, the deterministic search found no candidate, and the page has full text coverage. Every other case gives **`incomplete:decision_unknown`**, never absent. That includes a crop that did not include a possible decision region, a scan without text coverage, and a failed or refused locator or read.

**Expected shapes.**
- **D16 / D18 shape:** a scan with a stamp and an unclear mark reported by discovery is read. If it is not read, it is unknown, never absent.
- **D17 shape:** a handwritten code is read twice and mapped through the stamp's printed legend.
- **Other shapes:** rotated pages, a no-decision control, a receipt stamp, and conflicting marks.

## C4. Page and target association invariant (PA, and evaluator .10)

**Reader (PA).**
- **A1:** every own observation records `page_binding = {page, basis}`.
- **A2:** a dependent fact (revision or decision) of page p binds only to an identity established on page p. That means a validated, unguarded own identity read on p, or the deterministic identity of p. Without one, the fact is held, with `association = {"status": "held:no_page_target", "candidates": [...], "reason": ...}` and **no target**. It earns no recovery credit.
- **A3:** the reader never binds a fact to another page's identity. It produces no document-level association.

**Evaluator `m2-pilot-eval-2026-10-02.10`** (a new file; `.9` is unchanged and is still reported).
- **A4:** association is decided per fact. On a no-record page, only an asserted **identity** fact that is a copy of the document's identity on another page associates cross-page, which is the `.6` rule kept. A dependent fact in the same group is judged on its own page: false positive if asserted, held on a no-record page otherwise. It never inherits a component because the group's identity matched one.
- **A5:** a held fact with a `held:*` status and no target never associates.
- **A6:** a fact's outcome depends only on its own value, state, page, page binding and the frozen labels. It never depends on whether another fact of its group was asserted.

**Document-level association** is allowed only for copies of the document's identity on no-record pages (A4). No dependent fact crosses pages.

**D26 shape.** The same page-2 revision observation from a running footer scores identically however page 2's identity was emitted: held on a no-record page when held, and a false positive only when it is itself asserted. Under PA it is not asserted without a page-2 target.

## Configurations

| Name | Switches |
|---|---|
| accepted baseline | evidence reader off (`3d5607d` path; arm A) |
| reference evidence bases | the frozen L1 / L2 / L3 / L4 switch sets (G, Rsup, required-first, deadline, and ROI / X as declared) |
| identity guard only | reference base + IG |
| conflict adjudication only | reference base + CA |
| decision-region path only | reference base + DR |
| association invariant only | reference base + PA |
| combined candidate | L3 switch set (G, Rsup, required-first, deadline, X) + IG + CA + DR + PA; ROI off |

ROI is off in the combined candidate. Under C3.1 title-block discovery gives no decisions, and the ROI gate failed by rule in the final experiment. This choice is a candidate under test, not a default.

## Revision 1 (C2), after the offline regression

The flags-off replays and the first CA replay of L1 ran under the contract as first frozen (`logs/CONTRACT-FREEZE.json`). That replay found two **new false acceptances**: D12 page 1 and D19 page 2, D19 being a resolved label. In both cases the page's text layer breaks a long number across lines. The truncated first blind read is then a whole token in the source text, and the full number read by discovery is not. Under the first E4, the source text counted as the second support of a single blind reading, so a truncation was validated.

Revision 1 changes E4 only. Two distinct model readings must agree, and the source text is required by E3 but never counts as a support. The policy identity becomes `conflict-adjudication-2026-10-02.2`, so no cached or stored `.1` answer or attempt is reused. Every other clause is unchanged.

This revision was written after seeing the regression and before re-running anything. Its freeze is `logs/CONTRACT-FREEZE-R1.json`. The first version's failure is reported in OFFLINE-REPLAY.md and is not hidden.

Expected shapes under revision 1:
- **D04:** resolves, because discovery and the targeted read agree under the own label and the competitor has a reference role.
- **D06:** held.
- **D12 and D19 split-text shapes:** held. A single blind reading never wins.

## Revision 2 (C1 scope), after the combined replay

The combined replay (IG + CA + DR + PA on the L3 and L4 bases) showed an interaction on the D04 shape. The primary blind read lands on a referenced drawing under a reference label, so the verdict is a `conflict`. IG then guarded the conflict's provisional value, the first blind reading. Under C1's effect clause, that suppressed the targeted read, which was the independent second reading C2 needed. The conflict stayed held, which was safe but needlessly unresolved.

**Clarification (C1 scope).** The guard applies to a single-literal verdict, validated or candidate. A `conflict` verdict is already held, establishes no identity and asserts nothing. It keeps all its readings, and its targeted read is not suppressed. The guard applies to the field's **final** verdict: after the targeted read, which recomputes it, and after any C2 resolution, which `_adjudicate_page` guards. Nothing a conflict holds can be accepted without passing the guard. This is the only change. The policy identity becomes `identity-role-guard-2026-10-02.2`. The freeze is `logs/CONTRACT-FREEZE-R2.json`, written before the code change.
