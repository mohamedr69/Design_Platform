"""BOQ as per Shop Drawings: the floor-wise quantities, made from the IFC
BOQ and edited by hand; the amplifier and power calculations read it

Revision ID: a3c5e7b9d1f3
Revises: f4b6d8f0a2c4
Create Date: 2026-10-01 21:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3c5e7b9d1f3"
down_revision: Union[str, None] = "f4b6d8f0a2c4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "project_shop_boq",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False, unique=True),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("source", sa.JSON(), nullable=False),
        sa.Column("created_by_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("project_shop_boq")
