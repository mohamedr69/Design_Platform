"""ORCH-05.1 (Review 33 C-5): r32-labels-reviewed-2 (through labels_adapter_r32) -> the evaluator .10 input format.

Format learned from C:/t/iso/cand-r30n/backend/scripts/m2_eval6.py, m2_eval4.py and m2_pilot_eval.py (read-only, format only):
  register  {"documents": [{"doc": "EP-<ep>/<relative_path>", "ep", "labels": {"reference", "revision", "decision", "kind",
             "register"}, "confidence", "cohort", "stratum", "extension", "scan_like"}]}
  page      {"documents": {doc: {"records": [{"page": int, "component", "reference", "printed_revision", "decision",
             "register", "confidence"}], "no_record_pages": {"<page>": reason}, "unvalidated_pages": [int]}},
             "page1_corrections": []}
  uncertainty {"uncertainty": [{"doc", "pool_id", "page", "field", "reasons"}]}
  planned   [{"doc", "pool_id", "sha256", "pages", "extension": ".pdf"}]  (coverage_v4.document_coverage, max_pages 4)
Encoding of one (pool id, page, field) row (evaluator truth words of m2_eval4: UNSCORABLE / *_NEGATIVE):
  value         reference / printed_revision = the literal; decision = the class in the application vocabulary
                (approved -> 'approved', approved as noted -> 'ANN', revise and resubmit -> 'rejected', rejected -> 'rejected')
  ABSENT        identity / revision -> 'absent'; decision -> 'UR' (blank_decision_area) or 'n/a' (no_decision_area)
  NOT_SCORABLE  'ambiguous' (evaluator 'unscorable')
  a page whose three fields are all ABSENT -> no_record_pages (value {"reason", "decision": 'UR'|'n/a'}; the evaluator
                reads only the key); a page whose three fields are all NOT_SCORABLE -> unvalidated_pages
  every other labelled page -> one record (component 'page<p>'): compilations stay keyed by page, never one file value.
Exclusions (explicit, never silent): count-once aliases (scored through the canonical id; the run set holds canonical ids
only). What evaluator .10 cannot express is carried in `r32_sidecar` for ORCH-06: the (d1) decision alternatives, the
(g)(1) and suffix-base identity alternates, and rows where evaluator .10 would read a revision from the identity's
'-Rn' suffix. Pure; write_outputs writes only where it is told to."""
from __future__ import annotations

import collections
import hashlib
import json

import labels_adapter_r32 as A

FORMAT = "evaluator .10 input (scripts.m2_eval6.evaluate(register, page, rows, page['page1_corrections'], ai_context)); planned for coverage_v4"
DECISION_WORD = {"approved": "approved", "approved as noted": "ANN", "revise and resubmit": "rejected", "rejected": "rejected"}
ABSENT_DECISION = {"blank_decision_area": "UR", "no_decision_area": "n/a"}
FIELD_KEY = {"identity": "reference", "revision": "printed_revision", "decision": "decision"}


def encode(rec) -> str | None:
    kind = rec["truth_kind"]
    if kind == "not_scorable":
        return "ambiguous"
    if kind == "absent":
        return ABSENT_DECISION.get(rec.get("absent_kind"), "n/a") if rec["field"] == "decision" else "absent"
    if rec["field"] == "decision":
        return DECISION_WORD.get(rec.get("class"))
    return rec["literal"]


