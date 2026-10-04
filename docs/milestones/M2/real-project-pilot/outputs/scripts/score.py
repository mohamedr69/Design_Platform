"""Pilot step 6: expected (GOLDEN-LABELS.json) versus actual (rows-<profile>.json) per document and field, with exclusive
document execution outcomes, field-validation states, per project / cohort / stratum / format / kind summaries,
critical failures named one by one, page accounting and workload. Usage: score.py <scratch>"""
import json, sys, pathlib, collections, re

S = pathlib.Path(sys.argv[1]); ROWS = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else S
labels = json.load(open(S / "GOLDEN-LABELS.json", encoding="utf-8"))
NON = ("absent", "illegible", "unknown", "n/a", "unlabelled")
CRITICAL = ("reference", "revision", "decision")
SCOPE_PREFIXES = ("shop-drawing cover", "shop-drawing transmittal", "material submittal", "material approval", "material / equipment approval", "material sample",
                  "sample approval", "reply", "drawing sheet (shop drawing", "drawing sheet (contractor shop drawing", "shop drawing sheet", "stamped shop drawing",
                  "commented shop drawing", "technical submission", "document submittal", "pre-qualification", "transmittal", "word transmittal", "drawing sheet (scanned")


def in_scope(kind):
    k = (kind or "").lower()
    return any(k.startswith(p) for p in SCOPE_PREFIXES)
DECISION_MAP = {"approved": "approved", "ann": "ANN", "approved as noted": "ANN", "rejected": "rejected", "ur": "UR", "conflict": "conflict", "n/a": "none", "none": "none"}


def literal(v):
    """The literal value a label holds: the text before the first ' (' note; a non-value word when it starts with one."""
    if v is None: return None
    s = str(v).strip()
    low = s.lower()
    for n in NON:
        if low == n or low.startswith(n + " ") or low.startswith(n + "(") or low.startswith(n + ";"):
            return n
    s = re.split(r"\s\(", s, 1)[0].strip()
    return s


def norm_ref(v):
    return re.sub(r"\s+", "", v or "").upper()


def alnum(v):
    return re.sub(r"[^0-9A-Z]", "", (v or "").upper())


def norm_rev(v):
    v = (v or "").strip().upper()
    v = re.split(r"[\s;]", v, 1)[0]
    m = re.fullmatch(r"(?:R|REV\.?|REVISION|R\.)?\s*0*(\d+)", v)
    if m:
        return f"R{int(m.group(1))}"
    return v


def actual_of(row):
    ex = row.get("extracted") or {}
    recs = ex.get("records") or []; first = recs[0] if recs else None
    cov = ex.get("coverage") or {}
    return {"state": row["state"], "error": row["error"], "outcome": cov.get("outcome"), "stop": cov.get("stop_reason"), "records": len(recs), "mirror": row["mirror"], "role": row.get("role"),
            "reference": first.get("reference") if first else None, "revision": first.get("revision") if first else None, "status": first.get("status") if first else None,
            "category": first.get("category") if first else None, "system": first.get("system_code") if first else None, "raw_system": first.get("raw_system") if first else None,
            "floor": first.get("floor") if first else None, "name": first.get("name") if first else None, "page": first.get("page") if first else None,
            "flags": sorted({f for r in recs for f in (r.get("flags") or [])}), "candidates": list(first.get("decision_candidates") or []) if first else [],
            "observations": [o.get("kind") for o in ex.get("observations") or []], "notes": ex.get("notes") or [], "pages_visited": len(cov.get("pages_visited") or []),
            "pages_skipped": len(cov.get("pages_skipped") or []), "pages_failed": len(cov.get("pages_failed") or []), "pages_total": cov.get("pages_total"),
            "ocr": cov.get("ocr") or {}, "attempt": (ex.get("attempt") or {}).get("outcome"), "all_records": [(r.get("reference"), r.get("revision"), r.get("status"), r.get("page"), r.get("category")) for r in recs],
            "form": bool(ex.get("form")), "parser": ex.get("parser_version"), "profile": ex.get("profile")}


