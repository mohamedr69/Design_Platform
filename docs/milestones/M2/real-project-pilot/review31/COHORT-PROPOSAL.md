# Cohort proposal, Option B (metadata only, **not permitted**)

The selection was produced by `scripts/select_fresh_projects_r31.py`, using the tested rules in `scripts/selector_core.py` and the structured used sets in `scripts/used_sets.py`. The full output is in [cohort/FRESH-PROJECTS-R31.json](cohort/FRESH-PROJECTS-R31.json).

Only directory entries, file names, sizes and attributes were read. Nothing was opened, rendered, downloaded, staged or sent, and no OneDrive placeholder was hydrated.

**These projects are outside the Round 2 permission.** Downloading, staging, labelling or any provider use needs a **new written owner permission naming these EP numbers**. It has not been requested.

## Rules, fixed before the draw

1. **Topology, failing closed:**
   - A root folder is `project_at_root`, `container`, `contractor` or `no_projects`.
   - An EP folder is `project`, `project_with_nested_eps` or `nested_project`.
   - Only a plain `project` in exactly one folder is eligible. The 175 ambiguous hierarchies are excluded.
2. **Project freshness:** the EP must be absent from every used source (199 EPs), including **all 959 M1/M2 databases**.
3. **Contractor freshness:**
   - Contractor names are canonicalized and clustered by the alias rules: space-free equality, token subset, same distinctive first word, or similarity ≥ 0.85.
   - A cluster that aliases **any** used contractor is excluded. The used contractors are the 33 names plus the contractors of every used EP.
4. **Seeded order:** clusters are drawn in the order of seed `m2-r31-fresh-projects-2026-10-02`, one project per cluster.
5. **Metadata thresholds:** at least 20 PDFs, at least 5 paths with a review signal and at least 5 with a drawing signal, judged by file name only.

## Picks and alternates, with evidence

"Nearest used" is the most similar used contractor in canonical form. Every value is below the 0.85 alias threshold, and no other alias rule matched. Every listed project is a plain `project`, in one folder, absent from all used sources. The placeholder count is the number of PDFs not stored locally, which is all of them, so nothing has been hydrated.

| Role | EP | Contractor (raw → canonical) | PDFs | Review-signal paths | Drawing-signal paths | Not local | Nearest used (similarity) |
|---|---|---|---|---|---|---|---|
| pick | 3563 | Pivot Engineering → pivot engineering | 927 | 137 | 728 | 927 | ag engineering (0.759) |
| pick | 22349 | Ardh Al Kananh Building Contracting → ardh al kananh building | 130 | 7 | 80 | 130 | amana steel building (0.632) |
| pick | 27331 | Euro Gulf Technoservices LLC → euro gulf technoservices | 396 | 31 | 281 | 396 | al yunbou technical (0.513) |
| pick | 15744 | Al Abdouli Group → al abdouli | 83 | 5 | 10 | 83 | al abiya (0.625) |
| pick | 26687 | ENCO → enco | 75 | 12 | 40 | 75 | geco (0.75) |
| pick | 29255 | Scale EMC → scale emc | 844 | 118 | 211 | 844 | alemco (0.714) |
| alternate 1 | 22317 | Firepro Safety → firepro safety | 114 | 34 | 5 | 114 | fireco technical (0.429) |
| alternate 2 | 29628 | Steel Construction → steel construction | 493 | 16 | 416 | 493 | dutco construction (0.765) |
| alternate 3 | 25909 | Trojan → trojan | 721 | 30 | 470 | 721 | trikon (0.667) |
| alternate 4 | 28908 | MENASCO MECH → menasco mech | 3145 | 68 | 2966 | 3145 | emt electro mechanical (0.516) |

**Result:** six picks from six distinct, unused contractor clusters, with four alternates in seeded order. 27 clusters were reached but rejected below the metadata thresholds; they are listed in the JSON. Alternates enter only in seeded order and only when the picked projects' paths run out under the per-project caps ([FIELD-POPULATION-FEASIBILITY.v2.md](FIELD-POPULATION-FEASIBILITY.v2.md)).

## Review 30 picks, reconciled

The source is [cohort/R30-PICKS-RECONCILED.json](cohort/R30-PICKS-RECONCILED.json).

| Review 30 role | EP | Contractor | Review 31 |
|---|---|---|---|
| pick | 22936 | Al Hani Gulf | eligible, not drawn |
| pick | 19905 | ARJ Engineering | **excluded**: its cluster aliases used contractors (ag engineering, aswar engineering) |
| pick | 20561 | Binladin | eligible, not drawn |
| pick | 16385 | Venus Infrastructure | eligible, not drawn |
| pick | 29255 | Scale EMC | **selected again** |
| pick | 24752 | NOVA System | eligible, not drawn |
| alternate | 25883 | Al Ghazal | **excluded**: ambiguous hierarchy (nested EPs) |
| alternate | 19199 | MBM Gulf Electromechanical | **excluded**: ambiguous hierarchy |
| alternate | 28328 | Waagner Biro | **excluded**: ambiguous hierarchy |
| alternate | 26214 | Carawan EMW | eligible, not drawn |

## Not proposed

- **Option A, within-project:** it cannot close M2.
- **Sealed projects:** they stay sealed unless the owner separately releases them for this exact run.
