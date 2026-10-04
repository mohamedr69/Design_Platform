"""R14-05: a deterministic WITHIN-COHORT reallocation proposal for the 35-document shortfall -- a proposal only: nothing
is staged, the frozen EXPLORATION-SELECTION.json / EXPLORATION-MANIFEST.json are not changed, and no sealed project is
touched (the pools below are the exploration projects' own frozen replacement orders).

Rule (fixed before any candidate is read):
  * the short slots are taken in the manifest's shortfall order; each keeps its STRATUM;
  * receivers are the exploration projects not taken in full (quota < 90): 16830, 17428, 23323, 26208, 30549, in a
    rotation that advances by one per slot;
  * a slot takes the receiver's next unused candidate of that stratum in the FROZEN rank order (EXPLORATION-SELECTION
    replacements), provided the receiver stays within the 90 cap and its stratum within 45 % of its new quota; else the
    next receiver in the rotation; a slot no receiver can fill in its stratum is reported as unfillable (not re-typed);
  * every candidate is READ (the approved read-only workflow; OneDrive placeholders hydrate) and SHA-256 hashed: it
    must be distinct from all 415 staged documents, the recorded duplicates, the exposed cohorts' hashes and the
    candidates already proposed; an unreadable or duplicate candidate is recorded and the next one is tried.
Output: SHORTFALL-REALLOCATION-PROPOSAL.json (verified candidates, rejects, per-project effect)."""
import collections
import hashlib
import json
import math
import pathlib

W = pathlib.Path("C:/t/iso/work/r2x")
PILOT = pathlib.Path("C:/Users/moham/Desktop/dev/dev/ep-platform/docs/milestones/M2/real-project-pilot")
PREFIX = "\\\\?\\"
sha_f = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
SEL = W / "EXPLORATION-SELECTION.json"
MAN = W / "EXPLORATION-MANIFEST.json"
assert sha_f(SEL) == "4e8190d027444f03a58230357838eb1d0693ebcf9e0d14c236b3a46c1f59db4e"
assert sha_f(MAN) == "ee9df7b5e3e6f0035beec01643435e46f63d7f59eccfb9102d6633bf2b6f97cd"
sel = json.loads(SEL.read_text(encoding="utf-8"))
man = json.loads(MAN.read_text(encoding="utf-8"))
assert all("sealed" not in str(p.get("cohort", "")) for p in sel["projects"])
known = {d["sha256"] for d in man["documents"]} | {d["sha256"] for d in man["duplicates"]} | {b["sha256"] for b in man["boq_candidates"] if b.get("sha256")}
for f in ("FROZEN-SAMPLE.json", "FROZEN-BOQ-SET.json", "review05/holdout/HOLDOUT-SAMPLE.json", "review05/holdout/HOLDOUT-BOQ-SET.json"):
    d = json.loads((PILOT / f).read_text(encoding="utf-8"))
    known |= {x["sha256"] for x in (d.get("documents") or d.get("sheets") or []) if x.get("sha256")}
used_keys = {d["doc_key"] for d in man["documents"]} | {d["doc_key"] for d in man["duplicates"]} | {d["doc_key"] for d in man["unreadable"]}
pools = collections.defaultdict(list)
for r in sorted(sel["replacements"], key=lambda r: (r["ep"], r["stratum"], r["rank_in_stratum"])):
    if r["doc_key"] not in used_keys:
        pools[(r["ep"], r["stratum"])].append(r)
receivers = sorted(p["ep"] for p in sel["projects"] if p["quota"] < sel["cap_per_project"])
count = collections.Counter(d["ep"] for d in man["documents"])
strat = collections.Counter((d["ep"], d["stratum"]) for d in man["documents"])
proposal, rejects, unfillable = [], [], []
turn = 0
for slot in man["shortfall"]:
    s = slot["stratum"]
    placed = False
    for k in range(len(receivers)):
        ep = receivers[(turn + k) % len(receivers)]
        new_quota = count[ep] + 1
        if new_quota > sel["cap_per_project"] or strat[(ep, s)] + 1 > math.floor(sel["cap_per_stratum"] * new_quota):
            continue
        while pools[(ep, s)]:
            c = pools[(ep, s)].pop(0)
            try:
                data = open(PREFIX + str(pathlib.Path(c["folder"]) / c["relative_path"]), "rb").read()
            except OSError as exc:
                rejects.append({"doc_key": c["doc_key"], "reason": f"unreadable: {type(exc).__name__}"})
                continue
            h = hashlib.sha256(data).hexdigest()
            if h in known:
                rejects.append({"doc_key": c["doc_key"], "reason": "duplicate content", "sha256": h})
                continue
            known.add(h)
            proposal.append({"for_short_slot": {"ep": slot["ep"], "stratum": s, "was": slot["for"]}, "receiver": ep, "doc_key": c["doc_key"], "stratum": s,
                             "rank_in_stratum": c["rank_in_stratum"], "extension": c["extension"], "sha256": h, "bytes": len(data),
                             "hydrated": bool(c.get("placeholder_before"))})
            count[ep] += 1
            strat[(ep, s)] += 1
            placed = True
            break
        if placed:
            break
    if not placed:
        unfillable.append(slot)
    turn += 1
out = {"status": "PROPOSAL ONLY -- not executed; the frozen selection and manifest are unchanged; no sealed project involved",
       "rule": __doc__, "selection_sha256": sha_f(SEL), "manifest_sha256": sha_f(MAN), "short_slots": len(man["shortfall"]),
       "verified_distinct_candidates": len(proposal), "unfillable_slots": unfillable, "rejects": rejects, "candidates": proposal,
       "effect": {"distinct_documents_if_adopted": len(man["documents"]) + len(proposal),
                  "per_project_after": {ep: count[ep] for ep in sorted(count)},
                  "per_receiver_added": dict(collections.Counter(p["receiver"] for p in proposal))}}
(W / "r14/SHORTFALL-REALLOCATION-PROPOSAL.json").write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("slots", out["short_slots"], "| verified distinct", len(proposal), "| unfillable", len(unfillable), "| rejects", len(rejects))
print(out["effect"])
print(collections.Counter(p["stratum"] for p in proposal), collections.Counter(u["stratum"] for u in unfillable))
