"""R14-04: the worklist rebuilt for the review14 package with working links, and the AI source review attached.

* Page-image links are computed relative to the package's worklist folder and CHECKED (every link must resolve).
  Review 13's links pointed at `../review08/human-review-packet-v2/../../review07/...`, which resolves outside the
  milestone folder (all 23 were broken); the packet page is `../../review07/human-review-packet/pages/<file>`.
* The four sample units get direct page links (their renders, copied into this package; hash-listed).
* Each unit carries the AI review (status, observations, disposition) in a SEPARATE `ai_review` block with its
  provenance; the human answer fields stay empty (no Codex in human fields).
* The Review 13 sample rule and its disclosure are kept: written after the A / B runs began, prediction-independent by
  construction, not a prospectively frozen blind audit."""
import hashlib
import json
import os
import pathlib
import re
import shutil

PKG = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot/review14")
WL = PKG / "worklist"
(WL / "pages").mkdir(parents=True, exist_ok=True)
R = pathlib.Path("C:/Users/moham/.codex/visualizations/2026/09/27/01a0e218-6014-77a0-be80-501dcc922424/master-roadmap/reviews/M2-review-14")
W = pathlib.Path("C:/t/iso/work/r2x")
old = json.loads((PKG.parent / "review13/worklist/HUMAN-REVIEW-WORKLIST.json").read_text(encoding="utf-8"))
review = {a["id"]: a for a in json.loads((R / "AI-SOURCE-REVIEW.json").read_text(encoding="utf-8"))["answers"]}
amend = {u["unit"]: u for u in json.loads((W / "labels/r14/AI-REVIEW-AMENDMENT-r14.1.json").read_text(encoding="utf-8"))["units"]}
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def rel(target: pathlib.Path) -> str:
    return os.path.relpath(target, WL).replace("\\", "/")


def ai_block(uid):
    a, m = review[uid], amend[uid]
    return {"status": a["status"], "observations": a["observations"], "disposition": a["disposition"], "effect_in_labels_r14.1": m["effect"],
            "binding": "all images bound" if m["all_images_bound"] else "NOT all bound", "literal_note": m.get("literal_note"),
            "reviewer": a["reviewer"], "reviewer_type": "AI", "not": ["a human signature", "blind to earlier predictions"]}


items = []
s = old["sections"]
for x in s["1_source_findings"]:
    page_img = (PKG.parent / "review07/human-review-packet/pages" / pathlib.Path(x["page_image_packet_v2"]).name)
    items.append({"id": x["id"], "section": "source finding", "kind": x["kind"], "doc": x["doc"], "page": x["page"], "question": x["question"],
                  "page_link": rel(page_img), "crop_links": [rel(PKG.parent / "review13/worklist/crops/findings" / c) for c in x["crops"]],
                  "human_answer": x["answer"], "ai_review": ai_block(x["id"])})
for x in s["2_h06_boq_rows"]:
    items.append({"id": x["id"], "section": "H-06 BOQ row", "kind": x["kind"], "doc": x["doc"], "page": 1, "question": x["question"],
                  "crop_links": [rel(PKG.parent / "review13/worklist/crops" / c) for c in x["crops"]], "human_answer": x["answer"], "ai_review": ai_block(x["id"])})
for n, x in enumerate(s["3_small_batch_unresolved"]):
    uid = {0: "SB/535ffbdabfcf/u1", 1: "SB/0c9737211762/u2", 2: "SB/0c9737211762/u3", 3: "SB/bdce7913eb15/u4", 4: "SB/bdce7913eb15/u5",
           5: "SB/d8ba80a74660/u6", 6: "SB/2472d2cc65c3/u7"}[n]
    assert review[uid]["worklist_entry"]["question"] == x["question"], uid
    items.append({"id": uid, "section": "small-batch label question", "kind": x["kind"], "doc": x["doc"], "page": x["page"], "question": x["question"],
                  "crop_links": [rel(PKG.parent / "review13/worklist/crops/small-batch" / c) for c in x["crops"]], "human_answer": x["answer"], "ai_review": ai_block(uid)})
