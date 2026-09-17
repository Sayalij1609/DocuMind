"""
Duplicate result database model.

Stores detected duplicate relationships between
documents. Each row represents a single match pair.

Convention: document_id is the source (newly
checked), matched_document_id is the existing
document it matched against.
"""

from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import UniqueConstraint

from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class DuplicateResultModel(Base):

    __tablename__ = "duplicate_results"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "matched_document_id",
            name=(
                "uq_duplicate_results_pair"
            ),
        ),
        Index(
            "ix_duplicate_results_doc_similarity",
            "document_id",
            "similarity_score",
        ),
    )

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    document_id: Mapped[str] = mapped_column(
        ForeignKey(
            "documents.document_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    matched_document_id: Mapped[str] = mapped_column(
        ForeignKey(
            "documents.document_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    similarity_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    duplicate_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    detected_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    source_document = relationship(
        "Document",
        foreign_keys=[document_id],
    )

    matched_document = relationship(
        "Document",
        foreign_keys=[matched_document_id],
    )
