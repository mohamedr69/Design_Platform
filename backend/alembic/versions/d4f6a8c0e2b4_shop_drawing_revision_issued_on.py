"""shop drawing revisions: the date the drawing says it was issued

The title block's DATE cell (else the latest date of the sheet's revision
history), read by app.services.title_block and carried on the document-control
record as `issued`, is kept on the revision it stands for. Nullable: a sheet
that gives no date, and every revision read before this, has none. Beside
`submitted_at`, never instead of it.

Revision ID: d4f6a8c0e2b4
Revises: b7d9f1a3c5e7
Create Date: 2026-10-05 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4f6a8c0e2b4'
down_revision: Union[str, Sequence[str], None] = 'b7d9f1a3c5e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table('shop_drawing_revisions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('issued_on', sa.Date(), nullable=True))


def downgrade() -> None:
    """Downgrade schema.

    On SQLite the column goes by a table rebuild (batch: a temporary copy,
    then a rename), and Python's sqlite3 runs DDL outside any transaction
    until a data statement opens one. Run first in a downgrade from the head,
    the rebuild's CREATE of `_alembic_tmp_shop_drawing_revisions` was
    committed on its own, so a downgrade that failed further down the chain
    (tests/test_ep_archive_models walks it back to c4d5e6f7a8b9) left that
    empty copy behind after the rollback. A statement that touches no row
    opens the transaction first, and the rebuild is rolled back whole with
    the rest. Harmless elsewhere."""
    op.execute("DELETE FROM shop_drawing_revisions WHERE 1 = 0")
    with op.batch_alter_table('shop_drawing_revisions', schema=None) as batch_op:
        batch_op.drop_column('issued_on')
