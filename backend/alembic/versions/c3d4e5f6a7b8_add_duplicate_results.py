"""Add duplicate_results table.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-09-17 22:27:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "duplicate_results",
        sa.Column(
            "id",
            sa.Integer(),
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "document_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "matched_document_id",
            sa.String(length=36),
            nullable=False,
        ),
        sa.Column(
            "similarity_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "duplicate_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "detected_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.document_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["matched_document_id"],
            ["documents.document_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            "matched_document_id",
            name="uq_duplicate_results_pair",
        ),
    )


def downgrade() -> None:

    op.drop_table("duplicate_results")
