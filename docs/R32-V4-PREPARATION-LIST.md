# R32 v4 preparation list

Started 2026-10-07 under R43 task 36, step 5. A list of items the binding manifest and declaration v4 must carry or satisfy. It authorizes nothing: the binding manifest, declaration v4, its verification, the dry rehearsal and any D1 or D2 step each need the owner's separate authorization. Rows are logged in `R43-SESSION-LOG.md`.

| item | source | what v4 must do | status |
|---|---|---|---|
| V4-01 | review-43 condition C2 (`REVIEW-43-REPORT-2026-10-07.md`) | Carry `R43-RESIDUAL-F021-P4` (in `R43-REVIEW-PACKAGE`) in the declaration's disclosures or scope limitations, verbatim as to trigger and observed exposure: an F021-shaped sheet whose title block yields no number takes the first drawing-references row as its identity. | carried forward, not actioned |
| V4-02 | review-43 condition C3, closed by task 36 step 2 | Cite the R43 residuals addendum `C:/t/r2x/r42-sandbox/R43-RESIDUALS-ADDENDUM-2026-10-07.md` (F1, F2, F3; record only) beside `R43-RESIDUAL-F021-P4`. | recorded |
| V4-03 | review-43 condition C1, closed by task 36 step 1 (option 3) | Cite the ratification as **R43-35** in `docs/R43-SESSION-LOG.md`, not as "session log row 35". | recorded |
| V4-04 | review-43 finding F6; task 36 step 4 | Keep the v3 lane check in the v4 preflight: `DRAWINGS_AI_REVIEW_ENABLED=false` in every lane's environment and in the application's settings. The live installation's Drawings Assistant (`DRAWINGS_CHAT_AI_ENABLED=true` in the merged installation's environment file) is outside the lanes: the frozen and R43 trees have no such setting and no environment file of their own. | observed off in the lane; carried forward |
| V4-05 | task 35 commit record | Bind the R43 trees by commit: frozen-r13 `7ec3d2cf983b70a604844beda8eb6b1ec6173d34` (parent 3d5607d) and cand-r30 `436daef215c72fbe2429dcd783e087bf39756ad7` (parent a8aaced), patch-id `2aa4c0b7a22c9df16286337e5d92cc77379a8bc3`. | carried forward |
