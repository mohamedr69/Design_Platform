"""FA Interfaces runs: the publication gate's reasons, and the per-day Retry
review counter (FI-P1 implementation review F1/F5/F8)

Revision ID: f1a3c5e7b9d2
Revises: e8f0a2b4c6d8
Create Date: 2026-10-05 09:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a3c5e7b9d2"
down_revision: Union[str, None] = "e8f0a2b4c6d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("fa_interface_runs", sa.Column("publication_reasons", sa.JSON(), nullable=True))
    op.add_column("fa_interface_runs", sa.Column("review_retries", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("fa_interface_runs", sa.Column("review_retry_day", sa.String(10), nullable=True))


def downgrade() -> None:
    op.drop_column("fa_interface_runs", "review_retry_day")
    op.drop_column("fa_interface_runs", "review_retries")
    op.drop_column("fa_interface_runs", "publication_reasons")
