"""APS cabinets: the floor each is installed on, as the engineer decides

Revision ID: d2f4b6c8e0a2
Revises: c1e3a5b7d9f1
Create Date: 2026-10-01 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "d2f4b6c8e0a2"
down_revision: Union[str, None] = "c1e3a5b7d9f1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("project_amplifier_design") as batch:
        batch.add_column(sa.Column("locations", sa.JSON(), nullable=False, server_default="{}"))


def downgrade() -> None:
    with op.batch_alter_table("project_amplifier_design") as batch:
        batch.drop_column("locations")
