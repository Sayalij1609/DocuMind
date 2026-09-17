"""Add extraction_results table.

Revision ID: a1b2c3d4e5f6
Revises: cf538797a342
Create Date: 2026-09-09 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "cf538797a342"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "extraction_results",
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
            "document_type",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "extracted_fields",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "extraction_method",
            sa.String(length=50),
            nullable=False,
            server_default="unknown",
        ),
        sa.Column(
            "extraction_version",
            sa.String(length=20),
            nullable=False,
            server_default="1.0.0",
        ),
        sa.Column(
            "extracted_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.document_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            name="uq_extraction_results_document_id",
        ),
    )


def downgrade() -> None:

    op.drop_table("extraction_results")