for n, c in enumerate(s["5_critical_disagreements"]["critical_false_accepts"]):
    uid = f"CRIT/{n + 1}"
    items.append({"id": uid, "section": "critical accept (provisional truth)", "kind": "DECIDE", "doc": c["doc"], "page": c["page"],
                  "question": c["review_note"], "crop_links": [rel(PKG.parent / "review13/worklist/crops/critical" / f) for f in c["crops"]],
                  "human_answer": {"decision": None, "reviewer": None, "date": None}, "ai_review": ai_block(uid)})
for x in s["6_independent_sample"]["items"]:
    uid = f"SAMPLE/{x['rank']}"
    tag = x["unit"].split("/")[0]
    src = pathlib.Path(f"C:/t/r2x/renders/{tag}-p{x['page']}.jpg")
    dst = WL / "pages" / src.name
    shutil.copyfile(src, dst)
    items.append({"id": uid, "section": "independent 20 % sample", "kind": "CHECK", "doc": x["doc"], "page": x["page"], "unit": x["unit"],
                  "question": "Is the label of this unit correct?", "page_link": rel(dst), "human_answer": x["answer"], "ai_review": ai_block(uid)})
assert len(items) == 43
# link check
broken = []
for it in items:
    for link in [it.get("page_link")] + it.get("crop_links", []):
        if link and not (WL / link).resolve().exists():
            broken.append((it["id"], link))
wl = {"status": "Worklist for the review14 package. Human answer fields: EMPTY (no human signature exists). AI review: owner-delegated, "
                "independent, NOT a human signature and NOT blind to earlier predictions -- shown in each item's ai_review block.",
      "sample_rule_disclosure": old["rules"]["independent_sample"], "items": items, "links_checked": sum(bool(i.get("page_link")) + len(i.get("crop_links", [])) for i in items),
      "links_broken": broken}
(WL / "HUMAN-REVIEW-WORKLIST.r14.json").write_text(json.dumps(wl, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
L = ["# Human-review worklist, review14 version (R14-04)", "",
     "**Human answer fields are empty. No human signature exists.** Each item also shows the owner-delegated **AI source review** (Codex). "
     "That review is independent, but it is **not a human signature and not blind** to earlier predictions.", "",
     f"Links: {wl['links_checked']} checked, **{len(broken)} broken**. Page images of findings point at the Review 07 packet "
     "(`../../review07/human-review-packet/pages/`); crops point at the unchanged Review 13 copies; sample pages are copied into `pages/`.", "",
     "**Sample rule (disclosure kept).** The 20 % sample rule was written after the A / B runs began. It is prediction-independent by construction "
     "(a hash of label unit ids), but it was **not** prospectively frozen before predictions and is not a blind audit. For the next batch, the population, "
     "unit, seed, exclusions and selected ids are frozen before any prediction (LABELLING-PLAN.md).", "",
     "| ID | Section | Question | Page | Crops | AI review status | Effect in labels r14.1 |", "|---|---|---|---|---|---|---|"]
for it in items:
    page = f"[page]({it['page_link']})" if it.get("page_link") else "–"
    crops = ", ".join(f"[{n + 1}]({c})" for n, c in enumerate(it.get("crop_links", []))) or "–"
    q = re.sub(r"\s+", " ", it["question"]).replace("|", "/")
    L.append(f"| {it['id']} | {it['section']} | {q} | {page} | {crops} | {it['ai_review']['status']} | {it['ai_review']['effect_in_labels_r14.1']} |")
(WL / "HUMAN-REVIEW-WORKLIST.r14.md").write_text("\n".join(L) + "\n", encoding="utf-8")
# check the markdown's links too
md_links = re.findall(r"\]\(([^)]+)\)", "\n".join(L))
md_broken = [l for l in md_links if not (WL / l).resolve().exists()]
print(len(items), "items;", wl["links_checked"], "json links checked,", len(broken), "broken;", len(md_links), "markdown links,", len(md_broken), "broken")
