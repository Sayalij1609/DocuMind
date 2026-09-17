"""Production database design: Users, Classifications, Reviews, Model Metadata, and optimized indexes.

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=True),
        sa.Column(
            "role",
            sa.String(length=50),
            server_default="user",
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_is_active", "users", ["is_active"])

    # 2. Add user_id and performance indexes to documents
    with op.batch_alter_table("documents") as batch_op:
        batch_op.add_column(
            sa.Column("user_id", sa.String(length=36), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_documents_user_id",
            "users",
            ["user_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_documents_user_id", ["user_id"])
        batch_op.create_index("ix_documents_status", ["status"])
        batch_op.create_index("ix_documents_document_type", ["document_type"])
        batch_op.create_index("ix_documents_created_at", ["created_at"])
        batch_op.create_index(
            "ix_documents_type_status",
            ["document_type", "status"],
        )

    # 3. Add search columns and indexes to extraction_results
    with op.batch_alter_table("extraction_results") as batch_op:
        batch_op.add_column(
            sa.Column("invoice_number", sa.String(length=100), nullable=True)
        )
        batch_op.add_column(
            sa.Column("vendor", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("total_amount", sa.Float(), nullable=True)
        )
        batch_op.create_index(
            "ix_extraction_results_invoice_number",
            ["invoice_number"],
        )
        batch_op.create_index(
            "ix_extraction_results_vendor",
            ["vendor"],
        )
        batch_op.create_index(
            "ix_extraction_results_total_amount",
            ["total_amount"],
        )

    # 4. Create classification_results table
    op.create_table(
        "classification_results",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("document_type", sa.String(length=50), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "classifier_name",
            sa.String(length=100),
            server_default="sgd_tfidf",
            nullable=False,
        ),
        sa.Column("probabilities", sa.JSON(), nullable=True),
        sa.Column("classified_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.document_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id",
            name="uq_classification_results_document_id",
        ),
    )
    op.create_index(
        "ix_classification_results_document_id",
        "classification_results",
        ["document_id"],
    )
    op.create_index(
        "ix_classification_results_document_type",
        "classification_results",
        ["document_type"],
    )

    # 5. Create document_reviews table
    op.create_table(
        "document_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("reviewer_id", sa.String(length=36), nullable=True),
        sa.Column(
            "review_status",
            sa.String(length=30),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("corrections", sa.JSON(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.document_id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_document_reviews_document_id",
        "document_reviews",
        ["document_id"],
    )
    op.create_index(
        "ix_document_reviews_reviewer_id",
        "document_reviews",
        ["reviewer_id"],
    )
    op.create_index(
        "ix_document_reviews_review_status",
        "document_reviews",
        ["review_status"],
    )

    # 6. Create model_metadata table
    op.create_table(
        "model_metadata",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("model_type", sa.String(length=50), nullable=False),
        sa.Column("artifact_path", sa.String(length=500), nullable=False),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("metrics", sa.JSON(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("trained_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "name",
            "version",
            name="uq_model_metadata_name_version",
        ),
    )
    op.create_index(
        "ix_model_metadata_model_type",
        "model_metadata",
        ["model_type"],
    )
    op.create_index(
        "ix_model_metadata_is_active",
        "model_metadata",
        ["is_active"],
    )

    # 7. Add composite index to duplicate_results
    with op.batch_alter_table("duplicate_results") as batch_op:
        batch_op.create_index(
            "ix_duplicate_results_doc_similarity",
            ["document_id", "similarity_score"],
        )


def downgrade() -> None:
    # 1. Drop composite index on duplicate_results
    with op.batch_alter_table("duplicate_results") as batch_op:
        batch_op.drop_index("ix_duplicate_results_doc_similarity")

    # 2. Drop model_metadata
    op.drop_index("ix_model_metadata_is_active", table_name="model_metadata")
    op.drop_index("ix_model_metadata_model_type", table_name="model_metadata")
    op.drop_table("model_metadata")

    # 3. Drop document_reviews
    op.drop_index("ix_document_reviews_review_status", table_name="document_reviews")
    op.drop_index("ix_document_reviews_reviewer_id", table_name="document_reviews")
    op.drop_index("ix_document_reviews_document_id", table_name="document_reviews")
    op.drop_table("document_reviews")

    # 4. Drop classification_results
    op.drop_index(
        "ix_classification_results_document_type",
        table_name="classification_results",
    )
    op.drop_index(
        "ix_classification_results_document_id",
        table_name="classification_results",
    )
    op.drop_table("classification_results")

    # 5. Drop search columns and indexes from extraction_results
    with op.batch_alter_table("extraction_results") as batch_op:
        batch_op.drop_index("ix_extraction_results_total_amount")
        batch_op.drop_index("ix_extraction_results_vendor")
        batch_op.drop_index("ix_extraction_results_invoice_number")
        batch_op.drop_column("total_amount")
        batch_op.drop_column("vendor")
        batch_op.drop_column("invoice_number")

    # 6. Drop indexes and user_id from documents
    with op.batch_alter_table("documents") as batch_op:
        batch_op.drop_index("ix_documents_type_status")
        batch_op.drop_index("ix_documents_created_at")
        batch_op.drop_index("ix_documents_document_type")
        batch_op.drop_index("ix_documents_status")
        batch_op.drop_index("ix_documents_user_id")
        batch_op.drop_constraint("fk_documents_user_id", type_="foreignkey")
        batch_op.drop_column("user_id")

    # 7. Drop users table
    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
