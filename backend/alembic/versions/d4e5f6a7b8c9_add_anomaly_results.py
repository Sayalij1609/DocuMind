"""Add anomaly_results table.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-09-17 22:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "anomaly_results",
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
            "is_anomaly",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "anomaly_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "decision_function_score",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "features",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "model_version",
            sa.String(length=50),
            nullable=False,
            server_default="isolation_forest_v1",
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
            name="uq_anomaly_results_document_id",
        ),
    )

    op.create_index(
        "ix_anomaly_results_document_id",
        "anomaly_results",
        ["document_id"],
    )
    op.create_index(
        "ix_anomaly_results_is_anomaly",
        "anomaly_results",
        ["is_anomaly"],
    )


def downgrade() -> None:

    op.drop_index(
        "ix_anomaly_results_is_anomaly",
        table_name="anomaly_results",
    )
    op.drop_index(
        "ix_anomaly_results_document_id",
        table_name="anomaly_results",
    )
    op.drop_table("anomaly_results")
