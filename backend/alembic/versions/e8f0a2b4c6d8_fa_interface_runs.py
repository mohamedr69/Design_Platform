"""FA Interfaces drawing workflow: one row per run, with its manifest, the drawing
agents' and packages' reports, and the Fable orchestrator's review (FI-P1 r2 Part C)

Revision ID: e8f0a2b4c6d8
Revises: d7e9f1a3b5c7
Create Date: 2026-10-04 20:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e8f0a2b4c6d8"
down_revision: Union[str, None] = "d7e9f1a3b5c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "fa_interface_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("manifest", sa.JSON(), nullable=False),
        sa.Column("agent_reports", sa.JSON(), nullable=False),
        sa.Column("package_reports", sa.JSON(), nullable=False),
        sa.Column("review_state", sa.String(24), nullable=False),
        sa.Column("review", sa.JSON(), nullable=False),
        sa.Column("review_inputs", sa.JSON(), nullable=False),
        sa.Column("publication_state", sa.String(24), nullable=False),
        sa.Column("sources_digest", sa.String(64), nullable=True),
        sa.Column("accepted_by_id", sa.Integer(), nullable=True),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
    )
    op.create_index("ix_fa_interface_runs_project_id", "fa_interface_runs", ["project_id"])


def downgrade() -> None:
    op.drop_index("ix_fa_interface_runs_project_id", table_name="fa_interface_runs")
    op.drop_table("fa_interface_runs")
