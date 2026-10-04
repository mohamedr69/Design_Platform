"""FA Interface Schedule: the published schedule's evidence and the write generation
(FI-P1 r3 Stage 0.1)

The published schedule is stored as the readings it was built from, never as
its output, so the engineer's answers apply to it live. It is seeded once,
here, from the readings each project saved before this revision: basis
"seeded", generation left at 0. Projects created later start unpublished.

Revision ID: d7e9f1a3b5c7
Revises: c5e7a9b1d3f5
Create Date: 2026-10-04 18:00:00.000000

"""
import hashlib
import json
from datetime import datetime, timezone
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d7e9f1a3b5c7"
down_revision: Union[str, None] = "c5e7a9b1d3f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _digest(read: list[dict]) -> str:
    # the same identity as app.interfaces.evidence.digest, frozen here
    rows = sorted(
        [e.get("kind") or "", e.get("discipline") or "", e.get("relative_path") or "", e.get("sha256") or "",
         str((e.get("result") or {}).get("scan_version") or ""), str((e.get("result") or {}).get("schedule_version") or ""),
         str((e.get("visual") or {}).get("version") or ""), str((e.get("visual") or {}).get("status") or "")]
        for e in read if e.get("status") == "read")
    return hashlib.sha256(json.dumps(rows).encode()).hexdigest()


def upgrade() -> None:
    with op.batch_alter_table("project_fa_interfaces") as batch:
        batch.add_column(sa.Column("published", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("published_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("published_basis", sa.String(24), nullable=True))
        batch.add_column(sa.Column("published_by_id", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("published_reason", sa.Text(), nullable=True))
        batch.add_column(sa.Column("generation", sa.Integer(), nullable=False, server_default="0"))

    bind = op.get_bind()
    table = sa.table("project_fa_interfaces", sa.column("id", sa.Integer), sa.column("sources", sa.JSON),
                     sa.column("scanned_at", sa.DateTime), sa.column("published", sa.JSON),
                     sa.column("published_at", sa.DateTime), sa.column("published_basis", sa.String))
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for row_id, sources, scanned_at in bind.execute(sa.select(table.c.id, table.c.sources, table.c.scanned_at)).all():
        if isinstance(sources, str):
            sources = json.loads(sources)
        read = [e for e in sources or [] if isinstance(e, dict) and e.get("status") == "read"]
        if not read:
            continue
        snapshot = {"sources": read, "sources_digest": _digest(read), "job_id": None}
        bind.execute(table.update().where(table.c.id == row_id, table.c.published.is_(None)).values(
            published=snapshot, published_at=scanned_at or now, published_basis="seeded"))


def downgrade() -> None:
    with op.batch_alter_table("project_fa_interfaces") as batch:
        batch.drop_column("generation")
        batch.drop_column("published_reason")
        batch.drop_column("published_by_id")
        batch.drop_column("published_basis")
        batch.drop_column("published_at")
        batch.drop_column("published")
