"""Evaluator input for the page labels, DERIVED mechanically from the frozen SMALL-BATCH-LABELS.json (hash-checked,
not edited): evaluator .9 reads a null printed_revision as 'unscorable' but the literal 'absent' as a known negative
(scripts/m2_eval4.REVISION_NEGATIVE). The frozen labels already state each record's revision state in `states`; where
that state is 'absent' and the literal is null, the derived copy carries 'absent'. Nothing else changes. Found while
writing the scorer (2026-09-29), before any profile-B / C output was read; recorded in the declaration addendum."""
import copy
import hashlib
import json
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/labels")
src = P / "SMALL-BATCH-LABELS.json"
assert hashlib.sha256(src.read_bytes()).hexdigest() == sys.argv[1], "the frozen page labels changed"
lab = json.loads(src.read_text(encoding="utf-8"))
out = copy.deepcopy(lab)
changed = []
for key, d in out["documents"].items():
    for r in d["records"]:
        if r.get("printed_revision") is None and (r.get("states") or {}).get("revision") == "absent":
            r["printed_revision"] = "absent"
            changed.append({"doc": key, "page": r["page"], "field": "printed_revision", "from": None, "to": "absent"})
out["derived_from"] = {"file": src.name, "sha256": sys.argv[1], "rule": "printed_revision null + states.revision 'absent' -> 'absent'", "changes": changed}
o = P / "SMALL-BATCH-LABELS.eval.json"
o.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(changed), "records; sha256", hashlib.sha256(o.read_bytes()).hexdigest())
for c in changed:
    print("  ", c["doc"][-60:], "p", c["page"])
