"""Feasibility: the DRAFT page / field-aware coverage over the STORED ai-accuracy-pilot outputs (S / G / T; 12 planned
documents, 1-3 pages each, read only). Shows what a first-page-only view hides. Writes coverage-v3/PILOT-COVERAGE-V3-DRAFT.json."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import coverage_v3_draft as cv  # noqa: E402

A = pathlib.Path("C:/t/iso/work/r2x/ai-pilot")
decl = json.loads((A / "PILOT-DECLARATION.json").read_text(encoding="utf-8"))
sample = json.loads((A / "PILOT-SAMPLE.json").read_text(encoding="utf-8"))["documents"]
MAX = decl["arms"]["S"]["identities"]["MAX_PAGES_PER_DOCUMENT"]
out = {"mode": "OFFLINE, stored outputs read only", "max_pages": MAX, "arms": {}}
for arm, tag in (("S", "ai-pilot-S"), ("G", "ai-pilot-G"), ("T", "ai-pilot-T")):
    pol = decl["arms"][arm]["identities"]["EVIDENCE_POLICY_VERSION"]
    rows = json.loads(pathlib.Path(f"C:/t/r2x/runs/{tag}/out/rows.json").read_text(encoding="utf-8"))
    docs = []
    for d in sample:
        ai = ((rows.get(d["doc_key"]) or {}).get("extracted") or {}).get("ai_evidence") or {}
        atts = [a for a in ai.get("attempts") or [] if a.get("policy") == pol]
        docs.append(cv.document_coverage({"doc": d["doc_key"], "extension": ".pdf", "pages": d["pages"]}, atts[-1] if atts else None, max_pages=MAX))
    s = cv.summarize(docs)
    multi = [x for x in docs if len(x["pages"]) > 1]
    s["multi_page_documents"] = [{"doc": x["doc"].split("/")[-1], "state": x["state"], "pages": x["pages"]} for x in multi]
    out["arms"][arm] = {"summary": s, "documents": docs}
d = pathlib.Path("C:/t/iso/work/r2x/review20/coverage-v3")
d.mkdir(parents=True, exist_ok=True)
(d / "PILOT-COVERAGE-V3-DRAFT.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for arm, v in out["arms"].items():
    s = v["summary"]
    print(arm, "planned", s["documents_planned"], "required-complete", s["documents_required_complete"], "|", json.dumps(s["page_field_classes"]["own:decision"]))
    for m in s["multi_page_documents"]:
        print("    multi-page:", m["doc"][:40], m["state"], {p: sorted(set(c.values())) for p, c in m["pages"].items()})
