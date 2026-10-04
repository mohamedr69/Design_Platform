"""Review rulings: the engineers' not-needed and confirmed answers to the
Drawings Review, given to the model with the rules on every later review

Revision ID: f4b6d8f0a2c4
Revises: e3a5c7e9f1b3
Create Date: 2026-10-01 19:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f4b6d8f0a2c4"
down_revision: Union[str, None] = "e3a5c7e9f1b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "review_rulings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("drawing_id", sa.Integer(), nullable=False),
        sa.Column("finding_id", sa.String(40), nullable=False),
        sa.Column("decision", sa.String(16), nullable=False),
        sa.Column("room", sa.String(160), nullable=False, server_default=""),
        sa.Column("room_key", sa.String(80), nullable=False, server_default=""),
        sa.Column("room_type", sa.String(80), nullable=False, server_default=""),
        sa.Column("system", sa.String(40), nullable=False),
        sa.Column("action", sa.String(16), nullable=False),
        sa.Column("device", sa.String(120), nullable=False, server_default=""),
        sa.Column("instruction", sa.String(300), nullable=False, server_default=""),
        sa.Column("note", sa.String(500), nullable=False, server_default=""),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("project_id", "drawing_id", "finding_id", name="uq_review_ruling_finding"),
    )
    op.create_index("ix_review_rulings_project_id", "review_rulings", ["project_id"])
    op.create_index("ix_review_rulings_room_key", "review_rulings", ["room_key"])


def downgrade() -> None:
    op.drop_index("ix_review_rulings_room_key", table_name="review_rulings")
    op.drop_index("ix_review_rulings_project_id", table_name="review_rulings")
    op.drop_table("review_rulings")
