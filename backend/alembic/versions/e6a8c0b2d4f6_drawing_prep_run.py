"""Drawings Preparation: what each placing of a drawing's devices did -- the
placement agents, the coordination (columns, coverage), the orchestrator's
review and the gate (project_redesign.run)

Revision ID: e6a8c0b2d4f6
Revises: a2c4e6f8b0d2
Create Date: 2026-10-06 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e6a8c0b2d4f6"
down_revision: Union[str, None] = "a2c4e6f8b0d2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_redesign") as batch:
        batch.add_column(sa.Column("run", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("project_redesign") as batch:
        batch.drop_column("run")
