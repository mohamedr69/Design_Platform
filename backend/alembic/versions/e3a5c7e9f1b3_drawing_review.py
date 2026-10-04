"""Drawings Review: the FA IFC drawing's rooms reviewed by the model against
the company's coverage rules, and the engineer's word on each finding

Revision ID: e3a5c7e9f1b3
Revises: d2f4b6c8e0a2
Create Date: 2026-10-01 16:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e3a5c7e9f1b3"
down_revision: Union[str, None] = "d2f4b6c8e0a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_drawing_reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("drawing_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="idle"),
        sa.Column("source_sha256", sa.String(64), nullable=True),
        sa.Column("pdf_path", sa.Text(), nullable=True),
        sa.Column("model", sa.String(64), nullable=True),
        sa.Column("sheets", sa.JSON(), nullable=False),
        sa.Column("decisions", sa.JSON(), nullable=False),
        sa.Column("calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "drawing_id", name="uq_project_drawing_review"),
    )
    op.create_index("ix_project_drawing_reviews_project_id", "project_drawing_reviews", ["project_id"])
    op.create_index("ix_project_drawing_reviews_drawing_id", "project_drawing_reviews", ["drawing_id"])


def downgrade() -> None:
    op.drop_index("ix_project_drawing_reviews_drawing_id", table_name="project_drawing_reviews")
    op.drop_index("ix_project_drawing_reviews_project_id", table_name="project_drawing_reviews")
    op.drop_table("project_drawing_reviews")
