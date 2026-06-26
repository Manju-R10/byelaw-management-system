"""Widen byelaw_clause.clause_text to MEDIUMTEXT

A single extracted clause can exceed the 64 KB limit of MySQL TEXT when long
passages lie between detected headings (observed with large Malayalam bye-laws).
MEDIUMTEXT raises the ceiling to 16 MB.

Revision ID: 2b1c3d4e5f6a
Revises: 1da458f20ad2
Create Date: 2026-06-26
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision: str = "2b1c3d4e5f6a"
down_revision: Union[str, Sequence[str], None] = "1da458f20ad2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "byelaw_clause",
        "clause_text",
        existing_type=mysql.TEXT(),
        type_=mysql.MEDIUMTEXT(),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "byelaw_clause",
        "clause_text",
        existing_type=mysql.MEDIUMTEXT(),
        type_=mysql.TEXT(),
        existing_nullable=False,
    )