def judge(field, expected_raw, a):
    """(state, detail): correct / near (matches ignoring punctuation) / wrong / abstained (nothing accepted) / unscorable."""
    expected = literal(expected_raw)
    if expected in NON or expected is None:
        return ("unscorable", expected or "none")
    if field == "reference":
        got = a["reference"]
        if got is None:
            return ("abstained", "no record" if a["records"] == 0 else "no reference")
        if norm_ref(got) == norm_ref(expected): return ("correct", got)
        stripped = re.sub(r"\s*-\s*R\.?\s*0*(\d+)\s*$", "", expected, flags=re.I)
        suffix = re.search(r"-\s*R\.?\s*0*(\d+)\s*$", expected, flags=re.I)
        if suffix and norm_ref(got) == norm_ref(stripped):
            return ("correct", got + f" (suffix R{int(suffix.group(1))} read as the revision)") if norm_rev(a["revision"] or "") == f"R{int(suffix.group(1))}" else ("near", got)
        # any record on the document holding it
        if any(norm_ref(r[0]) == norm_ref(expected) for r in a["all_records"]): return ("correct-later-record", got)
        if alnum(got) == alnum(expected) or (len(alnum(expected)) >= 6 and (alnum(got).startswith(alnum(expected)) or alnum(expected).startswith(alnum(got)))): return ("near", got)
        return ("wrong", got)
    if field == "revision":
        got = a["revision"]
        if got is None:
            return ("abstained", "no record" if a["records"] == 0 else "no revision")
        return ("correct" if norm_rev(got) == norm_rev(expected) else "wrong", got)
    if field == "decision":
        exp = DECISION_MAP.get(expected.strip().lower(), expected)
        got = a["status"]
        if a["records"] == 0:
            return ("correct", "no record, none expected") if exp in ("none", "UR") else ("abstained", "no record")
        if got in (None, "UR"):
            if exp in ("UR", "conflict", "none"):
                return ("correct", "UR" + (" (conflict recorded)" if "decision_conflict" in a["flags"] else ""))
            held = any(c[0] == exp for c in a["candidates"])
            return ("abstained", "held as candidate" if held else "UR")
        if exp == "none":
            return ("wrong", f"{got} where no decision applies")
        return ("correct" if got == exp else "wrong", got)
    if field == "system":
        got = a["system"] or a["raw_system"]
        if got is None: return ("abstained", "none")
        e = expected.upper()
        if e.startswith("OTHER"): return ("wrong" if got.upper()[:3] in ("FAS", "ELS", "VES", "CBS") else "correct", got)
        return ("correct" if got.upper()[:3] in e or e[:3] == got.upper()[:3] else "wrong", got)
    return ("unscorable", "not scored")


def outcome_of(row):
    if row is None: return "not-run"
    if row["state"] == "removed": return "removed"
    ex = row.get("extracted") or {}
    if row["state"] == "failed":
        return "unavailable" if (ex.get("attempt") or {}).get("outcome") == "unavailable" else "failed"
    cov = ex.get("coverage") or {}
    if (ex.get("attempt") or {}).get("outcome") == "partial": return "partial"
    return cov.get("outcome") or ("transmittal" if ex.get("transmittal") or row.get("role") == "transmittal" else "no-ledger")


report = {"profiles": {}, "labels_summary": {}}
docs = labels["documents"]
report["labels_summary"] = {"documents": len(docs), "labelled": sum(1 for d in docs if d["confidence"] != "unlabelled"),
                            "by_confidence": dict(collections.Counter(d["confidence"] for d in docs)),
                            "decisions": dict(collections.Counter(literal(d["labels"]["decision"]) for d in docs))}
