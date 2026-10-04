# Cohort options (R30-03)

Neither option has been opened, staged, rendered, labelled or sent anywhere, and neither is selected. **No permission is assumed.**

## Option A: within-project confirmation

- **Pool:** previously unseen documents of the **10 exploration projects** of the frozen Round 2 selection: 16830, 17428, 19144, 22510, 23091, 23323, 26208, 27421, 28745 and 30549. The exploration selection (`review13/evidence/manifest/EXPLORATION-SELECTION.json`) lists 4,674 eligible replacement documents that were never chosen. "Unseen" means a document's path and SHA-256 appear in no staged set, label set or run sandbox.
- **Permission:** covered by the owner's Round 2 permission for the 34 frozen projects and the existing provider. The run itself still needs its own budget authorization.
- **Exposure:** **project templates are exposed.** These projects' layouts, title blocks, stamps and forms were seen in the exploration stage, the AI pilot, the continuation and the four-arm experiment, and the candidate's defects were found on them.
- **What it can show:** regression safety and within-project recovery on unseen documents only. **It cannot establish cross-project generalisation, and it cannot by itself close M2.**

## Option B: fresh-project validation

- **Selection:** metadata only, by `scripts/select_fresh_projects.py`, output [cohort/FRESH-PROJECT-CANDIDATES.json](cohort/FRESH-PROJECT-CANDIDATES.json). Directory entries, file names, sizes and attributes were read, and nothing else. Every PDF of every listed project is a cloud-only placeholder, and none was downloaded.
- **Exclusions:** every EP number referenced anywhere in the M1 and M2 documents, packages and backend tests, which is 207 numbers ([cohort/M2-USED-PROJECTS.json](cohort/M2-USED-PROJECTS.json)). That covers the 34 Round 2 projects (exposed, exploration and **sealed**), the Review 05 holdout, the pilot, the fixtures and numbers merely listed in selection records. **The 59 contractors of those projects are excluded too**, because their template families count as exposed.
- **Population after exclusions:** 544 projects from 194 contractors.
- **Draw:** seeded (`m2-r30-fresh-projects-2026-10-02`), one project per contractor.
- **Eligibility by name only:** at least 20 PDFs, at least 5 whose path names a review or approval signal, and at least 5 whose path names a drawing signal.

| Role | EP | Contractor | PDFs | Review-signal paths | Drawing-signal paths |
|---|---|---|---|---|---|
| pick | 22936 | Al Hani Gulf | 1,319 | 250 | 574 |
| pick | 19905 | ARJ Engineering | 629 | 38 | 312 |
| pick | 20561 | Binladin | 4,616 | 1,202 | 1,898 |
| pick | 16385 | Venus Infrastructure | 78 | 9 | 15 |
| pick | 29255 | Scale EMC | 844 | 118 | 211 |
| pick | 24752 | NOVA System | 92 | 16 | 39 |
| alternate | 25883 | Al Ghazal | 196 | 32 | 67 |
| alternate | 19199 | MBM Gulf Electromechanical | 1,208 | 134 | 868 |
| alternate | 28328 | Waagner Biro | 185 | 17 | 56 |
| alternate | 26214 | Carawan EMW | 369 | 34 | 89 |

That is six projects from six contractors, against the four required, and an alternate replaces a pick only under the seeded order.

**Required owner permission.** These projects are **outside** the Round 2 permission. Before any document is downloaded, opened or rendered, the owner must name these EP numbers, or a subset of at least four from four contractors, in a new written permission. The permission must cover all of the following:
- downloading the placeholders;
- staging hash-checked copies;
- independent labelling;
- sending pages to the existing evaluation provider.

**Sealed projects stay excluded.** The 10 sealed Round 2 projects are excluded unless the owner separately releases them for this exact run. The roadmap reserves them for the expanded sealed pilot after a profile is selected and frozen, and no profile is selected.

**What it can show:** recovery, precision and safety on projects and contractors the candidate was never tuned on. That is the generalisation evidence M2 closure needs.

## Recommendation

**Option B for M2 closure.** The M2 gates are at least 98% accepted precision, at least 90% recovery of readable critical fields and zero unresolved critical false acceptance. They must hold on documents whose templates did not shape the candidate. Every Review 29 fix was designed against defects observed on the exploration projects, so an Option A result is confirmation on familiar layouts. It is useful for regression safety, but it cannot separate "fixed the defect" from "fits these templates".

Option A can run under existing permission, as a smaller safety check, if the owner wants regression evidence before granting Option B. It does not replace Option B.

The evidence difference is this. Option A answers "does the candidate stay safe, and recover more, on unseen documents of the same projects?" Option B answers "does it hold on projects and contractors it has never seen?" Only B bears on M2 closure.
