"""Fire Alarm Interface Schedule: the equipment of the other trades the fire
alarm system monitors or controls, per project

One row per project: what each IFC drawing read showed (`sources`), what
the engineer decided (`decisions`) and the items they added (`manual`).
The schedule is built from these when read, never stored.

Revision ID: c1e3a5b7d9f1
Revises: b8d0f2a4c6e8
Create Date: 2026-09-30 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c1e3a5b7d9f1"
down_revision: Union[str, None] = "b8d0f2a4c6e8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_fa_interfaces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sources", sa.JSON(), nullable=False),
        sa.Column("decisions", sa.JSON(), nullable=False),
        sa.Column("manual", sa.JSON(), nullable=False),
        sa.Column("scanned_at", sa.DateTime(), nullable=True),
        sa.Column("scanned_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", name="uq_project_fa_interfaces"),
    )
    op.create_index("ix_project_fa_interfaces_project_id", "project_fa_interfaces", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_fa_interfaces_project_id", table_name="project_fa_interfaces")
    op.drop_table("project_fa_interfaces")
