"""Document-level (register-layer) labels for evaluator .9's --labels input, DERIVED mechanically from the page labels
SMALL-BATCH-LABELS.json (hash-checked): page 1's own record, or 'absent'. Only `kind` is added here (the register
layer's scope rule, scripts/m2_pilot_eval.SCOPE_PREFIXES); every kind is the page-label component described in words.
Same status as the page labels: AI-drafted proposals, provisional."""
import hashlib
import json
import pathlib
import sys

P = pathlib.Path("C:/t/iso/work/r2x/labels")
src = P / "SMALL-BATCH-LABELS.json"
assert hashlib.sha256(src.read_bytes()).hexdigest() == sys.argv[1], "the page labels changed"
pl = json.loads(src.read_text(encoding="utf-8"))
KIND = {  # by sha256 prefix
    "d7ac7576420d": ("pre-qualification table of contents", "other"),
    "535ffbdabfcf": ("technical submission section dividers (method statement)", "FA"),
    "a0db0f066f4e": ("cost estimation summary (commercial, not a register document)", "SCS"),
    "0c9737211762": ("design request form (internal, not a register document)", "ELV"),
    "bdce7913eb15": ("design sheet (commercial, not a register document)", "EML"),
    "35bd128789de": ("drawing sheet of another party's approval package (structural input, not a register document)", "other"),
    "a7763559b0bc": ("technical submission (lux calculation cover)", "EML"),
    "79e7e35bd807": ("shop drawing sheet", "FA"),
    "d8ba80a74660": ("technical submission attachment (previous project reference list)", "FA"),
    "73a723f42009": ("drawing sheet of the client's architectural input (not a register document)", "other"),
    "2ddc88e23639": ("word transmittal (sample board)", "EML"),
    "2472d2cc65c3": ("consultant calculation report (input, not a register document)", "other"),
}
docs = []
for key, d in pl["documents"].items():
    kind, system = KIND[d["sha256"][:12]]
    p1 = [r for r in d["records"] if r["page"] == 1]
    r = p1[0] if p1 else None
    docs.append({"doc": key, "ep": key.split("/", 1)[0][3:], "cohort": "exploration", "stratum": d.get("stratum"),
                 "extension": pathlib.PurePosixPath(key).suffix.lower(), "sha256": d["sha256"], "confidence": (r or {}).get("confidence", "high"),
                 "labels": {"kind": kind, "reference": (r or {}).get("reference") or "absent", "revision": (r or {}).get("printed_revision") or "absent",
                            "decision": (r or {}).get("decision") or "n/a", "system": system, "register": bool((r or {}).get("register"))}})
out = {"labels_version": "r2x-register-derived-1", "derived_from": {"file": src.name, "sha256": sys.argv[1]},
       "status": pl["status"], "labeller": pl["labeller"], "documents": docs}
o = P / "SMALL-BATCH-REGISTER-LABELS.json"
o.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(len(docs), "documents; sha256", hashlib.sha256(o.read_bytes()).hexdigest())
