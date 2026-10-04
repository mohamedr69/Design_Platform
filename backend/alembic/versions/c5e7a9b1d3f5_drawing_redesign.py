"""Drawings Redesign: the accepted review changes placed on the drawing,
and the redesigned copy AutoCAD made

Revision ID: c5e7a9b1d3f5
Revises: b4d6f8a0c2e4
Create Date: 2026-10-02 14:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c5e7a9b1d3f5"
down_revision: Union[str, None] = "b4d6f8a0c2e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_redesign",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("drawing_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="none"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("source_sha256", sa.String(64), nullable=True),
        sa.Column("changes", sa.JSON(), nullable=False),
        sa.Column("symbols", sa.JSON(), nullable=False),
        sa.Column("calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_status", sa.String(16), nullable=False, server_default="none"),
        sa.Column("output_error", sa.Text(), nullable=True),
        sa.Column("output_path", sa.Text(), nullable=True),
        sa.Column("output_relative", sa.Text(), nullable=True),
        sa.Column("output_at", sa.DateTime(), nullable=True),
        sa.Column("output_changes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "drawing_id", name="uq_redesign_drawing"),
    )
    op.create_index("ix_project_redesign_project_id", "project_redesign", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_project_redesign_project_id", table_name="project_redesign")
    op.drop_table("project_redesign")
