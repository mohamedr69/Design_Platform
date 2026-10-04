# Reviewer packet: independent label review of `r32-labels-draft-1`

**Reviewer:** the owner-delegated independent Codex reviewer. This is an AI review, not human sign-off, unless a named human signs it.

**Drafter:** the Claude Opus 5.5 coding assistant. The draft is **AI-authored, not human-signed and not independently reviewed**. Every reviewer column is blank. The drafter has not reviewed its own draft a second time.

## What is under review

| Item | File | sha256 |
|---|---|---|
| Draft labels, frozen | [labels/R32-LABELS-DRAFT-1.json](labels/R32-LABELS-DRAFT-1.json) | `ebd1e24d943b3b7b21e96c1930bdb34a1078e4c5d70e3c4c34a258332688a334` |
| Conventions, frozen before the first label | [LABEL-CONVENTIONS-R32.md](LABEL-CONVENTIONS-R32.md) | `5c09d4d2bc0867b8af93c93cd0e67c362f96bfeed5a0c109361931ce7dd5e570` |
| Selection (72 documents, metadata only, seeded) | [FROZEN-SELECTION.json](FROZEN-SELECTION.json) | `bf71779a612afb1207ac96cb7925979ae3682ea815d137b05eab8968212a5d21` |
| Staged copies (hashes, original unchanged) | [SOURCE-MANIFEST.json](SOURCE-MANIFEST.json) | `951e8697a69c3576c24ecdaf0b28de563d35ae7e99addca1fc60e3992df0e259` |
| Renders and crops (path, sha256, recipe, binding) | [EVIDENCE-INDEX.json](EVIDENCE-INDEX.json), [RENDERS.json](RENDERS.json), [CROPS.jsonl](CROPS.jsonl) | listed in the manifest |

The evidence images stay in the isolated staging area. Renders are in `C:/t/r2x/r32-stage/renders/`, crops in `C:/t/r2x/r32-stage/crops/`, and the staged PDFs in `C:/t/r2x/r32-stage/files/`. Every path in the worklists is absolute, and every image is bound by sha256. A full render is `<pool id>-p<page>.png`, and its text layer, which was used only to locate regions, is the `.txt` file beside it.

## What to rule

1. **Page-field rulings** ([review/PAGE-FIELD-WORKLIST.csv](review/PAGE-FIELD-WORKLIST.csv), 432 rows: 144 in-scope pages × 3 fields):
   - **Ruling:** `accept`, `correct` or `reject`.
   - **On a correction:** fill the corrected state, literal, class or association.
   - **Literals:** they must match the page as printed, including punctuation and spaces.
   - **Roles:** a value must have the stated semantic role. A document's own number is not a project, job, plot or form number.
2. **Document-field rulings** ([review/DOCUMENT-FIELD-WORKLIST.csv](review/DOCUMENT-FIELD-WORKLIST.csv), 210 rows):
   - **`resolved_for_scoring`:** whether the field truth and its document or page association are resolved enough for scoring.
   - **`carries_fact`:** whether the document carries the fact.

   The population gate counts **only** these rulings.
3. **Open questions** ([review/DOCUMENT-QUESTIONS.json](review/DOCUMENT-QUESTIONS.json), 56 items). The main ones:
   - **Decision class for mixed options:** "Approved as noted / Resubmit" (F001, F017, F022, F026, F031, F033) and "Code B+Resubmit" / "B+R" (F030). The draft classes them as `approved as noted`.
   - **Authority approvals:**
     - Civil Defence approved-plans stamps (F014, F016), alongside a faint "FOR INFORMATION ONLY" status;
     - Ajman Civil Defence initial or conditional approval (F038);
     - a du "No Objection" stamp (F027).

     The draft classes them as `approved`.
   - **Register status letters:** a status letter per listed drawing on EMAAR drawing registers (F008, F013, F020, F025, F028, F030, F032, F034, F036, F037). The actor is inferred, and the association is uncertain.
   - **Revision only as a suffix:** where the revision appears only as a suffix of the document number (for example `-R00`), the association is uncertain.
   - **Compilation files:** F035 (other projects' approvals, one per page) and F069 (two quotations).
   - **Duplicates:**
     - byte-identical: F052 = F038 and F070 = F067, each counted once;
     - content-identical pages: F031 pages 1-2 = F001 pages 1-2;
     - near-duplicate exports: F046 and F059.
   - **Ambiguous or illegible fields:** F019 revision (cell 00 against table 01), F035 page 2 revision and page 3 decision, F043 annex identity, F067 authorities-approval stamp.
4. **Convention rulings:** any convention the review changes. Earlier labels are never edited; rulings go into a new version.

Return [review/REVIEWER-RESPONSE-TEMPLATE.json](review/REVIEWER-RESPONSE-TEMPLATE.json), filled in. It must name the draft sha256 and state `independent_of_drafter: true` and `predictions_consulted: false`.

## What happens next

1. **New version:** the drafter preserves the draft and applies the rulings in a new immutable version, `r32-labels-reviewed-1`, with per-ruling provenance.
2. **Gate count:** the gate counts documents ruled `resolved_for_scoring = yes` and `carries_fact = yes` for each field. Byte-identical duplicates count once.
3. **Extensions:** if any field is below 12, extension-1 (36 documents, frozen order) is drafted the same way and reviewed. Extension-2 follows only if still needed. If a field is still short after both, the outcome is PREPARATION BLOCKED.
4. **Freeze:** at 12 or more in all three fields, the cohort, labels, evidence, counts and bindings are frozen and packaged for independent preparation review.

No prediction, model request, ledger scope or budget is involved at any step.
