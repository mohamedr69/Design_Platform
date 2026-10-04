"""Merge the G and Desktop migration lines

The G line (FA Interfaces, Drawings Review / Redesign, Draftsman, shop-drawing
BOQ, APS cabinet floors -- G's live database is at c5e7a9b1d3f5 -- then FI-P1's
d7e9f1a3b5c7, e8f0a2b4c6d8 and f1a3c5e7b9d2, the G line's head) and the Desktop
line (document classifications, document processing jobs, Design Sheet read
state, BOQ corrections; head a5b6c7d8e9f0) branched after 59 shared revisions
and touch different tables. This revision only joins the two heads: no schema
change. A G database (c5e7a9b1d3f5) and a Desktop database (a5b6c7d8e9f0) both
upgrade through it to the same schema.

Revision ID: b7d9f1a3c5e7
Revises: f1a3c5e7b9d2, a5b6c7d8e9f0
Create Date: 2026-10-05 01:00:00.000000

"""
from typing import Sequence, Union

revision: str = "b7d9f1a3c5e7"
down_revision: Union[str, Sequence[str], None] = ("f1a3c5e7b9d2", "a5b6c7d8e9f0")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
