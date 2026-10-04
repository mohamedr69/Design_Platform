"""Review 07 (E): dry-run impact of the incomplete / uncertain reference guard, read only.
BEFORE = the parse .8 sandbox (no guard), AFTER = the parse .9 sandbox (guard), same staged sources. Reported per
project: business rows (shop drawings, submittals) only on one side, document mirrors that changed, and the case list
(`document_sync.uncertain_reference_cases`) -- each case with whether an existing business row carries the uncertain
key. Also: the case list the guard would give over the BEFORE state (existing rows it would preserve)."""
import json
import os
import sqlite3
import sys

PROFILE = sys.argv[1] if len(sys.argv) > 1 else "default"
BEFORE = rf"C:\t\r6\det-pilot\db\{PROFILE}.db"
AFTER = rf"C:\t\r6\det9-pilot\db\{PROFILE}.db"


def snapshot(path):
    con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    out = {"drawings": {}, "submittals": {}, "mirrors": {}}
    for r in con.execute("select p.ep_number, d.drawing_reference, d.active from project_shop_drawings d join projects p on p.id = d.project_id"):
        out["drawings"].setdefault(r["ep_number"], set()).add(r["drawing_reference"])
    for r in con.execute("select p.ep_number, s.reference from project_submittals s join projects p on p.id = s.project_id"):
        out["submittals"].setdefault(r["ep_number"], set()).add(r["reference"])
    for r in con.execute("select p.ep_number, d.relative_path, d.reference, d.revision, d.status from project_documents d join projects p on p.id = d.project_id"):
        out["mirrors"][f"EP-{r['ep_number']}/{r['relative_path']}"] = (r["reference"], r["revision"], r["status"])
    con.close()
    return out


before, after = snapshot(BEFORE), snapshot(AFTER)
diff = {"profile": PROFILE, "business_rows": {}, "mirror_changes": []}
for kind in ("drawings", "submittals"):
    for ep in sorted(set(before[kind]) | set(after[kind])):
        b, a = before[kind].get(ep, set()), after[kind].get(ep, set())
        if b != a:
            diff["business_rows"].setdefault(ep, {})[kind] = {"only_before": sorted(b - a), "only_after": sorted(a - b)}
for doc in sorted(set(before["mirrors"]) | set(after["mirrors"])):
    if before["mirrors"].get(doc) != after["mirrors"].get(doc):
        diff["mirror_changes"].append({"doc": doc, "before": before["mirrors"].get(doc), "after": after["mirrors"].get(doc)})

# the application's own case list, over each state
sys.path.insert(0, r"C:\t\iso\ep-platform\backend")
os.chdir(r"C:\t\iso\ep-platform\backend")
cases = {}
for label, path in (("after", AFTER), ("before_state_if_guarded", BEFORE)):
    os.environ["DATABASE_URL"] = "sqlite:///" + path.replace("\\", "/")
    for mod in [m for m in list(sys.modules) if m.startswith("app")]:
        del sys.modules[mod]
    from app.core.config import get_settings
    get_settings.cache_clear() if hasattr(get_settings, "cache_clear") else None
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from app.models import Project
    from app.services import document_sync
    engine = create_engine(f"sqlite:///file:{path.replace(chr(92), '/')}?mode=ro&uri=true")
    with Session(engine) as db:
        cases[label] = {p.ep_number: document_sync.uncertain_reference_cases(db, p) for p in db.query(Project)}
        cases[label] = {k: v for k, v in cases[label].items() if v}
diff["uncertain_reference_cases"] = cases
json.dump(diff, open(rf"C:\t\iso\work\r7\GUARD-DRY-RUN-{PROFILE}.json", "w", encoding="utf-8"), indent=1, default=str)
print(json.dumps({"business_rows": diff["business_rows"], "mirror_changes": diff["mirror_changes"][:10],
                  "n_mirror_changes": len(diff["mirror_changes"]),
                  "cases_after": {k: [(c["path"][-40:], c["page"], c["reference_literal"], c["existing_business_row"]) for c in v] for k, v in cases["after"].items()},
                  "cases_before_if_guarded": {k: [(c["path"][-40:], c["reference_literal"], c["existing_business_row"]) for c in v] for k, v in cases["before_state_if_guarded"].items()}},
                 indent=1, default=str))
