"""Add composite index (master_id, display_order) on byelaw_clause

Supports fast, correctly ordered reconstruction of a bye-law's clauses on
view/export (FRS FR-06/FR-10 and Relationship Summary). The FULLTEXT index
ft_clause_text already exists from the initial migration and is now also declared
on the model, so no DDL is required for it here.

Revision ID: 3c2d4e6f8a1b
Revises: 2b1c3d4e5f6a
Create Date: 2026-06-26
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "3c2d4e6f8a1b"
down_revision: Union[str, Sequence[str], None] = "2b1c3d4e5f6a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_clause_master_display",
        "byelaw_clause",
        ["master_id", "display_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_clause_master_display", table_name="byelaw_clause")
