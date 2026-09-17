"""
Extraction result database model.

Stores the structured extraction output for each
document. The extracted_fields column holds the full
per-field results as JSON (value, confidence, source,
bbox for each field).
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import JSON
from sqlalchemy import String
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class ExtractionResultModel(Base):

    __tablename__ = "extraction_results"

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
        unique=True,
        index=True,
    )

    document_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    invoice_number: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        default=None,
    )

    vendor: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        default=None,
    )

    total_amount: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
        index=True,
        default=None,
    )

    extracted_fields: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    extraction_method: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="unknown",
    )

    extraction_version: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="1.0.0",
    )

    extracted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    document = relationship(
        "Document",
        back_populates="extraction",
    )
