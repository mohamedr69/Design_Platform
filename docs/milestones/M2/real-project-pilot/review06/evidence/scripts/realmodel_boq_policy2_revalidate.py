"""Exploration only (exposed data, shaped after seeing the EV1b readings): re-validate the stored AI-EV1b blind BOQ
readings under a stricter deterministic policy -- part compared literally (whitespace ignored); an empty blind quantity
cell leaves the quantity unverified (a component whose count is printed "( n )" in its description has an empty
quantity cell), instead of a conflict. No model call. A candidate for the next frozen policy, not a result claim."""
import collections, json, re
lit = lambda t: re.sub(r"\s+", "", str(t or "").upper())
num = lambda t: re.sub(r"[^0-9]", "", str(t or ""))
r = json.load(open("C:/t/r6/boq-ev1b/out/BOQ-EV1.json", encoding="utf-8"))
out = collections.Counter(); rows = []
for k, s in r["sheets"].items():
    for j in s.get("rows") or []:
        t, b, row = j.get("truth"), j.get("blind"), j["row"]
        if not b or t is None:
            continue
        part_conf = lit(row.get("part_number")) != lit(b.get("part_number")) and bool(row.get("part_number") or b.get("part_number"))
        bq = num(b.get("quantity"))
        state = "conflict" if (part_conf or (bq and bq != num(row.get("quantity")))) else ("validated_part_qty_unverified" if not bq else "validated")
        reader_right = lit(row.get("part_number")) == lit(t.get("part_number")) and num(row.get("quantity")) == num(t.get("quantity"))
        blind_part_right = lit(b.get("part_number")) == lit(t.get("part_number"))
        key = ("accepted" if j.get("accepted_by_reader") else "held") + (":reader_right" if reader_right else ":reader_wrong") + ":" + state
        out[key] += 1
        rows.append({"sheet": k, "reader": [row.get("part_number"), row.get("quantity")], "blind": [b.get("part_number"), b.get("quantity")],
                     "truth": [t.get("part_number"), t.get("quantity")], "state": state, "reader_right": reader_right, "blind_part_right": blind_part_right})
json.dump({"counts": dict(out), "rows": rows}, open("C:/t/iso/work/realmodel/score/boq-ev1b-policy2-revalidation.json", "w", encoding="utf-8"), indent=1)
for k, v in sorted(out.items()):
    print(k, v)
