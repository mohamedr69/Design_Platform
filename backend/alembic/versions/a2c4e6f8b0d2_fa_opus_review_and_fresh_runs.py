"""FA Interfaces: the Opus finding review's outcomes on the schedule's evidence
(project_fa_interfaces.reviews) and what each run actually did (fa_interface_runs.trace)

Revision ID: a2c4e6f8b0d2
Revises: d4f6a8c0e2b4
Create Date: 2026-10-05 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a2c4e6f8b0d2"
down_revision: Union[str, None] = "d4f6a8c0e2b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_fa_interfaces") as batch:
        batch.add_column(sa.Column("reviews", sa.JSON(), nullable=True))
    with op.batch_alter_table("fa_interface_runs") as batch:
        batch.add_column(sa.Column("trace", sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("fa_interface_runs") as batch:
        batch.drop_column("trace")
    with op.batch_alter_table("project_fa_interfaces") as batch:
        batch.drop_column("reviews")
