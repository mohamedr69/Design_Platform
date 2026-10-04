"""AI-pilot labels v2 (ai-pilot-labels-2026-09-30.2): the v1 labels (unchanged, hash-checked) plus ONLY the additive
source review of Independent Review 18 (SOURCE-REVIEW.json: an owner-delegated AI review, not human, not blind; four
hash-verified pages, not the cohort). Changes:
  * EP-16830 Reply to Comments: the U+00B7 separator uncertainty is RESOLVED as printed (image + text layer); revision
    00 confirmed; 'Comply' replies stay contractor replies (decision n/a).
  * EP-16830 Authorization: P10781 confirmed as printed; a supplier authorization, never a consultant decision.
  * EP-19144 SCS DRF: handwriting uncertainty KEPT; project association UNRESOLVED (the page prints EP-18101, the
    sampling folder is EP-19144: no association is inherited from the folder); footer 'Revision Number 03' is form
    template metadata, not a document revision (already so in v1).
  * EP-23323 DJ-295: revision 00 confirmed; the O/0 identity question stays OPEN.
  * all 12 documents are recorded as exposed from 2026-09-30 (predicted in the ai-accuracy-pilot).
Nothing else changes; v1 stays as it is. Writes labels-v2/ and LABEL-CHANGES-v2.json."""
import copy
import hashlib
import json
import pathlib

V1 = pathlib.Path("C:/t/iso/work/r2x/ai-pilot/labels")
OUT = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18/labels-v2")
RV = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-18")
V1_SHA = {"PILOT-PAGE-LABELS.json": "e5431322", "PILOT-REGISTER-LABELS.json": "e4ec4c3f", "PILOT-UNCERTAINTY-AND-EXPOSURE.json": "0f7ffe9f"}
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
for n, pre in V1_SHA.items():
    assert sha(V1 / n).startswith(pre), n
review = json.loads((RV / "SOURCE-REVIEW.json").read_bytes().decode("cp1252"))   # the reviewer file is cp1252 (0xB7 = U+00B7); decoded, never rewritten
REVIEW_SHA = sha(RV / "SOURCE-REVIEW.json")
rulings = {r["sha256"]: r for r in review["rulings"]}
VERSION = "ai-pilot-labels-2026-09-30.2"


def prov(ruling):
    return {"source": "Independent Review 18 SOURCE-REVIEW.json", "source_review_sha256": REVIEW_SHA, "reviewer": review["reviewer"],
            "scope": review["scope"], "document_sha256": ruling["sha256"], "page": ruling["page"], "rotation": ruling["rotation"],
            "render_sha256": ruling["render_sha256"], "rulings": ruling["rulings"]}


reg = json.loads((V1 / "PILOT-REGISTER-LABELS.json").read_text(encoding="utf-8"))
page = json.loads((V1 / "PILOT-PAGE-LABELS.json").read_text(encoding="utf-8"))
unc = json.loads((V1 / "PILOT-UNCERTAINTY-AND-EXPOSURE.json").read_text(encoding="utf-8"))
reg2, page2, unc2 = copy.deepcopy(reg), copy.deepcopy(page), copy.deepcopy(unc)
changes = []
for d in reg2["documents"]:
    r = rulings.get(d["sha256"])
    pl = page2["documents"][d["doc"]]
    if not r:
        continue
    d["source_review"] = pl["source_review"] = prov(r)
    tag = r["tag"]
    if tag == "reply":
        before = list(pl.get("unresolved") or [])
        pl["unresolved"] = [u for u in before if "U+00B7" not in u]
        changes.append({"doc": d["doc"], "change": "separator uncertainty resolved as printed (U+00B7 kept literally)", "removed_unresolved": before})
    elif tag == "drf":
        d["project_association"] = pl["project_association"] = {
            "state": "unresolved", "printed_project": "EP-18101", "sampling_folder": "EP-19144",
            "rule": "no project association is inherited from the sampling folder"}
        changes.append({"doc": d["doc"], "change": "project association unresolved (prints EP-18101, folder EP-19144); handwriting uncertainty kept"})
    elif tag == "authorization":
        changes.append({"doc": d["doc"], "change": "P10781 confirmed as printed; supplier authorization, not a consultant decision (values unchanged)"})
    elif tag == "dj295":
        changes.append({"doc": d["doc"], "change": "revision 00 confirmed; O/0 identity question stays open (values unchanged)"})
unc2["uncertainty"] = [u for u in unc["uncertainty"] if "U+00B7" not in u["item"]]
unc2["resolved_in_v2"] = [{**u, "resolved_by": "Independent Review 18 source review (AI, owner-delegated, not human)", "source_review_sha256": REVIEW_SHA}
                          for u in unc["uncertainty"] if "U+00B7" in u["item"]]
unc2["exposure_v2"] = "all 12 documents are exposed from 2026-09-30: predicted by the ai-accuracy-pilot arms A/S/G/T; any later use is a regression/control, not a prospective result"
for x in (reg2, page2, unc2):
    x["labels_version"] = VERSION
    x["status"] = ("AI-drafted proposals (v1) + additive owner-delegated AI source review of four pages (Review 18); not human truth; "
                   "not reviewed as a whole; metrics PROVISIONAL")
    x["previous_version"] = {"version": "ai-pilot-labels-2026-09-30.1", "kept_unchanged": True}
OUT.mkdir(parents=True, exist_ok=True)
files = {"PILOT-REGISTER-LABELS.v2.json": reg2, "PILOT-PAGE-LABELS.v2.json": page2, "PILOT-UNCERTAINTY-AND-EXPOSURE.v2.json": unc2}
for n, obj in files.items():
    (OUT / n).write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
(OUT / "LABEL-CHANGES-v2.json").write_text(json.dumps({"version": VERSION, "from": {n: sha(V1 / n) for n in V1_SHA}, "source_review_sha256": REVIEW_SHA,
                                                       "changes": changes, "files": {n: sha(OUT / n) for n in files}}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(changes, indent=1, ensure_ascii=False)[:1500])
print({n: sha(OUT / n)[:12] for n in files})
