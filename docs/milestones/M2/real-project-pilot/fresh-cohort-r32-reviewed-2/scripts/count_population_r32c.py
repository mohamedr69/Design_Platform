"""ORCH-04.1 (R32APPLY2-IMPL) step 3: count the field populations of r32-labels-reviewed-2.

count_population(reviewed, in_scope_pages=None) -> dict  (pure)
Rule (the same count-once rule as reviewed-1): per field, the distinct documents, after mapping each count-once alias
to the pool id it counts under, whose document review has resolved_for_scoring == "yes" AND carries_fact == "yes".
A document with "unresolved" in either value is excluded and listed (excluded_unresolved lists only fields that have
exclusions, so it is {} when nothing is unresolved). upper_bound_if_resolved re-counts with every "unresolved" value
read as "yes". Gate: identity, revision and decision each >= 12 -> READY FOR INDEPENDENT PREPARATION REVIEW, else
EXTENSION-1 REQUIRED (no extension is drawn here).
Consistency: every carries_fact "yes" has at least one in-scope labelled page with the field present, association
resolved and not excluded from scoring; every carries_fact "no" has none. Exceptions in both directions are listed.

CLI writes fresh-cohort-r32-reviewed-2/FIELD-POPULATION.json (refuses to overwrite).
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
STAGE = "initial pool after independent review and Review 33 rulings"
RULE = ("per field, count the distinct documents, after mapping each count-once alias to the pool id it counts under "
        "(frozen section 1 byte-identical F052->F038, F070->F067; Review 33 (c)(ii) content duplicates F031->F001, "
        "F059->F046), whose document review has resolved_for_scoring == 'yes' AND carries_fact == 'yes'; a document "
        "with 'unresolved' in either value is excluded and listed; gate: identity, revision and decision each >= 12 "
        "(the count-once rule of r32-labels-reviewed-1, unchanged)")


def _canon(reviewed, pid):
    return reviewed["count_once_aliases"].get(pid, pid)


def _count(reviewed, field, treat_unresolved_as_yes=False):
    members, excluded = set(), []
    for pid, d in sorted(reviewed["documents"].items()):
        e = d["review"][field]
        rs, cf = e["resolved_for_scoring"], e["carries_fact"]
        if "unresolved" in (rs, cf):
            excluded.append(pid)
            if not treat_unresolved_as_yes:
                continue
            rs = "yes" if rs == "unresolved" else rs
            cf = "yes" if cf == "unresolved" else cf
        if rs == "yes" and cf == "yes":
            members.add(_canon(reviewed, pid))
    return sorted(members), excluded


def _supporting_pages(doc, field, scope):
    """In-scope labelled pages with the field present, association resolved and not excluded from scoring."""
    out = []
    for pg, page in sorted((doc.get("pages") or {}).items(), key=lambda kv: int(kv[0])):
        if scope is not None and pg not in scope:
            continue
        f = page.get(field)
        if f and f.get("state") == "present" and f.get("association") == "resolved" \
                and not f.get("excluded_from_scoring"):
            out.append(pg)
    return out


def count_population(reviewed, in_scope_pages=None):
    gate_counts, members_by_field, excluded, upper = {}, {}, {}, {}
    for field in FIELDS:
        members, ex = _count(reviewed, field)
        ub, _ = _count(reviewed, field, treat_unresolved_as_yes=True)
        gate_counts[field] = len(members)
        members_by_field[field] = members
        if ex:
            excluded[field] = ex
        upper[field] = len(ub)
    gate_action = READY if all(gate_counts[f] >= GATE_MIN for f in FIELDS) else EXTEND

    docs = reviewed["documents"]
    aliases = dict(reviewed["count_once_aliases"])
    canon_ids = sorted({_canon(reviewed, p) for p in docs})
    with_rulings = sorted(p for p, d in docs.items() if d["review"]["identity"]["resolved_for_scoring"] is not None)

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

    by_project = collections.Counter({d.get("ep"): 0 for d in docs.values()})
    for c in members_by_field["decision"]:
        by_project[docs[c].get("ep")] += 1

    yes_missing, no_with, outside, unlabelled = [], [], [], {}
    checked_yes = checked_no = 0
    for pid, d in sorted(docs.items()):
        scope = None if in_scope_pages is None else set(in_scope_pages.get(pid, ()))
        labelled = set((d.get("pages") or {}).keys())
        if scope is not None:
            outside.extend("%s/p%s" % (pid, pg) for pg in sorted(labelled - scope, key=int))
            if scope - labelled:
                unlabelled[pid] = sorted(scope - labelled, key=int)
        for field in FIELDS:
            cf = d["review"][field]["carries_fact"]
            sup = _supporting_pages(d, field, scope)
            if cf == "yes":
                checked_yes += 1
                if not sup:
                    yes_missing.append({"pool_id": pid, "field": field,
                                        "issue": "carries_fact yes but no in-scope labelled page has the field "
                                                 "present, association resolved and not excluded"})
            elif cf == "no":
                checked_no += 1
                if sup:
                    no_with.append({"pool_id": pid, "field": field, "pages": sup,
                                    "issue": "carries_fact no although an in-scope page has the field present, "
                                             "association resolved and not excluded"})

    return {
        "status": "COUNTED",
        "rule": RULE,
        "stage": STAGE,
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
        "by_project_decision": dict(sorted(by_project.items(), key=lambda kv: str(kv[0]))),
        "by_project_decision_note": "information only: counted decision-carrying documents (after count-once) by "
                                    "project (document 'ep'); projects with none are listed with 0",
        "consistency_check": {
            "rule": "every carries_fact yes has at least one in-scope labelled page with that field present, "
                    "association resolved and not excluded from scoring; every carries_fact no has none",
            "in_scope": "all labelled pages" if in_scope_pages is None else "pages given by in_scope_pages",
            "checked_carries_fact_yes": checked_yes,
            "checked_carries_fact_no": checked_no,
            "yes_without_supporting_page": yes_missing,
            "no_with_supporting_page": no_with,
            "labelled_pages_outside_scope": outside,
            "in_scope_pages_without_labels": unlabelled,
            "ok": not yes_missing and not no_with and not outside,
        },
    }


# ------------------------------------------------------------------ CLI
PILOT = "C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot"
PKG = PILOT + "/fresh-cohort-r32-reviewed-2"
RENDERS = (PILOT + "/fresh-cohort-r32/RENDERS.json", "175a3a10ac871540dbbeb87f1ec7d2e68b369186d05a60bf5dd751b18e51e8be")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def in_scope_from_renders(renders):
    out = {}
    for d in renders["documents"]:
        pages = [str(r["page"]) for r in d["rendered"]]
        if len(pages) != d["pages_in_scope"]:
            raise SystemExit("RENDERS %s: %d rendered pages but pages_in_scope %r" % (d["pool_id"], len(pages),
                                                                                     d["pages_in_scope"]))
        out[d["pool_id"]] = pages
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reviewed", default=PKG + "/labels/R32-LABELS-REVIEWED-2.json")
    ap.add_argument("--out", default=PKG + "/FIELD-POPULATION.json")
    args = ap.parse_args(argv)
    if sha256_file(RENDERS[0]) != RENDERS[1]:
        print("PACKET MISMATCH", RENDERS[0])
        return 2
    with open(RENDERS[0], encoding="utf-8") as f:
        scope = in_scope_from_renders(json.load(f))
    with open(args.reviewed, encoding="utf-8") as f:
        reviewed = json.load(f)
    out = count_population(reviewed, scope)
    ap_ = reviewed["applied"]
    out["source"] = {"reviewed_file": "labels/R32-LABELS-REVIEWED-2.json",
                     "reviewed_sha256": sha256_file(args.reviewed),
                     "reviewed_version": reviewed["version"],
                     "derived_from": reviewed["derived_from"],
                     "review33_sha256": ap_["review33_sha256"],
                     "escalation_rulings_final_sha256": ap_["escalation_rulings_final_sha256"],
                     "dispositions_sha256": ap_["dispositions_sha256"],
                     "in_scope_pages_from": {"path": RENDERS[0], "sha256": RENDERS[1],
                                             "note": "RENDERS.json documents[].rendered pages (count = "
                                                     "pages_in_scope); bound by the packet manifest 15c4114d..."}}
    if os.path.exists(args.out):
        print("refusing to overwrite", args.out)
        return 3
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(out, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    print("gate_counts", out["gate_counts"], "excluded", out["excluded_unresolved"],
          "upper", out["upper_bound_if_resolved"], "->", out["gate_action"])
    cc = out["consistency_check"]
    print("consistency ok", cc["ok"], "yes", cc["checked_carries_fact_yes"], "no", cc["checked_carries_fact_no"],
          "exceptions", cc["yes_without_supporting_page"], cc["no_with_supporting_page"],
          "outside", cc["labelled_pages_outside_scope"], "unlabelled in scope", cc["in_scope_pages_without_labels"])
    print("by project", out["by_project_decision"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
