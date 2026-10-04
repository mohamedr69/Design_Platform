"""Assemble the immutable draft label version r32-labels-draft-1 from drafts/F###.json (step 9). Written once (never
overwritten); binds the selection, source manifest, renders, crop log and conventions by sha256; marks the labels
AI-authored and NOT human-signed; reviewer decisions are absent by construction. Also writes DRAFT-PROJECTION.json: counts of
documents whose draft has a field 'present' with association 'resolved' on some in-scope page -- a PROJECTION of the
drafter's own reading, never a gate count (the gate counts only independently reviewed, resolved documents)."""
import collections
import datetime
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE / "labels" / "R32-LABELS-DRAFT-1.json"
if OUT.exists():
    sys.exit("draft version exists: immutable")
OUT.parent.mkdir(exist_ok=True)
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()  # noqa: E731
docs = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((HERE / "drafts").glob("F*.json"))}
M = {r["pool_id"]: r for r in json.loads((HERE / "SOURCE-MANIFEST.json").read_text(encoding="utf-8"))["files"]}
for pid, d in docs.items():
    d["staged_sha256"] = M[pid]["staged_sha256"]
    d["ep"] = M[pid]["ep"]
out = {"version": "r32-labels-draft-1", "frozen_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "status": "DRAFT: AI-authored (Claude Opus 5.5 coding assistant), NOT human-signed, NOT independently reviewed; reviewer decisions blank",
       "prediction_blind": "no prediction, application output, register, extracted record or model-run evidence exists for these documents or was consulted; file names were not used as evidence",
       "model_requests": 0,
       "bindings": {"FROZEN-SELECTION.json": sha(HERE / "FROZEN-SELECTION.json"), "SOURCE-MANIFEST.json": sha(HERE / "SOURCE-MANIFEST.json"),
                    "RENDERS.json": sha(HERE / "RENDERS.json"), "CROPS.jsonl": sha(HERE / "CROPS.jsonl"), "LABEL-CONVENTIONS-R32.md": sha(HERE / "LABEL-CONVENTIONS-R32.md"),
                    "drafts": {pid: sha(HERE / "drafts" / f"{pid}.json") for pid in docs}},
       "documents": docs}
OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
proj = {f: [] for f in ("identity", "revision", "decision")}
for pid, d in docs.items():
    if d.get("duplicate_of"):
        continue
    for f in proj:
        if any(p.get(f, {}).get("state") == "present" and p[f].get("association") == "resolved" for p in d["pages"].values()):
            proj[f].append(pid)
conf = collections.Counter(d.get("confidence") for d in docs.values() if not d.get("duplicate_of"))
P = {"what": "PROJECTION ONLY: the drafter's own reading; not independently reviewed; NOT a population-gate count",
     "documents_labelled": sum(1 for d in docs.values() if not d.get("duplicate_of")), "byte_identical_duplicates": [p for p, d in docs.items() if d.get("duplicate_of")],
     "draft_confidence": dict(conf), "present_resolved_documents": {f: len(v) for f, v in proj.items()}, "documents": proj,
     "documents_high_confidence_present_resolved": {f: len([p for p in v if docs[p].get("confidence") == "high"]) for f, v in proj.items()},
     "draft_sha256": sha(OUT)}
(HERE / "labels" / "DRAFT-PROJECTION.json").write_text(json.dumps(P, indent=1) + "\n", encoding="utf-8")
print(sha(OUT))
print(json.dumps({k: P[k] for k in ("documents_labelled", "draft_confidence", "present_resolved_documents", "documents_high_confidence_present_resolved")}, indent=1))
