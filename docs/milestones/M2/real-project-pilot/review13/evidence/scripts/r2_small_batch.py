"""Round 2: freeze the small matched batch (persistence / accounting check) from the staging manifest, seeded, before
any label or prediction: one PDF per exploration project (strata not yet represented preferred), one Word transmittal,
one further PDF; plus the exposed EP-8430 BOQ sheet (H-06, labelled in Review 05's holdout BOQ labels)."""
import hashlib
import json
import pathlib
import random

MAN = pathlib.Path("C:/t/iso/work/r2x/EXPLORATION-MANIFEST.json")
man = json.loads(MAN.read_text(encoding="utf-8"))
rng = random.Random("m2-round2-small-batch-2026-09-29")
docs = sorted(man["documents"], key=lambda d: d["doc_key"])
pdfs = [d for d in docs if d["extension"] == ".pdf"]
chosen, seen_strata = [], set()
for ep in sorted({d["ep"] for d in pdfs}):
    pool = [d for d in pdfs if d["ep"] == ep]
    rng.shuffle(pool)
    pool.sort(key=lambda d: d["stratum"] in seen_strata)      # stable: unrepresented strata first, shuffled order within
    chosen.append(pool[0])
    seen_strata.add(pool[0]["stratum"])
words = [d for d in docs if d["extension"] != ".pdf"]
rng.shuffle(words)
chosen.append(words[0])
rest = [d for d in pdfs if d not in chosen]
rng.shuffle(rest)
chosen.append(rest[0])
batch = {"seed": "m2-round2-small-batch-2026-09-29", "manifest_sha256": hashlib.sha256(MAN.read_bytes()).hexdigest(),
         "documents": [{k: d[k] for k in ("doc_key", "ep", "stratum", "extension", "sha256", "staged_path", "pages", "scan_like") if k in d} for d in chosen],
         "boq_exposed": [{"doc_key": "EP-8430/EP-8430 Commercial/EP-8430 PAVA Revised Design Sheet - 23.10.2017.pdf", "ep": "8430", "cohort": "regression / exposed (R5 holdout)",
                          "labels": "review05/holdout/HOLDOUT-BOQ-LABELS.json", "purpose": "H-06"}]}
out = pathlib.Path("C:/t/iso/work/r2x/SMALL-BATCH.json")
out.write_text(json.dumps(batch, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
for d in batch["documents"]:
    print(d["ep"], d["stratum"], d.get("pages"), "scan" if d.get("scan_like") else "", d["doc_key"][-80:])
print("small batch sha256", hashlib.sha256(out.read_bytes()).hexdigest())