for profile in ("default", "promoted"):
    p = ROWS / f"rows-{profile}.json"
    if not p.is_file():
        continue
    rows = {k.replace("\\", "/"): v for k, v in json.load(open(p, encoding="utf-8")).items()}
    per_doc = []; crit = []
    for d in docs:
        row = rows.get(d["doc"].replace("\\", "/")); a = actual_of(row) if row else None
        entry = {"doc": d["doc"], "sha256": d.get("sha256"), "ep": d["ep"], "cohort": d["cohort"], "stratum": d["stratum"], "kind": literal(d["labels"]["kind"]), "in_scope": in_scope(d["labels"]["kind"]), "scan_like": d.get("scan_like"), "extension": d["extension"],
                 "eligibility": d["expected_eligibility"], "outcome": outcome_of(row), "expected": {k: d["labels"].get(k) for k in ("reference", "revision", "decision", "system", "printed_project")}, "confidence": d["confidence"], "actual": a, "fields": {}}
        if a is not None and d["expected_eligibility"] == "eligible" and d["confidence"] != "unlabelled" and d["extension"] == ".pdf":
            for f in CRITICAL + ("system",):
                entry["fields"][f] = judge(f, d["labels"].get(f, "unlabelled"), a)
            fr = entry["fields"]
            if fr["decision"][0] == "wrong" and a["status"] in ("approved", "ANN"):
                crit.append({"kind": "false consultant approval", "doc": d["doc"], "expected": d["labels"]["decision"], "actual": a["status"], "profile": profile})
            if fr["reference"][0] in ("wrong", "near"):
                crit.append({"kind": "wrong reference" if fr["reference"][0] == "wrong" else "reference differs in punctuation/suffix", "doc": d["doc"], "expected": literal(d["labels"]["reference"]), "actual": a["reference"], "profile": profile})
            if fr["revision"][0] == "wrong":
                crit.append({"kind": "wrong revision", "doc": d["doc"], "expected": literal(d["labels"]["revision"]), "actual": a["revision"], "profile": profile})
            pp = str(d["labels"].get("printed_project") or "")
            m = re.search(r"EP-?\s?(\d{5})", pp)
            if m and m.group(1) != d["ep"] and a["records"]:
                crit.append({"kind": "printed EP differs from the folder's EP (association to check)", "doc": d["doc"], "printed": m.group(0), "folder": f"EP-{d['ep']}", "actual_reference": a["reference"], "profile": profile})
        per_doc.append(entry)

    def summarise(keyfn):
        out = collections.defaultdict(lambda: {"documents": 0, "outcomes": collections.Counter(), "fields": {f: collections.Counter() for f in CRITICAL + ("system",)}})
        for e in per_doc:
            k = keyfn(e); out[k]["documents"] += 1; out[k]["outcomes"][e["outcome"]] += 1
            for f, (state, _) in e["fields"].items():
                out[k]["fields"][f][state] += 1
        return {k: {"documents": v["documents"], "outcomes": dict(v["outcomes"]), "fields": {f: dict(c) for f, c in v["fields"].items()}} for k, v in out.items()}

    def rates(fields_counter):
        out = {}
        for f, c in fields_counter.items():
            correct = c.get("correct", 0) + c.get("correct-later-record", 0); wrong = c.get("wrong", 0) + c.get("near", 0)
            accepted = correct + wrong; scorable = accepted + c.get("abstained", 0)
            out[f] = {"accepted": accepted, "correct": correct, "wrong": wrong, "near": c.get("near", 0), "abstained": c.get("abstained", 0), "unscorable": c.get("unscorable", 0),
                      "precision_of_accepted": round(correct / accepted, 4) if accepted else None, "automatic_recovery": round(correct / scorable, 4) if scorable else None,
                      "review_rate": round(c.get("abstained", 0) / scorable, 4) if scorable else None}
        return out

    overall = summarise(lambda e: "all")["all"]
    report["profiles"][profile] = {"documents": len(per_doc), "outcomes": overall["outcomes"], "field_rates": rates(overall["fields"]),
                                   "by_project": {k: {**v, "rates": rates(v["fields"])} for k, v in summarise(lambda e: e["ep"]).items()},
                                   "by_cohort": {k: {**v, "rates": rates(v["fields"])} for k, v in summarise(lambda e: e["cohort"]).items()},
                                   "by_stratum": {k: {**v, "rates": rates(v["fields"])} for k, v in summarise(lambda e: e["stratum"]).items()},
                                   "by_format": {k: {**v, "rates": rates(v["fields"])} for k, v in summarise(lambda e: ("scan" if e["scan_like"] else "text") if e["extension"] == ".pdf" else "word").items()},
                                   "by_scope": {k: {**v, "rates": rates(v["fields"])} for k, v in summarise(lambda e: "in scope (submissions, covers, replies, contractor shop-drawing sheets, transmittals)" if e["in_scope"] else "out of scope (consultant IFC/tender sheets, specs, letters, catalogues, calculations, authority documents, commercial)").items()},
                                   "by_scope_cohort": {k: {**v, "rates": rates(v["fields"])} for k, v in summarise(lambda e: f"{'in' if e['in_scope'] else 'out'} / {e['cohort']}").items()},
                                   "critical_failures": crit,
                                   "pages": {"visited": sum((e["actual"] or {}).get("pages_visited", 0) for e in per_doc), "skipped": sum((e["actual"] or {}).get("pages_skipped", 0) for e in per_doc),
                                             "failed": sum((e["actual"] or {}).get("pages_failed", 0) for e in per_doc), "total": sum((e["actual"] or {}).get("pages_total") or 0 for e in per_doc),
                                             "ocr_attempted": sum(((e["actual"] or {}).get("ocr") or {}).get("attempted", 0) for e in per_doc), "ocr_failed": sum(len(((e["actual"] or {}).get("ocr") or {}).get("failed", [])) for e in per_doc),
                                             "ocr_skipped_budget": sum(len(((e["actual"] or {}).get("ocr") or {}).get("skipped_budget", [])) for e in per_doc),
                                             "stop_reasons": dict(collections.Counter((e["actual"] or {}).get("stop") for e in per_doc if e["actual"]))}}
    json.dump(per_doc, open(ROWS / f"per-document-{profile}.json", "w", encoding="utf-8"), indent=1, default=str, ensure_ascii=False)
json.dump(report, open(ROWS / "ACCURACY.json", "w", encoding="utf-8"), indent=1, default=str, ensure_ascii=False)
for profile, r in report["profiles"].items():
    print("====", profile, r["outcomes"])
    for f, v in r["field_rates"].items(): print("  ", f, v)
    print("   pages", r["pages"])
    print("   critical", len(r["critical_failures"]), collections.Counter(c["kind"] for c in r["critical_failures"]))
    for c in r["critical_failures"]: print("     ", c["kind"][:34], "|", c["doc"][-60:], "|", c.get("expected", c.get("printed")), "->", c.get("actual", c.get("actual_reference")))
