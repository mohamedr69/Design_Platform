"""ORCH-05.1 sandbox ingestion CHILD: runs inside the frozen baseline tree (C:/t/iso/frozen-r12/backend, B's code at
3d5607d) with every root pointed at the sandbox. It creates the schema (the application's own upgrade_to_head), the
projects, and registers each staged file as a PENDING index row exactly as document_sync.sync's new-file branch does
(document_sync.listing: a stat per file, nothing opened, nothing hashed). It does NOT run the intake gate, the sync job,
the processing job or any reader, and makes no provider call: AI is disabled, the provider is a refusing stub and every
live provider class raises. Usage: sandbox_child_r32.py <sandbox root abs> <projects json abs>"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(sys.argv[1])
PROJECTS = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
assert ROOT.is_absolute() and str(ROOT).replace("\\", "/").startswith("C:/t/r2x/r33-sandbox/"), ROOT
DB = ROOT / "db" / "default.db"
EXPECT_URL = f"sqlite:///{DB.as_posix()}"
assert os.environ.get("DATABASE_URL") == EXPECT_URL, os.environ.get("DATABASE_URL")
assert os.environ.get("AI_ENABLED") == "false"
TREE = pathlib.Path(os.getcwd())
assert TREE.as_posix().lower() == "c:/t/iso/frozen-r12/backend", TREE
sys.path.insert(0, str(TREE))

from app.core.config import get_settings  # noqa: E402

st = get_settings()
assert st.database_url == EXPECT_URL and not st.data_root and not st.ai_enabled, (st.database_url, st.data_root, st.ai_enabled)
assert not st.ai_ledger_path, "no ledger in the ingestion"
for name in ("cache_root", "library_root", "uploads_root"):
    assert str(getattr(st, name) or "").replace("\\", "/").startswith(ROOT.as_posix()), (name, getattr(st, name))

from app.ai import provider as prov  # noqa: E402

blocked = []


def _forbidden(self, request):
    blocked.append(type(self).__name__)
    raise RuntimeError("sandbox ingestion: a provider request is forbidden")


for cls in (prov.ClaudeProvider, prov.OpenAiProvider, prov.ClaudeCodeProvider):
    cls.complete = _forbidden


class Refusing:
    name, ready, status = "refusing", True, "r33 ingestion: refuses every request"

    def complete(self, request):
        blocked.append("Refusing")
        raise RuntimeError("sandbox ingestion: a provider request is forbidden")


prov.set_provider(Refusing())

from app.database import SessionLocal, engine  # noqa: E402
from app.migrations import upgrade_to_head  # noqa: E402
from app.models import Project, ProjectDocument  # noqa: E402
from app.services import document_sync  # noqa: E402
from app.core.timeutils import utc_now  # noqa: E402
from app.models import User  # noqa: E402
from app.seed import seed_default_admin  # noqa: E402

upgrade_to_head(engine)
out = {"tree": str(TREE), "database": str(DB), "index_version": document_sync.INDEX_VERSION, "projects": {}}
with SessionLocal() as db:
    seed_default_admin(db)          # the application's own first user (as its start-up does); projects need a creator
    db.commit()
    admin = db.query(User).order_by(User.id).first()
    for ep, folder in sorted(PROJECTS.items()):
        project = Project(ep_number=ep, project_name=f"EP-{ep}", source_folder_path=folder, created_by_id=admin.id)
        db.add(project)
        db.flush()
        now = utc_now()
        files = document_sync.listing(pathlib.Path(folder))
        for path, relative, size, mtime in files:
            role = document_sync.ROLE_TRANSMITTAL if document_sync.transmittals.is_transmittal(relative) else document_sync.ROLE_DOCUMENT
            db.add(ProjectDocument(project_id=project.id, role=role, path=str(path), relative_path=relative, filename=path.name,
                                   first_seen_at=now, last_seen_at=now, acknowledged=[], findings=[], state=document_sync.PENDING,
                                   size=size, mtime=mtime))
        out["projects"][ep] = {"project_id": project.id, "files": len(files), "folder": folder}
    db.commit()
out["provider_attempts_blocked"] = blocked
assert not blocked, "a provider was reached"
(ROOT / "out" / "INGEST-CHILD.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({k: out[k] for k in ("projects", "index_version")}))
