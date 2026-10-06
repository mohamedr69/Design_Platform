# Evidence criteria written before reading the records (verifier, 2026-10-06)

Gate clause 1 "every critical fact/artifact has exactly one authoritative owner":
 - each delta row has a non-empty current owner (or explicit NOT_IMPLEMENTED/none) and where >1 writer exists the row says which is authoritative or links to a conflict id.
 - a definition of "critical" (or all rows treated as critical).
Gate clause 2 "producer and consumer contract": producer and consumer columns filled with file:line; for artifacts, capability map lists producer, consumers, version/fingerprint, invalidation.
Gate clause 3 "no unresolved conflict over tab/processor/memory owner": either (a) every conflict resolved with a decision, or (b) the conflict list is complete, each with candidate owners, evidence, and an explicit assignment to M3 with an owner-decision note; record must NOT claim gate met if (b).
Gate clause 4 "do not redo accepted audit wholesale": delta is additive; accepted files unmodified (git diff empty); drift listed per accepted row.
Deliverable matrix: CSV 173x22, same header, no id collision, file:line evidence each row, status vocabulary consistent with accepted.
Deliverable capability map: stages vs section 5 contract; claims sample-checked.
Deliverable protected behavior list: override writers with file:line; weakness tags supported by survey cells.
Deliverable traceable changes: per-accepted-row drift list referencing accepted field_ids; model coverage table.
GET-side work: census of GET handlers count verifiable by grep; each classified; side-effect producers cited correctly (sample).
Manual-override writers: list with file:line; sample shows they write user-chosen values.
Roadmap U3 additions: compliance/workload facts present as NOT_IMPLEMENTED/gap rows with owner/producer/override writer proposed or "M3 decides".
Over-claim checks: no tests/runtime/db claimed; hashes match 771001e; frozen folders unchanged; scope only under refresh folder.
