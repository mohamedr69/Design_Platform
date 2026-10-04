# Post-run adjudication notes (proposals only)

**This section cannot change the experimental score.** Every number in [FINAL-EXPERIMENT-REPORT.md](FINAL-EXPERIMENT-REPORT.md), [ARM-COMPARISON.md](ARM-COMPARISON.md) and the JSON outputs uses the frozen labels r26.2, bound by hash in declaration `6c0189b3…`. Those labels were re-checked before every dispatch and after the run. Nothing below was applied.

Any change would need four things:
1. a new label version;
2. a new declaration;
3. a separate re-score, labelled as post-hoc;
4. independent review.

The notes below were written after seeing results. Treat them accordingly.

## 1. D26 page 2 revision, the L2 critical acceptance

- **Frozen truth:** D26 is the CCTV specification control. Its confidence is medium, and it is on the uncertainty list. Pages 2 to 4 are labelled no-record by a declared convention: "continuation pages whose running header / footer repeat the section number and revision; labelled no-record". The uncertainty file states that a reader emitting the running-header values on pages 2 to 4 is scored by the no-record rule.
- **Frozen scores:**

| Arm | D26 p2 revision value | State | Frozen outcome | Evaluator association |
|---|---|---|---|---|
| L1 | "Rev. 00 – Sep. 2018" | held | held on a no-record page | negative page |
| L2 | "00" | validated | **false positive, critical** | negative page |
| L3 | "00" | held | held on a no-record page | negative page |
| L4 | "00" | held (conflict) | held correct | **cross-page**, to the page-1 record |

- **Observation:** The value "00" is printed on page 2 in the running footer, at region [428, 741, 533, 752] pt in L2. It is the section's real revision. The frozen convention treats it as no-record, so the L2 score is correct under the declared rules. Separately, the frozen evaluator associated the same emission differently in L4 than in L1 to L3. As a result, an identical value earns a critical, a held-on-negative or a held-correct outcome.
- **Proposal for the reviewer:**
  - Keep the frozen score.
  - Decide whether a later label version should record running-footer revisions on continuation pages as their own class, such as "repeated running header". That would avoid both a false positive and a credited recovery.
  - Examine why the evaluator's cross-page association applied in only one arm.
  - Neither item is applied here.

## 2. D03 page 1 identity, the L4 critical acceptance

- **Frozen truth:** D03 is the Eaton specifier's guide and datasheet. Its confidence is medium, and it is on the uncertainty list. By a declared convention, manufacturer product and catalogue codes are not the document's identity, and no page has an own identity.
- **What happened:** In L4, a targeted read with reason "unexplained empty document" returned the section heading "2.4 Accessories". The reader validated it.
- **Proposal:** None. "2.4 Accessories" is a section heading, not a product code, so it is wrong under any reasonable interpretation. The critical acceptance stands as a genuine error introduced by a targeted read.

## 3. Correct targeted values held behind a wrong first value

These cases appeared in L3 and L4:
- **D04 p1:** truth "17"; the first reading was "FA-101-106" or "FA-101-10"; the targeted read gave "17".
- **D06 p1:** truth "DCH-M-BSB-DWG-ZZ-ARC-41034"; the first reading was "ARC-41034"; the targeted read gave the full number.
- **D12 p1:** truth "BH2031_DIB_AMB_ID_MAIN"; the first reading was "BH2031_DIB_AMB_ID"; the targeted read gave the full value.

The frozen outcome is held wrong in each case.

- **Labels:** No label question arises for D06 or D12.
- **D04:** The form's own number "17" against the referenced drawing "FA-101-106" is the label's documented choice. The reviewer may confirm it.
- **Proposal:** No label change. This is a reader-design finding. The conflict rule keeps the earlier reading as the held value, even when the independent targeted reading agrees with the source text and the truth. Any change belongs to a future, separately reviewed reader version, not this experiment.

## 4. Wrong absences on consultant decisions

- **The cases:** D16 p1 in L1 and D18 p1 in L3 were scored "absent by discovery". Both pages carry a labelled "approved as noted" decision outside the title block.
- **Effect on the gate:** The coverage contract counts a discovery absence as usable coverage, so the predeclared ROI gate credits these wrong absences.
- **Proposal for the reviewer:** In a future gate version, count only completed reads, or verified absences where the truth has no decision, as decision coverage. The final report shows both counts. The frozen gate result is unchanged.

## 5. Smaller literal-form questions

The frozen scores are unchanged for each of these.

- **D22 p2 identity in L4:** "MEC/SD/PR56/0284 Rev. 00" against "MEC/SD/PR56/0284". The emitted literal includes the revision text. It stays held wrong.
- **D19 p2 identity:** "DJ-295-P-EN-SFD-01-ASY-00" against "…-ASY-0001-00". This is a truncated read in every arm, and it stays held wrong.
- **D15 revision:** The title-block reading "00" against R1 is a deterministic error, present in every arm including A. It stays as scored.
