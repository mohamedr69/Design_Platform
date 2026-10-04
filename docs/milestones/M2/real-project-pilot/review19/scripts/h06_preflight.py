"""H-06 preflight (read-only; no model request): immediately before any dispatch, verify the FROZEN continuation
declaration and its bindings (runner, queue, r16.1 harness, H-06 sheet / extraction / labels, accepted tree), the durable
live ledger (all original-experiment scopes: settled, open reservations, refusals; the H-06 scopes unused), the
exclusive per-document allowance store, the sandbox tags, and the real rolling EP-8430 project-day count NOW. Decides
`dispatch_allowed` for 12 per arm (both arms: 24) without raising or resetting anything. Writes h06/H06-PREFLIGHT-<utc>.json."""
import datetime
import hashlib
import json
import os
import pathlib
import sqlite3
import subprocess
import time

R18 = pathlib.Path("C:/t/iso/work/r2x/ai-pilot-r18")
D = R18 / "CONT-DECLARATION.json"
sha = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
now = time.time()
utc = datetime.datetime.fromtimestamp(now, datetime.timezone.utc)
res = {"at_utc": utc.isoformat(timespec="seconds"), "declaration": str(D).replace("\\", "/")}
res["declaration_sha256"] = sha(D)
decl = json.loads(D.read_text(encoding="utf-8"))
ok_bind = res["declaration_sha256"] == "7b2513b2f5909796835425553e4560c5a8dc9ae7b525ed7f5adf4213a2988de3"
b = {"cont_boq.py": sha(R18 / "cont_boq.py") == decl["code"]["scripts"]["cont_boq.py"],
     "boq_queue.py": sha("C:/t/iso/work/r2x/ai-pilot/boq_queue.py") == decl["code"]["boq_queue_sha256"],
     "r16_harness": all(sha(pathlib.Path("C:/t/iso/work/r2x/r16") / f) == h for f, h in decl["code"]["boq_harness_r16"].items()),
     "h06_sheet": sha(decl["sources"]["boq_sheet"]["staged_path"]) == decl["sources"]["boq_sheet"]["sha256"],
     "h06_extraction": sha(decl["sources"]["boq_extraction_A"]["file"]) == decl["sources"]["boq_extraction_A"]["sha256"],
     "h06_labels": sha(decl["sources"]["h06_labels"]["file"]) == decl["sources"]["h06_labels"]["sha256"],
     "accepted_tree_head": subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip() == decl["code"]["accepted_app"]["commit"],
     "accepted_tree_clean": not subprocess.run(["git", "-C", "C:/t/iso/frozen-r12", "status", "--porcelain"], capture_output=True, text=True).stdout.strip(),
     "boq_arm_binds_accepted_reader": decl["arms"]["S"]["commit"] == "3d5607d99fcebf08ac45f5df937ad615ecc16fb3"}
res["bindings"] = b
L = sqlite3.connect(f"file:{decl['ledger']['file']}?mode=ro", uri=True)
rows = L.execute("select scope, state, count(*) from entries where scope like 'ai-pilot%' group by scope, state").fetchall()
L.close()
settled = sum(n for s, st, n in rows if st == "settled")
open_res = sum(n for s, st, n in rows if st not in ("settled", "refused"))
h06_scopes = {v["scope"] for k, v in decl["ledger"]["scopes"].items() if k.startswith("BOQ")}
res["ledger"] = {"by_scope_state": [list(r) for r in rows], "settled_original_experiment": settled, "open_reservations": open_res,
                 "left_of_150": 150 - settled - open_res, "h06_scope_entries": sum(n for s, st, n in rows if s in h06_scopes),
                 "h06_scopes": sorted(h06_scopes)}
ALLOW = "C:/t/r2x/ledger/ai-pilot-r18-h06-allowance.sqlite"
if os.path.exists(ALLOW):
    A = sqlite3.connect(f"file:{ALLOW}?mode=ro", uri=True)
    res["allowance"] = {"exists": True, "rows": [list(r) for r in A.execute("select scope, profile, calls, escalations from allowance")],
                        "attempts": [list(r) for r in A.execute("select scope, profile, status, calls_at_start, calls_at_end from attempts")]}
    A.close()
else:
    res["allowance"] = {"exists": False, "note": "no H-06 allowance has been opened: both arms have their full 12"}
X = sqlite3.connect("file:C:/t/r2x/ledger/project-day.sqlite?mode=ro", uri=True)
ats = sorted(r[0] for r in X.execute("select at from calls where ep = '8430' and at >= ?", (now - 86400,)))
X.close()
used = len(ats)
fits = lambda n: 60 - used >= n
earliest = lambda n: None if fits(n) else datetime.datetime.fromtimestamp(ats[n - (60 - used) - 1] + 86400, datetime.timezone.utc).isoformat(timespec="seconds")
res["project_day_8430"] = {"used_in_rolling_24h_now": used, "limit": 60, "fits_12_now": fits(12), "fits_24_now": fits(24),
                           "earliest_utc_for_12": earliest(12), "earliest_utc_for_24": earliest(24)}
res["sandboxes_free"] = {t: not (pathlib.Path("C:/t/r2x/runs") / t).exists() for t in ("cont-h06-S", "cont-h06-T")}
res["dispatch_allowed"] = {"S": ok_bind and all(b.values()) and open_res == 0 and res["ledger"]["left_of_150"] >= 24 and res["ledger"]["h06_scope_entries"] == 0
                           and fits(12) and res["sandboxes_free"]["cont-h06-S"],
                           "both_arms": ok_bind and all(b.values()) and open_res == 0 and res["ledger"]["left_of_150"] >= 24 and fits(24)}
d = pathlib.Path("C:/t/iso/work/r2x/review19/h06")
d.mkdir(parents=True, exist_ok=True)
f = d / f"H06-PREFLIGHT-{utc.strftime('%Y%m%dT%H%M%SZ')}.json"
f.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: res[k] for k in ("at_utc", "declaration_sha256", "bindings", "ledger", "allowance", "project_day_8430", "sandboxes_free", "dispatch_allowed")}, indent=1))
print("written", f)
