"""Label version r15.1 = r14.1 + EXPLICIT states on every small-batch `supported_observations` entry, assigned by the
amendment UNIT that created it (never parsed from its free text). r14.1 is read (hash-checked) and not modified.
  role_state        : revision | footer_control_candidate_held
  association_state : no_target | proposal_only
  association_target: the proposed target literal, only for a proposal (the page-1 cover of the calculation)."""
import copy
import hashlib
import json
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x")
SRC = W / "labels/r14/SMALL-BATCH-LABELS.amended-r14.1.json"
SRC_SHA = "f6be1f13f170a13d8e779d9542d624a415b8027fc3ee202c25d3984058eede87"
assert hashlib.sha256(SRC.read_bytes()).hexdigest() == SRC_SHA
STATES = {  # amendment unit -> explicit states
    "SB/535ffbdabfcf/u1": {"role_state": "revision", "association_state": "no_target"},
    "CRIT/1": {"role_state": "revision", "association_state": "no_target"},
    "CRIT/4": {"role_state": "revision", "association_state": "no_target"},
    "CRIT/2": {"role_state": "revision", "association_state": "no_target"},
    "SB/d8ba80a74660/u6": {"role_state": "footer_control_candidate_held", "association_state": "no_target"},
    "CRIT/3": {"role_state": "revision", "association_state": "proposal_only", "association_target": "DCH-M-MHT-CAL-IFC-ELE-0001-00"},
}
lab = json.loads(SRC.read_text(encoding="utf-8"))
out = copy.deepcopy(lab)
n = 0
for d in out["documents"].values():
    for obs in (d.get("supported_observations") or {}).values():
        for o in obs:
            o.update(STATES[o["r14_review"]["unit"]])
            n += 1
out["r15_states"] = {"version": "r15.1", "derived_from": {"file": SRC.name, "sha256": SRC_SHA}, "rule": __doc__, "observations_with_states": n}
p = W / "labels/r15/SMALL-BATCH-LABELS.amended-r15.1.json"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(n, "observations; sha256", hashlib.sha256(p.read_bytes()).hexdigest())
