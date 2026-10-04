# M2 Round 2: selection plan, cohort inventory and freeze manifest (Review 06, §7)

**Status: selected and frozen at project level only.**
- Nothing new has been staged, labelled or run.
- No content of any new project has been read; only metadata (directory entries, sizes and file attributes) was used.
- The sealed cohort is listed and frozen here but will not be read until the candidate is frozen.

## Allocation

The reviewer's option to exceed 30 projects is taken, so that 10 exploration projects are kept.

| Cohort | Projects | Status |
|---|---|---|
| Regression / exposed | **14** | The 10 Round 1 pilot projects, plus the **4 Review 05 holdout projects, now exposed**. They never count as unseen again. |
| Exploration (new) | **10** | New projects. Candidate development and source-backed correction happen here. |
| Sealed validation (new) | **10** | New projects. Read only after the freeze. |
| **Total** | **34** | 34 distinct EP numbers. |

## Selection method

The method is reproducible: `evidence/round2/select_round2.py`, SHA-256 `f936372d…`.

- **Seed:** `m2-round2-2026-09-28`.
- **Archive root:** `C:\Users\moham\Juma Al Majid\SSD FIRE ALARM PROJECTS - Fire Alarm 2021 Projects`.
- **Population:**
  - 1,620 folders, 831 distinct EP numbers.
  - Eligible: **808** distinct EP numbers across **246** contractor containers.
- **Exclusions:**
  - 595 folders with no EP number;
  - 7 EP numbers found only in non-project containers: Catalogues, Maintenance, Authority Guideline, Systems, SPL Calculation, the IT Division folder, and Kuthup files;
  - the 14 exposed projects.

  121 EP numbers span several folders. For those, the project is its EP number with **all** of its folders, so two folders never count as two projects.
- **Stratum:** the contractor container.
  - Contractors are shuffled with the seed, and one project is taken per contractor per round.
  - A project needs at least 5 PDFs. Two draws were rejected for having fewer: EP-29021 (4 PDFs) and EP-31096 (3 PDFs).
- **Cohort split:** a second seeded shuffle (`seed + ":cohort"`): the first 10 go to exploration, the next 10 to sealed.

## New projects

PDF and Word counts come from metadata. "Not local" counts OneDrive placeholders that are not hydrated. Reading them downloads them; they are staged through the approved workflow only.

| Cohort | EP | Contractor container | Folders | PDF | Word | Not local |
|---|---|---|---|---|---|---|
| exploration | EP-23323 | Amana Steel | 2 | 864 | 54 | 1,891 |
| exploration | EP-17428 | Al Arabia EMW | 1 | 897 | 91 | 2,521 |
| exploration | EP-28745 | Proton EMC | 1 | 36 | 13 | 51 |
| exploration | EP-26208 | AKKA | 1 | 542 | 63 | 2,148 |
| exploration | EP-19144 | Trinity | 1 | 45 | 9 | 76 |
| exploration | EP-27421 | Jumeirah Beach Building | 1 | 56 | 5 | 110 |
| exploration | EP-23091 | Al Shola Al Modea | 1 | 58 | 20 | 80 |
| exploration | EP-30549 | Dutco Construction | 1 | 43 | 2 | 67 |
| exploration | EP-16830 | Al Yunbou Technical | 1 | 357 | 127 | 579 |
| exploration | EP-22510 | Al Haditha | 1 | 35 | 7 | 45 |
| sealed | EP-19245 | Adelte | 1 | 21 | 8 | 31 |
| sealed | EP-29648 | Trikon | 1 | 46 | 9 | 86 |
| sealed | EP-18196 | Al Futtaim Group | 1 | 32 | 16 | 52 |
| sealed | EP-17323 | Al Arabia (Al Shirawi Project) | **9** | 361 | 135 | 900 |
| sealed | EP-25651 | Gulf MEP | 1 | 834 | 76 | 1,953 |
| sealed | EP-27092 | Sharjah Broadcasting Authority | 2 | 46 | 2 | 71 |
| sealed | EP-29343 | SME EM LLC | 1 | 975 | 9 | 2,003 |
| sealed | EP-27519 | Artic | 1 | 46 | 6 | 84 |
| sealed | EP-13705 | ADC Energy | 1 | 122 | 41 | 181 |
| sealed | EP-31441 | Shreeji Electrical & Fixture | 1 | 34 | 7 | 42 |

Available PDFs: exploration **2,933**, sealed **2,517**. The 450 + 450 distinct-content document targets are reachable by inventory. Content deduplication cannot be computed until staging, and it may lower the counts.

### Risks recorded before any reading

- **EP-17323 (sealed)** spans 9 folders. Project identity must be verified at staging; if they are different projects, the next seeded draw replaces it, and that is recorded.
- **EP-18196 (sealed)** shares its contractor container, Al Futtaim Group, with the exposed EP-19138. Its layout families may be familiar, so they will be reported as *familiar-template*, not unseen. Likewise EP-17428 (exploration) shares Al Arabia EMW with the exposed EP-29076.
- **Large projects** (EP-23323, EP-17428, EP-26208, EP-25651, EP-29343) would dominate their cohorts. The frozen per-project quota rule is to cap each project's contribution so that no project exceeds 20% of its cohort. Small projects are inspected in full.
- **Template families are unobserved.** They are recorded at staging, before predictions are read.

## Freeze manifest

| Item | Hash / value |
|---|---|
| `ROUND2-SELECTION.json` | SHA-256 `5437e16449ece38c8b169dc26416521bb5ed576c953d56df76317fe0694ca3a7` |
| `select_round2.py` | SHA-256 `f936372d523bc233864245a92196d8574c8e0652ce045271b9bb8207de307e99` |
| Evaluators | `FREEZE-evaluators.json` (document .4, BOQ .3) |
| Candidate | not frozen for sealed use: M2 remains CHANGES STILL REQUIRED (see REVIEW-06-REPORT §Blockers) |

## Shortfalls and what blocks Round 2 scoring

1. **Independent source labels.** None exist yet for the 20 new projects. The instructions require labels made from source renders without consulting predictions, plus a **second independent source review** of:
   - all decision labels;
   - all critical disagreements;
   - all ambiguous identity, revision and part cases;
   - a seeded 20% of the rest.

   The policy says gold truth may not be "generated or approved solely by another model". The owner, or a reviewer the owner appoints, has to provide the second review. **This is a blocker; it is not waived.**
2. **Staging** of the exploration cohort through the approved workflow is not yet done, so content hashes, deduplication, template families and the document-level manifest do not exist yet. The sealed cohort is staged only after the candidate is frozen.
3. **BOQ, 40 sheets across at least 15 projects, at least 10 of them sealed.** Sheet availability in the new projects is unknown until staging. It is reported as a shortfall until inventoried.
4. **AI eligibility.** None of the 20 new projects is registered in the application, so none has a recorded `ai_policy`. Real-model runs on them need the owner's policy decision per project (see REAL-MODEL-RESULTS). Without it, the Round 2 AI variants cannot be evaluated on new data.
