# Pre-read criteria (written before reading records)
Clause A "trace current findings to source hashes": each of 35 RD-M1 findings + new candidates has a current file:line; that file has a sha256 in a hash manifest recomputable from the commit (771001e == HEAD for code); line quotes match the current code.
Clause B "input/output hashes": where a finding depends on input (DWG/DXF/PDF) - either a hashed input in repo or explicit statement it's absent (GC-01 owner machine); outputs (test logs/xml) hashed or committed.
Clause C "reproduce bounded cases": a test command + committed test output (junit xml/-rA) with counts; tests exist in repo at that commit; I can rerun (if env allows) or at least verify counts.
Clause D "historical findings not treated as fixed by new UI/AI code": each finding classified with rule; FIXED/SUPERSEDED only with code evidence/test exercising corrected path; no finding closed by UI label or AI path; RD-M2 code absence noted.
Also: no claims of AutoCAD/model/DB/Golden runs; frozen folders unchanged.
