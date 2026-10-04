"""ORCH-02.1 (R32APPLY-IMPL) step 3: count the reviewed field populations.

count_population(reviewed) -> dict  (pure)
Rule: per field, the distinct documents (count-once aliases applied: an alias is mapped to the lower pool id it
counts under) whose document review has resolved_for_scoring == "yes" AND carries_fact == "yes". A document with
"unresolved" in either value is excluded and listed. upper_bound_if_resolved re-counts with every "unresolved"
value read as "yes" (other values unchanged). Gate: all three fields >= 12 -> READY FOR INDEPENDENT PREPARATION
REVIEW, else EXTENSION-1 REQUIRED (no extension is drawn here).

CLI writes fresh-cohort-r32-reviewed/FIELD-POPULATION.json.
"""
import argparse
import collections
import hashlib
import json
import os
import sys

FIELDS = ("identity", "revision", "decision")
GATE_MIN = 12
READY = "READY FOR INDEPENDENT PREPARATION REVIEW"
EXTEND = "EXTENSION-1 REQUIRED"
RULE = ("per field, count the distinct documents, after mapping each count-once alias to the pool id it counts "
        "under (byte-identical F052->F038, F070->F067; content duplicates F031->F001, F059->F046 by final "
        "convention (c)), whose document review has resolved_for_scoring == 'yes' AND carries_fact == 'yes'; a "
        "document with 'unresolved' in either value is excluded and listed; gate: identity, revision and decision "
        "each >= 12")


def _canon(reviewed, pid):
    return reviewed["count_once_aliases"].get(pid, pid)


def _count(reviewed, field, treat_unresolved_as_yes=False):
    members = set()
    excluded = []
    for pid, d in sorted(reviewed["documents"].items()):
        e = d["review"][field]
        rs, cf = e["resolved_for_scoring"], e["carries_fact"]
        if "unresolved" in (rs, cf):
            excluded.append(pid)
            if treat_unresolved_as_yes:
                rs = "yes" if rs == "unresolved" else rs
                cf = "yes" if cf == "unresolved" else cf
            else:
                continue
        if rs == "yes" and cf == "yes":
            members.add(_canon(reviewed, pid))
    return sorted(members), excluded


def _page_supports(doc, field):
    """At least one labelled page with the field present, association resolved, not excluded from scoring."""
    for pg, page in sorted((doc.get("pages") or {}).items(), key=lambda kv: int(kv[0])):
        f = page.get(field)
        if f and f.get("state") == "present" and f.get("association") == "resolved" \
                and not f.get("excluded_from_scoring"):
            return True
    return False


def count_population(reviewed):
    gate_counts, members_by_field, excluded, upper = {}, {}, {}, {}
    for field in FIELDS:
        members, ex = _count(reviewed, field)
        ub, _ = _count(reviewed, field, treat_unresolved_as_yes=True)
        gate_counts[field] = len(members)
        members_by_field[field] = members
        excluded[field] = ex
        upper[field] = len(ub)
    gate_action = READY if all(gate_counts[f] >= GATE_MIN for f in FIELDS) else EXTEND

    docs = reviewed["documents"]
    aliases = dict(reviewed["count_once_aliases"])
    canon_ids = sorted({_canon(reviewed, p) for p in docs})
    with_rulings = sorted(p for p, d in docs.items() if d["review"]["identity"]["resolved_for_scoring"] is not None)

    # alias agreement (information): an alias whose own rulings say yes/yes while its canonical does not
    alias_disagreements = []
    for a, c in sorted(aliases.items()):
        for field in FIELDS:
            ea, ec = docs[a]["review"][field], docs[c]["review"][field]
            if ea["resolved_for_scoring"] is None:
                continue
            if (ea["resolved_for_scoring"], ea["carries_fact"]) != (ec["resolved_for_scoring"], ec["carries_fact"]):
                alias_disagreements.append({"alias": a, "canonical": c, "field": field,
                                            "alias_values": [ea["resolved_for_scoring"], ea["carries_fact"]],
                                            "canonical_values": [ec["resolved_for_scoring"], ec["carries_fact"]]})

    by_project = collections.Counter()
    for c in members_by_field["decision"]:
        by_project[docs[c].get("ep")] += 1

    inconsistencies, info_reverse = [], []
    for pid, d in sorted(docs.items()):
        for field in FIELDS:
            e = d["review"][field]
            if e["carries_fact"] == "yes" and not _page_supports(d, field):
                inconsistencies.append({"pool_id": pid, "field": field,
                                        "issue": "carries_fact yes but no labelled page has the field present with "
                                                 "association resolved after application"})
            if e["carries_fact"] == "no" and _page_supports(d, field):
                info_reverse.append({"pool_id": pid, "field": field,
                                     "note": "carries_fact no although a page has the field present/resolved"})

    return {
        "status": "COUNTED",
        "rule": RULE,
        "stage": "initial pool after independent review",
        "extensions_used": 0,
        "gate_minimum": GATE_MIN,
        "gate_counts": gate_counts,
        "counted_documents": members_by_field,
        "excluded_unresolved": excluded,
        "upper_bound_if_resolved": upper,
        "upper_bound_rule": "every 'unresolved' value read as 'yes', all other values unchanged",
        "gate_action": gate_action,
        "distinct_documents": {"staged_files": len(docs), "documents_with_own_rulings": len(with_rulings),
                               "distinct_after_count_once": len(canon_ids)},
        "count_once_aliases": aliases,
        "alias_agreement_check": {"disagreements": alias_disagreements},
        "by_project_decision": dict(sorted(by_project.items())),
        "by_project_decision_note": "information only: counted decision-carrying documents (after count-once) by "
                                    "project (document 'ep')",
        "consistency_check": {
            "rule": "every carries_fact yes has at least one labelled page with that field present, association "
                    "resolved and not excluded from scoring, after application (rulings not changed)",
            "checked_document_fields": sum(1 for d in docs.values() for f in FIELDS
                                           if d["review"][f]["carries_fact"] == "yes"),
            "inconsistencies": inconsistencies,
            "ok": not inconsistencies,
            "information_reverse": info_reverse,
        },
    }


PKG = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/fresh-cohort-r32-reviewed"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewed", default=PKG + "/labels/R32-LABELS-REVIEWED-1.json")
    ap.add_argument("--out", default=PKG + "/FIELD-POPULATION.json")
    args = ap.parse_args(argv)
    with open(args.reviewed, encoding="utf-8") as f:
        reviewed = json.load(f)
    out = count_population(reviewed)
    out["source"] = {"reviewed_file": "labels/R32-LABELS-REVIEWED-1.json",
                     "reviewed_sha256": sha256_file(args.reviewed),
                     "final_response_sha256": reviewed["applied"]["final_response_sha256"],
                     "reviewed_version": reviewed["version"]}
    if os.path.exists(args.out):
        print("refusing to overwrite", args.out)
        return 3
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    print("gate_counts", out["gate_counts"], "excluded", out["excluded_unresolved"],
          "upper", out["upper_bound_if_resolved"], "->", out["gate_action"])
    print("consistency ok", out["consistency_check"]["ok"], "inconsistencies", out["consistency_check"]["inconsistencies"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
