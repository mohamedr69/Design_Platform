# DRILL-CRITERION: the pass criterion of the dry baseline-facts drill (review45), declared before the first drill run

Task R43-42 (Verification 44 option 1; A-13 item 2). Written before any drill code ran on any document; its sha256 is
recorded in the R43 session log before the first drill execution (tests included). It is never edited after that; a
changed criterion would be a new file with a new hash and a disclosure. This file authorizes nothing.

## 1. What the drill is

- Mode: `runner_r32.py run --mode dry --dry-baseline-facts SPEC.json` (review45 harness), lane B only, baseline tree
  `C:/t/iso/frozen-r13` (HEAD `7ec3d2cf983b70a604844beda8eb6b1ec6173d34`, clean), no other lane, tree or mode.
- Documents, exactly (by pool id AND staged sha256; run set `9058f3d6...7ce8`; truth `4e237a4e...e064`):

  | Pool id | Project | Staged sha256 |
  |---|---|---|
  | F009 | EP-27331 (`B01-ASC-SD-ELE-0034`) | `970ddb0f5b59199b41f33bee8356dd87418d9daff26ec9a9b8a72a3538bab415` |
  | F020 | EP-27331 (`B01-ASC-SD-ELE-0047`) | `599d36be15e6eded0fcbe4226afdb49c9b282f6bcbbd13c3c3376872da1891db` |
  | F030 | EP-27331 (`B01-ASC-SD-ELE-0052`) | `feec64cdcb0b7a95262c9991fd09830d810f88e75d87be05ac308c106047010a` |

- Path: the lane's own code (`lane_r32.py` lane B, reader `application`): `document_processing.run` with the lane's
  `process` / `read_form_or_raise` / `apply_form_reading` hooks, `row_dict`, `b_tripwire` -> `tripwire_r32.py` ->
  `lane_judge_r32` (rule CP-R38) against the resolved truth, `after_document` for every document read and `final`.
- Provider: the refusing global provider (`run_control_r38.RefusingGlobalProvider`), installed right after the
  application's provider module is imported and before any other application module; AI off (`AI_ENABLED=false`); the
  application reads deterministically (text layer and, where the application uses it, OCR by the installed Tesseract).

## 2. Definitions

- **Critical (resolved):** a critical acceptance on resolved truth as `lane_judge_r32.critical_split` returns it in
  `resolved` (an automatic acceptance, accepted or validated, that is wrong or a false positive on a scorable row), in
  any of the three fields identity, revision and decision, in ANY tripwire evaluation of the three documents
  (`after_document` or `final`).
- **Unresolved critical:** `critical_on_unresolved_truth` (`unresolved`). Reported only; never a stop, as in live B.
- **The v3 stop condition:** the stop controller's comparison becomes
  `INVALID: baseline incomplete (critical acceptance on resolved truth in B)`.
- **Exercised:** the document's row was read by the application in lane B (registered, processed, `extracted` not
  null) and the tripwire evaluated at least one fact of it.
- **UNREAD:** the document was not read (the staged PDF needs OCR and the environment lacks it, the application failed
  to read it, or the lane stopped before it). An UNREAD document is reported as UNREAD with the reason; it is never
  substituted, re-run with another method or skipped silently.
- **Zero requests:** the refusing global provider received 0 calls, the dry stub 0 calls, no live provider class was
  reached, no `claude` process was started, and the AI ledger (opened `mode=ro`) reads 484 / 18 / 0 before and after.

## 3. The criterion

**PASS** if and only if all of the following hold:

1. zero critical acceptances on resolved truth in identity, revision and decision, for each of F009, F020 and F030, in
   every tripwire evaluation;
2. the v3 stop condition did not fire;
3. each of the three documents was exercised;
4. zero requests.

**FAIL** if any critical acceptance on resolved truth occurs (or the v3 stop condition fires), or if any request reached
a provider. A FAIL is reported with the document, page, field, the accepted value and the truth; it is **never fixed
here** (no code, grammar, label, truth or criterion change). Any later change is a new declaration with disclosure and an
owner decision.

**NOT PASS (incomplete)** if there is no critical and zero requests, but at least one of the three documents was not
exercised (UNREAD, zero facts, or not started); the report names the document and the reason.

Unresolved criticals, the facts themselves and per-field outcomes are reported for every document whatever the result.

## 4. Limits stated before the run (they do not change the criterion)

- AI is off in the drill. If the application treats a document as a submittal form, live B (AI on) would ask the model
  for the form reading after the deterministic reading; the drill judges the deterministic reading only (the same row
  the live `after_document` tripwire judges first). The report states each document's role.
- The drill's B sandbox registers only the three documents (project EP-27331); the other run-set documents of EP-27331
  are not in it, so project-level effects of those siblings are not reproduced.
- The drill shows the baseline's behaviour on three documents of 24; it is not a result, an accuracy figure or a
  prediction, and it says nothing about lane C.
