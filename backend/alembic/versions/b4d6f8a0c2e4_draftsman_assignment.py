"""Drawings > Assign Draftsman: what the draftsman is handed, what the
engineer skipped or marked ready, and the log of assignments

Revision ID: b4d6f8a0c2e4
Revises: a3c5e7b9d1f3
Create Date: 2026-10-02 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b4d6f8a0c2e4"
down_revision: Union[str, None] = "a3c5e7b9d1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_draftsman_assignment",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False, unique=True),
        sa.Column("skipped", sa.JSON(), nullable=False),
        sa.Column("ready", sa.JSON(), nullable=False),
        sa.Column("draftsman_name", sa.String(120), nullable=True),
        sa.Column("draftsman_email", sa.String(200), nullable=True),
        sa.Column("log", sa.JSON(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("project_draftsman_assignment")