def convert(truth: dict) -> dict:
    reg, page_docs, unc, planned, recon = [], {}, [], [], []
    side = {"pool_index": {}, "exclusions": [], "decision_alternatives": [], "identity_alternates": [], "suffix_revision_divergences": []}
    for pid in sorted(truth["documents"]):
        d = truth["documents"][pid]
        rows = A.doc_rows(truth, pid)
        if d["is_alias"]:
            for r in rows:
                recon.append({"row": f"{pid}|{r['page']}|{r['field']}", "truth_kind": r["truth_kind"], "maps_to": None,
                              "exclusion": f"count-once alias of {d['canonical_id']} ({d['alias_kind']}); scored through the canonical id"})
            side["exclusions"].append({"pool_id": pid, "doc": d["doc_key"], "why": f"count-once alias of {d['canonical_id']}", "rows": len(rows)})
            continue
        key = d["doc_key"]
        side["pool_index"][key] = pid
        by_page = collections.defaultdict(dict)
        for r in rows:
            by_page[r["page"]][r["field"]] = r
        records, no_record, unvalidated = [], {}, []
        for pg in sorted(by_page, key=int):
            fr = by_page[pg]
            kinds = {f: fr[f]["truth_kind"] for f in fr}
            if all(k == "absent" for k in kinds.values()) and len(kinds) == 3:
                no_record[str(pg)] = {"reason": "r32: identity, revision and decision all absent on this page",
                                      "decision": encode(fr["decision"])}
                target = f"no_record_pages[{pg}]"
            elif all(k == "not_scorable" for k in kinds.values()) and len(kinds) == 3:
                unvalidated.append(int(pg))
                target = f"unvalidated_pages[{pg}]"
            else:
                rec = {"page": int(pg), "component": f"page{pg}", "register": True, "confidence": "high", "pool_id": pid}
                for f in A.FIELDS:
                    rec[FIELD_KEY[f]] = encode(fr[f]) if f in fr else "ambiguous"
                records.append(rec)
                target = f"records[page {pg}]"
            for f, r in fr.items():
                value = encode(r)
                recon.append({"row": f"{pid}|{pg}|{f}", "truth_kind": r["truth_kind"], "maps_to": f"{key} {target}.{FIELD_KEY[f]}",
                              "encoded": value, "exclusion": None})
                if r["truth_kind"] == "not_scorable":
                    unc.append({"doc": key, "pool_id": pid, "page": int(pg), "field": f, "reasons": r["not_scorable_reasons"]})
                if f == "decision" and r["truth_kind"] == "value" and r.get("resubmission_required"):
                    side["decision_alternatives"].append({"doc": key, "pool_id": pid, "page": int(pg), "truth": value, "also_correct": ["rejected"],
                                                          "rule": "(d1) resubmission tolerance"})
                if f == "identity" and r["alternates"]:
                    side["identity_alternates"].append({"doc": key, "pool_id": pid, "page": int(pg), "truth": r["literal"], "alternates": r["alternates"],
                                                        "kinds": r["alternate_kinds"]})
        for rec in records:
            ref = rec["reference"]
            if ref not in (None, "absent", "ambiguous") and rec["printed_revision"] in ("absent", None):
                import re
                if re.search(r"-\s*R\.?\s*0*\d+\s*$", ref, re.I):
                    side["suffix_revision_divergences"].append({"doc": key, "pool_id": pid, "page": rec["page"], "reference": ref,
                                                                "why": "evaluator .10 revision_truth reads the reference's '-Rn' suffix as the revision when printed_revision is 'absent'"})
        first = records[0] if records else {}
        reg.append({"doc": key, "ep": d["ep"], "pool_id": pid, "cohort": "r32", "stratum": d["stratum"], "extension": None, "scan_like": None,
                    "confidence": "high", "labels": {"reference": first.get("reference", "absent"), "revision": first.get("printed_revision", "absent"),
                                                     "decision": first.get("decision", "n/a"), "kind": d["kind"], "register": True}})
        page_docs[key] = {"records": records, "no_record_pages": no_record, "unvalidated_pages": unvalidated}
        planned.append({"doc": key, "pool_id": pid, "sha256": d["staged_sha256"], "pages": d["page_count"], "extension": ".pdf"})
    return {"format": FORMAT, "source": {"truth_schema": truth["schema"], "labels_version": truth.get("source_version")},
            "register": {"documents": reg}, "page": {"documents": page_docs, "page1_corrections": []},
            "uncertainty": {"uncertainty": unc}, "planned": planned, "r32_sidecar": side, "reconciliation": recon,
            "reference_set_statement": "reference set independently AI-reviewed (Claude agents), not human-signed"}


def reconciliation_totals(out: dict, truth: dict) -> dict:
    recon = out["reconciliation"]
    keys = [r["row"] for r in recon]
    mapped = [r for r in recon if r["maps_to"]]
    excluded = [r for r in recon if r["exclusion"]]
    return {"truth_rows": len(truth["rows"]), "reconciled_rows": len(recon), "distinct": len(set(keys)),
            "mapped": len(mapped), "excluded": len(excluded), "every_row_once": sorted(keys) == sorted(truth["rows"]) and len(set(keys)) == len(keys),
            "mapped_by_kind": dict(collections.Counter(r["truth_kind"] for r in mapped)),
            "excluded_by_kind": dict(collections.Counter(r["truth_kind"] for r in excluded)),
            "records": sum(len(v["records"]) for v in out["page"]["documents"].values()),
            "no_record_pages": sum(len(v["no_record_pages"]) for v in out["page"]["documents"].values()),
            "unvalidated_pages": sum(len(v["unvalidated_pages"]) for v in out["page"]["documents"].values()),
            "documents": len(out["register"]["documents"]), "planned": len(out["planned"]),
            "decision_alternatives": len(out["r32_sidecar"]["decision_alternatives"]),
            "identity_alternates": len(out["r32_sidecar"]["identity_alternates"]),
            "suffix_revision_divergences": len(out["r32_sidecar"]["suffix_revision_divergences"])}


def decode(out: dict) -> dict:
    """The round trip: evaluator input -> {(pool id, page, field): (kind, value)} with value the literal (identity,
    revision) or the evaluator decision word."""
    back = {}
    idx = out["r32_sidecar"]["pool_index"]
    for key, pd in out["page"]["documents"].items():
        pid = idx[key]
        for pg, why in pd["no_record_pages"].items():
            for f in A.FIELDS:
                back[(pid, str(pg), f)] = ("absent", why.get("decision") if f == "decision" else None)
        for pg in pd["unvalidated_pages"]:
            for f in A.FIELDS:
                back[(pid, str(pg), f)] = ("not_scorable", None)
        for rec in pd["records"]:
            for f in A.FIELDS:
                v = rec[FIELD_KEY[f]]
                if v == "ambiguous":
                    back[(pid, str(rec["page"]), f)] = ("not_scorable", None)
                elif v in ("absent", "UR", "n/a"):
                    back[(pid, str(rec["page"]), f)] = ("absent", v if f == "decision" else None)
                else:
                    back[(pid, str(rec["page"]), f)] = ("value", v)
    return back


def write_json(obj, path) -> str:
    text = json.dumps(obj, sort_keys=True, indent=1, ensure_ascii=False) + "\n"
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
