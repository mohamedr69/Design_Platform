"""Document attribution, conflict records and the stage record (M6, ORCH-043)

Adds to document_classifications, all additive:
  attribution            whose document this is (OUR_SCOPE / LIKELY_OUR_SCOPE /
                         RELATED_EXTERNAL / REFERENCE_ONLY / UNKNOWN), a field of
                         its own beside the type -- never a stage string. Every
                         existing row reads UNKNOWN (neither in nor out of scope).
  attribution_basis      the evidence the rules weighed (JSON)
  attribution_version    the attribution rules' version (NULL: never attributed)
  attribution_conflict   attribution evidence that disagrees, kept (JSON)
  input_fingerprint, model, prompt_version, page_chars, producing_job_id,
  stage_status           the stage record a later registry (M7) can adopt;
                         nullable, NULL on every existing row

and a table document_classification_conflicts: an automated answer that
disagrees with an engineer-confirmed one is recorded there, never applied
(M3 P-02). Columns are added with ADD COLUMN, not a batch copy, so the
partial unique index (one current row per document) is left as it is.

Revision ID: c6d8e0f2a4b6
Revises: e6a8c0b2d4f6
Create Date: 2026-10-08 12:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c6d8e0f2a4b6"
down_revision: Union[str, None] = "e6a8c0b2d4f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _columns() -> tuple:
    return (
        sa.Column("attribution", sa.String(length=24), nullable=False, server_default="UNKNOWN"),
        sa.Column("attribution_basis", sa.JSON(), nullable=True),
        sa.Column("attribution_version", sa.String(length=40), nullable=True),
        sa.Column("attribution_conflict", sa.JSON(), nullable=True),
        sa.Column("input_fingerprint", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("prompt_version", sa.String(length=80), nullable=True),
        sa.Column("page_chars", sa.Integer(), nullable=True),
        sa.Column("producing_job_id", sa.Integer(), nullable=True),
        sa.Column("stage_status", sa.String(length=16), nullable=True),
    )


def upgrade() -> None:
    for column in _columns():
        op.add_column("document_classifications", column)
    op.create_table(
        "document_classification_conflicts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id"), nullable=False),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("project_documents.id"), nullable=False),
        sa.Column("confirmed_classification_id", sa.Integer(), sa.ForeignKey("document_classifications.id"), nullable=False),
        sa.Column("proposed_classification_id", sa.Integer(), sa.ForeignKey("document_classifications.id"), nullable=True),
        sa.Column("field", sa.String(length=24), nullable=False),
        sa.Column("confirmed_value", sa.String(length=64), nullable=True),
        sa.Column("proposed_value", sa.String(length=64), nullable=True),
        sa.Column("source", sa.String(length=16), nullable=False),
        sa.Column("version", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(), nullable=False),
        sa.Column("seen_count", sa.Integer(), nullable=False, server_default="1"),
    )
    op.create_index("ix_document_classification_conflicts_project_id", "document_classification_conflicts", ["project_id"])
    op.create_index("ix_document_classification_conflicts_document_id", "document_classification_conflicts", ["document_id"])
    op.create_index("ix_document_classification_conflicts_confirmed_classification_id", "document_classification_conflicts",
                    ["confirmed_classification_id"])


def downgrade() -> None:
    op.drop_index("ix_document_classification_conflicts_confirmed_classification_id",
                  table_name="document_classification_conflicts")
    op.drop_index("ix_document_classification_conflicts_document_id", table_name="document_classification_conflicts")
    op.drop_index("ix_document_classification_conflicts_project_id", table_name="document_classification_conflicts")
    op.drop_table("document_classification_conflicts")
    # The partial unique index is dropped around the batch copy and made again as it was.
    op.drop_index("uq_document_classifications_one_current", table_name="document_classifications")
    with op.batch_alter_table("document_classifications") as batch:
        for column in reversed(_columns()):
            batch.drop_column(column.name)
    op.create_index("uq_document_classifications_one_current", "document_classifications", ["document_id"], unique=True,
                    sqlite_where=sa.text("superseded_at IS NULL"), postgresql_where=sa.text("superseded_at IS NULL"))
